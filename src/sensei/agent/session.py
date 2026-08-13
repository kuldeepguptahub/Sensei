"""
Interactive session handler for Sensei.

Maintains conversation history and course state across turns.
Wraps the run() function to provide a stateful teaching experience.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .runner import run
from ..state.manager import load_course_state, save_course_state


class Session:
    """
    Manages an interactive teaching session for a course.

    Maintains conversation history and persists course state
    after each interaction.
    """

    def __init__(self, course_name: str, verbose: bool = False):
        """
        Initialize a session for a course.

        Args:
            course_name: Name of the course to session-ify
            verbose: If True, print tool call progress
        """
        self.course_name = course_name
        self.verbose = verbose
        self.history: List[Dict[str, str]] = []

        # Load course state
        self.course_state = load_course_state(course_name)
        self.state = self.course_state["state"]
        self.definition = self.course_state["definition"]
        self.planner = self.course_state["planner"]
        self.context = self.course_state["context"]

        # Update last_accessed
        self.state["last_accessed"] = datetime.now().isoformat()
        self._save_state()

    def send(self, user_message: str) -> str:
        """
        Send a user message and get the agent's response.

        Maintains conversation history and saves state after each turn.

        Args:
            user_message: The user's message

        Returns:
            The agent's response
        """
        # Build context for this turn
        context = {
            "course_name": self.course_name,
            "current_module": self.state.get("current_module", 0),
            "current_lesson": self.state.get("current_lesson", 0),
            "progress": self.state.get("progress", 0.0),
            "status": self.state.get("status", "active"),
            "competency": self.state.get("competency_index", {})
        }

        # Run the agent with history and context
        response = run(
            prompt=user_message,
            context=context,
            verbose=self.verbose,
            history=self.history
        )

        # Add to conversation history
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": response})

        # Update last timestamps
        now = datetime.now().isoformat()
        self.state["last_accessed"] = now
        self.state["last_updated"] = now
        self._save_state()

        return response

    def update_state(self, **kwargs) -> None:
        """
        Update state fields and persist.

        Args:
            **kwargs: Fields to update in state.json
        """
        self.state.update(kwargs)
        self._save_state()

    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state.

        Returns:
            Current state.json dict
        """
        return self.state.copy()

    def _save_state(self) -> None:
        """Persist state to disk."""
        save_course_state(self.course_name, self.state)
