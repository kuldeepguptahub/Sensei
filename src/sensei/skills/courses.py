"""
Course skills for Sensei.

These skills manage workspace lifecycle.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List

# Base directory for courses
COURSES_DIR = Path("courses")


def create_workspace(course_name: str) -> None:
    """
    Create a new course workspace with the required structure.

    Args:
        course_name: Name of the course to create

    Raises:
        ValueError: If the course already exists
        OSError: If workspace creation fails
    """
    course_dir = COURSES_DIR / course_name
    if course_dir.exists():
        raise ValueError(f"Course '{course_name}' already exists")

    # Create course directory
    course_dir.mkdir(parents=True)

    # Create artifacts directory
    artifacts_dir = course_dir / "artifacts"
    artifacts_dir.mkdir()

    # Create uploads directory
    uploads_dir = course_dir / "uploads"
    uploads_dir.mkdir()

    # Create empty artifacts
    (artifacts_dir / "definition.json").write_text('{}')
    (artifacts_dir / "planner.md").write_text('')
    (artifacts_dir / "state.json").write_text('{}')
    (artifacts_dir / "context.md").write_text('')
    (artifacts_dir / "notes.md").write_text('')


def list_courses() -> List[Dict[str, Any]]:
    """
    List all available courses.

    Returns:
        List of course information dictionaries
    """
    courses = []
    if COURSES_DIR.exists():
        for course_dir in COURSES_DIR.iterdir():
            if course_dir.is_dir():
                courses.append({
                    "name": course_dir.name,
                    "path": str(course_dir),
                    "created": course_dir.stat().st_ctime
                })
    return courses


def delete_course(course_name: str) -> None:
    """
    Delete a course workspace.

    Args:
        course_name: Name of the course to delete

    Raises:
        ValueError: If the course doesn't exist
        OSError: If deletion fails
    """
    course_dir = COURSES_DIR / course_name
    if not course_dir.exists():
        raise ValueError(f"Course '{course_name}' doesn't exist")

    shutil.rmtree(course_dir)


def rename_course(old_name: str, new_name: str) -> None:
    """
    Rename a course workspace.

    Args:
        old_name: Current course name
        new_name: New course name

    Raises:
        ValueError: If the old course doesn't exist or new name already exists
        OSError: If renaming fails
    """
    old_dir = COURSES_DIR / old_name
    new_dir = COURSES_DIR / new_name

    if not old_dir.exists():
        raise ValueError(f"Course '{old_name}' doesn't exist")
    if new_dir.exists():
        raise ValueError(f"Course '{new_name}' already exists")

    old_dir.rename(new_dir)