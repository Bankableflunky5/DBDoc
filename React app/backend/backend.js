require("dotenv").config();
console.log("🔎 DB_HOST:", process.env.DB_HOST, process.env.DB_USER, process.env.DB_PASSWORD); // Debugging


const express = require("express");
const mysql = require("mysql2");
const cors = require("cors");
const nodemailer = require("nodemailer");
const fs = require('fs');

const app = express();
app.use(express.json());
app.use(cors());

// Declare the db variable globally
let db;

app.use(express.json());

// Open form route
app.post("/api/open-form", (req, res) => {
    console.log("📌 Received request to open form");

    if (process.env.DB_SSL_CA) {
        console.log("🔎 Checking SSL files...");
        console.log("DB_SSL_CA:", fs.existsSync(process.env.DB_SSL_CA) ? "✅ Exists" : "❌ Not found");
        console.log("DB_SSL_CERT:", fs.existsSync(process.env.DB_SSL_CERT) ? "✅ Exists" : "❌ Not found");
        console.log("DB_SSL_KEY:", fs.existsSync(process.env.DB_SSL_KEY) ? "✅ Exists" : "❌ Not found");
    }

    db = mysql.createConnection({
        host: process.env.DB_HOST,
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        database: process.env.DB_NAME,
        ssl: process.env.DB_SSL_CA ? {
            ca: fs.readFileSync(process.env.DB_SSL_CA),
            cert: fs.readFileSync(process.env.DB_SSL_CERT),
            key: fs.readFileSync(process.env.DB_SSL_KEY),
            rejectUnauthorized: false,
        } : undefined
    });

    db.connect((err) => {
        if (err) {
            console.error("❌ Database connection failed:", err.message);
            return res.status(500).json({ error: "Database connection failed", details: err.message });
        } else {
            console.log("✅ Database connected");
            res.status(200).json({ message: "Database connection established" });
        }
    });
});




// 🔹 Nodemailer Configuration

const transporter = nodemailer.createTransport({
    host: "smtp.gmail.com", // ✅ Correct Gmail SMTP host
    port: 465, // ✅ Use port 465 for SSL (or 587 for TLS)
    secure: true, // ✅ Use true for SSL (false for TLS)
    auth: {
        user: process.env.SMTP_EMAIL,
        pass: process.env.SMTP_PASSWORD, // ✅ Use your 16-character Google App Password
    },
});

// 🔹 Fetch Next Job ID
app.get("/next-job-id", async (req, res) => {
    try {
        const [result] = await db.promise().query("SELECT MAX(jobID) AS maxJobID FROM jobs");
        const nextJobID = result[0].maxJobID ? result[0].maxJobID : 1; // Start from 1 if no jobs exist
        res.json({ nextJobID });
    } catch (error) {
        console.error("Error fetching next Job ID:", error);
        res.status(500).json({ error: "Failed to fetch Job ID" });
    }
});

// Backend API to reserve a Job ID
app.post("/api/reserve-job", (req, res) => {
    console.log("🔹 Reserve Job API called");

    const reserveJobQuery = `
    INSERT INTO jobs (CustomerID, DeviceBrand, DeviceType, Issue, DataSave, Password, Status, StartDate) 
    VALUES (NULL, NULL, NULL, NULL, NULL, NULL, 'In Progress', NOW())`;

    db.query(reserveJobQuery, (err, result) => {
        if (err) {
            console.error("❌ Error reserving Job ID:", err.sqlMessage);
            return res.status(500).json({ error: "Error reserving Job ID" });
        }

        const jobID = result.insertId; // Get the newly inserted Job ID
        console.log(`✅ Reserved Job ID: ${jobID}`);

        res.json({ jobID });
    });
});


