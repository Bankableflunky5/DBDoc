# ─────────────────────────────────────────────────────────────────────────────
# 📦 Standard Library
import os
from functools import partial
# ─────────────────────────────────────────────────────────────────────────────
# 🎨 PyQt5 Core
from PyQt5.QtCore import (
    Qt, QEasingCurve, QPropertyAnimation, QByteArray, QEvent
)

# 🖼 PyQt5 GUI Elements
from PyQt5.QtGui import QFont, QFontMetrics

# 🧱 PyQt5 Widgets
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QFrame, QHeaderView,
    QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidgetItem, QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy
)

# ─────────────────────────────────────────────────────────────────────────────
# 🧩 Project Modules
from FILE_OPS.file_ops import (
    view_current_schedule,
    clear_current_schedule,
    save_backup_schedule,
    export_database_to_excel, save_database_config
)
from db_utils import restore_database, change_db_password, backup_database

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QFileDialog, QHBoxLayout, QCheckBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
    QFileDialog, QMessageBox, QHBoxLayout, QFormLayout, QGroupBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

def create_settings_page(database_config, on_save, on_back):
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(50, 50, 50, 50)
    layout.setSpacing(25)
    layout.setAlignment(Qt.AlignTop)

    page.setStyleSheet("""
        QWidget {
            background-color: #2E2E2E;
            color: white;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }

        QLabel {
            color: #3A9EF5;
            font-size: 16px;
            font-weight: bold;
        }

        QLineEdit {
            background-color: #383838;
            color: white;
            border: 1px solid #3A9EF5;
            border-radius: 8px;
            padding: 10px;
        }

        QLineEdit:focus {
            border: 2px solid #64b5f6;
        }

        QPushButton {
            background-color: #3A9EF5;
            color: white;
            padding: 10px 20px;
            font-weight: bold;
            font-size: 14px;
            border-radius: 8px;
            border: none;
        }

        QPushButton:hover {
            background-color: #1E7BCC;
        }

        QPushButton:pressed {
            background-color: #1665B3;
        }

        QPushButton#backButton {
            background-color: transparent;
            color: #3A9EF5;
            font-weight: bold;
        }

        QPushButton#backButton:hover {
            color: #7aaaff;
            text-decoration: underline;
        }

        QCheckBox {
            padding: 5px;
        }

        QGroupBox {
            border: 1px solid #3A9EF5;
            border-radius: 10px;
            margin-top: 15px;
        }

        QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 10px;
            color: #4FC3F7;
            font-size: 15px;
        }
    """)

    # 🔧 Title
    title = QLabel("⚙ Settings")
    title.setFont(QFont("Arial", 24, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)
    layout.addSpacing(30)

    # 🔧 Form Fields
    form_layout = QFormLayout()
    form_layout.setSpacing(15)

    host_entry = QLineEdit(database_config["host"])
    host_entry.setPlaceholderText("Enter Database Host")
    form_layout.addRow("🌐 Host:", host_entry)

    database_entry = QLineEdit(database_config["database"])
    database_entry.setPlaceholderText("Enter Database Name")
    form_layout.addRow("💾 Database:", database_entry)

    # 🔐 SSL Settings Group
    ssl_group = QGroupBox("SSL Settings")
    ssl_group_layout = QVBoxLayout()

    ssl_checkbox = QCheckBox("🔐 Use SSL")
    ssl_checkbox.setChecked(database_config.get("ssl", {}).get("enabled", False))
    ssl_group_layout.addWidget(ssl_checkbox)

    ssl_path_layout = QHBoxLayout()
    ssl_path_entry = QLineEdit()
    ssl_path_entry.setPlaceholderText("Path to SSL Certificate")
    ssl_path_entry.setText(database_config.get("ssl", {}).get("cert_path", ""))
    ssl_path_entry.setEnabled(ssl_checkbox.isChecked())

    browse_button = QPushButton("📁 Browse")
    browse_button.setEnabled(ssl_checkbox.isChecked())

    ssl_path_layout.addWidget(ssl_path_entry)
    ssl_path_layout.addWidget(browse_button)
    ssl_group_layout.addLayout(ssl_path_layout)

    ssl_group.setLayout(ssl_group_layout)
    form_layout.addRow(ssl_group)

    # 🔁 Enable/Disable SSL Inputs
    def toggle_ssl_input(state):
        enabled = state == Qt.Checked
        ssl_path_entry.setEnabled(enabled)
        browse_button.setEnabled(enabled)

    ssl_checkbox.stateChanged.connect(toggle_ssl_input)

    # 📁 Browse Dialog
    def browse_ssl_folder():
        path = QFileDialog.getExistingDirectory(page, "Select Folder Containing SSL Certificates")
        if path:
            expected_files = ["mariadb.crt", "mariadb.key"]
            missing = [f for f in expected_files if not os.path.isfile(os.path.join(path, f))]
            if missing:
                QMessageBox.warning(page, "Missing Files", f"Missing SSL files: {', '.join(missing)}")
            else:
                ssl_path_entry.setText(path)

    browse_button.clicked.connect(browse_ssl_folder)

    layout.addLayout(form_layout)
    layout.addSpacing(20)

    # 💾 Save Button
    save_button = QPushButton("💾 Save Settings")
    save_button.clicked.connect(on_save)
    layout.addWidget(save_button, alignment=Qt.AlignCenter)
    layout.addSpacing(10)

    # ⬅ Back Button
    back_button = QPushButton("⬅ Back")
    back_button.setObjectName("backButton")
    back_button.clicked.connect(on_back)
    layout.addWidget(back_button, alignment=Qt.AlignCenter)

    return page, host_entry, database_entry, ssl_checkbox, ssl_path_entry

def save_settings(
    database_config,
    host_entry,
    database_entry,
    password_entry,
    ssl_checkbox,
    ssl_path_entry,
    SETTINGS_FILE,
    central_widget,
    login_page,
    parent_window  # 👈 pass your main window here
):
    """Save settings from the settings page into a JSON file, including SSL preferences."""

    # 💾 Gather data from UI
    database_config["password"] = password_entry.text()
    database_config["host"] = host_entry.text()
    database_config["database"] = database_entry.text()
    database_config["ssl"] = {
        "enabled": ssl_checkbox.isChecked(),
        "cert_path": ssl_path_entry.text().strip()
    }

    # 💾 Save to disk
    result = save_database_config(database_config, SETTINGS_FILE)

    # 💬 Show feedback to user
    show_save_feedback(result, parent_window, central_widget, login_page)

def show_save_feedback(result, parent_window, central_widget, login_page):
    """Display success or error message based on result content."""
    msg_box = QMessageBox(parent_window)
    
    is_success = "successfully" in result.lower()
    msg_box.setWindowTitle("✅ Settings Saved" if is_success else "❌ Error Saving Settings")
    msg_box.setIcon(QMessageBox.Information if is_success else QMessageBox.Critical)
    msg_box.setText(result)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #2E2E2E;
            color: #FFFFFF;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        QPushButton {
            background-color: #3A9EF5;
            color: white;
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1E7BCC;
        }
    """)

    if is_success:
        msg_box.buttonClicked.connect(lambda: central_widget.setCurrentWidget(login_page))

    msg_box.exec_()

def create_login_page(parent):
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(50, 50, 50, 50)
    layout.setSpacing(25)
    layout.setAlignment(Qt.AlignCenter)

    page.setStyleSheet("""
        QWidget {
            background-color: #2E2E2E;
            color: white;
            font-family: 'Segoe UI', sans-serif;
        }

        QLabel {
            font-size: 16px;
            font-weight: bold;
            color: #3A9EF5;
        }

        QLineEdit {
            background-color: #383838;
            color: white;
            border: 1px solid #3A9EF5;
            border-radius: 8px;
            padding: 10px;
            font-size: 14px;
        }

        QLineEdit:focus {
            border: 2px solid #64b5f6;
        }

        QPushButton {
            background-color: #3A9EF5;
            color: white;
            padding: 12px;
            font-weight: bold;
            font-size: 14px;
            border-radius: 8px;
        }

        QPushButton:hover {
            background-color: #1E7BCC;
        }

        QPushButton:pressed {
            background-color: #1665B3;
        }

        QPushButton#settingsButton {
            background-color: #444;
        }

        QPushButton#settingsButton:hover {
            background-color: #666;
        }

        QPushButton#toggleButton {
            background-color: #555;
            border-radius: 6px;
            padding: 5px;
            font-size: 12px;
        }

        QPushButton#toggleButton:hover {
            background-color: #777;
        }

        QLabel#errorLabel {
            color: #FF5555;
            font-size: 14px;
            font-weight: bold;
        }

        QGroupBox {
            border: 1px solid #3A9EF5;
            border-radius: 10px;
            margin-top: 15px;
        }

        QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            color: #4FC3F7;
            font-size: 15px;
        }
    """)

    # 🔹 Title
    title = QLabel("🩺 Database Doctor")
    title.setFont(QFont("Arial", 26, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    # 🔹 Error Label
    parent.error_label = QLabel("")
    parent.error_label.setObjectName("errorLabel")
    parent.error_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(parent.error_label)

    # 🔹 Login Form Group
    login_group = QGroupBox("Login Credentials")
    group_layout = QVBoxLayout()

    form_layout = QFormLayout()
    form_layout.setSpacing(15)

    parent.username_entry = QLineEdit()
    parent.username_entry.setPlaceholderText("Enter your username")
    parent.username_entry.setToolTip("This is your database username.")
    form_layout.addRow("👤 Username:", parent.username_entry)

    parent.password_entry = QLineEdit()
    parent.password_entry.setPlaceholderText("Enter your password")
    parent.password_entry.setEchoMode(QLineEdit.Password)
    parent.password_entry.setToolTip("Your password will be kept secure.")
    form_layout.addRow("🔒 Password:", parent.password_entry)

    group_layout.addLayout(form_layout)

    # 🔹 Password Toggle
    toggle_layout = QHBoxLayout()
    toggle_layout.setAlignment(Qt.AlignRight)

    toggle_button = QPushButton("👁 Show")
    toggle_button.setObjectName("toggleButton")
    toggle_button.setCheckable(True)
    toggle_button.setFixedWidth(60)

    def toggle_password():
        if toggle_button.isChecked():
            parent.password_entry.setEchoMode(QLineEdit.Normal)
            toggle_button.setText("🙈 Hide")
        else:
            parent.password_entry.setEchoMode(QLineEdit.Password)
            toggle_button.setText("👁 Show")

    toggle_button.clicked.connect(toggle_password)
    toggle_layout.addWidget(toggle_button)
    group_layout.addLayout(toggle_layout)

    login_group.setLayout(group_layout)
    layout.addWidget(login_group)

    # 🔹 Login Button
    parent.login_button = QPushButton("🔓 Login")
    parent.login_button.setFixedHeight(50)
    parent.login_button.setObjectName("animatedButton")
    parent.login_button.clicked.connect(parent.login)
    layout.addWidget(parent.login_button)

    # 🔹 Settings Button
    parent.settings_button = QPushButton("⚙ Settings")
    parent.settings_button.setObjectName("settingsButton")
    parent.settings_button.setFixedHeight(40)
    parent.settings_button.clicked.connect(
        lambda: parent.central_widget.setCurrentWidget(parent.settings_page)
    )
    layout.addWidget(parent.settings_button)

    return page

def open_schedule_backup_dialog(parent, save_callback):
    """
    Opens a styled dialog for scheduling backups.

    Args:
        parent: The main window or controller.
        save_callback: A function to call for saving the backup schedule.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle("📅 Schedule Backup")
    dialog.setStyleSheet(""" 
        QDialog {
            background-color: #1E1E1E;
            color: white;
            border-radius: 10px;
        }
        QLabel {
            font-size: 14px;
            font-weight: bold;
            color: #3A9EF5;
        }
        QLineEdit, QComboBox, QPushButton {
            background-color: #2A2A2A;
            color: white;
            border: 1px solid #3A9EF5;
            border-radius: 5px;
            padding: 6px;
        }
        QPushButton {
            background-color: #3A9EF5;
            font-weight: bold;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #1D7DD7;
        }
        QPushButton#cancelButton {
            background-color: #666;
        }
        QPushButton#cancelButton:hover {
            background-color: #888;
        }
    """)

    layout = QVBoxLayout()

    # Title
    title_label = QLabel("📅 Set Backup Schedule")
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
    layout.addWidget(title_label)

    # Frequency dropdown
    interval_label = QLabel("⏳ Select Backup Frequency:")
    interval_combo = QComboBox()
    interval_combo.addItems(["Daily", "Hourly", "Every X minutes"])
    layout.addWidget(interval_label)
    layout.addWidget(interval_combo)

    # Time entry
    time_label = QLabel("⏰ Time of Day for Daily Backup (HH:MM):")
    time_entry = QLineEdit()
    time_entry.setPlaceholderText("e.g., 00:00")
    time_entry.setStyleSheet("""
        QLineEdit::placeholder {
            color: #BBBBBB;
        }
    """)
    layout.addWidget(time_label)
    layout.addWidget(time_entry)

    # Backup directory
    backup_directory = []
    directory_label = QLabel("📂 Select Backup Location:")
    layout.addWidget(directory_label)

    directory_button = QPushButton("📁 Choose Directory")
    layout.addWidget(directory_button)

    def choose_directory():
        directory = QFileDialog.getExistingDirectory(parent, "Select Directory to Save Backup")
        if directory:
            backup_directory.clear()
            backup_directory.append(directory)
            directory_button.setText(f"📂 {os.path.basename(directory)}")

    directory_button.clicked.connect(choose_directory)

    # Submit button
    submit_button = QPushButton("💾 Save Schedule")
    submit_button.clicked.connect(lambda: save_callback(parent, interval_combo, time_entry, backup_directory, dialog))
    layout.addWidget(submit_button)

    # Cancel button
    cancel_button = QPushButton("❌ Cancel")
    cancel_button.setObjectName("cancelButton")
    cancel_button.clicked.connect(dialog.close)
    layout.addWidget(cancel_button)

    dialog.setLayout(layout)
    dialog.exec_()

