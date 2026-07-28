"""
Course workflows module for Sensei.

This module contains workflow functions for course operations including:
- Creating new courses
- Resuming existing courses
- Completing courses

Workflows coordinate database operations and validate inputs.
"""

from typing import Optional
from sensei.persistence.database import insert_course, get_course, update_course, delete_course
from datetime import datetime


def create_new_course(name: str) -> int:
    """
    Create a new course with the given name.

    Args:
        name: The name of the course to create

    Returns:
        The ID of the newly created course

    Raises:
        ValueError: If the course name is empty or already exists
    """
    # Validate input
    if not name or not name.strip():
        raise ValueError("Course name cannot be empty")

    name = name.strip()

    # Check if course already exists
    existing_course = get_course(name=name)

    if existing_course:
        raise ValueError(f"Course '{name}' already exists")

    # Create new course
    course_id = insert_course(name)

    return course_id


def resume_course(course_id: Optional[int] = None, course_name: Optional[str] = None) -> dict:
    """
    Resume an existing course by ID or name.

    Args:
        course_id: The ID of the course to resume
        course_name: The name of the course to resume

    Returns:
        A dictionary containing course information

    Raises:
        ValueError: If neither course_id nor course_name is provided,
                   or if the specified course doesn't exist
    """
    if not course_id and not course_name:
        raise ValueError("Either course_id or course_name must be provided")

    # Find course by ID or name
    course = get_course(course_id=course_id, name=course_name)

    if not course:
        if course_id:
            raise ValueError(f"Course with ID {course_id} not found")
        else:
            raise ValueError(f"Course '{course_name}' not found")

    # Update last accessed time
    update_course(course['id'], status='in_progress', last_accessed=datetime.now())

    # Return updated course information
    return {
        'id': course['id'],
        'name': course['name'],
        'status': 'in_progress',
        'created_at': course['created_at'],
        'last_accessed': datetime.now().isoformat()
    }


def complete_course(course_id: int) -> dict:
    """
    Mark a course as completed.

    Args:
        course_id: The ID of the course to complete

    Returns:
        A dictionary containing the updated course information

    Raises:
        ValueError: If the course doesn't exist

    Note:
        This is currently a stub implementation.
    """
    # Check if course exists
    course = get_course(course_id=course_id)

    if not course:
        raise ValueError(f"Course with ID {course_id} not found")

    # Update course status
    update_course(course_id, status='completed', last_accessed=datetime.now())

    # Return updated course information
    return {
        'id': course_id,
        'name': course['name'],
        'status': 'completed',
        'created_at': course['created_at'],
        'last_accessed': datetime.now().isoformat()
    }