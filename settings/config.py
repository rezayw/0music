import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # naik 1 level dari settings/

# macOS Music app auto-import folder
HOME_DIR = os.path.expanduser("~")
MUSIC_AUTO_ADD = os.path.join(HOME_DIR, "Music", "Music", "Media.localized", "Automatically Add to Music.localized")

# Use Music app's auto-import folder if it exists, otherwise use ~/Music
if os.path.exists(MUSIC_AUTO_ADD):
    OUTPUT_DIR = MUSIC_AUTO_ADD
else:
    OUTPUT_DIR = os.path.join(HOME_DIR, "Music", "0music")

DB_PATH = os.path.join(BASE_DIR, "settings", "music.db")

# Pastikan folder ada
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
