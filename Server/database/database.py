import sqlite3
from datetime import datetime

DB_PATH = "Server/database/faces.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_recognition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            face_encoding TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            count INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def add_or_update_face(face_encoding):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if the face already exists
    cursor.execute('SELECT id, count FROM face_recognition WHERE face_encoding = ?', (face_encoding,))
    result = cursor.fetchone()

    if result:
        # Update count if face exists
        face_id, count = result
        cursor.execute('UPDATE face_recognition SET count = ?, timestamp = ? WHERE id = ?', 
                       (count + 1, datetime.now(), face_id))
    else:
        # Insert new face
        cursor.execute('INSERT INTO face_recognition (face_encoding) VALUES (?)', (face_encoding,))

    conn.commit()
    conn.close()