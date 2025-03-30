# 🌐 DBDoc – Booking Form Frontend (React + Next.js)

This is the **customer-facing booking form** for DBDoc, built using **Next.js, React 19, Tailwind CSS**, and deployed over a local network. It connects to a secure Node.js backend and a MariaDB database to create and track repair jobs.

---

## ✨ Features

- 🎨 Beautiful, responsive UI with Tailwind styling
- 🧠 Pre-fills saved form data using `localStorage`
- 📥 Submits repair request with customer/device details
- 📬 Sends a confirmation email with a unique Job ID
- ✅ Tracks `termsAccepted` and `dataSave` preferences
- 🔐 Fully local – works offline over your LAN

---

## 📐 Tech Stack

| Tool       | Purpose                     |
|------------|-----------------------------|
| **Next.js**| React app framework         |
| **React 19** | UI logic & state management |
| **Tailwind CSS** | Styling & layout        |
| **Axios**  | HTTP requests to backend API |
| **Lucide Icons** | Optional visual elements  |

---

## 🚀 Setup Instructions

### 1. Install dependencies

```bash
cd frontend
npm install
```
### 2. Start development server
```bash
npm run dev
```
App runs at http://localhost:3000 or http://YourIPAdress:3000
---
## 🔄️ Page Flow
1. Homepage  
2. Form Page
3. Success Page
4. Terms & Conditions
 ---

## 🧠 Notes
- Job ID is reserved before form submission and creates and empty slot in the db
- Form data is saved to localStorage and cleared on submission
- Email confirmation is handled server-side
- Terms are enforced via checkbox in the UI
---
   