def ask_for_job_id(parent):
    """
    Prompts the user for a Job ID and, if valid, calls parent.view_notes(job_id).

    Args:
        parent: The object that implements `view_notes(job_id)`.
    """
    job_id, ok = QInputDialog.getText(None, "🔍 Search Job", "Enter Job ID:")
    
    if not ok or not job_id.strip():
        return  # User hit Cancel or left it blank

    job_id = job_id.strip()
    if not job_id.isdigit():
        QMessageBox.warning(None, "⚠ Invalid Input", "Job ID must be a number.")
        return

    parent.view_notes(job_id)

def edit_selected_job(parent):
    """
    Gets the selected job's ID from the table and opens the Edit Notes dialog.

    Args:
        parent: The object with access to `table_widget` and `view_notes(job_id)`.
    """
    selected_items = parent.table_widget.selectedItems()
    
    if not selected_items:
        QMessageBox.warning(None, "⚠ No Selection", "Please select a row to edit.")
        return

    selected_row = selected_items[0].row()
    job_id_item = parent.table_widget.item(selected_row, 0)

    if not job_id_item:
        QMessageBox.warning(None, "⚠ Missing Job ID", "No Job ID found in the selected row.")
        return

    job_id = job_id_item.text().strip()

    if not job_id.isdigit():
        QMessageBox.warning(None, "⚠ Invalid Job ID", "Selected Job ID is not a valid number.")
        return

    parent.view_notes(job_id)

