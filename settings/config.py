import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # naik 1 level dari settings/

# macOS Music app auto-import folder
HOME_DIR = os.path.expanduser("~")
MUSIC_AUTO_ADD = os.path.join(HOME_DIR, "Music", "Music", "Media.localized", "Automatically Add to Music.localized")


# Always use a safe working directory for downloads
OUTPUT_DIR = os.path.join(HOME_DIR, "Music", "0music")

# If Music auto-import exists, set a flag for post-processing
MUSIC_AUTO_ADD_EXISTS = os.path.exists(MUSIC_AUTO_ADD)

DB_PATH = os.path.join(BASE_DIR, "settings", "music.db")

# Pastikan folder ada
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
