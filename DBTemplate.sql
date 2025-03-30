SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE `communications` (
  `CommunicationID` int(11) NOT NULL AUTO_INCREMENT,
  `JobID` int(11) DEFAULT NULL,
  `CommunicationType` varchar(50) DEFAULT NULL,
  `DateTime` datetime DEFAULT current_timestamp(),
  `Note` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`CommunicationID`),
  KEY `JobID` (`JobID`),
  CONSTRAINT `communications_ibfk_1` FOREIGN KEY (`JobID`) REFERENCES `jobs` (`JobID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;


CREATE TABLE `costs` (
  `CostID` int(11) NOT NULL AUTO_INCREMENT,
  `JobID` int(11) DEFAULT NULL,
  `CostType` varchar(50) DEFAULT NULL,
  `Amount` decimal(10,2) DEFAULT NULL,
  `Description` text DEFAULT NULL,
  PRIMARY KEY (`CostID`),
  KEY `JobID` (`JobID`),
  CONSTRAINT `costs_ibfk_1` FOREIGN KEY (`JobID`) REFERENCES `jobs` (`JobID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;


CREATE TABLE `customers` (
  `CustomerID` int(11) NOT NULL AUTO_INCREMENT,
  `FirstName` varchar(50) DEFAULT NULL,
  `SurName` varchar(50) DEFAULT NULL,
  `Phone` varchar(15) DEFAULT NULL,
  `Email` varchar(255) DEFAULT NULL,
  `PostCode` varchar(15) DEFAULT NULL,
  `DoorNumber` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`CustomerID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;


CREATE TABLE `jobs` (
  `JobID` int(11) NOT NULL AUTO_INCREMENT,
  `CustomerID` int(11) DEFAULT NULL,
  `Technician` varchar(50) DEFAULT NULL,
  `DeviceBrand` varchar(255) DEFAULT NULL,
  `DeviceType` varchar(50) DEFAULT NULL,
  `DeviceModel` varchar(50) DEFAULT NULL,
  `Extras` varchar(50) DEFAULT NULL,
  `Issue` varchar(255) DEFAULT NULL,
  `DataSave` tinyint(1) DEFAULT NULL,
  `Password` varchar(50) DEFAULT NULL,
  `Status` enum('In Progress','Completed','Cancelled','Waiting for Parts','Picked Up') DEFAULT 'In Progress',
  `Notes` text DEFAULT NULL,
  `StartDate` datetime DEFAULT NULL,
  `EndDate` datetime DEFAULT NULL,
  PRIMARY KEY (`JobID`),
  KEY `CustomerID` (`CustomerID`),
  CONSTRAINT `jobs_ibfk_1` FOREIGN KEY (`CustomerID`) REFERENCES `customers` (`CustomerID`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;


CREATE TABLE `orders` (
  `PartID` int(11) NOT NULL AUTO_INCREMENT,
  `JobID` int(11) DEFAULT NULL,
  `OrderDate` date DEFAULT NULL,
  `Description` varchar(255) DEFAULT NULL,
  `Quantity` int(11) DEFAULT NULL,
  `TotalCost` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`PartID`),
  KEY `JobID` (`JobID`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`JobID`) REFERENCES `jobs` (`JobID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;


CREATE TABLE `payments` (
  `PaymentID` int(11) NOT NULL AUTO_INCREMENT,
  `JobID` int(11) DEFAULT NULL,
  `Date` DATE DEFAULT NULL,
  `Amount` decimal(10,2) DEFAULT NULL,
  `PaymentType` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`PaymentID`),
  KEY `JobID` (`JobID`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`JobID`) REFERENCES `jobs` (`JobID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;


CREATE TABLE `walkins` (
  `WalkinID` int(11) NOT NULL AUTO_INCREMENT,
  `WalkinDate` date DEFAULT current_timestamp(),
  `Amount` int(11) DEFAULT NULL,
  `Description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`WalkinID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `HowHeard` (
  `JobID` int(11) NOT NULL,
  `HowHeard` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`JobID`),
  CONSTRAINT `howheard_ibfk_1` FOREIGN KEY (`JobID`) REFERENCES `jobs` (`JobID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;



SET FOREIGN_KEY_CHECKS = 1;

DELIMITER $$

CREATE TRIGGER delete_job_password_on_customer_delete
BEFORE DELETE ON customers
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM jobs WHERE CustomerID = OLD.CustomerID) THEN
        UPDATE jobs
        SET Password = NULL
        WHERE CustomerID = OLD.CustomerID;
    END IF;
END $$

DELIMITER ;


DELIMITER $$

CREATE TRIGGER delete_communications_on_customer_delete
BEFORE DELETE ON customers
FOR EACH ROW
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE job_id_var INT;
    DECLARE cur CURSOR FOR SELECT JobID FROM jobs WHERE CustomerID = OLD.CustomerID;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO job_id_var;
        IF done THEN
            LEAVE read_loop;
        END IF;
        DELETE FROM communications WHERE JobID = job_id_var;
    END LOOP;
    CLOSE cur;
END $$

DELIMITER ;

SET GLOBAL event_scheduler = ON;

DELIMITER $$

CREATE PROCEDURE DeleteOldCustomers()
BEGIN
    DECLARE max_customer_id INT;

    -- Step 1: Create a temporary table of customers with no recent jobs
    CREATE TEMPORARY TABLE temp_old_customers AS 
    SELECT CustomerID FROM jobs 
    GROUP BY CustomerID
    HAVING MAX(StartDate) < NOW() - INTERVAL 1 YEAR;

    -- Step 2: Delete old customers
    DELETE FROM customers 
    WHERE CustomerID IN (SELECT CustomerID FROM temp_old_customers);

    -- Step 3: Check if the table is now empty
    SELECT COUNT(*) INTO max_customer_id FROM customers;

    -- Step 4: If no customers left, reset AUTO_INCREMENT to 1
    IF max_customer_id = 0 THEN
        SET @query = 'ALTER TABLE customers AUTO_INCREMENT = 1';
        PREPARE stmt FROM @query;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    ELSE
        -- Otherwise, set AUTO_INCREMENT to the next highest CustomerID +1
        SET @new_auto_increment = (SELECT MAX(CustomerID) + 1 FROM customers);
        SET @query = CONCAT('ALTER TABLE customers AUTO_INCREMENT = ', @new_auto_increment);
        PREPARE stmt FROM @query;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;

    -- Step 5: Remove the temporary table
    DROP TEMPORARY TABLE IF EXISTS temp_old_customers;
END $$

DELIMITER ;



DELIMITER $$

CREATE TRIGGER delete_old_customers_trigger
AFTER INSERT OR UPDATE ON jobs
FOR EACH ROW
BEGIN
    -- Call the stored procedure to check and delete old customers
    CALL DeleteOldCustomers();
END $$

DELIMITER ;



