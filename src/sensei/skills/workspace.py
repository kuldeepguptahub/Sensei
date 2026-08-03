"""
Workspace skills for Sensei.

These skills provide utility functions for workspace management.
"""

from pathlib import Path

# Base directory for courses
COURSES_DIR = Path("courses")


def workspace_exists(course_name: str) -> bool:
    """
    Check if a course workspace exists.

    Args:
        course_name: Name of the course to check

    Returns:
        True if the workspace exists, False otherwise
    """
    return (COURSES_DIR / course_name).exists()