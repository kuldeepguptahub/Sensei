"""
Chat page for Sensei Streamlit dashboard.
Phase 4 will implement the full chat interface.
"""

import streamlit as st
from typing import Optional


def render(course_name: str, mode: Optional[str] = None):
    """
    Render the chat page for a course.

    Args:
        course_name: Name of the course
        mode: Session mode — "new_course" or "resume_course"
    """
    st.header(f"🎓 {course_name}")
    st.caption(f"Mode: {mode or 'resume_course'}")

    # Placeholder for Phase 4
    st.info("Chat interface coming soon. This is a Phase 4 deliverable.")
