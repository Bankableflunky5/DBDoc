from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

# SplashScreen Class
# ----------------------
# This class creates a splash screen UI with a progress bar 
# using PyQt5. It extends QSplashScreen to display an initial 
# screen while the application is loading or initializing.
#
# The __init__() method sets up the splash screen by:
# - Loading and scaling a custom splash image (replace 'splash.png' 
#   with your own logo).
# - Adding a progress bar at the bottom of the screen, styled 
#   with custom CSS to match the application's design.
# - Adding a title ("Initializing...") above the progress bar.
#
# The update_progress() method is used to update the value of 
# the progress bar. It takes an integer value (0-100) to represent 
# the progress of the initialization process. This can be connected 
# to a background thread (e.g., InitializationThread) to reflect 
# real-time progress during application startup.


class SplashScreen(QSplashScreen): #UI
    """ Splash Screen with a progress bar """

    def __init__(self):
        super().__init__()

        # Load and scale a splash image (replace 'splash.png' with your own logo)
        self.setPixmap(QPixmap("splash.png").scaled(500, 300, Qt.KeepAspectRatio))

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 250, 400, 20)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3A9EF5;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3A9EF5;
                width: 10px;
            }
        """)

        # Title and Progress Bar Layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("<h2>🔄 Initializing...</h2>", self))
        self.layout.addWidget(self.progress_bar)
        self.setLayout(self.layout)

    def update_progress(self, value):
        """ Update the progress bar """
        self.progress_bar.setValue(value)
