"""
Interactive session handler for Sensei.

Maintains conversation history and course state across turns.
Wraps the run() function to provide a stateful teaching experience.
"""

from typing import Dict, Any, Optional, List, Generator
from datetime import datetime

from .runner import run, run_stream
from .context import compress_history, build_resumption_context
from ..state.manager import load_course_state, save_course_state, update_context, COURSES_DIR
from ..logger import SessionLogger


# Placeholder text in context.md that indicates no real context yet
CONTEXT_PLACEHOLDER = "# Course Context\n"


class Session:
    """
    Manages an interactive teaching session for a course.

    Maintains conversation history and persists course state
    after each interaction. Compresses history at checkpoints.
    """

    def __init__(self, course_name: str, verbose: bool = False, max_history: int = 10,
                 mode: str = "new_course"):
        """
        Initialize a session for a course.

        Args:
            course_name: Name of the course
            verbose: If True, print tool call progress
            max_history: Max messages to keep before compression (default: 10)
            mode: Session mode — "new_course" or "resume_course"
        """
        self.course_name = course_name
        self.verbose = verbose
        self.max_history = max_history
        self.mode = mode
        self.history: List[Dict[str, str]] = []

        # Load course state
        self.course_state = load_course_state(course_name)
        self.state = self.course_state["state"]
        self.definition = self.course_state["definition"]
        self.planner = self.course_state["planner"]
        self.context = self.course_state["context"]

        # Check if we have real context for resumption
        self.has_context = (
            self.context
            and self.context.strip() != CONTEXT_PLACEHOLDER.strip()
            and len(self.context.strip()) > len(CONTEXT_PLACEHOLDER.strip())
        )

        # Initialize logger
        self.logger = SessionLogger(course_name=course_name)
        self.logger.log_event("session_start", f"Status: {self.state.get('status', 'unknown')}")

        # Update last_accessed
        self.state["last_accessed"] = datetime.now().isoformat()
        self._save_state()

    def send(self, user_message: str) -> str:
        """
        Send a user message and get the agent's response.

        Maintains conversation history and saves state after each turn.
        Compresses history if it exceeds max_history.

        Args:
            user_message: The user's message

        Returns:
            The agent's response
        """
        # Inject context on first message if resuming
        effective_prompt = user_message
        if self.has_context and not self.history:
            resumption_block = build_resumption_context(self.context, self.state)
            effective_prompt = f"{resumption_block}\n\nLearner says: {user_message}"
            self.has_context = False
            if self.verbose:
                print("  [Resuming with context from previous session]")

        # Build context for this turn
        context = {
            "course_name": self.course_name,
            "current_module": self.state.get("current_module", 0),
            "current_lesson": self.state.get("current_lesson", 0),
            "progress": self.state.get("progress", 0.0),
            "status": self.state.get("status", "active"),
            "competency": self.state.get("competency_index", {})
        }

        # Track if agent called update_state during this turn
        state_before = self.state.copy()

        # Run the agent with history and context
        self.logger.log_user(user_message)
        try:
            response = run(
                prompt=effective_prompt,
                context=context,
                verbose=self.verbose,
                history=self.history,
                mode=self.mode
            )
        except Exception as e:
            self.logger.log_error(str(e), f"During send for course '{self.course_name}'")
            raise

        # Reload state from disk — agent may have called update_state which writes directly to file
        self._reload_state()

        # Check if agent called update_state (state on disk changed)
        state_was_updated = (
            self.state.get("current_module", 0) != state_before.get("current_module", 0)
            or self.state.get("current_lesson", 0) != state_before.get("current_lesson", 0)
        )

        self.logger.log_agent(response)

        # Add to conversation history
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": response})

        # Auto-advance lesson if agent taught but didn't update state
        if not state_was_updated and self._looks_like_teaching(response):
            self._auto_advance_lesson()

        # Update last timestamps
        now = datetime.now().isoformat()
        self.state["last_accessed"] = now
        self.state["last_updated"] = now
        self._save_state()

        # Compress history if needed
        self._compress_if_needed()

        return response

    def send_stream(self, user_message: str) -> Generator[str, None, None]:
        """
        Send a user message and stream the agent's response.

        Same as send() but yields text chunks for streaming display.
        The full response is accumulated and saved to history after streaming completes.

        Args:
            user_message: The user's message

        Yields:
            Text chunks from the agent's response
        """
        effective_prompt = user_message
        if self.has_context and not self.history:
            resumption_block = build_resumption_context(self.context, self.state)
            effective_prompt = f"{resumption_block}\n\nLearner says: {user_message}"
            self.has_context = False
            if self.verbose:
                print("  [Resuming with context from previous session]")

        context = {
            "course_name": self.course_name,
            "current_module": self.state.get("current_module", 0),
            "current_lesson": self.state.get("current_lesson", 0),
            "progress": self.state.get("progress", 0.0),
            "status": self.state.get("status", "active"),
            "competency": self.state.get("competency_index", {})
        }

        self.logger.log_user(user_message)

        # Track if agent called update_state during this turn
        state_before = self.state.copy()

        # Accumulate the full response for history
        full_response = ""
        try:
            for chunk in run_stream(
                prompt=effective_prompt,
                context=context,
                verbose=self.verbose,
                history=self.history,
                mode=self.mode
            ):
                full_response += chunk
                yield chunk
        except Exception as e:
            self.logger.log_error(str(e), f"During send_stream for course '{self.course_name}'")
            raise

        # Reload state from disk — agent may have called update_state which writes directly to file
        self._reload_state()

        # Check if agent called update_state (state on disk changed)
        state_was_updated = (
            self.state.get("current_module", 0) != state_before.get("current_module", 0)
            or self.state.get("current_lesson", 0) != state_before.get("current_lesson", 0)
        )

        self.logger.log_agent(full_response)

        # Add to conversation history
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": full_response})

        # Auto-advance lesson if agent taught but didn't update state
        if not state_was_updated and self._looks_like_teaching(full_response):
            self._auto_advance_lesson()

        # Update last timestamps
        now = datetime.now().isoformat()
        self.state["last_accessed"] = now
        self.state["last_updated"] = now
        self._save_state()

        self._compress_if_needed()

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

    def _reload_state(self) -> None:
        """Reload state from disk. Used after agent runs to pick up updates from update_state tool."""
        state_path = COURSES_DIR / self.course_name / "artifacts" / "state.json"
        if state_path.exists():
            import json
            with open(state_path, 'r', encoding='utf-8') as f:
                self.state = json.load(f)

    def _looks_like_teaching(self, text: str) -> bool:
        """
        Check if response text looks like teaching content.

        Args:
            text: The agent's response text

        Returns:
            True if it looks like a lesson was taught
        """
        if not text or len(text) < 100:
            return False
        indicators = ["##", "```", "lesson", "module", "concept", "example", "key take"]
        text_lower = text.lower()
        return any(ind in text_lower for ind in indicators)

    def _auto_advance_lesson(self) -> None:
        """
        Auto-advance the lesson counter when teaching content was delivered
        but the agent forgot to call update_state.

        This is a safety net to ensure progress tracking works even when
        the agent doesn't follow instructions to call update_state.
        """
        current_module = self.state.get("current_module", 0)
        current_lesson = self.state.get("current_lesson", 0)

        # Simple heuristic: increment lesson by 1
        # The agent should be calling update_state for proper tracking,
        # but this ensures progress doesn't get stuck.
        self.state["current_lesson"] = current_lesson + 1
        self.state["progress"] = min(1.0, self.state.get("progress", 0.0) + 0.1)

        if self.verbose:
            print(f"  [Auto-advanced: module {current_module}, lesson {current_lesson} -> {current_lesson + 1}]")

    def clear_history(self) -> None:
        """Clear conversation history for state transitions (e.g., planning → active)."""
        self.history = []
        self.has_context = False

    def _compress_if_needed(self) -> None:
        """
        Compress conversation history if it exceeds max_history.

        Takes the oldest messages beyond the window, summarizes them
        via LLM, writes the summary to context.md, and trims history.
        """
        if len(self.history) <= self.max_history:
            return

        if self.verbose:
            print(f"  [Compressing history: {len(self.history)} messages > {self.max_history} limit]")

        # Split history: old messages to compress, recent to keep
        old_messages = self.history[:-self.max_history]
        recent_messages = self.history[-self.max_history:]

        # Compress old messages into a summary
        try:
            summary = compress_history(old_messages, self.course_name)

            # Write summary to context.md
            update_context(self.course_name, summary)
            self.context = summary

            # Trim history
            self.history = recent_messages

            if self.verbose:
                print(f"  [Context compressed and saved to context.md]")
        except Exception as e:
            # If compression fails, keep history as-is
            if self.verbose:
                print(f"  [Compression failed: {e}. History kept as-is.]")
