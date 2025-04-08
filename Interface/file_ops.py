# file_ops.py
import os
import json

SETTINGS_FILE = "settings.json"

def load_settings():
    """Loads the database settings from a JSON file."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as file:
            return json.load(file)
    return {"host": "localhost", "database": ""}
