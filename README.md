# 💻 DBDoc – Full Stack Tech Repair Management Suite

A hybrid full-stack system for tech repair shops, featuring:

- 🖥️ A modern PyQt5 desktop app for technicians
- 🌐 A React.js web form for customer bookings
- ⚙️ A backend API that bridges both to a shared MariaDB database

> 🔒 Designed for secure, offline-first usage over a **local network**.

---

## 📐 System Architecture

```text
[ Customer ] → [ React.js Frontend ] ─────────────┐
                                                 │
[ Technician ] → [ PyQt5 GUI (Windows) ] ──┐      │
                                          │      │
                        [ Backend API (Flask or Node.js) ] → [ MariaDB ]
                                          ▲      ▲
>                                Secure via SSL (local)
🚀 Overview
DBDoc is designed to streamline the daily workflow of repair shops by offering:

🧾 Client Job Booking

🛠️ Technician-Facing Tools

📊 Real-Time Data Insights

💾 Scheduled Backups & Restoration

🗂️ Custom Table Management

🔐 Secure Login & Role-Based Access (Planned)

Built with an emphasis on usability, aesthetic polish, and real-world repair shop needs.
