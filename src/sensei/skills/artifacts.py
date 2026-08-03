"""
Artifact skills for Sensei.

These skills manage persistent knowledge in course workspaces.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

# Base directory for courses
COURSES_DIR = Path("courses")


def read_artifact(course_name: str, artifact_name: str) -> str:
    """
    Read an artifact from a course workspace.

    Args:
        course_name: Name of the course
        artifact_name: Name of the artifact to read

    Returns:
        Content of the artifact

    Raises:
        ValueError: If the course or artifact doesn't exist
        OSError: If reading fails
    """
    artifact_path = COURSES_DIR / course_name / "artifacts" / artifact_name
    if not artifact_path.exists():
        raise ValueError(f"Artifact '{artifact_name}' not found in course '{course_name}'")

    return artifact_path.read_text(encoding='utf-8')


def write_artifact(course_name: str, artifact_name: str, content: str) -> None:
    """
    Write an artifact to a course workspace.

    Args:
        course_name: Name of the course
        artifact_name: Name of the artifact to write
        content: Content to write to the artifact

    Raises:
        ValueError: If the course doesn't exist
        OSError: If writing fails
    """
    artifact_path = COURSES_DIR / course_name / "artifacts" / artifact_name
    if not artifact_path.parent.exists():
        raise ValueError(f"Course '{course_name}' doesn't exist")

    artifact_path.write_text(content, encoding='utf-8')


def list_artifacts(course_name: str) -> Dict[str, Dict[str, Any]]:
    """
    List all artifacts in a course workspace.

    Args:
        course_name: Name of the course

    Returns:
        Dictionary of artifact information

    Raises:
        ValueError: If the course doesn't exist
    """
    artifacts_dir = COURSES_DIR / course_name / "artifacts"
    if not artifacts_dir.exists():
        raise ValueError(f"Course '{course_name}' doesn't exist")

    artifacts = {}
    for artifact_path in artifacts_dir.iterdir():
        if artifact_path.is_file():
            artifacts[artifact_path.name] = {
                "path": str(artifact_path),
                "size": artifact_path.stat().st_size,
                "modified": artifact_path.stat().st_mtime
            }

    return artifacts