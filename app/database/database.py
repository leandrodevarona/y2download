import sqlite3

DATABASE_URL = "app/database/database.db"

def get_db_connection():
    """Returns a new sqlite3 database connection."""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # This allows you to access columns by name
    return conn

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()