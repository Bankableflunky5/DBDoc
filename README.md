# 💻 DBDoc

**A full-stack repair shop management system**  
with a beautiful desktop interface for technicians/admins and a browser-based booking form for customers.

Built for real-world tech repair workflows. Works over a **local network**, with both GUI and web interfaces communicating through a shared MariaDB database.

---

## ⚙️ System Architecture

```text
[ Customer ] → [ React.js Frontend ] ──┐
                                       │
[ Technician/Admin ] → [ PyQt5 Desktop GUI ] ──> [ Python/Node Backend ] → [ MariaDB ]
                                       │
                               (Local Network)


---

## 🚀 Overview

DBDoc is designed to streamline the daily workflow of repair shops by offering:

- 🧾 **Client Job Booking**
- 🛠️ **Technician-Facing Tools**
- 📊 **Real-Time Data Insights**
- 💾 **Scheduled Backups & Restoration**
- 🗂️ **Custom Table Management**
- 🔐 **Secure Login & Role-Based Access (Planned)**

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

- **Python 3.x**
- **PyQt5** – GUI
- **MariaDB / MySQL** – Database layer
- **pandas / openpyxl / matplotlib** – Data handling & visualizations
- **FPDF / Tkinter** – Optional dialogs and PDF generation
- **Threading / Scheduling** – For background tasks like automated backups

---

## 📦 Getting Started

> ⚙️ **Work in Progress** – Full install steps will be added soon.

### 🧰 Requirements

- Python 3.x
- `PyQt5`, `mariadb`, `pymysql`, `pandas`, `openpyxl`, `matplotlib`, `schedule`, `fpdf`
- A running MariaDB or MySQL database
- SSL certs for secure connection (`.crt`, `.key`)

### 🔧 Setup Notes

- Update the SSL cert paths in the login method:
  ```python
  ssl_ca = "C:/ssl/mariadb/mariadb.crt"
  ssl_cert = "C:/ssl/mariadb/mariadb.crt"
  ssl_key = "C:/ssl/mariadb/mariadb.key"
