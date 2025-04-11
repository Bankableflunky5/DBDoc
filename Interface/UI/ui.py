# ─────────────────────────────────────────────────────────────────────────────
# 📦 Standard Library
import os
from functools import partial

# ─────────────────────────────────────────────────────────────────────────────
# 🎨 PyQt5 Core
from PyQt5.QtCore import (
    Qt, QEvent, QPropertyAnimation, QEasingCurve
)

# 🖼 PyQt5 GUI Elements
from PyQt5.QtGui import QFont, QFontMetrics, QIcon

# 🧱 PyQt5 Widgets
from PyQt5.QtWidgets import (
    QAction, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QStyle,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView, QTextEdit, QAbstractItemView
)

# ─────────────────────────────────────────────────────────────────────────────
# 🧩 Project Modules
from data_access import (
    close_connection, fetch_table_data, fetch_primary_key_column,
    execute_sql_query, export_query_results_to_excel
)
from FILE_OPS.file_ops import (
    view_current_schedule, clear_current_schedule,
    save_backup_schedule, export_database_to_excel, save_database_config
)
from db_utils import restore_database, change_db_password, backup_database
from datetime import datetime


def create_settings_page(database_config, on_save, on_back):
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(70, 60, 70, 60)
    layout.setSpacing(40)
    layout.setAlignment(Qt.AlignTop)

    page.setStyleSheet("""
        QWidget {
            background-color: #2E2E2E;
            color: white;
            font-family: 'Segoe UI', sans-serif;
            font-size: 16px;
        }

        QLabel {
            color: #3A9EF5;
            font-size: 20px;
            font-weight: bold;
        }

        QLineEdit {
            background-color: #383838;
            color: white;
            border: 1px solid #3A9EF5;
            border-radius: 10px;
            padding: 14px;
            font-size: 16px;
        }

        QLineEdit:focus {
            border: 2px solid #64b5f6;
        }

        QPushButton {
            background-color: #3A9EF5;
            color: white;
            padding: 14px 26px;
            font-weight: bold;
            font-size: 16px;
            border-radius: 10px;
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
            font-size: 16px;
        }

        QPushButton#backButton:hover {
            color: #7aaaff;
            text-decoration: underline;
        }

        QCheckBox {
            font-size: 15px;
            padding: 6px;
        }

        QGroupBox {
            border: 1px solid #3A9EF5;
            border-radius: 10px;
            margin-top: 20px;
        }

        QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 6px 12px;
            color: #4FC3F7;
            font-size: 17px;
        }
    """)

    # 🔧 Title
    title = QLabel("⚙ Settings")
    title.setFont(QFont("Arial", 28, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)
    layout.addSpacing(40)

    # 🔧 Form Fields
    form_layout = QFormLayout()
    form_layout.setSpacing(20)

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

    def toggle_ssl_input(state):
        enabled = state == Qt.Checked
        ssl_path_entry.setEnabled(enabled)
        browse_button.setEnabled(enabled)

    ssl_checkbox.stateChanged.connect(toggle_ssl_input)

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
    layout.addSpacing(30)

    # 💾 Save Button
    save_button = QPushButton("💾 Save Settings")
    save_button.setFixedHeight(50)
    save_button.clicked.connect(on_save)
    layout.addWidget(save_button, alignment=Qt.AlignCenter)

    layout.addSpacing(15)

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
    layout.setContentsMargins(70, 60, 70, 60)
    layout.setSpacing(40)
    layout.setAlignment(Qt.AlignCenter)

    page.setStyleSheet("""
        QWidget {
            background-color: #2E2E2E;
            color: white;
            font-family: 'Segoe UI', sans-serif;
            font-size: 16px;
        }

        QLabel {
            font-size: 20px;
            font-weight: bold;
            color: #3A9EF5;
        }

        QLineEdit {
            background-color: #383838;
            color: white;
            border: 1px solid #3A9EF5;
            border-radius: 10px;
            padding: 14px;
            font-size: 16px;
        }

        QLineEdit:focus {
            border: 2px solid #64b5f6;
        }

        QPushButton {
            background-color: #3A9EF5;
            color: white;
            padding: 14px 24px;
            font-weight: bold;
            font-size: 16px;
            border-radius: 10px;
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
            border-radius: 8px;
            padding: 8px;
            font-size: 13px;
        }

        QPushButton#toggleButton:hover {
            background-color: #777;
        }

        QLabel#errorLabel {
            color: #FF5555;
            font-size: 15px;
            font-weight: bold;
        }

        QGroupBox {
            border: 1px solid #3A9EF5;
            border-radius: 10px;
            margin-top: 20px;
        }

        QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 6px 12px;
            color: #4FC3F7;
            font-size: 17px;
        }
    """)

    # 🔹 Title
    title = QLabel("🩺 Database Doctor")
    title.setFont(QFont("Arial", 30, QFont.Bold))
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
    form_layout.setSpacing(20)

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
    toggle_button.setFixedWidth(70)

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
    parent.login_button.setFixedHeight(55)
    parent.login_button.setObjectName("animatedButton")
    parent.login_button.clicked.connect(parent.login)
    layout.addWidget(parent.login_button)

    # 🔹 Settings Button
    parent.settings_button = QPushButton("⚙ Settings")
    parent.settings_button.setObjectName("settingsButton")
    parent.settings_button.setFixedHeight(45)
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
    Prompts the user for a Job ID with validation and modern dark-themed styling.
    If valid, it calls parent.view_notes(job_id).
    """

    # --- Custom Input Dialog ---
    input_dialog = QInputDialog(parent)
    input_dialog.setWindowTitle("🔍 Search Job")
    input_dialog.setLabelText("Enter Job ID:")
    input_dialog.setInputMode(QInputDialog.TextInput)
    input_dialog.setFixedSize(400, 150)
    input_dialog.setOkButtonText("Search")
    input_dialog.setCancelButtonText("Cancel")

    input_dialog.setStyleSheet("""
        QInputDialog {
            background-color: #2E2E2E;
            color: white;
            font-size: 15px;
        }

        QLabel {
            color: #3A9EF5;
            font-weight: bold;
            font-size: 15px;
        }

        QPushButton {
            background-color: #3A9EF5;
            color: white;
            padding: 6px 14px;
            font-weight: bold;
            border-radius: 6px;
            font-size: 14px;
        }

        QPushButton:hover {
            background-color: #1E7BCC;
        }

        QPushButton:pressed {
            background-color: #1665B3;
        }
    """)

    line_edit = input_dialog.findChild(QLineEdit)
    if line_edit:
        line_edit.setPlaceholderText("e.g., 12345")
        line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #383838;
                color: white;
                border: 1px solid #3A9EF5;
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #64b5f6;
            }
        """)
        line_edit.setFocus()

    if input_dialog.exec_() == QInputDialog.Accepted:
        job_id = input_dialog.textValue().strip()

        if not job_id.isdigit():
            # --- Custom Styled Warning Box ---
            msg = QMessageBox(parent)
            msg.setWindowTitle("⚠ Invalid Input")
            msg.setText("Job ID must be a number.")
            msg.setIcon(QMessageBox.Warning)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #2E2E2E;
                    color: white;
                    font-size: 15px;
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
            msg.exec_()
            return ask_for_job_id(parent)  # Prompt again
        else:
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

