"""
Input validation for Sensei.

Centralized validation functions for user-provided names and data.
Enforces strict naming rules to prevent path traversal and injection.
"""

import re
import json
from typing import Dict, Any


# Pattern: alphanumeric, hyphens, underscores, spaces (spaces converted to hyphens)
_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\- ]+$")
_MAX_NAME_LENGTH = 100
_MAX_FILE_NAME_LENGTH = 255


def validate_course_name(name: str) -> str:
    """
    Validate and sanitize a course name.

    Rules:
    - Cannot be empty or whitespace only
    - Max 100 characters
    - Only alphanumeric, hyphens, underscores, and spaces
    - Spaces are converted to hyphens
    - No path separators or traversal

    Args:
        name: Raw course name input

    Returns:
        Stripped, validated course name (spaces converted to hyphens)

    Raises:
        ValueError: If the name is invalid
    """
    if not name or not name.strip():
        raise ValueError("Course name cannot be empty")

    name = name.strip()

    if len(name) > _MAX_NAME_LENGTH:
        raise ValueError(
            f"Course name too long ({len(name)} chars). "
            f"Maximum is {_MAX_NAME_LENGTH} characters."
        )

    if not _NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid course name '{name}'. "
            f"Only letters, numbers, hyphens, underscores, and spaces are allowed."
        )

    # Convert spaces to hyphens for directory name
    name = name.replace(" ", "-")

    return name


def validate_artifact_name(name: str) -> str:
    """
    Validate an artifact name.

    Rules:
    - Cannot be empty
    - Max 255 characters
    - Only alphanumeric, hyphens, underscores, and dots
    - No path separators or traversal

    Args:
        name: Raw artifact name input

    Returns:
        Stripped, validated artifact name

    Raises:
        ValueError: If the name is invalid
    """
    if not name or not name.strip():
        raise ValueError("Artifact name cannot be empty")

    name = name.strip()

    if len(name) > _MAX_FILE_NAME_LENGTH:
        raise ValueError(
            f"Artifact name too long ({len(name)} chars). "
            f"Maximum is {_MAX_FILE_NAME_LENGTH} characters."
        )

    # Allow dots for file extensions (e.g., definition.json)
    artifact_pattern = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
    if not artifact_pattern.match(name):
        raise ValueError(
            f"Invalid artifact name '{name}'. "
            f"Only letters, numbers, hyphens, underscores, and dots are allowed."
        )

    # Specifically reject path traversal
    if ".." in name or "/" in name or "\\" in name:
        raise ValueError(f"Invalid artifact name '{name}'. Path separators are not allowed.")

    return name


def validate_file_name(name: str) -> str:
    """
    Validate a file name (for uploads).

    Rules:
    - Cannot be empty
    - Max 255 characters
    - Only alphanumeric, hyphens, underscores, and dots
    - No path separators or traversal

    Args:
        name: Raw file name input

    Returns:
        Stripped, validated file name

    Raises:
        ValueError: If the name is invalid
    """
    if not name or not name.strip():
        raise ValueError("File name cannot be empty")

    name = name.strip()

    if len(name) > _MAX_FILE_NAME_LENGTH:
        raise ValueError(
            f"File name too long ({len(name)} chars). "
            f"Maximum is {_MAX_FILE_NAME_LENGTH} characters."
        )

    # Allow dots for file extensions
    file_pattern = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
    if not file_pattern.match(name):
        raise ValueError(
            f"Invalid file name '{name}'. "
            f"Only letters, numbers, hyphens, underscores, and dots are allowed."
        )

    if ".." in name or "/" in name or "\\" in name:
        raise ValueError(f"Invalid file name '{name}'. Path separators are not allowed.")

    return name


def validate_state_json(json_str: str) -> Dict[str, Any]:
    """
    Validate and parse a state JSON string.

    Checks:
    - Valid JSON
    - Required fields exist
    - Field types are correct

    Args:
        json_str: JSON string to validate

    Returns:
        Parsed state dictionary

    Raises:
        ValueError: If JSON is invalid or missing required fields
    """
    try:
        state = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    if not isinstance(state, dict):
        raise ValueError("State must be a JSON object")

    # Required fields and their expected types
    required_fields = {
        "current_module": int,
        "current_lesson": int,
        "progress": (int, float),
        "status": str,
    }

    for field, expected_type in required_fields.items():
        if field not in state:
            raise ValueError(f"State missing required field: '{field}'")
        if not isinstance(state[field], expected_type):
            raise ValueError(
                f"Field '{field}' must be {expected_type}, "
                f"got {type(state[field]).__name__}"
            )

    # Validate status value
    valid_statuses = {"planning", "active", "paused", "completed"}
    if state["status"] not in valid_statuses:
        raise ValueError(
            f"Invalid status '{state['status']}'. "
            f"Must be one of: {', '.join(sorted(valid_statuses))}"
        )

    # Validate progress range
    if not (0.0 <= state["progress"] <= 1.0):
        raise ValueError(
            f"Progress must be between 0.0 and 1.0, got {state['progress']}"
        )

    return state