def event_filter(parent, source, event):
    """
    Filters out wheel events on QComboBox widgets to prevent accidental scrolling.

    Args:
        parent: The object that owns this filter and needs fallback eventFilter handling.
        source: The QObject that sent the event.
        event: The QEvent being processed.

    Returns:
        bool: True if the event is handled (blocked), otherwise False.
    """
    if isinstance(source, QComboBox) and event.type() == QEvent.Wheel:
        return True  # Block the wheel event

    # Fallback to the default eventFilter behavior of the parent
    return super(type(parent), parent).eventFilter(source, event)

def populate_table(table_widget, table_name, data):
    """Populates the table with fresh data without triggering unnecessary updates."""

    if not table_widget:
        QMessageBox.critical(None, "Error", "Table widget not initialized.")
        return

    table_widget.blockSignals(True)  # ✅ Prevent unwanted `itemChanged` triggers

    table_widget.clearContents()  # 🔥 Ensure old data is cleared
    table_widget.setRowCount(len(data))  # ✅ Ensure all rows are displayed

    # Detect status column index
    status_column_index = None
    if table_name == "jobs":
        for col_idx in range(table_widget.columnCount()):
            if table_widget.horizontalHeaderItem(col_idx).text().lower() == "status":
                status_column_index = col_idx
                break

    for row_idx, row_data in enumerate(data):
        for col_idx, value in enumerate(row_data):
            if col_idx == status_column_index:  # ✅ Apply dropdown if it's the status column
                status_combo = QComboBox()
                status_combo.addItems(["Waiting for Parts", "In Progress", "Completed", "Picked Up"])
                
                value_str = str(value).strip()  # Keep original case
                if value_str in ["Waiting for Parts", "In Progress", "Completed", "Picked Up"]:
                    status_combo.setCurrentText(value_str)
                else:
                    status_combo.setCurrentText("In Progress")  # Default
                
                status_combo.setEditable(False)
                status_combo.installEventFilter(table_widget)

                table_widget.setCellWidget(row_idx, col_idx, status_combo)

                status_combo.currentTextChanged.connect(
                    lambda text, row=row_idx: update_status_and_database(row, text)
                )

            else:
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setData(Qt.UserRole, item.text())  # ✅ Store original value for change detection
                table_widget.setItem(row_idx, col_idx, item)

    table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table_widget.verticalHeader().setVisible(False)

    table_widget.blockSignals(False)  # ✅ Allow actual edits to be detected

