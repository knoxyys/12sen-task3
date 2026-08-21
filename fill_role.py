# to be run separately from app.py!
# all this does is create db tables and preloaded users

import sqlite3

DB_NAME = "attendance.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            period INTEGER NOT NULL DEFAULT 1,
            class_name TEXT NOT NULL DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            reason TEXT DEFAULT '',
            event_time TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()


def create_users(): # would have a more efficient way for roll input in a proper system
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Preloaded users with period and class_name included
    sample_users = [
        ("100125", "Stirling Knox", 1, "12STU2"),
        ("100849", "Troy Harcoan", 1, "12ENA"),
        ("100865", "Charlie Pudsey", 1, "12STU2"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO users (user_id, name, period, class_name) VALUES (?, ?, ?, ?)
    """, sample_users)

    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    create_db()
    create_users()
    print("Roll database sample created")