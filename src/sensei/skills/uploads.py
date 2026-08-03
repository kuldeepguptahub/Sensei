"""
Upload skills for Sensei.

These skills manage user-provided resources during planning.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List

# Base directory for courses
COURSES_DIR = Path("courses")


def save_upload(course_name: str, file_name: str, content: bytes) -> None:
    """
    Save an uploaded file to a course workspace.

    Args:
        course_name: Name of the course
        file_name: Name of the file to save
        content: File content as bytes

    Raises:
        ValueError: If the course doesn't exist
        OSError: If saving fails
    """
    upload_path = COURSES_DIR / course_name / "uploads" / file_name
    if not upload_path.parent.exists():
        raise ValueError(f"Course '{course_name}' doesn't exist")

    upload_path.write_bytes(content)


def read_upload(course_name: str, file_name: str) -> bytes:
    """
    Read an uploaded file from a course workspace.

    Args:
        course_name: Name of the course
        file_name: Name of the file to read

    Returns:
        File content as bytes

    Raises:
        ValueError: If the course or file doesn't exist
        OSError: If reading fails
    """
    upload_path = COURSES_DIR / course_name / "uploads" / file_name
    if not upload_path.exists():
        raise ValueError(f"Upload '{file_name}' not found in course '{course_name}'")

    return upload_path.read_bytes()


def list_uploads(course_name: str) -> Dict[str, Dict[str, Any]]:
    """
    List all uploads in a course workspace.

    Args:
        course_name: Name of the course

    Returns:
        Dictionary of upload information

    Raises:
        ValueError: If the course doesn't exist
    """
    uploads_dir = COURSES_DIR / course_name / "uploads"
    if not uploads_dir.exists():
        raise ValueError(f"Course '{course_name}' doesn't exist")

    uploads = {}
    for upload_path in uploads_dir.iterdir():
        if upload_path.is_file():
            uploads[upload_path.name] = {
                "path": str(upload_path),
                "size": upload_path.stat().st_size,
                "modified": upload_path.stat().st_mtime
            }

    return uploads