def main_menu_page(parent):
    """Creates and displays the upgraded main menu UI with a unified modern dark theme."""

    if hasattr(parent, "main_menu"):
        parent.central_widget.setCurrentWidget(parent.main_menu)
        return

    parent.main_menu = QWidget()
    layout = QVBoxLayout(parent.main_menu)
    layout.setContentsMargins(50, 40, 50, 40)
    layout.setSpacing(25)
    layout.setAlignment(Qt.AlignTop)

    parent.main_menu.setStyleSheet("""
        QWidget {
            background-color: #2E2E2E;
            color: white;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }

        QLabel#titleLabel {
            font-size: 26px;
            font-weight: bold;
            color: #3A9EF5;
            padding: 10px;
            border-bottom: 2px solid #3A9EF5;
        }

        QPushButton {
            font-size: 16px;
            font-family: monospace;
            background-color: #3A9EF5;
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            text-align: center;
        }

        QPushButton:hover {
            background-color: #1E7BCC;
        }

        QPushButton:pressed {
            background-color: #1665B3;
        }

        QPushButton#logoutButton {
            background-color: #D9534F;
        }

        QPushButton#logoutButton:hover {
            background-color: #C9302C;
        }

        QFrame#menuFrame {
            background-color: #1f1f1f;
            border-radius: 12px;
            padding: 20px;
        }
    """)

    # 📌 Title
    title = QLabel("📌 Main Menu")
    title.setObjectName("titleLabel")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    # 📦 Menu Container
    menu_frame = QFrame()
    menu_frame.setObjectName("menuFrame")
    menu_layout = QVBoxLayout(menu_frame)
    menu_layout.setSpacing(18)

    # 📋 Buttons
    button_data = [
        ("📁  Tables", parent.view_tables),
        ("📝  Add Job Notes", lambda: ask_for_job_id(parent)),
        ("🔍  Query", parent.run_query),
        ("📑  Customer Lookup", parent.Customer_report),
        ("📊  Dashboard", parent.dashboard_page),
        ("⚙️  Settings", lambda: options_page(parent))
    ]

    # Ensure uniform width
    font_metrics = QFontMetrics(QPushButton().font())
    fixed_width = font_metrics.horizontalAdvance("📊  Dashboard   ") + 40

    for label, command in button_data:
        button = QPushButton(label)
        button.setCursor(Qt.PointingHandCursor)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedHeight(48)
        button.setMinimumWidth(fixed_width)
        button.clicked.connect(command)
        menu_layout.addWidget(button)

    # 🚪 Logout Button (styled separately)
    logout_button = QPushButton("🚪  Logout")
    logout_button.setObjectName("logoutButton")
    logout_button.setCursor(Qt.PointingHandCursor)
    logout_button.setFixedHeight(48)
    logout_button.setMinimumWidth(fixed_width)
    logout_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    logout_button.clicked.connect(parent.logout)
    menu_layout.addWidget(logout_button)

    layout.addWidget(menu_frame)
    parent.main_menu.setLayout(layout)
    parent.central_widget.addWidget(parent.main_menu)
    parent.central_widget.setCurrentWidget(parent.main_menu)
    
