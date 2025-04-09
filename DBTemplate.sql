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



