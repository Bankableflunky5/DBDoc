from PyQt5.QtWidgets import QInputDialog, QFileDialog, QMessageBox
import mariadb
from error_utils import log_error, handle_db_error
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMessageBox

def restore_database(conn, cursor, parent_widget=None):
    db_name, ok = QInputDialog.getText(parent_widget, "Database Name", "Enter the name of the new database:")
    if not ok or not db_name:
        QMessageBox.warning(parent_widget, "Input Error", "Database name cannot be empty.")
        return

    # Ask the user to select a backup file
    backup_file, _ = QFileDialog.getOpenFileName(
        parent_widget,
        "Select Backup File",
        "",
        "SQL Files (*.sql);;All Files (*)"
    )
    if not backup_file:
        QMessageBox.warning(parent_widget, "Input Error", "No backup file selected.")
        return

    try:
        if not conn:
            raise Exception("No valid database connection found.")

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")
        QMessageBox.information(parent_widget, "Success", f"Database '{db_name}' created successfully.")

        cursor.execute(f"USE {db_name};")

        # Open the backup file and execute its content
        with open(backup_file, "r") as file:
            sql_commands = file.read()

        # Execute each command in the SQL file
        for command in sql_commands.split(";"):
            command = command.strip()
            if command:
                try:
                    print(f"Executing: {command}")
                    cursor.execute(command)
                except mariadb.Error as e:
                    log_error(f"Failed to execute command: {command}. Error: {e}")
                    continue  # Skip the failed command

        conn.commit()
        QMessageBox.information(parent_widget, "Success", f"Database restored successfully to '{db_name}'.")

    except mariadb.Error as e:
        handle_db_error(e, context=f"Failed to restore database '{db_name}'")
    except Exception as e:
        log_error(f"An unexpected error occurred: {e}")


def change_db_password(database_config, conn):
    """Prompts the user to enter their old password, a new password, and confirm the new password before updating it."""

    # Ensure database configuration exists
    if not database_config or 'database' not in database_config:
        QMessageBox.critical(None, "Error", "Database configuration is missing!")
        return

    database_name = database_config.get("database")  # Fetch database name

    # Ask for old password
    old_password, ok = QInputDialog.getText(None, "Change Password", "Enter your current database password:", QLineEdit.Password)

    if not ok:
        return

    if not old_password:
        QMessageBox.warning(None, "Warning", "Current password cannot be empty.")
        return

    # Ask for new password twice for confirmation
    new_password, ok = QInputDialog.getText(None, "Change Password", "Enter new database password:", QLineEdit.Password)

    if not ok:
        return 

    if not new_password:
        QMessageBox.warning(None, "Warning", "New password cannot be empty.")
        return

    confirm_password, ok = QInputDialog.getText(None, "Change Password", "Confirm new database password:", QLineEdit.Password)

    if not ok:
        return

    if not confirm_password:
        QMessageBox.warning(None, "Warning", "Please confirm the new password.")
        return

    if new_password != confirm_password:
        QMessageBox.critical(None, "Error", "New passwords do not match. Please try again.")
        return

    # Ensure there is an active database connection
    if not conn:
        QMessageBox.critical(None, "Error", "Database connection is not established!")
        return

    cursor = None  # Ensure cursor is defined before try block

    try:
        cursor = conn.cursor()

        # Step 1: Get the currently logged-in database username
        cursor.execute("SELECT USER();")  # Returns 'username@host'
        db_user = cursor.fetchone()[0]  # Example: 'root@localhost'
        db_username, db_host = db_user.split('@')

        # Debugging: Print the username and host being used for verification
        print(f"Attempting to verify with {db_username}@{db_host}")

          # Specify the SSL certificate paths (adjust to your paths)
        ssl_ca = "C:/ssl/mariadb/mariadb.crt"  # Certificate Authority (CA) file
        ssl_cert = "C:/ssl/mariadb/mariadb.crt"  # Client certificate file
        ssl_key = "C:/ssl/mariadb/mariadb.key "  # Client private key file

        # Step 2: Verify the old password by attempting a reconnection
        try:
            temp_conn = mariadb.connect(
                user=db_username,
                password=old_password,
                host=database_config.get("host", "localhost"),
                database=database_config.get("database", ""),
                ssl_ca=ssl_ca,
                ssl_cert=ssl_cert,
                ssl_key=ssl_key
            )
            temp_conn.close()  # If successful, close temporary connection
        except mariadb.Error as err:
            # Error handling for connection issues
            print(f"Error while reconnecting: {err}")
            QMessageBox.critical(None, "Error", "Old password is incorrect.")
            return

        # Step 3: Update password using ALTER USER
        cursor.execute(f"ALTER USER '{db_username}'@'{db_host}' IDENTIFIED BY '{new_password}';")
        conn.commit()

        # Step 4: Flush privileges to apply changes
        cursor.execute("FLUSH PRIVILEGES;")
        conn.commit()

        QMessageBox.information(None, "Success", "Database password changed successfully!")

    except mariadb.Error as e:
        print(f"Error during password verification: {str(e)}")
        QMessageBox.critical(None, "Error", f"Failed to change password: {str(e)}")

    finally:
        if cursor:
            cursor.close()