// 🔹 Handle Form Submission with Reserved Job ID
app.post("/submit", async (req, res) => {
    const { jobID, firstName, lastName, phone, email, doorNumber, postCode, howHeard, deviceType, deviceBrand, issue, password, dataSave } = req.body;

    console.log("📥 Received submission:", req.body);
    const dataSaveValue = dataSave ? 1 : 0;

    // Ensure db connection exists before proceeding
    if (!db) {
        return res.status(500).json({ error: "Database connection not established" });
    }

    try {
        // Ensure a valid jobID is provided
        if (!jobID) {
            return res.status(400).json({ error: "Job ID is required" });
        }

        // Step 1: Check if the customer exists
        const [customerResults] = await db.promise().query(
            "SELECT CustomerID FROM customers WHERE FirstName = ? AND SurName = ? AND Email = ?",
            [firstName, lastName, email]
        );

        let customerId;

        if (customerResults.length > 0) {
            // ✅ Customer exists
            customerId = customerResults[0].CustomerID;
            console.log(`✅ Existing customer found: CustomerID ${customerId}`);
        } else {
            // 🆕 Customer does NOT exist, insert a new customer
            console.log("🆕 New customer detected. Inserting into database.");

            const [customerInsert] = await db.promise().query(
                "INSERT INTO customers (FirstName, SurName, Phone, Email, PostCode, DoorNumber) VALUES (?, ?, ?, ?, ?, ?)",
                [firstName, lastName, phone, email, postCode, doorNumber]
            );

            customerId = customerInsert.insertId;
            console.log(`✅ New customer added: CustomerID ${customerId}`);
        }

        // Step 2: Update the existing job record using the provided jobID
        await db.promise().query(
            "UPDATE jobs SET CustomerID = ?, DeviceBrand = ?, DeviceType = ?, Issue = ?, DataSave = ?, Password = ?, Status = 'In Progress', StartDate = NOW() WHERE jobID = ?",
            [customerId, deviceBrand, deviceType, issue, dataSaveValue, password, jobID]
        );

        console.log(`✅ Job successfully updated: JobID ${jobID}`);

        // Step 3: Insert howHeard into the HowHeard table
        await db.promise().query(
            "INSERT INTO HowHeard (JobID, HowHeard) VALUES (?, ?)",
            [jobID, howHeard]
        );

        // Send Confirmation Email
        sendConfirmationEmail(email, firstName, lastName, jobID);

        res.json({ message: "Form submitted successfully! You will receive an email confirmation shortly.", jobID });

    } catch (error) {
        console.error("❌ Error in form submission:", error);
        res.status(500).json({ error: "Error processing form submission", details: error.message });
    }
});



// 🔹 Function to Send Email
function sendConfirmationEmail(email, firstName, lastName, jobId) {
    const mailOptions = {
        from: '"The Laptop Doctor" <dscoenterprisesukltd@gmail.com>', // ✅ Custom display name
        to: email,
        subject: "Your Repair Job Confirmation",
        html: `
            <p>Dear ${firstName} ${lastName},</p>
            <p>Thank you for submitting your repair request.</p>
            <p>Your Job ID is: <strong>${jobId}</strong></p>
            <p>We will contact you soon with further details.</p>
            <p>Best regards,</p>
            <p><strong>The Laptop Doctor</strong></p>
        `,
    };
    

    transporter.sendMail(mailOptions, (error, info) => {
        if (error) {
            console.error("❌ Email sending failed:", error);
        } else {
            console.log("📧 Email sent successfully:", info.response);
        }
    });
}

app.post("/close-connection", (req, res) => {
    if (!db) {
        return res.status(400).json({ error: "No active database connection found" });
    }

    db.end((err) => {
        if (err) {
            console.error("❌ Error closing the database connection:", err);
            return res.status(500).json({ error: "Error closing database connection" });
        }

        console.log("✅ Database connection closed successfully");
        res.json({ message: "Database connection closed successfully" });
    });
});

// 🔹 Start the Backend Server
app.listen(5000, "0.0.0.0", () => console.log("🚀 Server running on http://0.0.0.0:5000"));

