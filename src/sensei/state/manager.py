"""
State manager for Sensei courses.

This module handles the file-based state management for courses.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

# Base directory for course state
COURSES_DIR = Path("courses")


def create_course_state(course_name: str) -> None:
    """
    Create the directory structure and initial files for a new course.

    Args:
        course_name: The name of the course to create

    Raises:
        OSError: If the course directory cannot be created
    """
    # Create course directory
    course_dir = COURSES_DIR / course_name
    course_dir.mkdir(parents=True, exist_ok=False)

    # Create initial definition.json
    definition_path = course_dir / "definition.json"
    with open(definition_path, 'w') as f:
        json.dump({"course_name": "",
  "topic": "",
  "source_material": [],
  "portfolio_project": "",
  "roadmap": [],
  "objectives": [],
  "created_at": ""}, f)

    # Create initial state.json
    state_path = course_dir / "state.json"
    with open(state_path, 'w') as f:
        json.dump({"current_module": 0,
  "current_lesson": 0,
  "competency_index": {},
  "last_accessed": "",
  "last_updated": ""}, f)

    # Create initial context.md
    context_path = course_dir / "context.md"
    with open(context_path, 'w') as f:
        f.write("# Course Context\n")

    # Create initial notes.md
    notes_path = course_dir / "notes.md"
    with open(notes_path, 'w') as f:
        f.write("# Session Notes\n")


def load_course_state(course_name: str) -> Dict[str, Any]:
    """
    Load the state for a course.

    Args:
        course_name: The name of the course to load

    Returns:
        A dictionary containing the course state with keys:
        - definition: Contents of definition.json
        - state: Contents of state.json
        - context: Contents of context.md
        - notes: Contents of notes.md

    Raises:
        FileNotFoundError: If the course directory doesn't exist
    """
    course_dir = COURSES_DIR / course_name

    # Load definition.json
    definition_path = course_dir / "definition.json"
    with open(definition_path, 'r') as f:
        definition = json.load(f)

    # Load state.json
    state_path = course_dir / "state.json"
    with open(state_path, 'r') as f:
        state = json.load(f)

    # Load context.md
    context_path = course_dir / "context.md"
    with open(context_path, 'r') as f:
        context = f.read()

    # Load notes.md
    notes_path = course_dir / "notes.md"
    with open(notes_path, 'r') as f:
        notes = f.read()

    return {
        "definition": definition,
        "state": state,
        "context": context,
        "notes": notes
    }


def save_course_state(course_name: str, state: Dict[str, Any]) -> None:
    """
    Save the state for a course.

    Args:
        course_name: The name of the course to save
        state: The state data to save (only updates state.json)

    Raises:
        FileNotFoundError: If the course directory doesn't exist
    """
    course_dir = COURSES_DIR / course_name
    state_path = course_dir / "state.json"

    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)


def update_context(course_name: str, context: str) -> None:
    """
    Update the context for a course.

    Args:
        course_name: The name of the course to update
        context: The new context content

    Raises:
        FileNotFoundError: If the course directory doesn't exist
    """
    course_dir = COURSES_DIR / course_name
    context_path = course_dir / "context.md"

    with open(context_path, 'w') as f:
        f.write(context)