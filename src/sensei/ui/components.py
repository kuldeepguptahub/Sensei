"""
Reusable UI components for Sensei Streamlit dashboard.
"""

import streamlit as st
from typing import Dict, Any


def status_badge(status: str) -> str:
    """
    Return colored HTML badge for course status.

    Args:
        status: Course status string (planning, active, completed)

    Returns:
        HTML string for the badge
    """
    colors = {
        "planning": ("#f0ad4e", "#000"),
        "active": ("#5cb85c", "#fff"),
        "completed": ("#5bc0de", "#000"),
        "in_progress": ("#5cb85c", "#fff"),
    }
    bg, fg = colors.get(status, ("#777", "#fff"))
    return (
        f'<span style="background-color:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:12px;font-size:0.75em;font-weight:600;">{status}</span>'
    )


def progress_display(state: Dict[str, Any]):
    """
    Display course progress with module/lesson info and a progress bar.

    Args:
        state: Course state dict with current_module, current_lesson, progress, status
    """
    module = state.get("current_module", 0)
    lesson = state.get("current_lesson", 0)
    progress = state.get("progress", 0.0)
    status = state.get("status", "unknown")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Module", module)
    with col2:
        st.metric("Lesson", lesson)
    with col3:
        st.metric("Status", status)

    st.progress(progress, text=f"Progress: {progress:.0%}")


def course_card(course: Dict[str, Any], key_prefix: str = "") -> bool:
    """
    Render a course card with name, status badge, and timestamp.
    Returns True if the card was clicked.

    Args:
        course: Course dict with name, status, last_accessed
        key_prefix: Unique prefix for Streamlit widget keys

    Returns:
        True if the user clicked this course card
    """
    name = course.get("name", "Unknown")
    status = course.get("status", "unknown")
    last_accessed = course.get("last_accessed", "Never")

    # Format timestamp
    if last_accessed and last_accessed != "Never":
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(last_accessed.replace("Z", "+00:00"))
            last_accessed = dt.strftime("%b %d, %Y %H:%M")
        except (ValueError, TypeError):
            pass

    badge_html = status_badge(status)

    with st.container():
        st.markdown(
            f"""
            <div style="border:1px solid #333;border-radius:8px;padding:12px;margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong style="font-size:1.05em;">{name}</strong>
                    {badge_html}
                </div>
                <div style="color:#888;font-size:0.8em;margin-top:4px;">
                    Last accessed: {last_accessed}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        clicked = st.button(
            "Open",
            key=f"{key_prefix}_{name}",
            use_container_width=True,
        )
        return clicked
