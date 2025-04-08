from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, QByteArray
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QComboBox, QTableWidgetItem, QMessageBox, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QComboBox

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

def create_settings_page(database_config, on_save, on_back):
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(50, 50, 50, 50)
    layout.setAlignment(Qt.AlignCenter)

    page.setStyleSheet(""" ... your full stylesheet ... """)

    title = QLabel("⚙ Settings")
    title.setFont(QFont("Arial", 24, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    form_layout = QFormLayout()

    host_entry = QLineEdit(database_config["host"])
    host_entry.setPlaceholderText("Enter Database Host")
    form_layout.addRow("🌐 Host:", host_entry)

    database_entry = QLineEdit(database_config["database"])
    database_entry.setPlaceholderText("Enter Database Name")
    form_layout.addRow("💾 Database:", database_entry)

    layout.addLayout(form_layout)

    save_button = QPushButton("💾 Save Settings")
    save_button.clicked.connect(on_save)
    layout.addWidget(save_button)

    back_button = QPushButton("⬅ Back")
    back_button.setObjectName("backButton")
    back_button.clicked.connect(on_back)
    layout.addWidget(back_button)

    return page, host_entry, database_entry


def main_menu_page(parent):
    """Creates and displays the main menu UI with improved layout, centered text, and aligned emojis."""

    if hasattr(parent, "main_menu"):
        parent.central_widget.setCurrentWidget(parent.main_menu)
        return

    parent.main_menu = QWidget()
    layout = QVBoxLayout(parent.main_menu)
    layout.setContentsMargins(40, 20, 40, 20)
    layout.setSpacing(15)

    title = QLabel("📌 Main Menu")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("""
        font-size: 26px;
        font-weight: bold;
        color: #FFFFFF;
        padding: 10px;
        border-bottom: 2px solid #3A9EF5;
    """)
    layout.addWidget(title)

    menu_frame = QFrame()
    menu_frame.setStyleSheet("""
        background-color: #2E2E2E;
        border-radius: 10px;
        padding: 20px;
    """)
    menu_layout = QVBoxLayout(menu_frame)
    menu_layout.setSpacing(12)

    from ui import options_page  # local import to avoid circular issues

    button_data = [
        ("📁  Tables", parent.view_tables),
        ("📝  Add Job Notes", parent.ask_for_job_id),
        ("🔍  Query", parent.run_query),
        ("📑  Customer Lookup", parent.Customer_report),
        ("📊  Dashboard", parent.dashboard_page),
        ("⚙️  Settings", lambda: options_page(parent))
    ]

    font_metrics = QFontMetrics(QPushButton().font())
    fixed_width = font_metrics.horizontalAdvance("🔄  Sync Google Forms  ")

    for label, command in button_data:
        button = QPushButton(label)
        button.setCursor(Qt.PointingHandCursor)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setMinimumWidth(fixed_width)
        button.setFixedHeight(45)
        button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-family: monospace;
                background-color: #3A9EF5;
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #307ACC;
            }
        """)
        button.clicked.connect(command)
        menu_layout.addWidget(button)

    logout_button = QPushButton("🚪  Logout")
    logout_button.setCursor(Qt.PointingHandCursor)
    logout_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    logout_button.setMinimumWidth(fixed_width)
    logout_button.setFixedHeight(45)
    logout_button.setStyleSheet("""
        QPushButton {
            font-size: 16px;
            font-family: monospace;
            background-color: #D9534F;
            color: white;
            padding: 12px;
            border-radius: 5px;
            font-weight: bold;
            text-align: center;
        }
        QPushButton:hover {
            background-color: #C9302C;
        }
    """)
    logout_button.clicked.connect(parent.logout)
    menu_layout.addWidget(logout_button)

    menu_frame.setLayout(menu_layout)
    layout.addWidget(menu_frame)

    parent.main_menu.setLayout(layout)
    parent.central_widget.addWidget(parent.main_menu)
    parent.central_widget.setCurrentWidget(parent.main_menu)

def create_login_page(parent):  # UI, pass the parent (main window) as a parameter
    """Creates a modern, visually appealing login UI with improved layout and animations."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(50, 50, 50, 50)
    layout.setSpacing(20)  # Increased spacing for a cleaner look
    layout.setAlignment(Qt.AlignCenter)

    # 🎨 **Dark Mode Styling**
    page.setStyleSheet("""
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
            border-radius: 8px;
            padding: 10px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border: 2px solid #3A9EF5;
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
        }
        QPushButton#toggleButton:hover {
            background-color: #777;
        }
        QLabel#errorLabel {
            color: #FF5555;
            font-size: 14px;
            font-weight: bold;
        }
    """)

    # 🔹 **Title Label**
    title = QLabel("🩺 Database Doctor")
    title.setFont(QFont("Arial", 26, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    # 🔹 **Error Message Label**
    parent.error_label = QLabel("")
    parent.error_label.setObjectName("errorLabel")
    parent.error_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(parent.error_label)

    # 🔹 **Form Layout (Username & Password)**
    form_layout = QFormLayout()
    form_layout.setSpacing(15)

    parent.username_entry = QLineEdit()
    parent.username_entry.setPlaceholderText("Enter your username")
    form_layout.addRow("👤 Username:", parent.username_entry)

    parent.password_entry = QLineEdit()
    parent.password_entry.setPlaceholderText("Enter your password")
    parent.password_entry.setEchoMode(QLineEdit.Password)
    form_layout.addRow("🔒 Password:", parent.password_entry)

    layout.addLayout(form_layout)

    # 🔹 **Password Toggle Button**
    toggle_layout = QHBoxLayout()
    toggle_layout.setAlignment(Qt.AlignRight)

    toggle_button = QPushButton("👁 Show")
    toggle_button.setObjectName("toggleButton")
    toggle_button.setCheckable(True)
    toggle_button.setFixedWidth(60)

    def toggle_password():
        """Toggles password visibility with animation."""
        if toggle_button.isChecked():
            parent.password_entry.setEchoMode(QLineEdit.Normal)
            toggle_button.setText("🙈 Hide")
        else:
            parent.password_entry.setEchoMode(QLineEdit.Password)
            toggle_button.setText("👁 Show")

    toggle_button.clicked.connect(toggle_password)
    toggle_layout.addWidget(toggle_button)
    layout.addLayout(toggle_layout)

    # 🔹 **Login Button with Animation**
    parent.login_button = QPushButton("🔓 Login")
    parent.login_button.setFixedHeight(50)
    parent.login_button.setObjectName("animatedButton")
    parent.login_button.clicked.connect(parent.login)
    layout.addWidget(parent.login_button)

    # 🔹 **Settings Button with Animation**
    parent.settings_button = QPushButton("⚙ Settings")
    parent.settings_button.setObjectName("settingsButton")
    parent.settings_button.setFixedHeight(40)
    parent.settings_button.clicked.connect(lambda: parent.central_widget.setCurrentWidget(parent.settings_page))
    layout.addWidget(parent.settings_button)

    # 🔹 **Apply Animation to Buttons**
    apply_button_hover_animation(parent, parent.login_button)
    apply_button_hover_animation(parent, parent.settings_button)

    return page

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
    export_button.clicked.connect(parent.export_database_to_excel)
    layout.addWidget(export_button)

    backup_button = QPushButton("💾 Backup Database")
    backup_button.clicked.connect(parent.backup_database)
    layout.addWidget(backup_button)

    # 🕓 Backup Schedule Button
    scheduling_options_button = QPushButton("⏰ Backup Schedule Options")
    from functools import partial
    from ui import open_scheduling_options_dialog
    scheduling_options_button.clicked.connect(partial(open_scheduling_options_dialog, parent))
    layout.addWidget(scheduling_options_button)

    restore_button = QPushButton("🔄 Create from Backup")
    restore_button.clicked.connect(parent.restore_database)
    layout.addWidget(restore_button)

    change_password_button = QPushButton("🔑 Change Password")
    change_password_button.clicked.connect(parent.change_db_password)
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
    schedule_button.clicked.connect(parent.open_schedule_backup_dialog)
    layout.addWidget(schedule_button)

    # ✅ View Current Schedule
    view_schedule_button = QPushButton("👀 View Current Schedule")
    view_schedule_button.clicked.connect(parent.view_current_schedule)
    layout.addWidget(view_schedule_button)

    # ✅ Clear Current Schedule
    clear_schedule_button = QPushButton("🧹 Clear Current Schedule")
    clear_schedule_button.clicked.connect(parent.clear_current_schedule)
    layout.addWidget(clear_schedule_button)

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