def options_page(parent):
    """Creates a visually enhanced settings/options page in PyQt."""

    parent.settings_page = QWidget()
    layout = QVBoxLayout(parent.settings_page)

    parent.settings_page.setStyleSheet("""
        QWidget {
            background-color: #2E2E2E;
            color: white;
            font-size: 14px;
        }
        QLabel {
            font-size: 22px;
            font-weight: bold;
            color: #3A9EF5;
            padding: 10px;
        }
        QPushButton {
            background-color: #3A9EF5;
            color: white;
            padding: 12px;
            font-weight: bold;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #1E7BCC;
        }
        QPushButton#backButton {
            background-color: #D9534F;
        }
        QPushButton#backButton:hover {
            background-color: #C9302C;
        }
        QLineEdit {
            background-color: #444;
            color: white;
            border: 1px solid #3A9EF5;
            border-radius: 5px;
            padding: 8px;
        }
        QLineEdit:focus {
            border: 2px solid #3A9EF5;
        }
    """)

    title_label = QLabel("⚙️ Settings")
    title_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(title_label)

    export_button = QPushButton("📥 Export Entire Database to Excel")
    export_button.clicked.connect(lambda: export_database_to_excel(parent, parent.cursor))
    layout.addWidget(export_button)

    backup_button = QPushButton("💾 Backup Database")
    backup_button.clicked.connect(lambda: backup_database(parent.cursor))
    layout.addWidget(backup_button)

    # 🕓 Backup Schedule Button
    scheduling_options_button = QPushButton("⏰ Backup Schedule Options")
    scheduling_options_button.clicked.connect(partial(open_scheduling_options_dialog, parent))
    layout.addWidget(scheduling_options_button)

    restore_button = QPushButton("🔄 Create from Backup")
    restore_button.clicked.connect(lambda: restore_database(parent.conn, parent.cursor, parent))
    layout.addWidget(restore_button)

    change_password_button = QPushButton("🔑 Change Password")
    change_password_button.clicked.connect(
    lambda: change_db_password(parent.database_config, parent.conn)
)

    layout.addWidget(change_password_button)

    back_button = QPushButton("⬅ Back to Main Menu")
    back_button.setObjectName("backButton")
    back_button.clicked.connect(lambda: main_menu_page(parent))
    layout.addWidget(back_button)

    parent.settings_page.setLayout(layout)
    parent.central_widget.addWidget(parent.settings_page)
    parent.central_widget.setCurrentWidget(parent.settings_page)

