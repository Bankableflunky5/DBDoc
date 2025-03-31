# 💻 DBDoc

**A full-stack desktop management system for tech repair shops** — with integrated booking, data handling, secure login, backups, and reporting tools. Built with 💙 PyQt5 for a modern, responsive GUI and MariaDB/MySQL support under the hood.

---

```markdown
## 📐 System Architecture


[ Customer ] ──> [ React.js Frontend ] ──> [ Node.js Backend ] ──> [ MariaDB ]
                                                                       ▲
                   (API handles form submissions & secures DB access)  │
                                                                       │
[ Technician/Admin ] ─────────────> [ PyQt5 Desktop GUI ] ─────────────┘
                      (Direct connection to database via SSL)

                        🔒 All systems hosted on a secure Local Network


```
---

## 🚀 Overview

DBDoc is designed to streamline the daily workflow of repair shops by offering:

- 🧾 **Client Job Booking**
- 🛠️ **Technician-Facing Tools**
- 📊 **Real-Time Data Insights**
- 💾 **Scheduled Backups & Restoration**
- 🗂️ **Custom Table Management**
- 🔐 **Secure Login**

It's built with an emphasis on usability, aesthetic polish, and real-world repair shop needs.

---

## ✨ Key Features

- **Modern Dark-Themed UI** built with PyQt5
- **Secure login system** with animated elements and password visibility toggle
- **Settings Manager** with host/db config stored in JSON
- **Main Menu** for quick navigation with emoji-aligned buttons
- **Table Viewer & Editor** with:
  - Inline editing
  - Pagination
  - Status dropdowns (with conditional logic)
  - Auto-refresh
  - Search by column
- **Scheduled & Manual Database Backups**
- **Database Restore Function** with `.sql` import
- **Excel Export** for full databases (multi-sheet)
- **Change DB Password Tool** built-in
- **Dynamic AUTO_INCREMENT logic** to avoid primary key conflicts

---

## 🖥️ Platform Support

- ✅ **Built for Windows**  
- 🐧 Linux/macOS not yet tested — some paths and SSL cert configs are OS-specific

---

## 🧠 Technologies Used

- **Python 3.8+**
- **PyQt5** – GUI
- **MariaDB / MySQL** – Database layer
- **pandas / openpyxl / matplotlib** – Data handling & visualizations
- **Threading / Scheduling** – For background tasks like automated backups

---

## 📦 Getting Started

> ⚙️ **Work in Progress** – Full install steps will be added soon.

### 🧰 Requirements

- Python 3.8+
- `PyQt5`, `mariadb`, `pymysql`, `pandas`, `openpyxl`, `matplotlib`, `schedule`
- A running MariaDB or MySQL database
- SSL certs for secure connection (`.crt`, `.key`)
- node.js

---

## 🛣️ Roadmap / Planned Updates

> Short-term development goals for improving the project:

- [✔️] **Introduce more environment variables** in the React app  
  Move away from hardcoded values and centralize config for flexibility and cleaner deployment.

- [ ] **Add data visualizations** to the PyQt5 desktop interface  
  Charts, graphs, or dashboards to give technicians/admins insight into business trends (e.g., Busy time of day, who is booking in the most jobs).

- [ ] **Refactor the PyQt5 "god file"** into multiple modules  
  Improve maintainability and readability by splitting the large monolithic script into separate components.


