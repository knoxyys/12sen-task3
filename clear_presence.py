# not needed anymore! debug button does this

import sqlite3

DB_NAME = "attendance.db"

def clear_presence_table():
    """Wipes all rows from the presence table in attendance.db."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Delete all presence records
        cursor.execute("DELETE FROM presence;")
        
        conn.commit()
        print("Successfully cleared all presence records.")

    except sqlite3.OperationalError as e:
        print(f"Error accessing database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    clear_presence_table()