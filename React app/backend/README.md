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
## 🌐 Environment variables
Create a .env file in root of backend with 
```bash
DB_HOST=your_host
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=database_name
DB_SSL_CA=pathto/mariadb.crt
DB_SSL_CERT=pathto/mariadb.crt  
DB_SSL_KEY=pathto/mariadb.key  

SMTP_EMAIL=your_email_username
SMTP_PASSWORD=your_app_password

```
---



## 🔐 SSL Configuration

💡 You may uncomment this section in `backend.js` to enable SSL when connecting to MariaDB:

```js
    db = mysql.createConnection({
        host: process.env.DB_HOST,
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        database: process.env.DB_NAME,
        #ssl: process.env.DB_SSL_CA ? {
        #    ca: fs.readFileSync(process.env.DB_SSL_CA),
        #    cert: fs.readFileSync(process.env.DB_SSL_CERT),
        #    key: fs.readFileSync(process.env.DB_SSL_KEY),
        #    rejectUnauthorized: false,
     #   } : undefined
    });
```
---

## 🔄 Data Workflow

React frontend calls `/api/open-form`  
Backend connects to DB  
Frontend calls `/api/reserve-job` to get a Job ID  
Form data is submitted via `/submit`  
Backend links or creates the customer record  
Job row is updated  
Email is sent with confirmation  
DB connection can be closed with `/close-connection`

---

## 🛡 Security Notes

- DB access is wrapped in error handling  
- Email fields and queries are parameterized  
- Use SSL for both DB and SMTP for full end-to-end encryption  
- Only bind to `0.0.0.0` on trusted local networks

---