def populate_table(table_widget, table_name, data, status_update_callback):
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
                lambda text, row=row_idx: status_update_callback(row, text)
            )

            else:
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setData(Qt.UserRole, item.text())  # ✅ Store original value for change detection
                table_widget.setItem(row_idx, col_idx, item)

    table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table_widget.verticalHeader().setVisible(False)

    table_widget.blockSignals(False)  # ✅ Allow actual edits to be detected

def main_menu_page(parent, username ="User"):
    """Creates and displays the upgraded main menu UI with user profile header and unified dark theme."""

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

        QLabel#profileName {
            font-size: 18px;
            font-weight: bold;
            color: #FFFFFF;
        }

        QLabel#profileRole {
            font-size: 13px;
            color: #AAAAAA;
        }

        QLabel#avatar {
            background-color: #3A9EF5;
            border-radius: 25px;
            min-width: 50px;
            min-height: 50px;
            max-width: 50px;
            max-height: 50px;
            font-size: 24px;
            color: white;
            text-align: center;
            qproperty-alignment: AlignCenter;
        }

        QPushButton {
            font-size: 16px;
            font-family: monospace;
            background-color: #3A9EF5;
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
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

    # 🧑‍💼 Profile Header
    profile_layout = QHBoxLayout()
    profile_layout.setSpacing(15)

    avatar = QLabel("👤")
    avatar.setObjectName("avatar")
    avatar.setAlignment(Qt.AlignCenter)

    name_box = QVBoxLayout()
    username = getattr(parent, "username", "User")
    role = getattr(parent, "role", "Technician")

    name_label = QLabel(f"Welcome, {username}")
    name_label.setObjectName("profileName")

    role_label = QLabel(role)
    role_label.setObjectName("profileRole")

    name_box.addWidget(name_label)
    name_box.addWidget(role_label)

    profile_layout.addWidget(avatar)
    profile_layout.addLayout(name_box)
    layout.addLayout(profile_layout)

    # 📌 Menu Title
    title = QLabel("📌 Main Menu")
    title.setObjectName("titleLabel")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    # 📦 Menu Container
    menu_frame = QFrame()
    menu_frame.setObjectName("menuFrame")
    menu_layout = QVBoxLayout(menu_frame)
    menu_layout.setSpacing(18)

    button_data = [
        ("📁  Tables", parent.view_tables),
        ("📝  Add Job Notes", lambda: ask_for_job_id(parent)),
        ("🔍  Query", lambda: run_query(parent.cursor, parent.conn, parent)),
        ("📑  Customer Lookup", parent.Customer_report),
        ("📊  Dashboard", parent.dashboard_page),
        ("⚙️  Settings", lambda: options_page(parent))
    ]

    font_metrics = QFontMetrics(QPushButton().font())
    fixed_width = font_metrics.horizontalAdvance("📊  Dashboard   ") + 40

    for label, command in button_data:
        button = QPushButton(label)
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedHeight(48)
        button.setMinimumWidth(fixed_width)
        button.clicked.connect(command)
        menu_layout.addWidget(button)

    # 🚪 Logout Button
    logout_button = QPushButton("🚪  Logout")
    logout_button.setObjectName("logoutButton")
    logout_button.setCursor(Qt.PointingHandCursor)
    logout_button.setFixedHeight(48)
    logout_button.setMinimumWidth(fixed_width)
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
    layout.setContentsMargins(60, 50, 60, 50)
    layout.setSpacing(30)

    parent.settings_page.setStyleSheet("""
        QWidget {
            background-color: #2E2E2E;
            color: white;
            font-size: 16px;
            font-family: 'Segoe UI', sans-serif;
        }

        QLabel {
            font-size: 26px;
            font-weight: bold;
            color: #3A9EF5;
            padding-bottom: 20px;
        }

        QPushButton {
            background-color: #3A9EF5;
            color: white;
            padding: 14px;
            font-weight: bold;
            font-size: 16px;
            border-radius: 8px;
        }

        QPushButton:hover {
            background-color: #1E7BCC;
        }

        QPushButton:pressed {
            background-color: #1665B3;
        }

        QPushButton#backButton {
            background-color: #D9534F;
        }

        QPushButton#backButton:hover {
            background-color: #C9302C;
        }

        QGroupBox {
            border: 1px solid #3A9EF5;
            border-radius: 10px;
            margin-top: 20px;
        }

        QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 6px 12px;
            font-size: 18px;
            color: #4FC3F7;
        }
    """)

    # 🔹 Title
    title_label = QLabel("⚙️ Settings")
    title_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(title_label)

    # 🔸 Grouped Actions
    action_group = QGroupBox("Database Tools")
    group_layout = QVBoxLayout()
    group_layout.setSpacing(20)

    export_button = QPushButton("📥 Export Entire Database to Excel")
    export_button.clicked.connect(lambda: export_database_to_excel(parent, parent.cursor))
    group_layout.addWidget(export_button)

    backup_button = QPushButton("💾 Backup Database")
    backup_button.clicked.connect(lambda: backup_database(parent.cursor))
    group_layout.addWidget(backup_button)

    scheduling_options_button = QPushButton("⏰ Backup Schedule Options")
    scheduling_options_button.clicked.connect(partial(open_scheduling_options_dialog, parent))
    group_layout.addWidget(scheduling_options_button)

    restore_button = QPushButton("🔄 Create from Backup")
    restore_button.clicked.connect(lambda: restore_database(parent.conn, parent.cursor, parent))
    group_layout.addWidget(restore_button)

    change_password_button = QPushButton("🔑 Change Password")
    change_password_button.clicked.connect(
        lambda: change_db_password(parent.database_config, parent.conn)
    )
    group_layout.addWidget(change_password_button)

    action_group.setLayout(group_layout)
    layout.addWidget(action_group)

    # 🔙 Back Button
    back_button = QPushButton("⬅ Back to Main Menu")
    back_button.setObjectName("backButton")
    back_button.setFixedHeight(45)
    back_button.clicked.connect(lambda: main_menu_page(parent))
    layout.addWidget(back_button, alignment=Qt.AlignCenter)

    # Final layout setup
    parent.settings_page.setLayout(layout)
    parent.central_widget.addWidget(parent.settings_page)
    parent.central_widget.setCurrentWidget(parent.settings_page)

def apply_button_hover_animation(parent, button):
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

def keyPressEvent(parent, event): 
    """Handles key press events for the login window."""
    if event.key() == Qt.Key_Return:  # Check if the "Enter" key is pressed
        parent.login()  # Call the login method

def refresh_page(parent, offset=None):
    parent.table_widget.blockSignals(True)
    parent.table_widget.setRowCount(0)
    
    load_table(
        table_widget=parent.table_widget,
        cursor=parent.cursor,
        table_name=parent.current_table_name,
        update_status_callback=parent.update_status_and_database,
        table_offset=offset if offset is not None else parent.table_offset,
        limit=parent.table_limit,
        event_filter=parent
    )

    parent.table_widget.blockSignals(False)

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

def display_tables_ui(tables, on_table_select_callback):
    """
    Displays a modern searchable UI listing the tables.
    """
    dialog = QDialog()
    dialog.setWindowTitle("📂 Database Tables")
    dialog.setGeometry(400, 250, 420, 480)
    dialog.setStyleSheet("""
        QDialog {
            background-color: #2E2E2E;
            color: white;
            border-radius: 12px;
        }

        QLabel {
            color: #3A9EF5;
            font-weight: bold;
        }

        QLineEdit {
            background-color: #383838;
            border: 1px solid #3A9EF5;
            border-radius: 8px;
            padding: 10px;
            color: white;
            font-size: 14px;
        }

        QPushButton {
            background-color: #D9534F;
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #C9302C;
        }

        QListWidget {
            background-color: #444;
            border-radius: 8px;
            padding: 5px;
            color: white;
        }

        QListWidget::item {
            padding: 10px;
            border-radius: 6px;
        }

        QListWidget::item:selected {
            background-color: #3A9EF5;
            color: white;
        }

        QListWidget::item:hover {
            background-color: #2D8BE7;
        }
    """)

    main_layout = QVBoxLayout()
    main_layout.setSpacing(20)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Title
    title = QLabel("📂 Available Tables")
    title.setAlignment(Qt.AlignCenter)
    title.setFont(QFont("Arial", 20, QFont.Bold))
    main_layout.addWidget(title)

    # Search bar
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("🔍 Search tables...")
    main_layout.addWidget(search_bar)

    # Table list
    table_list = QListWidget()
    table_list.setFont(QFont("Arial", 13))
    icons_enabled = True  # Toggle if you want to use icons or not

    # Store all table names for filtering
    all_tables = tables.copy()

    def populate_list(filter_text=""):
        table_list.clear()
        for table in all_tables:
            if filter_text.lower() in table.lower():
                item = QListWidgetItem(table)
                if icons_enabled:
                    item.setIcon(QIcon("icons/table_icon.png"))
                table_list.addItem(item)

    populate_list()
    main_layout.addWidget(table_list)

    # Selection logic
    def handle_table_selection():
        selected_item = table_list.currentItem()
        if selected_item:
            dialog.close()
            on_table_select_callback(selected_item.text())
        else:
            QMessageBox.warning(dialog, "⚠️ No Selection", "Please select a table.")

    table_list.itemDoubleClicked.connect(handle_table_selection)

    # Also support Enter key
    table_list.setFocus()
    table_list.setCurrentRow(0)
    table_list.returnPressed = handle_table_selection  # pseudo-handler for idea clarity
    table_list.keyPressEvent = lambda e: (
        handle_table_selection() if e.key() == Qt.Key_Return else QListWidget.keyPressEvent(table_list, e)
    )

    # Search bar filter logic
    search_bar.textChanged.connect(lambda text: populate_list(text))

    # Close button
    close_button = QPushButton("❌ Close")
    close_button.setFont(QFont("Arial", 12))
    close_button.clicked.connect(dialog.close)
    main_layout.addWidget(close_button)

    # Apply layout
    dialog.setLayout(main_layout)

    # Fade-in animation
    animation = QPropertyAnimation(dialog, b"windowOpacity")
    animation.setDuration(300)
    animation.setStartValue(0)
    animation.setEndValue(1)
    animation.setEasingCurve(QEasingCurve.InOutQuad)
    animation.start()

    dialog.exec_()

def handle_login(ui_instance, database_config, connect_func, on_success_callback):
    """
    Handles login interaction, connection attempt, and page transition.
    """

    username = ui_instance.username_entry.text().strip()
    password = ui_instance.password_entry.text()
    host = database_config.get("host", "localhost")
    database = database_config.get("database", "")

    ssl_config = database_config.get("ssl", {})
    ssl_enabled = ssl_config.get("enabled", False)
    ssl_cert_path = ssl_config.get("cert_path", "").strip()

    if not username or not password or not database:
        msg = QMessageBox(ui_instance)
        msg.setWindowTitle("❌ Missing Fields")
        msg.setText("Please fill in all fields and ensure settings are configured.")
        msg.setIcon(QMessageBox.Critical)
        msg.setStyleSheet(_custom_messagebox_stylesheet())
        msg.exec_()
        return

    try:
        conn, cursor = connect_func(
            username, password, host, database, ssl_enabled, ssl_cert_path
        )

        # Store connection info
        ui_instance.conn = conn
        ui_instance.cursor = cursor
        ui_instance.username = username
        ui_instance.role = "Technician"  # Swap for actual role lookup if available

        # Success feedback
        success_msg = QMessageBox(ui_instance)
        success_msg.setWindowTitle("✅ Login Successful")
        success_msg.setText(
            f"<b>Successfully connected to:</b><br><br>"
            f"📂 <b>Database:</b> {database}<br>"
            f"🌍 <b>Host:</b> {host}"
        )
        success_msg.setIcon(QMessageBox.Information)
        success_msg.setStyleSheet(_custom_messagebox_stylesheet())
        success_msg.exec_()

        # Cleanup
        ui_instance.password_entry.clear()

        # Redirect to main app view
        on_success_callback(ui_instance)

    except Exception as e:
        # Avoid leaking technical errors unless debugging
        error_msg = QMessageBox(ui_instance)
        error_msg.setWindowTitle("⚠️ Connection Failed")
        error_msg.setText("Could not connect to the database.\n\nPlease check your credentials or network settings.")
        error_msg.setDetailedText(str(e))  # Expandable in case user clicks "Show Details"
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setStyleSheet(_custom_messagebox_stylesheet())
        error_msg.exec_()

        ui_instance.password_entry.clear()

def _custom_messagebox_stylesheet():
    return """
        QMessageBox {
            background-color: #2E2E2E;
            color: white;
            font-size: 15px;
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
    """

def handle_logout(ui_instance):
    """Logs out the user, resets UI elements, and closes DB connection."""

    confirm = QMessageBox.question(
        ui_instance, "Logout", "Are you sure you want to log out?",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    )

    if confirm != QMessageBox.Yes:
        return

    # 🔒 Reset to login page
    ui_instance.central_widget.setCurrentWidget(ui_instance.login_page)

    # 🔐 Clear stored login entries
    ui_instance.username_entry.clear()
    ui_instance.password_entry.clear()

    # 🔄 Recreate the settings page (fresh)
    ui_instance.settings_page, ui_instance.host_entry, ui_instance.database_entry, ui_instance.ssl_checkbox, ui_instance.ssl_path_entry = create_settings_page(
        ui_instance.database_config,
        lambda: save_settings(
            ui_instance.database_config,
            ui_instance.host_entry,
            ui_instance.database_entry,
            ui_instance.password_entry,
            ui_instance.ssl_checkbox,
            ui_instance.ssl_path_entry,
            ui_instance.SETTINGS_FILE,
            ui_instance.central_widget,
            ui_instance.login_page
        ),
        lambda: ui_instance.central_widget.setCurrentWidget(ui_instance.login_page)
    )

    ui_instance.settings_page.setStyleSheet("""
        QWidget {
            background-color: #2E2E2E;
            color: white;
        }
        QLabel {
            font-size: 16px;
            font-weight: bold;
            color: #3A9EF5;
        }
        QLineEdit {
            background-color: #444;
            color: white;
            border: 1px solid #3A9EF5;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton {
            background-color: #3A9EF5;
            color: white;
            padding: 10px;
            font-weight: bold;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #1E7BCC;
        }
        QPushButton#backButton {
            background-color: #666;
        }
        QPushButton#backButton:hover {
            background-color: #888;
        }
    """)

    ui_instance.central_widget.addWidget(ui_instance.settings_page)

    # ❌ Close the DB connection (securely)
    ui_instance.conn = close_connection(getattr(ui_instance, "conn", None))
    ui_instance.cursor = None

    # ✅ Let the user know they're out
    QMessageBox.information(ui_instance, "Logged Out", "✅ You have been successfully logged out.")

def load_table(table_widget, cursor, table_name, update_status_callback, table_offset=0, limit=50, event_filter=None):

        # ✅ Refresh the connection
    if hasattr(cursor, "connection"):
        cursor.connection.commit()  # Pull latest committed data
        cursor = cursor.connection.cursor()  # Create a fresh cursor

    data = fetch_table_data(cursor, table_name, limit, table_offset)
    total_rows = len(data)

    primary_key_column = fetch_primary_key_column(cursor, table_name)
    data = fetch_table_data(cursor, table_name, limit, table_offset, order_by=primary_key_column)

    if not primary_key_column:
        print(f"❌ ERROR: No primary key found for table {table_name}.")
        return

    # Determine primary key column index
    primary_key_index = next(
        (i for i in range(table_widget.columnCount())
         if table_widget.horizontalHeaderItem(i).text() == primary_key_column),
        None
    )

    table_widget.clearContents()
    table_widget.setRowCount(total_rows)

    # Optional: handle 'jobs' specific logic
    status_column_index = None
    if table_name == "jobs":
        status_column_index = next(
            (i for i in range(table_widget.columnCount())
             if table_widget.horizontalHeaderItem(i).text().lower() == "status"),
            None
        )

    for row_idx, row_data in enumerate(data):
        for col_idx, value in enumerate(row_data):
            if col_idx == status_column_index:
                combo = QComboBox()
                combo.addItems(["Waiting for Parts", "In Progress", "Completed", "Picked Up"])
                options = [combo.itemText(i) for i in range(combo.count())]
                combo.setCurrentText(value if value in options else "In Progress")
                combo.setEditable(False)
                if event_filter:
                    combo.installEventFilter(event_filter)
                combo.currentTextChanged.connect(lambda text, row=row_idx: update_status_callback(row, text))
                table_widget.setCellWidget(row_idx, col_idx, combo)
            else:
                item = QTableWidgetItem(str(value) if value is not None else "")
                if col_idx == primary_key_index:
                    item.setData(Qt.UserRole, str(value))
                table_widget.setItem(row_idx, col_idx, item)

    table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table_widget.verticalHeader().setVisible(False)

def update_table_offset_ui(
    table_widget,
    pagination_label,
    prev_button,
    next_button,
    fetch_function,
    table_name,
    current_offset,
    limit,
    change,  # <- not needed anymore
    refresh_callback,
    parent=None
):
    # ✅ Fetch new page data based on fixed offset
    data = fetch_function(table_name, limit, current_offset)
    total_rows = len(data)

    # ✅ Stop if you're at the end
    if not data and current_offset > 0:
        if parent:
            QMessageBox.information(parent, "End of Data", "No more records to load.")
        return

    # ✅ Clear and refill table
    table_widget.clearContents()
    table_widget.setRowCount(total_rows)
    refresh_callback()

    # ✅ Reset scroll bar
    table_widget.verticalScrollBar().setValue(0)

    # ✅ Update page label
    current_page = (current_offset // limit) + 1
    pagination_label.setText(f"Page {current_page}")

    # ✅ Update buttons
    prev_button.setEnabled(current_offset > 0)
    next_button.setEnabled(total_rows == limit)

def create_table_view_dialog(
    table_name,
    columns,
    table_widget,
    pagination_label,
    refresh_handler,
    search_handler,
    prev_handler,
    next_handler,
    add_handler,
    edit_handler,
    delete_handler,
    close_handler
):
    dialog = QDialog()
    dialog.setWindowFlags(Qt.Window)
    dialog.setWindowTitle(f"{table_name} Data")
    dialog.showMaximized()
    dialog.setFont(QFont("Segoe UI", 10))
    dialog.setStyleSheet("background-color: #1F1F1F; color: #E0E0E0;")

    main_layout = QVBoxLayout()

    # ───────────────────── Title
    title = QLabel(f"📊 {table_name} Data")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("color: #2D9CDB; padding: 20px; font-size: 20px;")
    main_layout.addWidget(title)

    # ───────────────────── Search Bar
    search_layout = QHBoxLayout()

    search_entry = QLineEdit()
    search_entry.setPlaceholderText("Enter search query...")
    search_entry.setFont(QFont("Segoe UI", 10))
    search_entry.setStyleSheet("""
        background-color: #2A2A2A;
        color: #E0E0E0;
        padding: 6px;
        border-radius: 5px;
        border: 1px solid #3A3A3A;
    """)

    clear_action = QAction(search_entry)
    clear_action.setIcon(search_entry.style().standardIcon(QStyle.SP_DialogCloseButton))
    clear_action.triggered.connect(search_entry.clear)
    search_entry.addAction(clear_action, QLineEdit.TrailingPosition)

    refresh_button = QPushButton("🔃")
    refresh_button.clicked.connect(refresh_handler)
    refresh_button.setFont(QFont("Segoe UI", 10))
    refresh_button.setFixedHeight(32)
    refresh_button.setStyleSheet("""
        QPushButton {
            background-color: #2D9CDB;
            color: white;
            border-radius: 5px;
            padding: 4px 12px;
        }
        QPushButton:hover {
            background-color: #2385BA;
        }
    """)

    # ───── Filter Button
    filter_toggle_btn = QPushButton("🔍 Filter Columns ▾")
    filter_toggle_btn.setFont(QFont("Segoe UI", 10))
    filter_toggle_btn.setFixedHeight(32)
    filter_toggle_btn.setStyleSheet("""
        QPushButton {
            background-color: #2A2A2A;
            color: #2D9CDB;
            border: 1px solid #2D9CDB;
            border-radius: 5px;
            padding: 4px 12px;
        }
        QPushButton:hover {
            background-color: #1A1A1A;
        }
    """)

    # ───── Floating Filter Panel
    filter_popup = QFrame(dialog)
    filter_popup.setFrameShape(QFrame.StyledPanel)
    filter_popup.setStyleSheet("""
        QFrame {
            background-color: #1F1F1F;
            border: 1px solid #3A3A3A;
            border-radius: 8px;
        }
    """)
    filter_popup.setFixedSize(220, 250)
    filter_popup.setVisible(False)

    popup_layout = QVBoxLayout(filter_popup)
    popup_layout.setContentsMargins(8, 8, 8, 8)

    column_list = QListWidget(filter_popup)
    column_list.setSelectionMode(QAbstractItemView.MultiSelection)
    column_list.setStyleSheet("""
    QListWidget {
        background-color: #2A2A2A;
        color: #E0E0E0;
        border: none;
    }
    QListWidget::item:selected {
        background-color: #2D9CDB;
        color: white;
    }
    QListWidget::item:hover {
        background-color: #333333;
    }
    QScrollBar:vertical {
        background: #2A2A2A;
        width: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #555555;
        border-radius: 4px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
""")

    column_list.setAlternatingRowColors(False)


    for col in columns:
        item = QListWidgetItem(col)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        column_list.addItem(item)

    popup_layout.addWidget(column_list)

    def toggle_filter_popup():
        if filter_popup.isVisible():
            filter_popup.setVisible(False)
        else:
            button_pos = filter_toggle_btn.mapToGlobal(filter_toggle_btn.rect().bottomLeft())
            dialog_pos = dialog.mapFromGlobal(button_pos)
            filter_popup.move(dialog_pos)
            filter_popup.setVisible(True)
            filter_popup.raise_()

    filter_toggle_btn.clicked.connect(toggle_filter_popup)

    def get_checked_columns():
        checked = [
            column_list.item(i).text()
            for i in range(column_list.count())
            if column_list.item(i).checkState() == Qt.Checked
        ]
        return checked if checked else columns  # fallback to all columns


    search_entry.textChanged.connect(
        lambda text: search_handler(get_checked_columns(), text)
    )

    # Layout: search bar row
    search_layout.addWidget(filter_toggle_btn)
    search_layout.addWidget(search_entry)
    search_layout.addWidget(refresh_button)
    main_layout.addLayout(search_layout)

    # Add popup to top-level (it floats)
    filter_popup.setParent(dialog)

    # ───────────────────── Table
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    table_widget.setStyleSheet("""
        QTableWidget {
            background-color: #2A2A2A;
            color: #E0E0E0;
            gridline-color: #3A3A3A;
            selection-background-color: #2D9CDB;
            selection-color: #FFFFFF;
            font-size: 10pt;
        }
        QTableWidget::item {
            background-color: #2E2E2E;
        }
        QHeaderView::section {
            background-color: #2D2D2D;
            color: #E0E0E0;
            font-weight: bold;
            padding: 8px;
            border: 0px;
        }
    """)

    table_widget.setAlternatingRowColors(False)
    scroll_area.setWidget(table_widget)
    main_layout.addWidget(scroll_area)

    # ───────────────────── Pagination
    pagination_layout = QHBoxLayout()
    pagination_layout.addStretch(1)

    prev_button = QPushButton("⬅ Prev")
    next_button = QPushButton("Next ➡")

    prev_button.clicked.connect(prev_handler)
    next_button.clicked.connect(next_handler)

    for btn in [prev_button, next_button]:
        btn.setFont(QFont("Segoe UI", 10))
        btn.setFixedSize(120, 40)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2D9CDB;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2385BA;
            }
        """)

    pagination_label.setFont(QFont("Segoe UI", 10))
    pagination_label.setAlignment(Qt.AlignCenter)
    pagination_label.setStyleSheet("padding: 0 15px;")

    pagination_layout.addWidget(prev_button)
    pagination_layout.addWidget(pagination_label)
    pagination_layout.addWidget(next_button)
    pagination_layout.addStretch(1)
    main_layout.addLayout(pagination_layout)

    # ───────────────────── CRUD Buttons
    button_layout = QHBoxLayout()
    button_layout.addStretch(1)

    def styled_button(text, handler, color, hover="#666666"):
        btn = QPushButton(text)
        btn.setFixedSize(150, 40)
        btn.clicked.connect(handler)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """)
        return btn

    button_layout.addWidget(styled_button("➕ Add Record", add_handler, "#2D9CDB", "#2385BA"))

    if table_name.lower() == "jobs":
        button_layout.addWidget(styled_button("📝 Edit Job", edit_handler, "#FFA500", "#CC8400"))

    button_layout.addWidget(styled_button("🗑 Delete Record", delete_handler, "#D9534F", "#C9302C"))
    button_layout.addWidget(styled_button("❌ Close", close_handler, "#444444", "#666666"))
    button_layout.addStretch(1)
    main_layout.addLayout(button_layout)

    # ───────────────────── Status Bar
    status_bar = QLabel("✅ Ready")
    status_bar.setFont(QFont("Segoe UI", 9))
    status_bar.setStyleSheet("""
        background-color: #2A2A2A;
        color: #AAAAAA;
        padding: 8px 12px;
        border-top: 1px solid #3A3A3A;
    """)
    main_layout.addWidget(status_bar)

    dialog.setLayout(main_layout)

    return dialog, prev_button, next_button, refresh_button, status_bar

