# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect("cargo.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            itemId TEXT PRIMARY KEY,
            name TEXT,
            width INTEGER,
            depth INTEGER,
            height INTEGER,
            priority INTEGER,
            expiryDate TEXT,
            usageLimit INTEGER,
            preferredZone TEXT,
            containerId TEXT,
            startX INTEGER,
            startY INTEGER,
            startZ INTEGER,
            FOREIGN KEY(containerId) REFERENCES containers(containerId)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS containers (
            containerId TEXT PRIMARY KEY,
            zone TEXT,
            width INTEGER,
            depth INTEGER,
            height INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect("cargo.db", check_same_thread=False)