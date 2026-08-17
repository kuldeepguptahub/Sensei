"""
Artifact skills for Sensei.

These skills manage persistent knowledge in course workspaces.
"""

from typing import Dict, Any

from ..path_utils import safe_course_path, safe_artifact_path, safe_artifacts_dir


def read_artifact(course_name: str, artifact_name: str) -> str:
    """
    Read an artifact from a course workspace.

    Args:
        course_name: Name of the course
        artifact_name: Name of the artifact to read

    Returns:
        Content of the artifact

    Raises:
        ValueError: If the course or artifact doesn't exist, or names are invalid
        OSError: If reading fails
    """
    artifact_path = safe_artifact_path(course_name, artifact_name)
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
        ValueError: If the course doesn't exist or names are invalid
        OSError: If writing fails
    """
    artifact_path = safe_artifact_path(course_name, artifact_name)
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
        ValueError: If the course doesn't exist or name is invalid
    """
    artifacts_dir = safe_artifacts_dir(course_name)
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