def run_query(cursor, conn, parent=None):
    query_window = QDialog(parent)
    query_window.setWindowTitle("📊 Run SQL Query")
    query_window.setGeometry(100, 100, 800, 650)
    query_window.setStyleSheet("""
        QDialog {
            background-color: #1E1E1E;
            color: #E0E0E0;
            font-family: 'Segoe UI';
            font-size: 11pt;
        }
        QLabel {
            font-weight: bold;
            color: #4FC3F7;
        }
        QTextEdit {
            background-color: #2B2B2B;
            color: #FFFFFF;
            border: 1px solid #3A3A3A;
            border-radius: 5px;
        }
        QTableWidget {
            background-color: #242424;
            color: #FFFFFF;
            border: 1px solid #3A3A3A;
            border-radius: 5px;
            gridline-color: #3A3A3A;
            selection-background-color: #3A9EF5;
            selection-color: #FFFFFF;
            font-size: 10pt;
        }
        QTableWidget::item {
            background-color: #2E2E2E;
        }
        QTableWidget::item:alternate {
            background-color: #262626;
        }
        QHeaderView::section {
            background-color: #3A3A3A;
            color: #FFFFFF;
            font-weight: bold;
            padding: 6px;
            border: 0;
        }
        QPushButton {
            background-color: #3A9EF5;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #2385BA;
        }
    """)

    layout = QVBoxLayout()

    query_label = QLabel("📝 Enter SQL Query:")
    layout.addWidget(query_label)

    query_input = QTextEdit()
    query_input.setPlaceholderText("Type your SQL query here...")
    query_input.setFixedHeight(120)
    layout.addWidget(query_input)

    results_label = QLabel("📊 Query Results:")
    layout.addWidget(results_label)

    results_table = QTableWidget()
    results_table.setAlternatingRowColors(True)
    results_table.setStyleSheet("""
        QTableWidget::item {
            background-color: #2E2E2E;
        }
        QTableWidget::item:alternate {
            background-color: #262626;
        }
    """)
    layout.addWidget(results_table)

    query_results = []

    def execute_query():
        nonlocal query_results
        query = query_input.toPlainText().strip()
        try:
            result = execute_sql_query(cursor, conn, query)
            if result["type"] == "select":
                query_results[:] = result["results"]
                headers = result["headers"]

                results_table.setRowCount(len(query_results))
                results_table.setColumnCount(len(headers))
                results_table.setHorizontalHeaderLabels(headers)

                for row_idx, row in enumerate(query_results):
                    for col_idx, value in enumerate(row):
                        item = QTableWidgetItem(str(value))
                        results_table.setItem(row_idx, col_idx, item)

                results_table.resizeColumnsToContents()
                QMessageBox.information(query_window, "✅ Success", "Query executed successfully.")
            else:
                QMessageBox.information(query_window, "✅ Success", f"{result['rowcount']} rows affected.")
        except Exception as e:
            QMessageBox.critical(query_window, "⚠ Error", f"Failed to execute query:\n{e}")

    def export_to_excel():
        if not query_results:
            QMessageBox.critical(query_window, "⚠ Error", "No data to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(query_window, "Save File", "", "Excel Files (*.xlsx);;All Files (*)")
        if file_path:
            try:
                headers = [desc[0] for desc in cursor.description]
                export_query_results_to_excel(query_results, headers, file_path)
                QMessageBox.information(query_window, "✅ Success", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(query_window, "⚠ Error", f"Export failed:\n{e}")

    def clear_query():
        query_input.clear()

    def clear_results():
        results_table.setRowCount(0)

    button_layout = QHBoxLayout()
    button_layout.setSpacing(10)

    for label, func, color in [
        ("🚀 Execute Query", execute_query, "#3A9EF5"),
        ("📂 Export to Excel", export_to_excel, "#4CAF50"),
        ("📝 Clear Query", clear_query, "#D9534F"),
        ("🗑 Clear Results", clear_results, "#D9534F")
    ]:
        btn = QPushButton(label)
        btn.clicked.connect(func)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #666666;
            }}
        """)
        button_layout.addWidget(btn)

    layout.addLayout(button_layout)
    query_window.setLayout(layout)
    query_window.exec_()

def add_record_dialog(table_name, columns, column_types, db_insert_func, refresh_callback, parent=None):
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFrame, QGridLayout, QLineEdit, QTextEdit, QComboBox,
        QMessageBox, QSizePolicy
    )
    from PyQt5.QtCore import Qt
    from datetime import datetime

    add_window = QDialog(parent)
    add_window.setWindowTitle(f"➕ Add Record to {table_name}")
    add_window.setFixedSize(640, 740)
    add_window.setStyleSheet("""
        QDialog {
            background-color: #121212;
            color: #E0E0E0;
            font-size: 14px;
        }
    """)

    layout = QVBoxLayout(add_window)
    layout.setContentsMargins(30, 30, 30, 20)
    layout.setSpacing(25)

    # ───── Card Frame
    card = QFrame()
    card.setStyleSheet("""
        QFrame {
            background-color: #1C1C1C;
            border-radius: 12px;
            padding: 25px;
            border: 1px solid #2A2A2A;
        }
    """)
    card_layout = QVBoxLayout(card)
    card_layout.setSpacing(30)

    # ───── Title
    title = QLabel(f"➕ Add New Entry to '{table_name}'")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("""
        font-size: 22px;
        font-weight: bold;
        color: #2D9CDB;
        padding-bottom: 6px;
    """)
    card_layout.addWidget(title)

    # ───── Form Grid
    form_grid = QGridLayout()
    form_grid.setHorizontalSpacing(20)
    form_grid.setVerticalSpacing(16)

    entry_widgets = {}
    non_auto_columns = [col for col in columns if col != columns[0]]
    row = 0

    for col in non_auto_columns:
        label = QLabel(col)
        label.setStyleSheet("""
            color: #B0B0B0;
            font-weight: 600;
            font-size: 13px;
        """)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setFixedWidth(140)

        col_type = column_types.get(col, "").lower()
        entry = None

        # Smart field handling
        if col.lower() == "status":
            entry = QComboBox()
            entry.addItems(["In Progress", "Waiting for Parts", "Completed", "Picked Up"])
            entry.setCurrentText("In Progress")

        elif col.lower() == "datasave":
            entry = QLineEdit("1")

        elif col.lower() in ["startdate", "date"] or ("date" in col_type and col.lower() != "enddate"):
            entry = QLineEdit(datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S") if "time" in col_type else datetime.now().strftime("%Y-%m-%d"))
            entry.setPlaceholderText("YYYY-MM-DD or timestamp")

        elif col.lower() == "enddate":
            entry = QLineEdit()
            entry.setPlaceholderText("Leave empty unless ending now")

        elif "text" in col_type or "varchar(255)" in col_type:
            entry = QTextEdit()
            entry.setMinimumHeight(80)
        else:
            entry = QLineEdit()

        entry.setStyleSheet("""
            QLineEdit, QTextEdit, QComboBox {
                background-color: #1E1E1E;
                color: white;
                border: 1px solid #3A9EF5;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #2D9CDB;
            }
        """)

        # Size consistency
        if isinstance(entry, QLineEdit):
            entry.setMinimumHeight(36)
        elif isinstance(entry, QTextEdit):
            entry.setMinimumHeight(80)
        elif isinstance(entry, QComboBox):
            entry.setMinimumHeight(36)

        entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        entry_widgets[col] = entry

        form_grid.addWidget(label, row, 0)
        form_grid.addWidget(entry, row, 1)
        row += 1

    card_layout.addLayout(form_grid)
    card_layout.addStretch()

    # ───── Buttons
    button_layout = QHBoxLayout()
    button_layout.setSpacing(20)
    button_layout.addStretch(1)

    save_button = QPushButton("💾 Save")
    cancel_button = QPushButton("❌ Cancel")

    save_button.setStyleSheet("""
        QPushButton {
            background-color: #4CAF50;
            color: white;
            padding: 10px 24px;
            font-weight: bold;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #3FA045;
        }
    """)
    cancel_button.setStyleSheet("""
        QPushButton {
            background-color: #F44336;
            color: white;
            padding: 10px 24px;
            font-weight: bold;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #D32F2F;
        }
    """)

    button_layout.addWidget(save_button)
    button_layout.addWidget(cancel_button)
    button_layout.addStretch(1)
    card_layout.addLayout(button_layout)

    layout.addWidget(card)

    # ───── Save Logic
    def save():
        values = []
        for widget in entry_widgets.values():
            if isinstance(widget, QTextEdit):
                value = widget.toPlainText().strip()
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            else:
                value = widget.text().strip()
            values.append(value if value else None)

        success = db_insert_func(table_name, non_auto_columns, values)
        if success:
            msg = QMessageBox(parent)
            msg.setWindowTitle("✅ Success")
            msg.setText("Record added successfully!")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1E1E1E;
                    color: white;
                    border-radius: 10px;
                }
                QLabel {
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton {
                    background-color: #3A9EF5;
                    color: white;
                    padding: 8px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #307ACC;
                }
            """)
            msg.exec_()
            refresh_callback()
            add_window.accept()
        else:
            QMessageBox.critical(add_window, "❌ Error", "Failed to add record.")

    save_button.clicked.connect(save)
    cancel_button.clicked.connect(add_window.reject)

    # Auto focus first field
    if entry_widgets:
        first_widget = next(iter(entry_widgets.values()))
        if hasattr(first_widget, "setFocus"):
            first_widget.setFocus()

    add_window.exec_()
