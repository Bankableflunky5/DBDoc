import time
from PyQt5.QtCore import QThread, pyqtSignal

# InitializationThread Class
# ---------------------------
# This class simulates the initialization process of an application
# using a background thread. It extends QThread to run the loading
# process in a separate thread, so the main UI remains responsive.
#
# The run() method simulates a task by emitting progress values from
# 0 to 100, with a small delay (0.05 seconds) between each value 
# to mimic work being done (such as loading or initializing resources).
#
# The progress values are emitted through the 'progress' signal 
# (pyqtSignal), which can be connected to a UI element such as a 
# progress bar to show the user the current loading status.
#
# The InitializationThread class is useful for showing loading 
# progress without freezing the main user interface.

class InitializationThread(QThread): #UI
    """ Simulates application initialization with a progress signal. """
    progress = pyqtSignal(int)

    def run(self):
        """ Simulates the application startup process """
        for i in range(101):  # Simulating a loading process
            time.sleep(0.05)  # Simulate work being done
            self.progress.emit(i)  # Emit progress value
