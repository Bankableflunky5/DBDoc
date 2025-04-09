# error_utils.py
import logging
from PyQt5.QtWidgets import QMessageBox

# Initialize logging once
logging.basicConfig(
    filename="app_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_error(error_message):
    """
    Logs an error and displays it in a styled QMessageBox.
    """
    logging.error(error_message)

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Application Error")
    msg.setText("An unexpected error occurred. Please check the logs.")
    msg.setDetailedText(error_message)
    msg.setStyleSheet("""
        QMessageBox { background-color: #2A2A2A; }
        QLabel { color: black; font-size: 14px; }
        QPushButton { background-color: #3A9EF5; color: white; padding: 10px; border-radius: 5px; }
    """)
    msg.exec_()

def handle_db_error(error, context="Database Error"):
    """
    Logs and displays a database-specific error message.
    """
    error_message = f"{context}: {error}"
    logging.error(error_message)

    QMessageBox.critical(
        None,
        "Database Error",
        f"⚠ An error occurred:\n{error}\n\nPlease check the logs for details."
    )

