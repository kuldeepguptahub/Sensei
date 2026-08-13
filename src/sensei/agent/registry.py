"""
Skill registry for Sensei.

This module maintains a registry of available skills.
"""

from typing import Dict, Callable, Any
from ..skills.courses import (
    create_workspace,
    list_courses,
    delete_course,
    rename_course,
    update_state
)
from ..skills.artifacts import (
    read_artifact,
    write_artifact,
    list_artifacts
)
from ..skills.uploads import (
    save_upload,
    read_upload,
    list_uploads
)
from ..skills.workspace import workspace_exists

# Global skill registry
_skill_registry: Dict[str, Callable] = {
    # Courses skills
    'create_workspace': create_workspace,
    'list_courses': list_courses,
    'delete_course': delete_course,
    'rename_course': rename_course,
    'update_state': update_state,

    # Artifacts skills
    'read_artifact': read_artifact,
    'write_artifact': write_artifact,
    'list_artifacts': list_artifacts,

    # Uploads skills
    'save_upload': save_upload,
    'read_upload': read_upload,
    'list_uploads': list_uploads,

    # Workspace skills
    'workspace_exists': workspace_exists
}


def register(skill_name: str) -> Callable:
    """
    Decorator to register a skill function.

    Args:
        skill_name: The name to register the skill under

    Returns:
        The decorator function
    """
    def decorator(func: Callable) -> Callable:
        _skill_registry[skill_name] = func
        return func
    return decorator


def get_skill(skill_name: str) -> Callable:
    """
    Get a registered skill by name.

    Args:
        skill_name: The name of the skill to retrieve

    Returns:
        The skill function

    Raises:
        KeyError: If the skill is not registered
    """
    return _skill_registry[skill_name]


def list_skills() -> Dict[str, Callable]:
    """
    List all registered skills.

    Returns:
        A dictionary of skill names to skill functions
    """
    return _skill_registry.copy()