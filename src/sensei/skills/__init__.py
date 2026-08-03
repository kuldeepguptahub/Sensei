"""
Skills package for Sensei.

This package provides deterministic capabilities for the agent.
"""

from .courses import (
    create_workspace,
    list_courses,
    delete_course,
    rename_course
)
from .artifacts import (
    read_artifact,
    write_artifact,
    list_artifacts
)
from .uploads import (
    save_upload,
    read_upload,
    list_uploads
)
from .workspace import workspace_exists

__all__ = [
    # Courses skills
    'create_workspace',
    'list_courses',
    'delete_course',
    'rename_course',

    # Artifacts skills
    'read_artifact',
    'write_artifact',
    'list_artifacts',

    # Uploads skills
    'save_upload',
    'read_upload',
    'list_uploads',

    # Workspace skills
    'workspace_exists'
]