def apply_button_hover_animation(parent, button): #UI
        """Applies a hover animation effect to a QPushButton."""
        original_width = button.sizeHint().width()
        animation = QPropertyAnimation(button, QByteArray(b"minimumWidth"))
        animation.setDuration(150)  # Animation duration in ms
        animation.setStartValue(original_width)
        animation.setEndValue(original_width + 10)
        animation.setEasingCurve(QEasingCurve.InOutQuad)

        def on_hover(event):
            animation.setDirection(QPropertyAnimation.Forward)
            animation.start()

        def on_leave(event):
            animation.setDirection(QPropertyAnimation.Backward)
            animation.start()

        button.enterEvent = on_hover
        button.leaveEvent = on_leave

def open_scheduling_options_dialog(parent):
    """Open a dialog with options related to backup scheduling with improved UI."""
    
    # Create the dialog
    scheduling_dialog = QDialog(parent)
    scheduling_dialog.setWindowTitle("⚙ Backup Scheduling Options")
    scheduling_dialog.setStyleSheet("""
        QDialog {
            background-color: #1E1E1E;  /* Dark background */
            color: white;  /* White text */
            border-radius: 10px;
        }
        QLabel {
            font-size: 16px;
            font-weight: bold;
            color: #3A9EF5;  /* Light blue text */
        }
        QPushButton {
            background-color: #2A2A2A;
            color: white;
            border: 1px solid #3A9EF5;
            border-radius: 5px;
            padding: 8px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #3A9EF5;
            color: white;
        }
        QPushButton#closeButton {
            background-color: #D9534F;
        }
        QPushButton#closeButton:hover {
            background-color: #C9302C;
        }
    """)

    layout = QVBoxLayout()

    # ✅ Title Label
    title_label = QLabel("⚙ Backup Scheduling Options")
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
    layout.addWidget(title_label)

    # ✅ Schedule a new backup
    schedule_button = QPushButton("⏰ Schedule New Backup")
    schedule_button.clicked.connect(lambda: open_schedule_backup_dialog(parent, save_backup_schedule))
    layout.addWidget(schedule_button)

    # ✅ View Current Schedule
    view_schedule_button = QPushButton("👀 View Current Schedule")
    view_schedule_button.clicked.connect(lambda: view_current_schedule(parent))
    layout.addWidget(view_schedule_button)

    # ✅ Clear Current Schedule
    clear_button = QPushButton("🧹 Clear Backup Schedule")
    clear_button.clicked.connect(lambda: clear_current_schedule(parent))
    layout.addWidget(clear_button)

    # ✅ Close Button
    close_button = QPushButton("❌ Close")
    close_button.setObjectName("closeButton")
    close_button.clicked.connect(scheduling_dialog.reject)
    layout.addWidget(close_button)

    scheduling_dialog.setLayout(layout)
    scheduling_dialog.exec_() 

def keyPressEvent(parent, event): #UI
    """Handles key press events for the login window."""
    if event.key() == Qt.Key_Return:  # Check if the "Enter" key is pressed
        parent.login()  # Call the login method

def refresh_page(parent):
    """
    Reloads the current page while keeping the dropdowns intact.

    Args:
        parent: The object (typically a UI controller or main window)
                that holds table_widget, table_name, table_offset, and load_table().
    """
    parent.table_widget.blockSignals(True)  # Prevents unwanted table updates
    parent.table_widget.setRowCount(0)      # Clears all existing rows
    parent.load_table(parent.table_name, parent.table_offset)  # Loads the appropriate data
    parent.table_widget.blockSignals(False)  # Re-enable signals

def exit_app(parent):
    """
    Closes the main application window.
    
    Args:
        parent: The main window or QWidget that should be closed.
    """
    parent.close()

def reset_window_size(parent):
    """
    Closes the dashboard dialog and returns to the main menu.

    Args:
        parent: The main window or controller with access to `dashboard_dialog` and `main_menu_page()`.
    """
    parent.dashboard_dialog.close()
    main_menu_page(parent)
