from pathlib import Path
import sqlite3

# get database path
def get_database_path():
    return Path("sensei.db")

# initialize database
def initialize_database():
    db_path = get_database_path()
    if not db_path.exists():
        #create db
        db_path.touch()
    
    with sqlite3.connect(db_path) as conn:
        conn.execute('''
                        CREATE TABLE IF NOT EXISTS courses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
                     '''
        )

        conn.commit()


# get connection
def get_connection():
    db_path = get_database_path()
    if not db_path.exists():
        initialize_database()
    return sqlite3.connect(db_path)

def list_courses():
    conn = get_connection()
    cursor = conn.execute('''
SELECT * FROM courses        
                 ''')
    return cursor.fetchall()
