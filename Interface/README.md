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
  pip install PyQt5 mariadb pandas openpyxl matplotlib schedule
  ```
---

## 🔒 SSL Config
To enable SSL database connections, update the login() method:
Uncomment and configure these lines to secure your DB connection.
```bash
ssl_ca = "C:/ssl/mariadb/ca.crt"
ssl_cert = "C:/ssl/mariadb/client.crt"
ssl_key = "C:/ssl/mariadb/client.key"
```
Uncomment and configure these lines to secure your DB connection.
---

---
## 💼 Settings File
App config is saved in settings.json after you hit 💾 Save Settings.
```bash
{
  "host": "localhost",
  "database": "repair_shop"
}
```
---
## 🛑 Limitations

- Currently built as a single large file
- Windows file paths are hardcoded in SSL config
- GUI doesnt yet suport roles/multi-user permissions
---

## 🛣️ Planned Upgrades
- Modular codebase with multiple files/classes
- SSL routes stored in environment variables
- More Visualizations
- Role-based access
- Linux/macOS support

