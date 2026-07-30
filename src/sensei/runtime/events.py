"""
Runtime events for Sensei.

This module defines the events emitted by the runtime during course execution.
"""

from enum import Enum, auto


class RuntimeEvent(Enum):
    """Events emitted by the Sensei runtime."""

    # Course lifecycle events
    COURSE_LOADING = auto()
    COURSE_LOADED = auto()
    COURSE_CREATING = auto()
    COURSE_CREATED = auto()
    COURSE_RESUMING = auto()

    # Processing events
    THINKING = auto()

    # Retry events
    RETRYING = auto()

    # Completion events
    SESSION_COMPLETE = auto()

    # Error events
    ERROR = auto()