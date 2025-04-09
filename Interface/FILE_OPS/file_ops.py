# ─────────────────────────────────────────────────────────────────────────────
# 📦 Standard Library
import json
import os
import time

# ─────────────────────────────────────────────────────────────────────────────
# 📊 Data Handling
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# 🔁 Scheduling
import schedule

# ─────────────────────────────────────────────────────────────────────────────
# 🎨 PyQt5 GUI Elements
from PyQt5.QtWidgets import QMessageBox, QFileDialog



SETTINGS_FILE = "settings.json"
SCHEDULE_FILE_PATH = "backup_schedule.json"


def save_database_config(database_config, settings_file):
    """Save database configuration settings into a JSON file."""

    try:
        # Save the current password, host, and database information into the config
        database_config["password"] = database_config["password"]  # You can modify this to match your structure
        database_config["host"] = database_config["host"]
        database_config["database"] = database_config["database"]

        with open(settings_file, "w") as file:
            json.dump(database_config, file)

        return "Settings saved successfully."

    except Exception as e:
        return f"Failed to save settings: {e}"

def schedule_backup(interval="daily", time_of_day="00:00", backup_directory=None, backup_func=None):
    """
    Registers a scheduled backup job using the schedule library.

    Args:
        interval (str): e.g., "daily", "hourly", "every X minutes"
        time_of_day (str): Time for daily backups (HH:MM)
        backup_directory (str): Path where backups are stored
        backup_func (callable): Function to call to perform the backup
    """
    if not backup_func:
        raise ValueError("backup_func must be provided")

    if interval == "daily":
        schedule.every().day.at(time_of_day).do(backup_func, backup_directory)
    elif interval == "hourly":
        schedule.every().hour.do(backup_func, backup_directory)
    elif interval.startswith("every"):
        try:
            minutes = int(interval.split()[1])
            schedule.every(minutes).minutes.do(backup_func, backup_directory)
        except ValueError:
            print(f"⚠️ Invalid interval format: {interval}")
            return

    print(f"✅ Backup scheduled: {interval} at {time_of_day} to → {backup_directory}")

def run_scheduled_backups(stop_event):
    """
    Continuously runs scheduled tasks until the stop_event is set.

    Args:
        stop_event (threading.Event): An event that can be triggered to stop the loop.
    """
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

def save_schedule_to_json(schedule_data, schedule_path, parent=None):
    """
    Save the backup schedule to a JSON file.

    Args:
        schedule_data (dict): The schedule data to save.
        schedule_path (str): Path to the output JSON file.
        parent (optional): QWidget used for QMessageBox (if provided).
    """
    try:
        with open(schedule_path, "w") as json_file:
            json.dump(schedule_data, json_file, indent=4)
        print(f"✅ Backup schedule saved: {schedule_data}")
    except Exception as e:
        if parent:
            QMessageBox.critical(parent, "Error", f"❌ Failed to save backup schedule:\n{e}")

def export_database_to_excel(parent, cursor):
    """
    Exports all tables from the connected database to an Excel file.

    Args:
        parent: QWidget or QMainWindow to use for QFileDialog and QMessageBox.
        cursor: A database cursor object connected to the target database.
    """
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Save Database Export",
        "",
        "Excel files (*.xlsx);;All files (*)"
    )
    
    if not file_path:
        return

    try:
        if not file_path.endswith(".xlsx"):
            file_path += ".xlsx"

        # Get all table names
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]

        # Export each table to its own Excel sheet
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            for table in tables:
                cursor.execute(f"SELECT * FROM {table};")
                data = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(data, columns=columns)
                df.to_excel(writer, sheet_name=table, index=False)

        QMessageBox.information(parent, "✅ Success", f"Database exported successfully to:\n{file_path}")
    
    except Exception as e:
        QMessageBox.critical(parent, "❌ Error", f"Failed to export database:\n{e}")

def load_schedule_from_json(schedule_path, parent=None):
    """
    Loads the backup schedule from a JSON file.

    Args:
        schedule_path (str): Path to the schedule JSON file.
        parent (QWidget, optional): Used as the parent for error message boxes.

    Returns:
        dict or None: The loaded schedule data, or None if loading fails.
    """
    if os.path.exists(schedule_path):
        try:
            with open(schedule_path, "r") as f:
                return json.load(f)
        except Exception as e:
            if parent:
                QMessageBox.critical(parent, "Error", f"Failed to load backup schedule:\n{e}")
    return None

