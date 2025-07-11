import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # naik 1 level dari settings/
OUTPUT_DIR = os.path.join(BASE_DIR, "music")  # ~/Desktop/0Music/music
DB_PATH = os.path.join(BASE_DIR, "settings", "music.db")  # ~/Desktop/0Music/settings/music.db

# Pastikan folder ada
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
