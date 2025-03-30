# 🖥️ DBDoc Desktop GUI – Technician Interface

This is the local desktop interface for technicians and admins to manage repair shop data, built using **PyQt5**.  
It connects directly to the MariaDB database over a secure SSL connection.

---

## 🚀 Features

- 🔐 Secure login screen with password toggle
- 🎛 Settings page to configure DB host and name
- 📁 View all database tables with pagination
- ✏️ Inline editing + dropdowns for job statuses
- 📊 Dashboard + query tools (planned expansion)
- 💾 Backup/Restore `.sql` dumps
- 📥 Export entire database to Excel (multi-sheet)
- ⏰ Schedule backups using a JSON config
- 🔑 Change DB user password from the GUI
- 🎨 Modern dark-themed UI with animations and emoji buttons

---

## ⚙️ Requirements

- **Python 3.8+**
- **Windows OS** (tested)
- Packages:
  ```bash
  pip install PyQt5 mariadb pandas openpyxl matplotlib schedule fpdf
'''
---

## 🔒 SSL Config
'''bash
ssl_ca = "C:/ssl/mariadb/ca.crt"
ssl_cert = "C:/ssl/mariadb/client.crt"
ssl_key = "C:/ssl/mariadb/client.key"