def load_schedule_on_startup(parent):
    """
    Load the backup schedule from a JSON file and apply it during app startup.

    Args:
        parent: The main app/controller, must implement `load_schedule_from_json()` and `schedule_backup(...)`.
    """
    schedule_data = load_schedule_from_json(SCHEDULE_FILE_PATH)
    if not schedule_data:
        return  # Nothing to load

    interval = schedule_data.get("interval")
    time_of_day = schedule_data.get("time_of_day")
    backup_directory = schedule_data.get("backup_directory")

    if interval == "Daily":
        # Apply the schedule using file_ops version
        schedule_backup(
                            interval=interval,
                            time_of_day=time_of_day,
                            backup_directory=backup_directory[0],
                            backup_func=parent.trigger_backup
                        )
    elif interval == "Hourly":
        parent.schedule_backup(interval="hourly", backup_directory=backup_directory)
    elif interval and interval.startswith("every"):
        try:
            minutes = int(interval.split()[1])
            parent.schedule_backup(interval=f"every {minutes} minutes", backup_directory=backup_directory)
        except (IndexError, ValueError):
            # Optional: log or warn about malformed interval
            pass

def save_backup_schedule(parent, interval_combo, time_entry, backup_directory, dialog):
    """
    Save the selected backup schedule and apply it.

    Args:
        parent: Main app/controller with scheduling and save methods.
        interval_combo: QComboBox with the interval selection.
        time_entry: QLineEdit for time input.
        backup_directory: List containing selected backup directory.
        dialog: The QDialog instance to close on success.
    """
    interval = interval_combo.currentText()
    time_of_day = time_entry.text()

    if not backup_directory:
        QMessageBox.warning(parent, "Input Error", "Please select a backup directory.")
        return

    if interval == "Daily" and not time_of_day:
        QMessageBox.warning(parent, "Input Error", "Please specify a time of day for the daily backup.")
        return

    schedule_data = {
        "interval": interval,
        "time_of_day": time_of_day,
        "backup_directory": backup_directory[0]
    }

    # Save to JSON
    save_schedule_to_json(schedule_data, SCHEDULE_FILE_PATH, parent)

    # Apply scheduling logic
    if interval == "Daily":
        schedule_backup(
                            interval="daily",
                            time_of_day=time_of_day,
                            backup_directory=backup_directory[0],
                            backup_func=parent.trigger_backup  # ✅ the real backup logic still lives in your main app
                        )
    elif interval == "Hourly":
        parent.schedule_backup(interval="hourly", backup_directory=backup_directory[0])
    elif interval == "Every X minutes":
        try:
            minutes = int(time_of_day)
            parent.schedule_backup(interval=f"every {minutes} minutes", backup_directory=backup_directory[0])
        except ValueError:
            QMessageBox.warning(parent, "Input Error", "Please enter a valid number of minutes.")
            return

    dialog.accept()
    QMessageBox.information(parent, "✅ Success", "Backup schedule saved successfully.")

def clear_current_schedule(parent):
    """
    Clears the current backup schedule by removing the schedule JSON file.

    Args:
        parent: The main application/controller, must have `load_schedule_from_json()` and `SCHEDULE_FILE_PATH`.
    """
    schedule_data = load_schedule_from_json(SCHEDULE_FILE_PATH)

    if schedule_data:
        try:
            os.remove(parent.SCHEDULE_FILE_PATH)
            QMessageBox.information(parent, "🧹 Schedule Cleared", "✅ The backup schedule has been cleared.")
        except Exception as e:
            QMessageBox.critical(parent, "❌ Error", f"Failed to clear the backup schedule:\n{e}")
    else:
        QMessageBox.information(parent, "No Schedule", "⚠️ No backup schedule to clear.")

def view_current_schedule(parent):
    """
    Displays the current backup schedule using a message box.

    Args:
        parent: The main window or controller. Must have `load_schedule_from_json()`.
    """
    schedule_data = load_schedule_from_json(SCHEDULE_FILE_PATH)

    if schedule_data:
        schedule_details = (
            f"📅 Interval: {schedule_data.get('interval', 'N/A')}\n"
            f"⏰ Time of Day: {schedule_data.get('time_of_day', 'N/A')}\n"
            f"📂 Backup Directory: {schedule_data.get('backup_directory', 'N/A')}"
        )
        QMessageBox.information(parent, "🗓 Current Backup Schedule", schedule_details)
    else:
        QMessageBox.information(parent, "No Schedule", "⚠️ No backup schedule is set.")

def load_settings():
    """Loads the database settings from a JSON file."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as file:
            return json.load(file)
    return {"host": "localhost", "database": ""}

