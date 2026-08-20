"""
State manager for Sensei courses.

This module handles the file-based state management for courses.
Note: This is a legacy module that will be replaced by skills.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any

# Use the resolved COURSES_DIR from path_utils to avoid path inconsistencies
from ..path_utils import COURSES_DIR


def create_course_state(course_name: str) -> None:
    """
    Create the directory structure and initial files for a new course.
    This is a legacy function that will be replaced by create_workspace skill.

    Args:
        course_name: The name of the course to create

    Raises:
        OSError: If the course directory cannot be created
    """
    # Create course directory
    course_dir = COURSES_DIR / course_name
    course_dir.mkdir(parents=True, exist_ok=False)

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
            "source_material": [],
            "portfolio_project": "",
            "roadmap": [],
            "objectives": [],
            "created_at": ""
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


def load_course_state(course_name: str) -> Dict[str, Any]:
    """
    Load the state for a course.
    This is a legacy function that will be replaced by artifact skills.

    Args:
        course_name: The name of the course to load

    Returns:
        A dictionary containing the course state with keys:
        - definition: Contents of definition.json
        - state: Contents of state.json
        - context: Contents of context.md
        - notes: Contents of notes.md
        - planner: Contents of planner.md

    Raises:
        FileNotFoundError: If the course directory doesn't exist
    """
    artifacts_dir = COURSES_DIR / course_name / "artifacts"

    # Load definition.json
    definition_path = artifacts_dir / "definition.json"
    with open(definition_path, 'r', encoding='utf-8') as f:
        definition = json.load(f)

    # Load state.json
    state_path = artifacts_dir / "state.json"
    with open(state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)

    # Load context.md
    context_path = artifacts_dir / "context.md"
    with open(context_path, 'r', encoding='utf-8') as f:
        context = f.read()

    # Load notes.md
    notes_path = artifacts_dir / "notes.md"
    with open(notes_path, 'r', encoding='utf-8') as f:
        notes = f.read()

    # Load planner.md
    planner_path = artifacts_dir / "planner.md"
    with open(planner_path, 'r', encoding='utf-8') as f:
        planner = f.read()

    return {
        "definition": definition,
        "state": state,
        "context": context,
        "notes": notes,
        "planner": planner
    }


def save_course_state(course_name: str, state: Dict[str, Any]) -> None:
    """
    Save the state for a course.

    Args:
        course_name: The name of the course
        state: The state dictionary to save

    Raises:
        FileNotFoundError: If the course directory doesn't exist
    """
    artifacts_dir = COURSES_DIR / course_name / "artifacts"
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Course '{course_name}' does not exist")

    state_path = artifacts_dir / "state.json"
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
        f.flush()
        os.fsync(f.fileno())


def update_context(course_name: str, content: str) -> None:
    """
    Update the context.md file for a course.

    Args:
        course_name: The name of the course
        content: The new context content

    Raises:
        FileNotFoundError: If the course directory doesn't exist
    """
    artifacts_dir = COURSES_DIR / course_name / "artifacts"
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Course '{course_name}' does not exist")

    context_path = artifacts_dir / "context.md"
    with open(context_path, 'w') as f:
        f.write(content)
