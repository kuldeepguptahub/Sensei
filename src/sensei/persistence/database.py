from pathlib import Path
import sqlite3
from typing import Optional, Dict, Any, List

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

def list_courses() -> List[tuple]:
    """List all courses in the database.

    Returns:
        A list of course tuples (id, name, status, created_at, last_accessed)
    """
    conn = get_connection()
    cursor = conn.execute('''
    SELECT * FROM courses
    ''')
    return cursor.fetchall()


def insert_course(name: str, status: str = 'created') -> int:
    """Insert a new course into the database.

    Args:
        name: The name of the course
        status: The initial status of the course (default: 'created')

    Returns:
        The ID of the newly inserted course
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO courses (name, status) VALUES (?, ?)',
        (name, status)
    )
    course_id = cursor.lastrowid
    conn.commit()

    return course_id


def get_course(course_id: Optional[int] = None, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get a course by ID or name.

    Args:
        course_id: The ID of the course to retrieve
        name: The name of the course to retrieve

    Returns:
        A dictionary containing course information, or None if not found
    """
    if not course_id and not name:
        raise ValueError("Either course_id or name must be provided")

    conn = get_connection()
    cursor = conn.cursor()

    if course_id:
        cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    else:
        cursor.execute('SELECT * FROM courses WHERE name = ?', (name,))

    course = cursor.fetchone()

    if not course:
        return None

    return {
        'id': course[0],
        'name': course[1],
        'status': course[2],
        'created_at': course[3],
        'last_accessed': course[4]
    }


def update_course(course_id: int, **kwargs) -> bool:
    """Update a course with the given parameters.

    Args:
        course_id: The ID of the course to update
        **kwargs: Fields to update (name, status, last_accessed)

    Returns:
        True if the course was updated, False if not found
    """
    if not kwargs:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    # Check if course exists
    cursor.execute('SELECT id FROM courses WHERE id = ?', (course_id,))
    if not cursor.fetchone():
        return False

    # Build the update query
    set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values())
    values.append(course_id)

    query = f'UPDATE courses SET {set_clause} WHERE id = ?'
    cursor.execute(query, values)
    conn.commit()

    return True


def delete_course(course_id: int) -> bool:
    """Delete a course from the database.

    Args:
        course_id: The ID of the course to delete

    Returns:
        True if the course was deleted, False if not found

    Note:
        This is currently a stub implementation.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Check if course exists
    cursor.execute('SELECT id FROM courses WHERE id = ?', (course_id,))
    if not cursor.fetchone():
        return False

    # Delete the course
    cursor.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    conn.commit()

    return True