# 🧾 DBDoc – Full-Stack Booking App (React + Node.js)

This is the **customer-facing booking system** for DBDoc, a local repair shop management suite.  
It includes a modern **React/Next.js frontend** and a **Node.js backend**, connected via API and designed to run over a secure **local network**.

---

## 📦 What’s Inside

| Layer      | Tech Stack             | Purpose                                  |
|------------|------------------------|------------------------------------------|
| Frontend   | React (Next.js) + Tailwind CSS | User interface and booking form     |
| Backend    | Node.js + Express + MySQL2     | Handles logic, DB inserts, email sending |
| Database   | MariaDB / MySQL        | Stores jobs, customer info, form data    |

---

## ✨ Key Features

- 📋 Job booking form with validation and form state memory
- 🔁 Reserves Job ID before customer submits data
- 📧 Sends confirmation emails with job ID
- 🔐 SSL support for secure DB connections (optional)
- 🧠 Smart customer linking (re-use if same email/name)
- ✅ Works entirely on local network (no public cloud needed)

---

## 🚀 Getting Started

You’ll need:

- Node.js (18+)
- MariaDB or MySQL running locally or on your LAN
- Python (for technician GUI, if using full DBDoc stack)

---

### 1. Backend Setup (`/backend`)

```bash
cd backend
npm install
