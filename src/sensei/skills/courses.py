"""
Course skills for Sensei.

These skills manage workspace lifecycle.
"""

import json
import os
import shutil
from typing import Dict, Any, List

from ..path_utils import safe_course_path, safe_artifact_path, safe_artifacts_dir, COURSES_DIR
from ..validation import validate_state_json


def create_workspace(course_name: str) -> None:
    """
    Create a new course workspace with the required structure.

    Args:
        course_name: Name of the course to create

    Raises:
        ValueError: If the course already exists or name is invalid
        OSError: If workspace creation fails
    """
    course_dir = safe_course_path(course_name)
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

    # Create initial definition.json
    definition_path = artifacts_dir / "definition.json"
    with open(definition_path, 'w') as f:
        json.dump({
            "course_name": "",
            "topic": "",
            "goals": [],
            "desired_outcome": "",
            "portfolio_project": "",
            "current_knowledge": "",
            "learning_style": "",
            "constraints": [],
            "completion_criteria": ""
        }, f)

    # Create initial state.json
    state_path = artifacts_dir / "state.json"
    with open(state_path, 'w') as f:
        json.dump({
            "current_module": 0,
            "current_lesson": 0,
            "competency_index": {},
            "last_accessed": "",
            "last_updated": "",
            "progress": 0.0,
            "status": "planning",
            "last_checkpoint": ""
        }, f)

    # Create initial context.md
    context_path = artifacts_dir / "context.md"
    with open(context_path, 'w') as f:
        f.write("# Course Context\n")

    # Create initial notes.md
    notes_path = artifacts_dir / "notes.md"
    with open(notes_path, 'w') as f:
        f.write("# Session Notes\n")

    # Create initial planner.md
    planner_path = artifacts_dir / "planner.md"
    with open(planner_path, 'w') as f:
        f.write("# Learning Roadmap\n\n")


def list_courses() -> List[Dict[str, Any]]:
    """
    List all available courses.

    Returns:
        List of course information dictionaries with name, status, progress
    """
    import json
    courses = []
    if COURSES_DIR.exists():
        for course_dir in COURSES_DIR.iterdir():
            if course_dir.is_dir():
                info = {
                    "name": course_dir.name,
                    "path": str(course_dir),
                    "created": course_dir.stat().st_ctime,
                    "status": "unknown",
                    "progress": 0.0,
                }
                state_path = course_dir / "artifacts" / "state.json"
                if state_path.exists():
                    try:
                        with open(state_path, 'r', encoding='utf-8') as f:
                            state = json.load(f)
                        info["status"] = state.get("status", "unknown")
                        info["progress"] = state.get("progress", 0.0)
                    except Exception:
                        pass
                courses.append(info)
    return courses


def delete_course(course_name: str) -> None:
    """
    Delete a course workspace.

    Args:
        course_name: Name of the course to delete

    Raises:
        ValueError: If the course doesn't exist or name is invalid
        OSError: If deletion fails
    """
    course_dir = safe_course_path(course_name)
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
        ValueError: If names are invalid, old course doesn't exist,
                   or new name already exists
        OSError: If renaming fails
    """
    old_dir = safe_course_path(old_name)
    new_dir = safe_course_path(new_name)

    if not old_dir.exists():
        raise ValueError(f"Course '{old_name}' doesn't exist")
    if new_dir.exists():
        raise ValueError(f"Course '{new_name}' already exists")

    old_dir.rename(new_dir)


def update_state(course_name: str, state_json: str) -> None:
    """
    Update the state.json file for a course.

    Args:
        course_name: Name of the course
        state_json: JSON string of the state to save

    Raises:
        ValueError: If the course doesn't exist, name is invalid, or JSON is invalid
    """
    course_dir = safe_course_path(course_name)
    if not course_dir.exists():
        raise ValueError(f"Course '{course_name}' doesn't exist")

    # Validate the JSON structure
    state = validate_state_json(state_json)

    state_path = course_dir / "artifacts" / "state.json"
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
