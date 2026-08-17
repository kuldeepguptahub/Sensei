"""
Workspace skills for Sensei.

These skills provide utility functions for workspace management.
"""

from ..path_utils import safe_course_path


def workspace_exists(course_name: str) -> bool:
    """
    Check if a course workspace exists.

    Args:
        course_name: Name of the course to check

    Returns:
        True if the workspace exists, False otherwise

    Raises:
        ValueError: If the course name is invalid
    """
    course_path = safe_course_path(course_name)
    return course_path.exists()
