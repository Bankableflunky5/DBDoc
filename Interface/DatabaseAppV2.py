# ─────────────────────────────────────────────────────────────────────────────
# 📦 Standard Library
import sys
import threading
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# 🛢 Database
import mariadb

# ─────────────────────────────────────────────────────────────────────────────
# 📊 Data Handling & Visualization
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# ─────────────────────────────────────────────────────────────────────────────
# 🎨 PyQt5 Core & GUI
from PyQt5.QtCore import QDate, QDateTime, Qt
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QComboBox, QDialog, QFileDialog,
    QFormLayout, QHBoxLayout, QHeaderView, QInputDialog,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QStackedWidget,
    QStyle, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget
)

# ─────────────────────────────────────────────────────────────────────────────
# 🧩 Project Modules
from FILE_OPS.file_ops import (
    load_schedule_on_startup, load_settings,
    run_scheduled_backups, schedule_backup
)

from UI.ui import (
    create_login_page, create_settings_page, display_tables_ui,
    edit_selected_job, event_filter, keyPressEvent, main_menu_page,
    refresh_page, reset_window_size, save_settings, handle_login, 
    handle_logout, load_table, populate_table, update_table_offset_ui
)

from UI.splashscreen import SplashScreen
from UI.initthread import InitializationThread

from data_access import fetch_tables, connect_to_database, fetch_data,  get_primary_key_column, check_primary_key_exists, check_duplicate_primary_key, update_column, update_primary_key, update_auto_increment_if_needed

from error_utils import handle_db_error, log_error
from data_access import update_status, fetch_primary_key_column
from data_access import fetch_table_data_with_columns
from UI.ui import create_table_view_dialog  # You’ll create this in ui.py



