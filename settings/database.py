import sqlite3
from .config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS music (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            genre TEXT,
            downloaded DATETIME DEFAULT CURRENT_TIMESTAMP,
            filename TEXT,
            lurl TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_song(title, filename, author, genre, downloaded, lurl):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO music (title, author, genre, downloaded, filename, lurl) VALUES (?, ?, ?, ?, ?, ?)', (title, author, genre, downloaded, filename, lurl))
    conn.commit()
    conn.close()

def get_all_songs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM music ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows
