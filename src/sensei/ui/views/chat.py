"""
Chat page for Sensei Streamlit dashboard.

Full chat interface with streaming, tool call indicators, progress display,
and approval flow for the course creation workflow.
"""

import sys
import streamlit as st
from pathlib import Path
from typing import Optional

# Ensure src is on path
_src = str(Path(__file__).resolve().parent.parent.parent.parent)
if _src not in sys.path:
    sys.path.insert(0, _src)

from sensei.agent.session import Session
from sensei.ui.components import progress_display


def _get_session(course_name: str, mode: str) -> Session:
    """Get or create a Session in st.session_state for the given course."""
    key = f"session_{course_name}"
    if key not in st.session_state or st.session_state[key] is None:
        st.session_state[key] = Session(course_name, mode=mode)
    return st.session_state[key]


def _init_messages(session: Session, mode: str):
    """Pre-populate chat messages from session history if empty."""
    if st.session_state.messages:
        return

    if mode == "resume_course" and session.history:
        for msg in session.history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                st.session_state.messages.append({"role": "user", "content": content})
            elif role == "assistant":
                st.session_state.messages.append({"role": "assistant", "content": content})


def _render_sidebar(session: Session):
    """Render the progress sidebar with current state."""
    with st.sidebar:
        st.subheader("Progress")
        state = session.get_state()
        progress_display(state)

        with st.expander("Course State"):
            st.json(state)


def render(course_name: str, mode: Optional[str] = None):
    """
    Render the chat page for a course.

    Args:
        course_name: Name of the course
        mode: Session mode — "new_course" or "resume_course"
    """
    mode = mode or "resume_course"
    session = _get_session(course_name, mode)
    _init_messages(session, mode)

    # --- Header ---
    col1, col2 = st.columns([4, 1])
    with col1:
        mode_label = "Planning" if mode == "new_course" else "Resuming"
        st.header(f"🎓 {course_name}")
        st.caption(f"{mode_label} — Ask questions, learn, and grow.")
    with col2:
        if st.button("← Back", key="back_btn"):
            st.session_state.selected_course = None
            st.session_state.mode = None
            st.session_state.messages = []
            key = f"session_{course_name}"
            if key in st.session_state:
                del st.session_state[key]
            st.rerun()

    # --- Progress in sidebar ---
    _render_sidebar(session)

    # --- Display chat history ---
    for msg in st.session_state.messages:
        role = msg["role"]
        icon = "🎓" if role == "assistant" else "👤"
        with st.chat_message(role, avatar=icon):
            st.markdown(msg["content"])

    # --- Auto-start for new sessions ---
    if not st.session_state.messages:
        _auto_start(session, mode)

    # --- User input ---
    if prompt := st.chat_input("Type your message..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Get agent response with streaming
        with st.chat_message("assistant", avatar="🎓"):
            response = _stream_response(session, prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})

        # Reload sidebar with updated state
        st.rerun()


def _auto_start(session: Session, mode: str):
    """
    Send the initial empty message to kick off the conversation.
    Only runs once per session.
    """
    if st.session_state.get("_auto_started"):
        return
    st.session_state["_auto_started"] = True

    initial_msg = ""

    with st.chat_message("assistant", avatar="🎓"):
        response = _stream_response(session, initial_msg)
        st.session_state.messages.append({"role": "assistant", "content": response})

    st.rerun()


def _stream_response(session: Session, user_message: str) -> str:
    """
    Stream the agent's response with real-time token-by-token display.

    Uses st.empty() to create a placeholder that gets updated incrementally,
    providing true streaming feel to the user.

    Args:
        session: The Session object
        user_message: The user's message

    Returns:
        The complete response text
    """
    # Create a placeholder for the streaming text
    placeholder = st.empty()
    status = st.status("Thinking...", expanded=False)

    full_response = ""

    try:
        # Stream via Session.send_stream
        for chunk in session.send_stream(user_message):
            full_response += chunk
            # Update the placeholder with accumulated text
            placeholder.markdown(full_response + "▌")
            status.update(label=f"Streaming... ({len(full_response)} chars)")

        # Final update without cursor
        placeholder.markdown(full_response)
        status.update(label="Response complete", expanded=False)

    except Exception as e:
        status.update(label="Error occurred", expanded=False)
        full_response = f"Error: {str(e)}"
        placeholder.error(full_response)

    return full_response