class DatabaseApp(QMainWindow):
    SETTINGS_FILE = "settings.json"
    SCHEDULE_FILE_PATH = "backup_schedule.json"
    
    def __init__(self): #MAIN
        super().__init__()
        

        # ✅ Load and apply scheduled jobs
        load_schedule_on_startup(self)

        self.is_refreshing = False
        self.is_backup_running = False
        self.is_adding_new_record = False
        

        self.setWindowTitle("The Laptop Doctor")
        self.setGeometry(100, 100, 500, 500)
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QLabel { color: #FFFFFF; font-size: 14px; }
            QLineEdit { background-color: #2A2A2A; color: #FFFFFF; border: 1px solid #444; padding: 5px; border-radius: 5px; }
            QPushButton { background-color: #3A9EF5; color: #FFFFFF; border-radius: 5px; padding: 10px; }
            QPushButton:hover { background-color: #1D7DD7; }
        """)

        # ✅ Load database settings
        self.database_config = load_settings()

        # ✅ UI Page setup
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.login_page = create_login_page(self)
        self.settings_page, self.host_entry, self.database_entry, self.ssl_checkbox, self.ssl_path_entry = create_settings_page(
            self.database_config,
            lambda: save_settings(self.database_config, self.host_entry, self.database_entry, self.password_entry, self.ssl_checkbox, self.ssl_path_entry, self.SETTINGS_FILE, self.central_widget, self.login_page, self),
            lambda: self.central_widget.setCurrentWidget(self.login_page)
        )

        self.central_widget.addWidget(self.login_page)
        self.central_widget.addWidget(self.settings_page)

        # ✅ Start backup scheduler thread
        self.scheduler_stop_event = threading.Event()
        self.scheduler_thread = threading.Thread(
            target=run_scheduled_backups,
            args=(self.scheduler_stop_event,),
            daemon=True
        )
        self.scheduler_thread.start()
    
    def view_tables(self): #MAIN
        try:
            tables = fetch_tables(self.cursor)
            display_tables_ui(tables, self.view_table_data)
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))

    def keyPressEvent(self, event): #MAIN
        keyPressEvent(self, event)  # Calls the one from ui.py

    def login(self): #MAIN
        handle_login(
            ui_instance=self,
            database_config=self.database_config,
            connect_func=connect_to_database,
            on_success_callback=main_menu_page
        )

    def fetch_data(self, table_name, limit=50, offset=0): #MAIN
        return fetch_data(self.cursor, table_name, limit, offset)

    def logout(self): #MAIN
        handle_logout(self)

    def eventFilter(self, source, event): #MAIN
            return event_filter(self, source, event)

    def update_table_offset(self, change, prev_button, next_button):
        # ✅ Compute new offset safely
        new_offset = max(0, self.table_offset + change)
        self.table_offset = new_offset  # ✅ Store for future pages

        print(f"🔄 Current offset is now: {self.table_offset}")  # Debug log

        # ✅ Refresh the table with the correct offset
        update_table_offset_ui(
            table_widget=self.table_widget,
            pagination_label=self.pagination_label,
            prev_button=prev_button,
            next_button=next_button,
            fetch_function=self.fetch_data,  # Must reflect the new offset!
            table_name=self.table_name,
            current_offset=self.table_offset,
            limit=self.table_limit,
            change=0,  # We've already applied it
            refresh_callback=lambda: refresh_page(self),
            parent=self
        )

    def update_database(self, item):  # MAIN
        self.table_widget.blockSignals(True)

        try:
            row = item.row()
            column = item.column()
            new_value = item.text().strip() or None

            pk_column = get_primary_key_column(self.cursor, self.current_table_name)
            if not pk_column:
                print("❌ ERROR: No primary key found.")
                self._update_status("❌ No primary key found.")
                return

            pk_index = next(
                (i for i in range(self.table_widget.columnCount())
                if self.table_widget.horizontalHeaderItem(i).text() == pk_column),
                None
            )
            if pk_index is None:
                print(f"❌ ERROR: ID column '{pk_column}' not found in UI.")
                self._update_status(f"❌ ID column '{pk_column}' not found.")
                return

            pk_item = self.table_widget.item(row, pk_index)
            if not pk_item:
                print(f"❌ ERROR: No ID item found in row {row}.")
                self._update_status(f"❌ No ID item found in row {row}.")
                return

            old_pk = pk_item.data(Qt.UserRole) or pk_item.text().strip()
            db_old_pk = check_primary_key_exists(self.cursor, self.current_table_name, pk_column, old_pk)

            if db_old_pk is None:
                print(f"❌ ERROR: Old ID {old_pk} not found in DB.")
                self._update_status(f"❌ ID {old_pk} not found in database.")
                return

            if new_value == str(db_old_pk):
                self._update_status("ℹ️ Value unchanged.")
                return

            now = datetime.now().strftime("%H:%M:%S")

            if column == pk_index:
                # Updating PK
                if check_duplicate_primary_key(self.cursor, self.current_table_name, pk_column, new_value):
                    print(f"❌ PK {new_value} already exists.")
                    self._update_status(f"❌ Duplicate PK: {new_value}")
                    pk_item.setText(str(db_old_pk))  # revert
                    return

                update_primary_key(self.cursor, self.conn, self.current_table_name, pk_column, db_old_pk, new_value)
                pk_item.setData(Qt.UserRole, new_value)
                pk_item.setText(str(new_value))
                print(f"✅ ID updated from {db_old_pk} → {new_value}")
                self._update_status(f"🔑 ID updated from {db_old_pk} to {new_value}")

            else:
                col_name = self.table_widget.horizontalHeaderItem(column).text()
                update_column(self.cursor, self.conn, self.current_table_name, col_name, new_value, pk_column, db_old_pk)
                self._update_status(f"✅ Updated '{col_name}' to '{new_value}' for ID {db_old_pk}")


            update_auto_increment_if_needed(self.cursor, self.conn, self.current_table_name, pk_column)

        except Exception as e:
            print(f"❌ ERROR updating database: {e}")
            if column == pk_index:
                self.table_widget.item(row, pk_index).setText(str(db_old_pk))
            self._update_status("❌ Error occurred while updating.")

        finally:
            self.table_widget.blockSignals(False)

    def update_status_and_database(self, row_idx, new_status):  # MAIN
        try:
            primary_key_item = self.table_widget.item(row_idx, 0)
            if not primary_key_item:
                print(f"❌ ERROR: No primary key item found in row {row_idx}.")
                self._update_status(f"❌ No primary key item in row {row_idx}")
                return

            pk_value = primary_key_item.data(Qt.UserRole) or primary_key_item.text().strip()

            pk_column = fetch_primary_key_column(self.cursor, self.current_table_name)
            if not pk_column:
                print(f"❌ ERROR: No primary key column found for {self.current_table_name}")
                self._update_status(f"❌ No PK column for '{self.current_table_name}'")
                return

            success = update_status(
                cursor=self.cursor,
                conn=self.conn,
                table_name=self.current_table_name,
                pk_column=pk_column,
                pk_value=pk_value,
                new_status=new_status
            )

            if success:
                print(f"✅ Status updated to '{new_status}' for {pk_column} = {pk_value}")
                self._update_status(f"✅ Status updated to '{new_status}' for {pk_value}")
                #self.refresh_table(suppress_status=True)
            else:
                print(f"❌ Failed to update status.")
                self._update_status(f"❌ Failed to update status for ID {pk_value}")

        except Exception as e:
            print(f"❌ ERROR in update_status_and_database: {e}")
            self._update_status(f"❌ Error: {str(e)}")

    def _update_status(self, message: str):
        if hasattr(self, "status_bar"):
            now = datetime.now().strftime("%H:%M:%S")
            self.status_bar.setText(f"{now} : {message}.")

    def view_table_data(self, table_name): #MAIN
        self.table_name = table_name
        self.current_table_name = table_name
        self.table_offset = 0
        self.table_limit = 50

        try:
            data, columns = fetch_table_data_with_columns(
                self.cursor,
                table_name,
                limit=self.table_limit,
                offset=self.table_offset
            )

            self.table_widget = QTableWidget()
            self.table_widget.setColumnCount(len(columns))
            self.table_widget.setHorizontalHeaderLabels(columns)
            self.table_widget.setAlternatingRowColors(True)
            self.table_widget.itemChanged.connect(self.update_database)

            # ✅ Load table data
            load_table(
                table_widget=self.table_widget,
                cursor=self.cursor,
                table_name=table_name,
                update_status_callback=self.update_status_and_database,
                table_offset=self.table_offset,
                limit=self.table_limit,
                event_filter=self
            )

            self.pagination_label = QLabel()
            current_page = (self.table_offset // self.table_limit) + 1
            self.pagination_label.setText(f"Page {current_page}")

            # ✅ Create the dialog UI (next step)
            self.dialog, prev_btn, next_btn, self.refresh_button, self.status_bar = create_table_view_dialog(
            table_name=table_name,
            columns=columns,
            table_widget=self.table_widget,
            pagination_label=self.pagination_label,
            refresh_handler=self.refresh_table,
            search_handler=lambda col, val: self.search_table(col, val),
            prev_handler=lambda: self.update_table_offset(
                -self.table_limit,
                prev_button=prev_btn,
                next_button=next_btn
            ),
            next_handler=lambda: self.update_table_offset(
                self.table_limit,
                prev_button=prev_btn,
                next_button=next_btn
            ),
            add_handler=lambda: self.add_record(table_name, columns, self.table_widget),
            edit_handler=lambda: edit_selected_job(self),
            delete_handler=lambda: self.delete_record(table_name, self.table_widget, columns[0]),
            close_handler=lambda: self.dialog.close()
        )


            self.dialog.exec_()

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load data for {table_name}: {e}")

    def search_table(self, selected_columns, search_text):
        """Search using multiple tokens across selected columns."""

        if not selected_columns or not search_text.strip():
            self.status_bar.setText("ℹ️ Select column(s) and enter search text.")
            return

        try:
            tokens = [word.strip() for word in search_text.strip().split() if word.strip()]
            if not tokens:
                self.status_bar.setText("ℹ️ No valid keywords entered.")
                return

            now = datetime.now().strftime("%H:%M:%S")

            # Build WHERE clause: each token must match at least one column
            conditions = []
            params = []

            for token in tokens:
                token_conditions = [f"`{col}` LIKE %s" for col in selected_columns]
                conditions.append(f"({' OR '.join(token_conditions)})")
                params.extend([f"%{token}%"] * len(selected_columns))

            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT * FROM `{self.current_table_name}`
                WHERE {where_clause};
            """

            self.cursor.execute(query, tuple(params))
            results = self.cursor.fetchall()

            if not results:
                self.table_widget.setRowCount(0)
                self.status_bar.setText(
                    f"⚠ No matches for '{search_text.strip()}' in {', '.join(selected_columns)}"
                )
            else:
                populate_table(self.table_widget, self.current_table_name, results, self.update_status_and_database)
                self.status_bar.setText(
                    f"🔍 {len(results)} result(s) for '{search_text.strip()}' in {', '.join(selected_columns)} at {now}"
                )

        except mariadb.Error as e:
            QMessageBox.critical(self, "Database Error", f"❌ Database Error: {e}")
            self.status_bar.setText("❌ Search failed.")

    def refresh_table(self, suppress_status=False):
        """UI logic to refresh the table."""
        if self.is_refreshing:
            print("❌ Refresh is already in progress. Please wait...")
            self.status_bar.setText("⏳ Refresh already in progress...")
            return
        
        if not suppress_status:
            self.is_refreshing = True
            self.refresh_button.setEnabled(False)
            self.status_bar.setText("🔄 Refreshing table...")

        try:
            self.table_widget.itemChanged.disconnect(self.update_database)
            self.table_widget.setRowCount(0)

            load_table(
                table_widget=self.table_widget,
                cursor=self.cursor,
                table_name=self.current_table_name,
                update_status_callback=self.update_status_and_database,
                table_offset=self.table_offset,
                limit=50,
                event_filter=self
            )

            print(f"✅ Table {self.current_table_name} refreshed successfully.")
            if not suppress_status:
                now = datetime.now().strftime("%H:%M:%S")
                self.status_bar.setText(f"✅ Refreshed '{self.current_table_name}' at {now}")


        except Exception as e:
            print(f"❌ ERROR: Failed to refresh table {self.current_table_name}: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to refresh table: {e}")
            self.status_bar.setText("❌ Failed to refresh table.")

        finally:
            self.table_widget.itemChanged.connect(self.update_database)
            self.is_refreshing = False
            self.refresh_button.setEnabled(True)

    def add_record(self, table_name, columns, table_widget): #UI + DATA_ACCESS
        """Opens a dark-themed dialog to add a new record to the specified table."""

        # Fetch column types from the database
        self.is_adding_new_record = True
        self.cursor.execute(f"DESCRIBE {table_name}")
        column_details = {col[0]: col[1] for col in self.cursor.fetchall()}  # {column_name: data_type}

        # Create the dialog window
        add_window = QDialog()
        add_window.setWindowTitle(f"➕ Add Record to {table_name}")
        add_window.setGeometry(400, 200, 550, 600)
        add_window.setStyleSheet("""
            QDialog {
                background-color: #121212;  /* Fully dark background */
                color: white;
                font-size: 14px;
                border-radius: 8px;
            }
        """)

        # Create a form layout for the input fields
        form_layout = QFormLayout()
        entry_widgets = {}

        # Exclude the first column (assumed to be the primary key)
        non_auto_columns = [col for col in columns if col != columns[0]]

        for col in non_auto_columns:
            label = QLabel(f"🔹 {col}")
            label.setStyleSheet("font-weight: bold; color: #3A9EF5; margin-bottom: 3px;")
            column_type = column_details.get(col, "").lower()

            # **Set Default Values for Special Fields**
            if col.lower() == "status":
                entry_widget = QLineEdit("In Progress")
            elif col.lower() == "datasave":
                entry_widget = QLineEdit("1")
            elif col.lower() == "startdate":
                entry_widget = QLineEdit(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            elif col.lower() == "date":
                entry_widget = QLineEdit(datetime.now().strftime("%Y-%m-%d"))
            elif col.lower() == "enddate":
                entry_widget = QLineEdit("")
            elif "date" in column_type:
                entry_widget = QLineEdit(datetime.now().strftime("%Y-%m-%d"))
            elif "text" in column_type or "varchar(255)" in column_type:
                entry_widget = QTextEdit()
                entry_widget.setFixedHeight(50)
            else:
                entry_widget = QLineEdit()

            entry_widget.setStyleSheet("""
                QLineEdit, QTextEdit {
                    background-color: #1E1E1E;
                    color: white;
                    border: 1px solid #3A9EF5;
                    border-radius: 5px;
                    padding: 6px;
                }
            """)

            entry_widgets[col] = entry_widget
            form_layout.addRow(label, entry_widget)

        # Create Save and Cancel buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("💾 Save")
        cancel_button = QPushButton("❌ Cancel")

        save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        cancel_button.setStyleSheet("background-color: #F44336; color: white; padding: 10px; border-radius: 5px;")

        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        # **Save Function**
        def save_new_record():
            """Saves the new record into the database and refreshes the UI properly."""
            values = []
            for col, widget in entry_widgets.items():
                if isinstance(widget, QTextEdit):
                    value = widget.toPlainText().strip()
                else:
                    value = widget.text().strip()

                values.append(value if value else None)  # Convert empty values to None

            try:
                placeholders = ", ".join(["%s"] * len(non_auto_columns))
                query = f"INSERT INTO {table_name} ({', '.join(non_auto_columns)}) VALUES ({placeholders})"

                self.cursor.execute(query, values)
                self.conn.commit()

                msg_box = QMessageBox()
                msg_box.setWindowTitle("✅ Success")
                msg_box.setText("Record added successfully!")

                # ✅ Apply a Dark Mode StyleSheet
                msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1E1E1E;  /* Dark Background */
                    color: white;  /* White Text */
                    border-radius: 10px;
                }
                QLabel {
                    color: white;  /* Ensure text is readable */
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


                msg_box.exec_()

                now = datetime.now().strftime("%H:%M:%S")
                if hasattr(self, "status_bar"):
                    self.status_bar.setText(f"✅ Record added to '{table_name}' at {now}.")

                # ✅ Refresh the table without passing arguments
                self.refresh_table(suppress_status=True) # ✅ Correct function call

                add_window.close()  # Close the add window
                self.is_adding_new_record = False  # Reset flag

                

            except mariadb.Error as e:
                QMessageBox.critical(add_window, "❌ Error", f"Failed to add record: {e}")

        # ✅ Connect Save and Cancel buttons
        save_button.clicked.connect(save_new_record)
        cancel_button.clicked.connect(add_window.close)

        # Add widgets to layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        add_window.setLayout(layout)

        # Show the dialog
        add_window.exec_()

    def delete_record(self, table_name, table_widget, primary_key_column):  # UI + DATA_ACCESS
        """Deletes a selected record from the table safely with error handling."""

        global is_deletion
        is_deletion = True  # Prevent updates during deletion

        selected_row = table_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "⚠ No record selected.")
            self._update_status("⚠ No record selected for deletion.")
            is_deletion = False
            return

        primary_key_value = table_widget.item(selected_row, 0).text()

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"🗑 Are you sure you want to delete this record ({primary_key_value})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                # 🔍 Check if record exists
                self.cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE {primary_key_column} = %s;",
                    (primary_key_value,)
                )
                record_count = self.cursor.fetchone()[0]

                if record_count == 0:
                    QMessageBox.warning(self, "Warning", "⚠ Record not found. It may have already been deleted.")
                    self._update_status(f"⚠ Record {primary_key_value} not found.")
                    is_deletion = False
                    return

                # ✅ Delete the record
                self.cursor.execute(
                    f"DELETE FROM {table_name} WHERE {primary_key_column} = %s;",
                    (primary_key_value,)
                )
                self.conn.commit()

                # 🔄 Handle auto-increment
                self.cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                remaining_records = self.cursor.fetchone()[0]

                if remaining_records > 0:
                    self.cursor.execute(f"SELECT MAX({primary_key_column}) FROM {table_name};")
                    highest_primary_key = self.cursor.fetchone()[0]

                    if highest_primary_key is not None:
                        self.cursor.execute(
                            f"ALTER TABLE {table_name} AUTO_INCREMENT = {highest_primary_key + 1};"
                        )
                        self.conn.commit()
                else:
                    self.cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1;")
                    self.conn.commit()

                # ✅ Refresh the UI
                self.refresh_table(suppress_status=True)

                # ✅ Show dialog and update status bar
                QMessageBox.information(self, "Success", f"✅ Record {primary_key_value} deleted successfully.")
                self._update_status(f"🗑 Record {primary_key_value} deleted")

            except mariadb.Error as e:
                handle_db_error(e, f"Failed to delete record from {table_name}")
                self._update_status(f"❌ Failed to delete record: {e}")

            finally:
                is_deletion = False

    def view_notes(self, job_id=None): #UI + DATA_ACCESS
        """Displays and edits job notes for a given Job ID."""
        
        # ✅ Step 1: If job_id is None, ask user for input
        if job_id is None:
            job_id, ok = QInputDialog.getText(None, "🔍 Search Job", "Enter Job ID:")
            
            # ✅ Handle "Cancel" button or empty input
            if not ok or not job_id:  # Ensures job_id is a valid string
                return  # Exit if user cancels or enters nothing
        
        # ✅ Step 2: Ensure `job_id` is a string before using `.strip()`
        job_id = str(job_id).strip()  # Convert to string to avoid AttributeError

        # ✅ Step 3: Validate Job ID format
        if not job_id.isdigit():
            QMessageBox.warning(None, "⚠ Invalid Input", "Job ID must be a number.")
            return
        
        # ✅ Step 4: Query the database for job details
        self.cursor.execute("SELECT notes, status, technician FROM jobs WHERE JOBID = %s", (job_id,))
        result = self.cursor.fetchone()

        if not result:
            QMessageBox.critical(None, "❌ Job Not Found", f"No job found with ID {job_id}.")
            return

        # ✅ Proceed with opening the edit dialog...




        existing_notes, existing_status, existing_technician = result
        existing_notes = existing_notes if existing_notes else ""
        existing_status = existing_status if existing_status else ""
        existing_technician = existing_technician if existing_technician else ""

        # Step 3: Create a dark-themed dialog window for editing
        edit_dialog = QDialog()
        edit_dialog.setWindowFlags(Qt.Window)
        edit_dialog.setWindowTitle(f"📝 Edit Notes for Job {job_id}")
        edit_dialog.setGeometry(100, 100, 450, 550)
        edit_dialog.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: white;
                border-radius: 8px;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #3A9EF5;
            }
        """)

        main_layout = QVBoxLayout()

        # **Status Dropdown**
        status_label = QLabel("📌 Status:")
        status_combobox = QComboBox()
        status_options = ["Waiting for parts", "In Progress", "Completed", "Picked Up"]
        status_combobox.addItems(status_options)
        status_combobox.setCurrentText(existing_status)
        status_combobox.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: white;
                border: 1px solid #3A9EF5;
                padding: 5px;
                border-radius: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2A2A2A;
                selection-background-color: #3A9EF5;
                color: white;
            }
        """)
        main_layout.addWidget(status_label)
        main_layout.addWidget(status_combobox)

        # **Technician Entry**
        technician_label = QLabel("👨‍🔧 Technician:")
        technician_entry = QLineEdit()
        technician_entry.setText(existing_technician)
        technician_entry.setStyleSheet("""
            QLineEdit {
                background-color: #333;
                color: white;
                border: 1px solid #3A9EF5;
                padding: 6px;
                border-radius: 5px;
            }
        """)
        main_layout.addWidget(technician_label)
        main_layout.addWidget(technician_entry)

        # **Notes Text Area**
        notes_label = QLabel("📝 Edit Notes:")
        notes_text = QTextEdit()
        notes_text.setText(existing_notes)
        notes_text.setStyleSheet("""
            QTextEdit {
                background-color: #333;
                color: white;
                border: 1px solid #3A9EF5;
                padding: 6px;
                border-radius: 5px;
            }
        """)
        main_layout.addWidget(notes_label)
        main_layout.addWidget(notes_text)

        # **Save Function**
        def save_notes():
            new_notes = notes_text.toPlainText().strip()
            new_status = status_combobox.currentText().strip()
            new_technician = technician_entry.text().strip()

            if new_notes == existing_notes and new_status == existing_status and new_technician == existing_technician:
                QMessageBox.information(edit_dialog, "ℹ No Changes", "No changes were made.")
                return

            end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if new_status == "Completed" else None

            try:
                if end_date:
                    self.cursor.execute(
                        "UPDATE jobs SET notes = %s, status = %s, technician = %s, EndDate = %s WHERE JOBID = %s",
                        (new_notes, new_status, new_technician, end_date, job_id)
                    )
                else:
                    self.cursor.execute(
                        "UPDATE jobs SET notes = %s, status = %s, technician = %s WHERE JOBID = %s",
                        (new_notes, new_status, new_technician, job_id)
                    )
                self.conn.commit()
                QMessageBox.information(edit_dialog, "✅ Success", f"Job ID {job_id} has been updated.")
            except mariadb.Error as e:
                QMessageBox.critical(edit_dialog, "❌ Database Error", f"An error occurred: {e}")
            

        # **Buttons Section**
        button_layout = QHBoxLayout()

        save_button = QPushButton("💾 Save Changes")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        save_button.clicked.connect(save_notes)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("❌ Close")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #D9534F;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #C9302C;
            }
        """)
        
        

        # Step 6: Costs Window
        def view_costs():
            """Displays all costs associated with the current job, allows adding and deleting costs, and enables adding parts to orders."""
            costs_dialog = QDialog(edit_dialog)
            costs_dialog.setWindowTitle(f"💰 Costs for Job {job_id}")
            costs_dialog.setGeometry(600, 100, 600, 500)

            costs_layout = QVBoxLayout()

            # ✅ **Step 1: Get column names dynamically**
            self.cursor.execute(f"SHOW COLUMNS FROM costs")
            columns = [col[0] for col in self.cursor.fetchall()]  # Extract column names

            # ✅ **Remove costID & JobID from displayed columns but keep for internal use**
            display_columns = [col for col in columns if col.lower() not in ["costid", "jobid"]]
            all_columns = columns  # Keep all columns for querying (including costID & JobID)

            # ✅ **Step 2: Create a TableWidget with dynamic columns (+2 for delete & add-to-orders buttons)**
            costs_table = QTableWidget()
            costs_table.setColumnCount(len(display_columns) + 2)  # Extra columns for delete and add buttons
            costs_table.setHorizontalHeaderLabels(display_columns + ["➕ Add to Orders", "🗑 Delete"])
            costs_table.setStyleSheet("background-color: white; color: black;")

            costs_layout.addWidget(costs_table)

            # ✅ **Step 3: Display Total Cost**
            total_label = QLabel("💰 Total Cost: £0.00")
            total_label.setAlignment(Qt.AlignRight)
            total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #3A9EF5; padding-top: 10px;")
            costs_layout.addWidget(total_label)

            from functools import partial  # ✅ Import this at the top of your file

            def load_costs():
                """Loads costs dynamically, updates total amount, and adds delete/add-to-orders buttons."""
                self.cursor.execute(f"SELECT {', '.join(all_columns)} FROM costs WHERE JOBID = %s", (job_id,))
                costs = self.cursor.fetchall()

                # ✅ Clear table before updating to prevent duplicate entries
                costs_table.clearContents()
                costs_table.setRowCount(len(costs))

                total_amount = 0  # Store total cost

                # ✅ **Find correct index mapping for CostType, Amount, and Description**
                try:
                    cost_type_index = all_columns.index("CostType")  # ✅ Use `all_columns` instead of `display_columns`
                    amount_index = all_columns.index("Amount")
                    description_index = all_columns.index("Description")
                except ValueError as e:
                    QMessageBox.critical(None, "❌ Column Error", f"Missing required column: {e}")
                    return

                for row_idx, row_data in enumerate(costs):
                    cost_id = row_data[0]  # ✅ The first column in row_data is always CostID (PK)

                    # ✅ Map `display_columns` correctly, skipping CostID
                    for col_idx, column_name in enumerate(display_columns):  
                        try:
                            value = row_data[all_columns.index(column_name)]  # ✅ Correct alignment by using `all_columns`
                            costs_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))  # ✅ Proper column alignment

                            # ✅ Fix: Check "Amount" column using correct index
                            if column_name.lower() == "amount":
                                try:
                                    total_amount += float(value)
                                except ValueError:
                                    pass  # Skip non-numeric values

                        except IndexError:
                            QMessageBox.critical(None, "❌ Index Error", f"Column index {col_idx} is out of range for row {row_idx}.")
                            return

                    # ✅ **Find Correct Column for Buttons**
                    add_button_col = len(display_columns)  # "Add to Orders" column index
                    delete_button_col = add_button_col + 1  # "Delete" column index

                    # ✅ **Show "➕ Add to Orders" Button for All Records**
                    add_button = QPushButton("➕ Add to Orders")
                    add_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px; padding: 5px;")

                    # ✅ Use `partial()` to correctly pass arguments
                    add_button.clicked.connect(partial(add_to_orders_dialog, row_data[description_index]))  # ✅ Corrected Description Mapping

                    # ✅ Ensure button appears by wrapping it inside a `QWidget`
                    button_container = QWidget()
                    button_layout = QHBoxLayout(button_container)
                    button_layout.addWidget(add_button)
                    button_layout.setContentsMargins(0, 0, 0, 0)  # ✅ Remove spacing
                    button_layout.setAlignment(Qt.AlignCenter)
                    
                    costs_table.setCellWidget(row_idx, add_button_col, button_container)  # ✅ Button now appears for all records

                    # ✅ **Add Delete Button**
                    delete_button = QPushButton("🗑")
                    delete_button.setStyleSheet("background-color: #D9534F; color: white; border-radius: 5px; padding: 5px;")
                    delete_button.clicked.connect(partial(delete_cost, cost_id))

                    button_container_del = QWidget()
                    button_layout_del = QHBoxLayout(button_container_del)
                    button_layout_del.addWidget(delete_button)
                    button_layout_del.setContentsMargins(0, 0, 0, 0)  # ✅ Remove spacing
                    button_layout_del.setAlignment(Qt.AlignCenter)

                    costs_table.setCellWidget(row_idx, delete_button_col, button_container_del)  # ✅ Delete button properly placed

                total_label.setText(f"💰 Total Cost: £{total_amount:.2f}")  # ✅ Update total cost label


            # ✅ **Step 5: Function to Delete a Cost**
            def delete_cost(cost_id):
                """Deletes a cost entry and refreshes the table."""
                confirmation = QMessageBox.question(costs_dialog, "🗑 Confirm Deletion",
                                                    "Are you sure you want to delete this cost?",
                                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if confirmation == QMessageBox.Yes:
                    try:
                        self.cursor.execute("DELETE FROM costs WHERE CostID = %s", (cost_id,))
                        self.conn.commit()
                        QMessageBox.information(costs_dialog, "✅ Success", "Cost deleted successfully.")
                        load_costs()  # Refresh table after deletion
                    except mariadb.Error as e:
                        QMessageBox.critical(costs_dialog, "❌ Database Error", f"An error occurred: {e}")

            # ✅ **Step 6: Add Cost Button**
            def add_cost():
                """Opens a pop-up dialog to add a new cost entry with a dropdown for cost type."""
                input_dialog = QDialog(costs_dialog)
                input_dialog.setWindowTitle("➕ Add Cost")
                input_layout = QVBoxLayout()

                # ✅ Cost Type Dropdown
                cost_type_dropdown = QComboBox()
                cost_type_dropdown.addItems(["Parts", "Labor", "Shipping", "Miscellaneous"])
                input_layout.addWidget(QLabel("Select Cost Type:"))
                input_layout.addWidget(cost_type_dropdown)

                # ✅ Amount Entry
                amount_entry = QLineEdit()
                amount_entry.setPlaceholderText("e.g., 50.00")
                input_layout.addWidget(QLabel("Enter Amount (£):"))
                input_layout.addWidget(amount_entry)

                # ✅ Description Entry
                description_entry = QTextEdit()
                description_entry.setPlaceholderText("Enter details about the cost")
                input_layout.addWidget(QLabel("Enter Description:"))
                input_layout.addWidget(description_entry)

                # ✅ Submit Button
                add_button = QPushButton("✅ Add Cost")

                def submit_cost():
                    """Validates and inserts the cost record into the database."""
                    cost_type = cost_type_dropdown.currentText().strip()  # Get selected value from dropdown
                    amount = amount_entry.text().strip()
                    description = description_entry.toPlainText().strip()

                    if not amount or not description:
                        QMessageBox.warning(input_dialog, "⚠ Input Error", "All fields must be filled.")
                        return

                    try:
                        amount = float(amount)  # Ensure amount is numeric
                        self.cursor.execute(
                            "INSERT INTO costs (JobID, CostType, Amount, Description) VALUES (%s, %s, %s, %s)",
                            (job_id, cost_type, amount, description)
                        )
                        self.conn.commit()
                        input_dialog.close()
                        load_costs()
                    except ValueError:
                        QMessageBox.warning(input_dialog, "⚠ Input Error", "Amount must be a number.")

                add_button.clicked.connect(submit_cost)
                input_layout.addWidget(add_button)

                input_dialog.setLayout(input_layout)
                input_dialog.exec_()

            # ✅ **Step 7: Add Cost Button**
            add_cost_button = QPushButton("➕ Add Cost")
            add_cost_button.clicked.connect(add_cost)
            costs_layout.addWidget(add_cost_button)

            load_costs()  # ✅ Load costs AFTER defining functions

            costs_dialog.setLayout(costs_layout)
            costs_dialog.exec_()


        def add_to_orders_dialog(part_description):
            """Opens a pop-up dialog to add the part to the orders table with specific details."""
            order_dialog = QDialog()
            order_dialog.setWindowTitle("📦 Add Part to Orders")
            order_layout = QVBoxLayout()

            # ✅ **Step 2: Total Cost Input**
            total_cost_label = QLabel("Enter Total Cost (£):")
            total_cost_entry = QLineEdit()
            total_cost_entry.setPlaceholderText("e.g., 30.00")
            order_layout.addWidget(total_cost_label)
            order_layout.addWidget(total_cost_entry)

            # ✅ **Step 3: Submit Button**
            submit_button = QPushButton("✅ Add to Orders")

            def submit_order():
                """Validates and inserts the part into the orders table."""
                total_cost = total_cost_entry.text().strip()

                if not total_cost:
                    QMessageBox.warning(order_dialog, "⚠ Input Error", "Total cost must be entered.")
                    return

                try:
                    total_cost = float(total_cost)  # Ensure cost is a valid number
                    quantity = 1  # ✅ Always set quantity to 1

                    self.cursor.execute(
                        "INSERT INTO orders (JobID, OrderDate, Description, Quantity, TotalCost) VALUES (%s, NOW(), %s, %s, %s)",
                        (job_id, part_description, quantity, total_cost)
                    )
                    self.conn.commit()

                    QMessageBox.information(order_dialog, "✅ Success", "Part added to orders successfully.")
                    order_dialog.close()
                except ValueError:
                    QMessageBox.warning(order_dialog, "⚠ Input Error", "Total cost must be a valid number.")

            submit_button.clicked.connect(submit_order)
            order_layout.addWidget(submit_button)

            order_dialog.setLayout(order_layout)
            order_dialog.exec_()

        def view_payments():
            """Displays all payments associated with the current job and allows adding/deleting records."""
            payments_dialog = QDialog(edit_dialog)
            payments_dialog.setWindowTitle(f"💳 Payments for Job {job_id}")
            payments_dialog.setGeometry(600, 100, 600, 500)

            payments_layout = QVBoxLayout()
            payments_table = QTableWidget()
            payments_table.setColumnCount(5)
            payments_table.setHorizontalHeaderLabels(["Payment ID", "Amount", "Payment Type", "Date", "🗑 Delete"])
            payments_layout.addWidget(payments_table)

            total_label = QLabel("💰 Total Payments: £0.00")
            total_label.setAlignment(Qt.AlignRight)
            payments_layout.addWidget(total_label)

            # **Load Payments**
            def load_payments():
                self.cursor.execute("SELECT PaymentID, Amount, PaymentType, Date FROM payments WHERE JOBID = %s", (job_id,))
                payments = self.cursor.fetchall()
                payments_table.setRowCount(len(payments))

                total_amount = 0
                for row_idx, row_data in enumerate(payments):
                    payment_id, amount, payment_type, payment_date = row_data
                    total_amount += float(amount)

                    payments_table.setItem(row_idx, 0, QTableWidgetItem(str(payment_id)))
                    payments_table.setItem(row_idx, 1, QTableWidgetItem(f"£{amount:.2f}"))
                    payments_table.setItem(row_idx, 2, QTableWidgetItem(payment_type))
                    payments_table.setItem(row_idx, 3, QTableWidgetItem(str(payment_date)))

                    delete_button = QPushButton("🗑")
                    delete_button.clicked.connect(lambda _, p_id=payment_id: delete_payment(p_id))
                    payments_table.setCellWidget(row_idx, 4, delete_button)

                total_label.setText(f"💰 Total Payments: £{total_amount:.2f}")

            # **Delete Payment**
            def delete_payment(payment_id):
                self.cursor.execute("DELETE FROM payments WHERE PaymentID = %s", (payment_id,))
                self.conn.commit()
                load_payments()

            def add_payment():
                input_dialog = QDialog(payments_dialog)
                input_dialog.setWindowTitle("➕ Add Payment")
                input_layout = QVBoxLayout()

                # Amount Entry
                amount_entry = QLineEdit()
                amount_entry.setPlaceholderText("Enter Amount (£)")
                input_layout.addWidget(amount_entry)

                # Payment Type Dropdown
                payment_type_dropdown = QComboBox()
                payment_type_dropdown.addItems(["Card", "Cash", "Bank Transfer"])
                input_layout.addWidget(payment_type_dropdown)

                # Date Field (Pre-filled but Editable)
                date_entry = QDateEdit()
                date_entry.setDate(QDate.currentDate())  # Set to today's date
                date_entry.setCalendarPopup(True)  # Allow user to select a date
                input_layout.addWidget(date_entry)

                # Add Payment Button
                add_button = QPushButton("✅ Add Payment")

                def submit_payment():
                    amount = amount_entry.text().strip()
                    payment_type = payment_type_dropdown.currentText()  # Get selected payment type
                    payment_date = date_entry.date().toString("yyyy-MM-dd")  # Get selected date

                    if not amount:
                        QMessageBox.warning(input_dialog, "⚠ Input Error", "Amount field must be filled.")
                        return

                    try:
                        amount = float(amount)  # Ensure amount is numeric

                        # Insert with selected date
                        self.cursor.execute(
                            "INSERT INTO payments (JobID, Amount, PaymentType, Date) VALUES (%s, %s, %s, %s)",
                            (job_id, amount, payment_type, payment_date)
                        )
                        self.conn.commit()
                        input_dialog.close()
                        load_payments()
                    except ValueError:
                        QMessageBox.warning(input_dialog, "⚠ Input Error", "Amount must be a number.")

                add_button.clicked.connect(submit_payment)
                input_layout.addWidget(add_button)

                input_dialog.setLayout(input_layout)
                input_dialog.exec_()

            load_payments()

            add_payment_button = QPushButton("➕ Add Payment")
            add_payment_button.clicked.connect(add_payment)
            payments_layout.addWidget(add_payment_button)

            payments_dialog.setLayout(payments_layout)
            payments_dialog.exec_()


        def view_communications():
            """Displays all communications associated with the current job and includes a properly-sized vertical table for customer details."""
            comms_dialog = QDialog(edit_dialog)
            comms_dialog.setWindowTitle(f"📞 Communications for Job {job_id}")
            comms_dialog.setGeometry(600, 100, 700, 500)

            comms_layout = QVBoxLayout()

            # ✅ **Step 1: Fetch Customer Contact Information**
            self.cursor.execute("""
                SELECT customers.FirstName, customers.SurName, customers.Phone, customers.Email 
                FROM customers 
                JOIN jobs ON customers.CustomerID = jobs.CustomerID 
                WHERE jobs.JOBID = %s
            """, (job_id,))
            
            customer_data = self.cursor.fetchone()

            if customer_data:
                customer_firstname, customer_surname, customer_phone, customer_email = customer_data
            else:
                customer_firstname, customer_surname, customer_phone, customer_email = "N/A", "N/A", "N/A", "N/A"

            # ✅ **Step 2: Create Vertical Customer Info Table with Auto-Resizing**
            customer_table = QTableWidget()
            customer_table.setRowCount(4)  # One row for each field
            customer_table.setColumnCount(2)  # Label + Value
            customer_table.setHorizontalHeaderLabels(["Field", "Value"])

            customer_table.setItem(0, 0, QTableWidgetItem("First Name"))
            customer_table.setItem(0, 1, QTableWidgetItem(customer_firstname))
            customer_table.setItem(1, 0, QTableWidgetItem("Surname"))
            customer_table.setItem(1, 1, QTableWidgetItem(customer_surname))
            customer_table.setItem(2, 0, QTableWidgetItem("📞 Phone"))
            customer_table.setItem(2, 1, QTableWidgetItem(customer_phone))
            customer_table.setItem(3, 0, QTableWidgetItem("✉ Email"))
            customer_table.setItem(3, 1, QTableWidgetItem(customer_email))

            customer_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable editing
            customer_table.setStyleSheet("background-color: white; color: black;")

            # ✅ **Auto-resizing columns and rows to fit content**
            customer_table.horizontalHeader().setStretchLastSection(True)  
            customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            customer_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

            comms_layout.addWidget(customer_table)

            # ✅ **Step 3: Setup Communications Table with Auto-Resizing**
            comms_table = QTableWidget()
            comms_table.setColumnCount(5)  # Adding a delete column
            comms_table.setHorizontalHeaderLabels(["Communication ID", "Date", "Type", "Message", "🗑 Delete"])

            # ✅ **Auto-resizing columns to fit text**
            comms_table.horizontalHeader().setStretchLastSection(True)
            comms_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            comms_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

            comms_layout.addWidget(comms_table)

            # ✅ **Step 4: Load Communications**
            def load_comms():
                self.cursor.execute("SELECT CommunicationID, DateTime, CommunicationType, Note FROM communications WHERE JOBID = %s", (job_id,))
                comms = self.cursor.fetchall()
                comms_table.setRowCount(len(comms))

                for row_idx, row_data in enumerate(comms):
                    comm_id, date_time, comm_type, message = row_data
                    comms_table.setItem(row_idx, 0, QTableWidgetItem(str(comm_id)))
                    comms_table.setItem(row_idx, 1, QTableWidgetItem(str(date_time)))
                    comms_table.setItem(row_idx, 2, QTableWidgetItem(comm_type))
                    comms_table.setItem(row_idx, 3, QTableWidgetItem(message))

                    delete_button = QPushButton("🗑")
                    delete_button.setStyleSheet("background-color: #D9534F; color: white; border-radius: 5px; padding: 5px;")
                    delete_button.clicked.connect(lambda _, c_id=comm_id: delete_comm(c_id))
                    comms_table.setCellWidget(row_idx, 4, delete_button)

                # ✅ **Auto-resize rows after adding data**
                comms_table.resizeRowsToContents()

            # ✅ **Step 5: Delete Communication**
            def delete_comm(comm_id):
                self.cursor.execute("DELETE FROM communications WHERE CommunicationID = %s", (comm_id,))
                self.conn.commit()
                load_comms()

            # ✅ **Step 6: Add Communication**
            def add_comm():
                input_dialog = QDialog(comms_dialog)
                input_dialog.setWindowTitle("➕ Add Communication")
                input_layout = QVBoxLayout()

                # ✅ **Communication Type Dropdown**
                comm_type_label = QLabel("Select Communication Type:")
                comm_type_dropdown = QComboBox()
                comm_type_dropdown.addItems(["Email", "Call", "SMS", "In-Person", "Other"])
                input_layout.addWidget(comm_type_label)
                input_layout.addWidget(comm_type_dropdown)

                # ✅ **Message Entry**
                message_label = QLabel("Enter Message:")
                message_entry = QTextEdit()
                message_entry.setPlaceholderText("Enter Message")
                message_entry.setFixedHeight(100)  # Ensures message box is large enough
                input_layout.addWidget(message_label)
                input_layout.addWidget(message_entry)

                # ✅ **Submit Button**
                add_button = QPushButton("✅ Add Communication")
                def submit_comm():
                    comm_type = comm_type_dropdown.currentText().strip()
                    message = message_entry.toPlainText().strip()

                    if not comm_type or not message:
                        QMessageBox.warning(input_dialog, "⚠ Input Error", "All fields must be filled.")
                        return

                    self.cursor.execute(
                        "INSERT INTO communications (JobID, CommunicationType, Note) VALUES (%s, %s, %s)",
                        (job_id, comm_type, message)
                    )
                    self.conn.commit()
                    input_dialog.close()
                    load_comms()

                add_button.clicked.connect(submit_comm)
                input_layout.addWidget(add_button)

                input_dialog.setLayout(input_layout)
                input_dialog.exec_()

            # ✅ **Step 7: Load Communications**
            load_comms()

            # ✅ **Step 8: Add Buttons at the Bottom**
            button_layout = QHBoxLayout()

            add_comm_button = QPushButton("➕ Add Communication")
            add_comm_button.clicked.connect(add_comm)
            add_comm_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; border-radius: 5px;")
            button_layout.addWidget(add_comm_button)

            close_button = QPushButton("❌ Close")
            close_button.clicked.connect(comms_dialog.close)
            close_button.setStyleSheet("background-color: #D9534F; color: white; padding: 8px; border-radius: 5px;")
            button_layout.addWidget(close_button)

            comms_layout.addLayout(button_layout)

            comms_dialog.setLayout(comms_layout)
            comms_dialog.exec_()


        def view_orders():
            """Displays all orders associated with the current job and allows adding/deleting records."""
            orders_dialog = QDialog(edit_dialog)
            orders_dialog.setWindowTitle(f"📦 Orders for Job {job_id}")
            orders_dialog.setGeometry(600, 100, 600, 500)

            orders_layout = QVBoxLayout()

            # ✅ **Step 1: Create Orders Table**
            orders_table = QTableWidget()
            orders_table.setColumnCount(5)  # 7 columns + 1 new column for the Delivered button
            orders_table.setHorizontalHeaderLabels(
                ["Order ID", "Order Date", "Description", "Quantity", "Total Cost (£)", "🗑 Delete"]
            )
            orders_layout.addWidget(orders_table)

            # ✅ **Step 4: Add Order Function** (Move this here)
            def add_order():
                """Opens a pop-up dialog to add a new order entry."""
                input_dialog = QDialog(orders_dialog)
                input_dialog.setWindowTitle("➕ Add Order")
                input_layout = QVBoxLayout()

                # ✅ **Order Description**
                description_label = QLabel("Enter Part Description:")
                description_entry = QLineEdit()
                description_entry.setPlaceholderText("e.g., Hard Drive, RAM Module")
                input_layout.addWidget(description_label)
                input_layout.addWidget(description_entry)

                # ✅ **Quantity Entry**
                quantity_label = QLabel("Enter Quantity:")
                quantity_entry = QLineEdit()
                quantity_entry.setPlaceholderText("e.g., 2")
                input_layout.addWidget(quantity_label)
                input_layout.addWidget(quantity_entry)

                # ✅ **Total Cost Entry**
                total_cost_label = QLabel("Enter Total Cost (£):")
                total_cost_entry = QLineEdit()
                total_cost_entry.setPlaceholderText("e.g., 100.00")
                input_layout.addWidget(total_cost_label)
                input_layout.addWidget(total_cost_entry)

                # ✅ **Submit Button**
                add_button = QPushButton("✅ Add Order")
                def submit_order():
                    """Validates and inserts the order record into the database."""
                    description = description_entry.text().strip()
                    quantity = quantity_entry.text().strip()
                    total_cost = total_cost_entry.text().strip()

                    if not description or not quantity or not total_cost:
                        QMessageBox.warning(input_dialog, "⚠ Input Error", "All fields must be filled.")
                        return

                    try:
                        quantity = int(quantity)
                        total_cost = float(total_cost)

                        self.cursor.execute(
                            "INSERT INTO orders (JobID, OrderDate, Description, Quantity, TotalCost) VALUES (%s, NOW(), %s, %s, %s)",
                            (job_id, description, quantity, total_cost)
                        )
                        self.conn.commit()

                        QMessageBox.information(input_dialog, "✅ Success", "Order added successfully.")
                        input_dialog.close()
                        load_orders()  # ✅ Refresh orders list
                    except ValueError:
                        QMessageBox.warning(input_dialog, "⚠ Input Error", "Quantity must be an integer and cost must be a number.")

                add_button.clicked.connect(submit_order)
                input_layout.addWidget(add_button)

                input_dialog.setLayout(input_layout)
                input_dialog.exec_()

            # ✅ **Step 2: Load Orders Data**
            def load_orders():
                self.cursor.execute(
                    "SELECT PartID, OrderDate, Description, Quantity, TotalCost FROM orders WHERE JOBID = %s", 
                    (job_id,)
                )
                orders = self.cursor.fetchall()
                orders_table.setRowCount(len(orders))

                for row_idx, row_data in enumerate(orders):
                    order_id, order_date, description, quantity, total_cost = row_data
                    orders_table.setItem(row_idx, 0, QTableWidgetItem(str(order_id)))
                    orders_table.setItem(row_idx, 1, QTableWidgetItem(str(order_date)))
                    orders_table.setItem(row_idx, 2, QTableWidgetItem(description))
                    orders_table.setItem(row_idx, 3, QTableWidgetItem(str(quantity)))
                    

                    # Check if total_cost is None, and handle it
                    if total_cost is None:
                        total_cost_str = "0.00"  # You can change this to "0.00" or any default value you prefer
                    else:
                        total_cost_str = f"£{total_cost:.2f}"

                    orders_table.setItem(row_idx, 4, QTableWidgetItem(total_cost_str))

                    # ✅ **Delete Button**
                    delete_button = QPushButton("🗑")
                    delete_button.setStyleSheet("background-color: #D9534F; color: white; border-radius: 5px; padding: 5px;")
                    delete_button.clicked.connect(lambda _, o_id=order_id: delete_order(o_id))
                    orders_table.setCellWidget(row_idx, 5, delete_button)

            # ✅ **Step 3: Delete Order Function**
            def delete_order(order_id):
                """Deletes an order entry and refreshes the table."""
                confirmation = QMessageBox.question(
                    orders_dialog, "🗑 Confirm Deletion",
                    "Are you sure you want to delete this order?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if confirmation == QMessageBox.Yes:
                    try:
                        self.cursor.execute("DELETE FROM orders WHERE PartID = %s", (order_id,))
                        self.conn.commit()
                        QMessageBox.information(orders_dialog, "✅ Success", "Order deleted successfully.")
                        load_orders()  # ✅ Refresh table after deletion
                    except mariadb.Error as e:
                        QMessageBox.critical(orders_dialog, "❌ Database Error", f"An error occurred: {e}")

            # ✅ **Step 4: Load Orders Data Initially**
            load_orders()

            # ✅ **Step 5: Add "Add Order" Button**
            add_order_button = QPushButton("➕ Add Order")
            add_order_button.clicked.connect(add_order)  # Now this function is defined above
            orders_layout.addWidget(add_order_button)

            orders_dialog.setLayout(orders_layout)
            orders_dialog.exec_()


        def view_edit_job_details():
            """Displays and allows editing of job details except EndDate and primary key (JobID) with Dark UI."""
            job_details_dialog = QDialog()
            job_details_dialog.setWindowTitle(f"🛠 Edit Job Details - Job {job_id}")
            job_details_dialog.setGeometry(600, 100, 700, 500)
            job_details_dialog.setStyleSheet("""
                QDialog {
                    background-color: #1E1E1E;
                    color: white;
                    border-radius: 8px;
                }
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #3A9EF5;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: #333;
                    color: white;
                    border: 1px solid #3A9EF5;
                    padding: 6px;
                    border-radius: 5px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2A2A2A;
                    selection-background-color: #3A9EF5;
                    color: white;
                }
                QCheckBox {
                    color: white;
                }
                QPushButton {
                    background-color: #3A9EF5;
                    color: white;
                    border-radius: 5px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #307ACC;
                }
            """)

            job_layout = QVBoxLayout()

            # ✅ **Step 1: Fetch Column Names Dynamically (excluding JobID and EndDate)**
            self.cursor.execute("SHOW COLUMNS FROM jobs")
            columns = [col[0] for col in self.cursor.fetchall()]
            excluded_columns = {"JobID", "EndDate", "CustomerID", "Notes", "Technician", "Status"}
            display_columns = [col for col in columns if col not in excluded_columns]

            # ✅ **Step 2: Fetch Current Job Data**
            self.cursor.execute(f"SELECT {', '.join(display_columns)} FROM jobs WHERE JOBID = %s", (job_id,))
            job_data = self.cursor.fetchone()

            if not job_data:
                QMessageBox.critical(None, "❌ Job Not Found", "No job details found.")
                return

            # ✅ **Step 3: Create Editable Fields**
            input_fields = {}
            for idx, column in enumerate(display_columns):
                label = QLabel(f"{column}:")
                job_layout.addWidget(label)

                if column.lower() == "issue":
                    field = QTextEdit()
                    field.setText(str(job_data[idx]))
                elif column.lower() == "datasave":
                    field = QCheckBox()
                    field.setChecked(bool(job_data[idx]))
                else:
                    field = QLineEdit()
                    field.setText(str(job_data[idx]))

                input_fields[column] = field
                job_layout.addWidget(field)

            # ✅ **Step 4: Save Changes Function**
            def save_job_details():
                """Saves the updated job details to the database."""
                updated_values = []
                changes_made = False

                for column, field in input_fields.items():
                    if isinstance(field, QComboBox):
                        new_value = field.currentText()
                    elif isinstance(field, QTextEdit):
                        new_value = field.toPlainText().strip()
                    elif isinstance(field, QCheckBox):
                        new_value = int(field.isChecked())  # Convert checkbox to 1 or 0
                    else:
                        new_value = field.text().strip()

                    updated_values.append(new_value)

                # ✅ **Check if changes were made**
                if tuple(updated_values) != job_data:
                    changes_made = True

                if not changes_made:
                    QMessageBox.information(job_details_dialog, "ℹ No Changes", "No changes were made.")
                    job_details_dialog.close()
                    return

                try:
                    # ✅ **Update only if changes were made**
                    update_query = f"UPDATE jobs SET {', '.join([f'{col} = %s' for col in display_columns])} WHERE JOBID = %s"
                    self.cursor.execute(update_query, (*updated_values, job_id))
                    self.conn.commit()
                    QMessageBox.information(job_details_dialog, "✅ Success", "Job details updated successfully.")
                    job_details_dialog.close()
                except mariadb.Error as e:
                    QMessageBox.critical(job_details_dialog, "❌ Database Error", f"An error occurred: {e}")

            # ✅ **Step 5: Create Save & Cancel Buttons**
            button_layout = QHBoxLayout()
            
            save_button = QPushButton("💾 Save Changes")
            save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
            save_button.clicked.connect(save_job_details)
            button_layout.addWidget(save_button)

            cancel_button = QPushButton("❌ Cancel")
            cancel_button.setStyleSheet("background-color: #D9534F; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
            cancel_button.clicked.connect(job_details_dialog.close)
            button_layout.addWidget(cancel_button)

            job_layout.addLayout(button_layout)
            job_details_dialog.setLayout(job_layout)
            job_details_dialog.exec_()




       # Step 8: Create and Style Buttons
        button_layout = QHBoxLayout()

        save_button = QPushButton("💾 Save Changes")
        save_button.clicked.connect(save_notes)
        button_layout.addWidget(save_button)

        costs_button = QPushButton("💰 Costs")
        costs_button.clicked.connect(view_costs)
        button_layout.addWidget(costs_button)

        # ✅ **ADD NEW BUTTONS HERE**
        payments_button = QPushButton("💳 Payments")
        payments_button.clicked.connect(view_payments)  # Ensure this function is implemented
        button_layout.addWidget(payments_button)

        comms_button = QPushButton("📞 Communications")
        comms_button.clicked.connect(view_communications)  # Ensure this function is implemented
        button_layout.addWidget(comms_button)

        orders_button = QPushButton("📦 Orders")  # ✅ **New Orders Button**
        orders_button.clicked.connect(view_orders)  # ✅ **Ensure this function is implemented**
        button_layout.addWidget(orders_button)

        # ✅ **New Job Details Button**
        job_details_button = QPushButton("🛠 Job Details")  
        job_details_button.clicked.connect(view_edit_job_details)  # ✅ Ensure this function is implemented
        button_layout.addWidget(job_details_button)

        cancel_button = QPushButton("❌ Close")
        cancel_button.clicked.connect(edit_dialog.close)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        edit_dialog.setLayout(main_layout)
        edit_dialog.exec_()

    def Customer_report(self): #UI + DATA_ACCESS
        # Step 1: Ask for Job ID
        job_id, ok = QInputDialog.getText(self, "Search Job", "Enter Job ID:")
        
        if not ok:
            return 
        
        if not job_id.strip():
            QMessageBox.warning(self, "Input Error", "Job ID cannot be empty.")
            return

        # Step 2: Retrieve CustomerID
        self.cursor.execute("SELECT CustomerID FROM Jobs WHERE JobID = %s", (job_id,))
        result = self.cursor.fetchone()
        if not result:
            QMessageBox.critical(self, "Job Not Found", f"No job found with ID {job_id}.")
            return
        customer_id = result[0]

        # Step 3: Create Customer Report Window
        customer_window = QDialog(self)
        customer_window.setWindowTitle(f"Customer Report - ID {customer_id}")
        customer_window.setGeometry(100, 100, 1000, 700)
        
        layout = QVBoxLayout()
        tab_widget = QTabWidget()

        # Step 4: Customer Information Tab
        self.cursor.execute("DESCRIBE Customers")
        customer_columns = [col[0] for col in self.cursor.fetchall()]
        self.cursor.execute("SELECT * FROM Customers WHERE CustomerID = %s", (customer_id,))
        customer_info = self.cursor.fetchone()

        customer_tab = QWidget()
        customer_layout = QVBoxLayout()
        customer_table = QTableWidget()
        customer_table.setColumnCount(2)
        customer_table.setHorizontalHeaderLabels(["Field", "Value"])
        customer_table.setRowCount(len(customer_columns))
        
        for row, (col, value) in enumerate(zip(customer_columns, customer_info)):
            customer_table.setItem(row, 0, QTableWidgetItem(col))
            customer_table.setItem(row, 1, QTableWidgetItem(str(value)))

        customer_table.resizeColumnsToContents()
        customer_layout.addWidget(customer_table)
        customer_tab.setLayout(customer_layout)
        tab_widget.addTab(customer_tab, "Customer Info")

        # Step 5: Jobs Tab
        self.cursor.execute("DESCRIBE Jobs")
        job_columns = [col[0] for col in self.cursor.fetchall()]
        self.cursor.execute("SELECT * FROM Jobs WHERE CustomerID = %s", (customer_id,))
        all_jobs = self.cursor.fetchall()

        jobs_tab = QWidget()
        jobs_layout = QVBoxLayout()
        jobs_table = QTableWidget()
        jobs_table.setColumnCount(len(job_columns))
        jobs_table.setHorizontalHeaderLabels(job_columns)
        jobs_table.setRowCount(len(all_jobs))
        
        for row, job in enumerate(all_jobs):
            for col, value in enumerate(job):
                jobs_table.setItem(row, col, QTableWidgetItem(str(value)))

        jobs_table.resizeColumnsToContents()
        jobs_layout.addWidget(jobs_table)
        jobs_tab.setLayout(jobs_layout)
        tab_widget.addTab(jobs_tab, "Jobs")
        
        # Step 6: Individual Tables as Tabs
        self.cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in self.cursor.fetchall()]
        
        for table_name in tables:
            if table_name.lower() in ["customers", "jobs", "walkins"]:
                continue

            self.cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in self.cursor.fetchall()]
            
            table_tab = QWidget()
            table_layout = QVBoxLayout()
            
            table_widget = QTableWidget()
            table_widget.setColumnCount(len(columns))
            table_widget.setHorizontalHeaderLabels(columns)
            
            self.cursor.execute(f"SELECT * FROM `{table_name}` WHERE JobID IN (SELECT JobID FROM Jobs WHERE CustomerID = %s)", (customer_id,))
            table_data = self.cursor.fetchall()
            table_widget.setRowCount(len(table_data))
            
            for row_idx, row in enumerate(table_data):
                for col_idx, value in enumerate(row):
                    table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            
            table_widget.resizeColumnsToContents()
            table_layout.addWidget(table_widget)
            table_tab.setLayout(table_layout)
            tab_widget.addTab(table_tab, table_name.capitalize())
        
        # Step 7: Buttons
        button_layout = QHBoxLayout()
        export_button = QPushButton("Export to Excel")
        close_button = QPushButton("Close")
        button_layout.addWidget(export_button)
        button_layout.addWidget(close_button)
        
        def export_to_excel():
            file_path, _ = QFileDialog.getSaveFileName(customer_window, "Save File", "", "Excel Files (*.xlsx)")
            if not file_path:
                return

            report_data = {
                "Customer Information": pd.DataFrame([customer_info], columns=customer_columns),
                "Jobs": pd.DataFrame(all_jobs, columns=job_columns)
            }
            
            for table_name in tables:
                if table_name.lower() in ["customers", "jobs", "walkins"]:
                    continue

                self.cursor.execute(f"DESCRIBE `{table_name}`")
                columns = [col[0] for col in self.cursor.fetchall()]
                self.cursor.execute(f"SELECT * FROM `{table_name}` WHERE JobID IN (SELECT JobID FROM Jobs WHERE CustomerID = %s)", (customer_id,))
                table_data = self.cursor.fetchall()
                
                if table_data:
                    report_data[table_name] = pd.DataFrame(table_data, columns=columns)
            
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                for sheet_name, df in report_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            QMessageBox.information(customer_window, "Export Successful", f"Customer report exported to {file_path}")

        export_button.clicked.connect(export_to_excel)
        close_button.clicked.connect(customer_window.close)
        
        layout.addWidget(tab_widget)
        layout.addLayout(button_layout)
        customer_window.setLayout(layout)
        customer_window.exec_()

    def dashboard_page(self): #UI + DATA_ACCESS
        """Displays the dashboard with income prediction and new features."""
        
        self.dashboard_dialog = QDialog(self)
        self.dashboard_dialog.setWindowTitle("📊 Business Dashboard")
        self.dashboard_dialog.setGeometry(400, 400, 1500, 950)
        self.dashboard_dialog.setWindowState(Qt.WindowFullScreen)


        layout = QVBoxLayout()

        # Scrollable Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        layout.addWidget(QLabel("<h2>📊 Business Dashboard</h2>", alignment=Qt.AlignCenter))
        layout.addWidget(scroll_area)

        def add_chart_to_layout(fig, title=""):
            """Adds a chart to the scrollable layout with spacing and fixed size."""
            fig.suptitle(title, fontsize=14, fontweight='bold')
            canvas = FigureCanvas(fig)
            canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            canvas.setFixedHeight(400)
            scroll_layout.addWidget(canvas)
            scroll_layout.addSpacing(20)


        try:
            ### CUSTOMER ACQUISITION ###
            self.cursor.execute("SELECT HowHeard, COUNT(*) FROM howheard GROUP BY HowHeard;")
            results = self.cursor.fetchall()
            if results:
                # Filter out None values from results
                results = [(source, count) for source, count in results if source is not None and count is not None]
                if results:
                    labels, values = zip(*results)
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Set2.colors)
                    add_chart_to_layout(fig, "Customer Acquisition by Referral Source")

            ### TOP CUSTOMERS BY JOB COUNT ###
            self.cursor.execute("SELECT CustomerID, COUNT(*) FROM JOBS GROUP BY CustomerID ORDER BY COUNT(*) DESC LIMIT 10;")
            results = self.cursor.fetchall()
            if results:
                # Filter out None values from customers or job counts
                results = [(cust, count) for cust, count in results if cust is not None and count is not None]
                if results:
                    customers, job_counts = zip(*results)
                    customers = list(map(str, customers))  # Convert CustomerID to string if needed
                    job_counts = np.array(job_counts, dtype=float)  # Ensure counts are numeric

                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(customers, job_counts, color="blue")
                    ax.set_xlabel("Customer ID")
                    ax.set_ylabel("Job Count")
                    ax.tick_params(axis='x', rotation=45)  # Rotate x-axis labels for better readability
                    add_chart_to_layout(fig, "Top Customers by Job Count")

            ### MOST FREQUENT DEVICE Brands ###
            self.cursor.execute("SELECT DeviceBrand, COUNT(*) FROM JOBS GROUP BY DeviceBrand ORDER BY COUNT(*) DESC LIMIT 10;")
            results = self.cursor.fetchall()
            if results:
                # Filter out None values from issues or counts
                results = [(issue, count) for issue, count in results if issue is not None and count is not None]
                if results:
                    issues, counts = zip(*results)
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.barh(issues, counts, color="orange")
                    ax.set_xlabel("Count")
                    ax.set_ylabel("Device Brand")
                    add_chart_to_layout(fig, "Most Frequent Device Brands")

            ### DEVICE AND ISSUE TRENDS ###
            self.cursor.execute("""
                SELECT DeviceType, COUNT(*) 
                FROM JOBS
                GROUP BY DeviceType
                ORDER BY COUNT(*) DESC
                LIMIT 10;
            """)
            results = self.cursor.fetchall()
            if results:
                # Filter out None values from device types or job counts
                results = [(device, count) for device, count in results if device is not None and count is not None]
                if results:
                    device_types, job_counts = zip(*results)
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(device_types, job_counts, color="orange")
                    ax.set_xlabel("Device Type")
                    ax.set_ylabel("Job Count")
                    ax.set_title("Most Common Device Types")
                    ax.tick_params(axis='x', rotation=45)
                    plt.subplots_adjust(bottom=0.3)  # Increases space at the bottom
                    add_chart_to_layout(fig)

            
            ### JOB STATUS DISTRIBUTION ###
            self.cursor.execute("SELECT Status, COUNT(*) FROM JOBS GROUP BY Status;")
            results = self.cursor.fetchall()
            if results:
                # Filter out None values from results
                results = [(status, count) for status, count in results if status is not None and count is not None]
                if results:
                    labels, values = zip(*results)
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ax.bar(labels, values, color=["blue", "green", "red", "purple", "yellow"])
                    ax.set_xlabel("Job Status")
                    ax.set_ylabel("Count")
                    add_chart_to_layout(fig, "Job Status Distribution")

            ### JOB DURATION ANALYSIS (in Days) ###
            self.cursor.execute("""
                SELECT Technician, AVG(TIMESTAMPDIFF(DAY, StartDate, EndDate)) 
                FROM JOBS 
                WHERE StartDate IS NOT NULL AND EndDate IS NOT NULL
                GROUP BY Technician;
            """)
            results = self.cursor.fetchall()
            if results:
                # Filter out None values from technicians or average durations
                results = [(technician, avg_duration) for technician, avg_duration in results if technician is not None and avg_duration is not None]
                if results:
                    technicians, avg_durations = zip(*results)
                    
                    # Create the bar plot with days as the unit
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(technicians, avg_durations, color="purple")
                    
                    # Set axis labels and title
                    ax.set_xlabel("Technician")
                    ax.set_ylabel("Average Duration (Days)")  # Change label to 'Days'
                    ax.set_title("Average Job Duration by Technician (in Days)")  # Title adjusted for days
                    ax.tick_params(axis='x', rotation=45)  # Rotate x-axis labels for better readability
                    add_chart_to_layout(fig)


            

            self.cursor.execute("""
                SELECT Issue, COUNT(*) 
                FROM JOBS
                GROUP BY Issue
                ORDER BY COUNT(*) DESC
                LIMIT 10;
            """)
            results = self.cursor.fetchall()
            if results:
                # Filter out None values from issues or issue counts
                results = [(issue, count) for issue, count in results if issue is not None and count is not None]
                if results:
                    issues, issue_counts = zip(*results)
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.barh(issues, issue_counts, color="blue")
                    ax.set_xlabel("Count")
                    ax.set_ylabel("Device Issue")
                    ax.set_title("Most Frequent Device Issues")
                    add_chart_to_layout(fig)

            ### WORKLOAD DISTRIBUTION ###
            self.cursor.execute("""
                SELECT Technician, COUNT(*) 
                FROM JOBS
                GROUP BY Technician
                ORDER BY COUNT(*) DESC;
            """)
            results = self.cursor.fetchall()
            if results:
                # Filter out None values from technicians or job counts
                results = [(technician, count) for technician, count in results if technician is not None and count is not None]
                if results:
                    technicians, job_counts = zip(*results)
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(technicians, job_counts, color="cyan")
                    ax.set_xlabel("Technician")
                    ax.set_ylabel("Job Count")
                    ax.set_title("Technician Workload Distribution")
                    ax.tick_params(axis='x', rotation=45)
                    add_chart_to_layout(fig)

            ### JOB COMPLETION TIME ANALYSIS (in Days) ###
            self.cursor.execute("""
                SELECT AVG(TIMESTAMPDIFF(DAY, StartDate, EndDate)) 
                FROM JOBS
                WHERE StartDate IS NOT NULL AND EndDate IS NOT NULL;
            """)
            result = self.cursor.fetchone()
            if result and result[0] is not None:
                avg_duration = result[0]
                
                # Create a bar chart for average job duration in days
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.bar(["Average Job Duration"], [avg_duration], color="red")
                
                # Set axis labels and title
                ax.set_ylabel("Average Duration (Days)")  # Change label to 'Days'
                ax.set_title("Average Job Completion Time (in Days)")  # Title adjusted for days
                
                add_chart_to_layout(fig)


            ### WALK-IN VOLUME & TRENDS ###
            self.cursor.execute("""
                SELECT DATE(WalkinDate), COUNT(*) 
                FROM walkins
                GROUP BY DATE(WalkinDate)
                ORDER BY DATE(WalkinDate);
            """)
            results = self.cursor.fetchall()
            if results:
                # Filter out None values from dates or walkin counts
                results = [(date, count) for date, count in results if date is not None and count is not None]
                if results:
                    dates, walkin_counts = zip(*results)
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.plot(dates, walkin_counts, marker="o", color="brown")
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Walk-In Count")
                    ax.set_title("Walk-In Volume Over Time")
                    ax.tick_params(axis='x', rotation=45)
                    add_chart_to_layout(fig)

            ### WALK-IN SERVICE TYPE ###
            self.cursor.execute("""
                SELECT Description, COUNT(*) 
                FROM walkins
                GROUP BY Description
                ORDER BY COUNT(*) DESC
                LIMIT 10;
            """)
            results = self.cursor.fetchall()
            if results:
                # Filter out None values from descriptions or service counts
                results = [(desc, count) for desc, count in results if desc is not None and count is not None]
                if results:
                    descriptions, service_counts = zip(*results)
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.barh(descriptions, service_counts, color="pink")
                    ax.set_xlabel("Count")
                    ax.set_ylabel("Walk-In Service Description")
                    ax.set_title("Most Common Walk-In Services")
                    add_chart_to_layout(fig)

            


            # SQL to calculate the average jobs per day per week
            self.cursor.execute("""
                SELECT WEEK(StartDate) AS WeekNumber, DAYOFWEEK(StartDate) AS DayOfWeek, COUNT(*) AS JobCount
                FROM JOBS
                WHERE StartDate IS NOT NULL AND DAYOFWEEK(StartDate) != 1  -- Exclude Sunday
                GROUP BY WeekNumber, DayOfWeek
                ORDER BY WeekNumber, DayOfWeek;
            """)
            results = self.cursor.fetchall()

            if results:
                # Map day numbers to names
                days_of_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                
                # Initialize data structures to hold weekly job counts
                weekly_job_counts = {}
                
                # Populate the weekly job counts
                for week_number, day_of_week, job_count in results:
                    if week_number not in weekly_job_counts:
                        weekly_job_counts[week_number] = [0] * 6  # We only need Monday-Saturday
                    weekly_job_counts[week_number][day_of_week - 2] = job_count  # Map day to 0-based index (Mon=0, Sat=5)
                
                # Calculate the average jobs per day for each week
                avg_jobs_per_day_per_week = {}
                for week_number, job_counts in weekly_job_counts.items():
                    avg_jobs_per_day_per_week[week_number] = sum(job_counts) / len([job_count for job_count in job_counts if job_count > 0])  # Exclude days with no jobs
                
                # Plot the job counts and averages
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Plot the job counts for each week
                for week_number, job_counts in weekly_job_counts.items():
                    ax.plot(days_of_week[1:7], job_counts, marker="o", label=f"Week {week_number}")

                ax.set_xlabel("Day of the Week")
                ax.set_ylabel("Job Count")
                ax.set_title("Job Counts Per Day (Excluding Sunday) for Each Week")
                ax.legend(title="Weeks")
                
                add_chart_to_layout(fig)

                # Query for the average job intake per day of the week, excluding Sundays
                # Get the earliest job date from the database
                self.cursor.execute("""
                    SELECT MIN(StartDate) 
                    FROM jobs;
                """)
                earliest_record = self.cursor.fetchone()

                # Extract the earliest job date from the result
                start_date = earliest_record[0] if earliest_record and earliest_record[0] else '2000-01-01'  # Default to a very old date if no record is found

                # Average job intake per day (excluding Sunday)
                self.cursor.execute("""
                    SELECT DAYOFWEEK(StartDate) AS DayOfWeek, COUNT(*) / COUNT(DISTINCT WEEK(StartDate)) AS AvgJobCount
                    FROM jobs
                    WHERE DAYOFWEEK(StartDate) != 1 AND StartDate >= %s
                    GROUP BY DayOfWeek
                    ORDER BY DayOfWeek;
                """, (start_date,))

                results = self.cursor.fetchall()

                if results:
                    # Filter out None values
                    results = [(day_of_week, avg_count) for day_of_week, avg_count in results if day_of_week is not None and avg_count is not None]

                    if results:
                        # Map days of the week to their corresponding names (excluding Sunday)
                        days_of_week = {
                            2: "Monday",
                            3: "Tuesday",
                            4: "Wednesday",
                            5: "Thursday",
                            6: "Friday",
                            7: "Saturday"
                        }

                        # Prepare data for plotting
                        days, avg_counts = zip(*results)
                        days = [days_of_week[day] for day in days]

                        # Create a bar chart
                        fig1, ax1 = plt.subplots(figsize=(8, 4))
                        ax1.bar(days, avg_counts, color="blue")
                        ax1.set_xlabel("Day of the Week")
                        ax1.set_ylabel("Average Job Count")
                        ax1.set_title("Average Job Intake per Day of Week (Excluding Sunday)")
                        ax1.tick_params(axis='x', rotation=45)
                        plt.tight_layout()
                        add_chart_to_layout(fig1)

                
                # Step 1: Extract the time of day (in minutes) from the startdate for all jobs
                # Step 1: Extract the time of day (in minutes) from the startdate for all jobs
                self.cursor.execute("""
                    SELECT TIMESTAMPDIFF(SECOND, DATE(StartDate), StartDate)
                    FROM JOBS
                    WHERE StartDate IS NOT NULL;
                """)
                times_in_seconds = [row[0] for row in self.cursor.fetchall() if row[0] is not None]

                # Convert to minutes for easier readability
                times_in_minutes = [time / 60 for time in times_in_seconds]

                # Step 2: Plot the histogram of time distribution (overall)
                fig, ax = plt.subplots(figsize=(10, 6))
                counts, bins, patches = ax.hist(times_in_minutes, bins=24, color='orange', edgecolor='black')  # 24 bins for each hour
                ax.set_xlabel('Time of Day (minutes from midnight)')
                ax.set_ylabel('Number of Jobs')
                ax.set_title('Overall Job Start Time Distribution')

                # Format the x-axis labels to show time in HH:MM format
                ax.set_xticks(range(0, 1440, 60))
                ax.set_xticklabels([f'{i//60:02}:{i%60:02}' for i in range(0, 1440, 60)])

                # Step 3: Calculate the overall average time of day (in minutes)
                avg_time_minutes = sum(times_in_minutes) / len(times_in_minutes)

                # Step 4: Add a vertical line for the average time
                ax.axvline(avg_time_minutes, color='red', linestyle='dashed', linewidth=2, 
                            label=f'Avg: {avg_time_minutes//60:02}:{avg_time_minutes%60:02} ({avg_time_minutes/60:.2f} hrs)')

                # Step 5: Find the busiest time interval (bin with the maximum count)
                max_count_bin_index = counts.argmax()  # Get the index of the bin with the most jobs
                max_count_bin_start = bins[max_count_bin_index]
                max_count_bin_end = bins[max_count_bin_index + 1]

                # Label the busiest time period on the plot
                ax.text(
                    max_count_bin_start + (max_count_bin_end - max_count_bin_start) / 2,  # Position at the center of the bin
                    counts[max_count_bin_index] + 1,  # Position a little above the highest bar
                    f'Busiest: {int(max_count_bin_start // 60):02}:{int(max_count_bin_start % 60):02} - {int(max_count_bin_end // 60):02}:{int(max_count_bin_end % 60):02}',
                    color='blue', ha='center', fontsize=10, fontweight='bold'
                )

                # Step 6: Add the average time label at the top of the graph
                avg_time_hours = int(avg_time_minutes // 60)  # Hours part
                avg_time_minutes_only = int(avg_time_minutes % 60)  # Minutes part

                # Format the time as HH:MM
                formatted_avg_time = f'{avg_time_hours:02}:{avg_time_minutes_only:02}'

                # Add the label at the top of the graph
                ax.text(
                    avg_time_minutes,  # Position it near the average time vertical line
                    counts.max() * 0.85,  # Place the label slightly below the top of the bars
                    f'Avg Time: {formatted_avg_time}',  # Using the formatted time
                    color='red', ha='center', fontsize=12, fontweight='bold'
)

                # Step 7: Adjust layout and add to your layout
                plt.tight_layout()

                # Assuming add_chart_to_layout is a function that takes in a matplotlib figure
                add_chart_to_layout(fig)  # Adding the figure to your layout





            


                # Fetch the number of customers and jobs
                self.cursor.execute("SELECT COUNT(*) FROM customers;")
                customer_count = self.cursor.fetchone()[0]  # Fetch customer count

                self.cursor.execute("SELECT COUNT(*) FROM jobs;")
                job_count = self.cursor.fetchone()[0]  # Fetch job count

                self.cursor.execute("SELECT COUNT(*) FROM Walkins;")
                walkin_count = self.cursor.fetchone()[0]  # Fetch Walkin count

                # Format the output nicely
                info_text = f"""
                <b>📌 Database Summary:</b><br>
                ✔ <b>Number of Customers:</b> {customer_count}<br>
                ✔ <b>Number of Jobs:</b> {job_count}<br>
                ✔ <b>Number of Walkins:</b> {walkin_count}
                """

                # Create QLabel for displaying the counts
                self.database_summary_label = QLabel(info_text)
                self.database_summary_label.setAlignment(Qt.AlignCenter)
                self.database_summary_label.setStyleSheet("""
                    QLabel {
                        font-size: 16px;
                        font-weight: bold;
                        color: #2c3e50;
                        background-color: #ecf0f1;
                        padding: 10px;
                        border-radius: 8px;
                    }
                """)

                # Add label to the layout (replace add_chart_to_layout)
                scroll_layout.addWidget(self.database_summary_label, alignment=Qt.AlignCenter)









        except mariadb.Error as e:
            scroll_layout.addWidget(QLabel(f"⚠ Error retrieving data: {e}", alignment=Qt.AlignCenter))

        # Navigation Buttons
        button_layout = QHBoxLayout()

        # Back Button
        back_button = QPushButton("🔙 Back to Main Menu")
        back_button.setStyleSheet("background-color: #3A9EF5; color: white; padding: 10px; border-radius: 5px;")

        def close_graphs_and_return():
            """Closes all open Matplotlib figures and returns to the main menu."""
            plt.close('all')
            reset_window_size(self)

        back_button.clicked.connect(close_graphs_and_return)
        button_layout.addWidget(back_button)

        layout.addLayout(button_layout)
        self.dashboard_dialog.setLayout(layout)
        self.dashboard_dialog.exec_()
   
if __name__ == "__main__": #MAIN
    try:
        app = QApplication(sys.argv)
        
        # ✅ Global StyleSheet (Ensure text is visible)
        app.setStyleSheet("""
            QMessageBox { background-color: #2A2A2A; }
            QLabel { color: black; font-size: 14px; }  /* Ensure text is readable */
            QPushButton { background-color: #3A9EF5; color: white; padding: 10px; border-radius: 5px; }
        """)

        # ✅ Create and Show Splash Screen
        splashscreen = SplashScreen()
        splashscreen.show()
        app.processEvents()  # ✅ Ensure UI updates before proceeding

        # ✅ Start Loading Thread
        loading_thread = InitializationThread()
        loading_thread.progress.connect(splashscreen.update_progress)

        def start_main_app():
            """ Called when initialization is complete """
            splashscreen.close()  # ✅ Close splash screen first
            app.processEvents()  # ✅ Ensure UI updates before creating the main window

            # ✅ Initialize the main application window
            window = DatabaseApp()
            window.show()

        loading_thread.finished.connect(start_main_app)
        loading_thread.start()  # Start loading process

        sys.exit(app.exec_())

    except Exception as e:
        error_message = f"Unexpected error: {e}\n{traceback.format_exc()}"
        log_error(error_message)




# I need one way for logging errors not lots of little ways and little files.
# refactor the code
