"""
Runtime orchestrator for Sensei.

This module coordinates the entire learning session from course loading
to response generation.
"""

import json

from ..courses import resume_course, create_new_course
from ..state import load_course_state
from ..prompt_assembler import build_start_prompt, build_resume_prompt
from ..gateway import generate, GatewayError
from .events import RuntimeEvent


def _emit_event(callback: Optional[Callable[[RuntimeEvent], None]], event: RuntimeEvent, data: Optional[str] = None) -> None:
    """
    Emit an event to the callback if provided.

    Args:
        callback: Optional callback function
        event: The event to emit
        data: Optional additional data for the event
    """
    if callback:
        callback(event, data)


def _run_course_flow(
    course_name: str,
    is_new_course: bool,
    callback: Optional[Callable[[RuntimeEvent, Optional[str]], None]] = None
) -> str:
    """
    Internal function to run the course flow.

    Args:
        course_name: Name of the course to run
        is_new_course: Whether this is a new course
        callback: Optional event callback

    Returns:
        The generated response from the gateway

    Raises:
        RuntimeError: If the course flow fails after retries
    """
    try:
        # Load course data
        _emit_event(callback, RuntimeEvent.COURSE_LOADING)

        if is_new_course:
            _emit_event(callback, RuntimeEvent.COURSE_CREATING)
            try:
                create_new_course(course_name)
                _emit_event(callback, RuntimeEvent.COURSE_CREATED)
            except ValueError as e:
                if "already exists" in str(e):
                    # Course already exists, ensure state directory exists
                    _emit_event(callback, RuntimeEvent.COURSE_RESUMING)
                    from sensei.state import create_course_state
                    try:
                        create_course_state(course_name)
                    except OSError:
                        # Directory already exists, continue
                        pass
                    resume_course(course_name=course_name)
                else:
                    raise
        else:
            _emit_event(callback, RuntimeEvent.COURSE_RESUMING)
            resume_course(course_name=course_name)

        # Load course state
        course_state = load_course_state(course_name)
        definition = json.dumps(course_state["definition"], indent=2)
        state = json.dumps(course_state["state"], indent=2)
        context = course_state["context"]

        _emit_event(callback, RuntimeEvent.COURSE_LOADED)

        # Assemble prompt
        if is_new_course:
            prompt = build_start_prompt(definition, state, context)
        else:
            prompt = build_resume_prompt(definition, state, context)

        # Generate response with retry
        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                _emit_event(callback, RuntimeEvent.THINKING)
                response = generate(prompt)
                _emit_event(callback, RuntimeEvent.SESSION_COMPLETE)
                return response
            except GatewayError as e:
                last_error = e
                if attempt < max_retries:
                    retry_message = f"Retrying ({attempt}/{max_retries})..."
                    _emit_event(callback, RuntimeEvent.RETRYING, retry_message)
                    time.sleep(1 * attempt)  # Exponential backoff
                continue

        # If we get here, all retries failed
        _emit_event(callback, RuntimeEvent.ERROR, str(last_error))
        raise RuntimeError(f"Failed to generate response after {max_retries} attempts: {last_error}")

    except Exception as e:
        _emit_event(callback, RuntimeEvent.ERROR, str(e))
        raise RuntimeError(f"Course flow failed: {e}")


def run_new_course(
    course_name: str,
    callback: Optional[Callable[[RuntimeEvent, Optional[str]], None]] = None
) -> str:
    """
    Run a new course session.

    Args:
        course_name: Name of the new course to create and run
        callback: Optional callback for runtime events

    Returns:
        The generated response from the gateway
    """
    return _run_course_flow(course_name, is_new_course=True, callback=callback)


def run_resume_course(
    course_name: str,
    callback: Optional[Callable[[RuntimeEvent, Optional[str]], None]] = None
) -> str:
    """
    Run a resume course session.

    Args:
        course_name: Name of the existing course to resume
        callback: Optional callback for runtime events

    Returns:
        The generated response from the gateway
    """
    return _run_course_flow(course_name, is_new_course=False, callback=callback)