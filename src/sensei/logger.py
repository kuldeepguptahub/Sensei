"""
Logging module for Sensei.

Maintains a rolling buffer of the last 100 messages and writes
readable logs to log/sensei.log for debugging and issue tracing.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from collections import deque
from typing import Optional


# Log directory (project root / log/)
LOG_DIR = Path(__file__).parent.parent.parent / "log"
LOG_FILE = LOG_DIR / "sensei.log"
MAX_MESSAGES = 100


class SessionLogger:
    """
    Rolling logger that keeps the last 100 messages.

    Writes to log/sensei.log in a human-readable format.
    Thread-safe via deque with maxlen.
    """

    def __init__(self, course_name: Optional[str] = None):
        """
        Initialize the logger.

        Args:
            course_name: Optional course name to tag log entries
        """
        self.course_name = course_name
        self.messages: deque = deque(maxlen=MAX_MESSAGES)
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """Create log directory if it doesn't exist."""
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log_user(self, message: str):
        """
        Log a user message.

        Args:
            message: The user's message text
        """
        entry = {
            "time": self._timestamp(),
            "role": "USER",
            "course": self.course_name,
            "content": message,
        }
        self.messages.append(entry)
        self._write_entry(entry)

    def log_agent(self, message: str):
        """
        Log an agent response.

        Args:
            message: The agent's response text
        """
        entry = {
            "time": self._timestamp(),
            "role": "AGENT",
            "course": self.course_name,
            "content": message,
        }
        self.messages.append(entry)
        self._write_entry(entry)

    def log_tool(self, tool_name: str, args: dict, result: str):
        """
        Log a tool call and its result.

        Args:
            tool_name: Name of the tool called
            args: Arguments passed to the tool
            result: Tool execution result
        """
        entry = {
            "time": self._timestamp(),
            "role": "TOOL",
            "course": self.course_name,
            "tool": tool_name,
            "args": args,
            "result": result,
        }
        self.messages.append(entry)
        self._write_entry(entry)

    def log_error(self, error: str, context: Optional[str] = None):
        """
        Log an error with optional context.

        Args:
            error: Error message
            context: Optional context about what was happening
        """
        entry = {
            "time": self._timestamp(),
            "role": "ERROR",
            "course": self.course_name,
            "error": error,
            "context": context,
        }
        self.messages.append(entry)
        self._write_entry(entry)

    def log_event(self, event: str, details: Optional[str] = None):
        """
        Log a general event (session start, state change, etc.).

        Args:
            event: Event description
            details: Optional additional details
        """
        entry = {
            "time": self._timestamp(),
            "role": "EVENT",
            "course": self.course_name,
            "event": event,
            "details": details,
        }
        self.messages.append(entry)
        self._write_entry(entry)

    def _write_entry(self, entry: dict):
        """
        Append a formatted entry to the log file.

        Args:
            entry: Log entry dict
        """
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(self._format_entry(entry))
                f.write("\n")
        except OSError:
            pass  # Don't crash if logging fails

    def _format_entry(self, entry: dict) -> str:
        """
        Format a log entry for human readability.

        Args:
            entry: Log entry dict

        Returns:
            Formatted string
        """
        role = entry.get("role", "UNKNOWN")
        time_str = entry.get("time", "")
        course = entry.get("course", "")

        prefix = f"[{time_str}] [{role}]"
        if course:
            prefix += f" [{course}]"

        if role == "USER":
            return f"{prefix}\n  {entry['content']}\n"

        elif role == "AGENT":
            content = entry.get("content", "")
            # Truncate very long responses for readability
            if len(content) > 2000:
                content = content[:2000] + "\n  ... (truncated)"
            return f"{prefix}\n  {content}\n"

        elif role == "TOOL":
            tool = entry.get("tool", "")
            args = json.dumps(entry.get("args", {}), ensure_ascii=False)
            result = entry.get("result", "")
            return f"{prefix} tool={tool}\n  args: {args}\n  result: {result}\n"

        elif role == "ERROR":
            error = entry.get("error", "")
            context = entry.get("context", "")
            block = f"{prefix}\n  ERROR: {error}\n"
            if context:
                block += f"  CONTEXT: {context}\n"
            return block

        elif role == "EVENT":
            event = entry.get("event", "")
            details = entry.get("details", "")
            block = f"{prefix} {event}\n"
            if details:
                block += f"  {details}\n"
            return block

        return f"{prefix} {json.dumps(entry, ensure_ascii=False)}\n"

    def get_recent(self, n: int = 20) -> list:
        """
        Get the last n messages from the buffer.

        Args:
            n: Number of messages to retrieve

        Returns:
            List of log entry dicts
        """
        return list(self.messages)[-n:]

    def clear(self):
        """Clear the in-memory buffer and truncate the log file."""
        self.messages.clear()
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"=== Log cleared at {self._timestamp()} ===\n\n")
        except OSError:
            pass

    def get_session_summary(self) -> str:
        """
        Get a human-readable summary of the current session.

        Returns:
            Formatted summary string
        """
        if not self.messages:
            return "No messages logged yet."

        lines = [f"Session Log ({len(self.messages)} messages)\n"]
        lines.append("=" * 60 + "\n")

        for entry in self.messages:
            lines.append(self._format_entry(entry))

        return "".join(lines)


# Module-level singleton for simple usage
_default_logger: Optional[SessionLogger] = None


def get_logger(course_name: Optional[str] = None) -> SessionLogger:
    """
    Get or create the default logger.

    Args:
        course_name: Course name to tag entries (only set on first call)

    Returns:
        SessionLogger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = SessionLogger(course_name=course_name)
    return _default_logger


def log_user(message: str):
    """Log a user message using the default logger."""
    get_logger().log_user(message)


def log_agent(message: str):
    """Log an agent response using the default logger."""
    get_logger().log_agent(message)


def log_tool(tool_name: str, args: dict, result: str):
    """Log a tool call using the default logger."""
    get_logger().log_tool(tool_name, args, result)


def log_error(error: str, context: Optional[str] = None):
    """Log an error using the default logger."""
    get_logger().log_error(error, context)


def log_event(event: str, details: Optional[str] = None):
    """Log an event using the default logger."""
    get_logger().log_event(event, details)
