# ⚙️ DBDoc Backend – Node.js API

This is the Node.js backend for **DBDoc**, responsible for handling customer form submissions, reserving job IDs, emailing confirmations, and securely connecting to the database.

---

## 🚀 What This Does

- 📥 Receives booking data from the React.js frontend
- 📌 Reserves a Job ID in advance
- 🔁 Links customers to jobs (new or existing)
- 📨 Sends confirmation emails with Job ID
- 🔐 Connects to MariaDB **via SSL**
- ✅ Supports graceful DB connection closure

---

## 🧱 Tech Stack

- **Node.js + Express** – API server
- **mysql2** – DB driver (async/await compatible)
- **nodemailer** – Email confirmations
- **fs** – Reads SSL certs
- **cors + express.json** – Middleware

---

## 🔧 Setup

```bash
cd backend
npm install
node backend.js
```

---

## 🔐 SSL Configuration

💡 You may uncomment this section in `backend.js` to enable SSL when connecting to MariaDB:

```js
db = mysql.createConnection({
  host: "your-db-host",
  user: "your-db-user",
  password: "your-db-password",
  database: "your-db-name",
  ssl: {
    ca: fs.readFileSync("C:/ssl/mariadb/ca.crt"),
    cert: fs.readFileSync("C:/ssl/mariadb/client.crt"),
    key: fs.readFileSync("C:/ssl/mariadb/client.key"),
    rejectUnauthorized: false
  }
});
### 📨 Email Confirmation

The API sends an email to the customer with their Job ID after submission.

To enable this:

- Set up a Gmail account
- Generate a **Google App Password** (required if you have 2FA enabled)

Then configure the transporter in your backend code like this:

```js
const transporter = nodemailer.createTransport({
  host: "smtp.gmail.com",
  port: 465,
  secure: true,
  auth: {
    user: "your-email@gmail.com",     // Replace with your Gmail
    pass: "your-app-password"         // Use your App Password, not normal Gmail password
  }
});
##🔄 Data Workflow
React frontend calls /api/open-form

Backend connects to DB

Frontend calls /api/reserve-job to get a Job ID

Form data is submitted via /submit

Backend links or creates the customer record

Job row is updated

Email is sent with confirmation

DB connection can be closed with /close-connection
---
##🛡 Security Notes
DB access is wrapped in error handling

Email fields and queries are parameterized

Use SSL for both DB and SMTP for full end-to-end encryption

Only bind to 0.0.0.0 on trusted local networks
---



