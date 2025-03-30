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
