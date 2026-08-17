"""
Path safety utilities for Sensei.

Constructs safe filesystem paths for course workspaces,
preventing path traversal attacks.
"""

from pathlib import Path
from typing import Optional

from .validation import validate_course_name, validate_artifact_name, validate_file_name


# Base directory for all courses
COURSES_DIR = Path("courses").resolve()


def safe_course_path(course_name: str) -> Path:
    """
    Construct a safe, validated path for a course directory.

    Validates the course name and ensures the resulting path
    is within COURSES_DIR (prevents path traversal).

    Args:
        course_name: Name of the course

    Returns:
        Resolved Path within COURSES_DIR

    Raises:
        ValueError: If the course name is invalid or path is unsafe
    """
    validate_course_name(course_name)

    course_path = (COURSES_DIR / course_name).resolve()

    # Ensure the path is within COURSES_DIR
    if not str(course_path).startswith(str(COURSES_DIR)):
        raise ValueError(f"Invalid course name: path traversal detected")

    return course_path


def safe_artifact_path(course_name: str, artifact_name: str) -> Path:
    """
    Construct a safe, validated path for an artifact file.

    Args:
        course_name: Name of the course
        artifact_name: Name of the artifact

    Returns:
        Resolved Path to the artifact file

    Raises:
        ValueError: If names are invalid or path is unsafe
    """
    validate_course_name(course_name)
    validate_artifact_name(artifact_name)

    artifact_path = (COURSES_DIR / course_name / "artifacts" / artifact_name).resolve()

    # Ensure the path is within COURSES_DIR
    if not str(artifact_path).startswith(str(COURSES_DIR)):
        raise ValueError(f"Invalid path: traversal detected")

    return artifact_path


def safe_upload_path(course_name: str, file_name: str) -> Path:
    """
    Construct a safe, validated path for an upload file.

    Args:
        course_name: Name of the course
        file_name: Name of the file

    Returns:
        Resolved Path to the upload file

    Raises:
        ValueError: If names are invalid or path is unsafe
    """
    validate_course_name(course_name)
    validate_file_name(file_name)

    upload_path = (COURSES_DIR / course_name / "uploads" / file_name).resolve()

    # Ensure the path is within COURSES_DIR
    if not str(upload_path).startswith(str(COURSES_DIR)):
        raise ValueError(f"Invalid path: traversal detected")

    return upload_path


def safe_uploads_dir(course_name: str) -> Path:
    """
    Construct a safe, validated path for the uploads directory.

    Args:
        course_name: Name of the course

    Returns:
        Resolved Path to the uploads directory

    Raises:
        ValueError: If the course name is invalid or path is unsafe
    """
    validate_course_name(course_name)

    uploads_dir = (COURSES_DIR / course_name / "uploads").resolve()

    if not str(uploads_dir).startswith(str(COURSES_DIR)):
        raise ValueError(f"Invalid path: traversal detected")

    return uploads_dir


def safe_artifacts_dir(course_name: str) -> Path:
    """
    Construct a safe, validated path for the artifacts directory.

    Args:
        course_name: Name of the course

    Returns:
        Resolved Path to the artifacts directory

    Raises:
        ValueError: If the course name is invalid or path is unsafe
    """
    validate_course_name(course_name)

    artifacts_dir = (COURSES_DIR / course_name / "artifacts").resolve()

    if not str(artifacts_dir).startswith(str(COURSES_DIR)):
        raise ValueError(f"Invalid path: traversal detected")

    return artifacts_dir
