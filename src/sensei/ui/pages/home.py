"""
Home page for Sensei Streamlit dashboard.

Displays course list with management actions: create, delete, resume.
"""

import streamlit as st
from typing import List, Dict, Any

from sensei.skills.courses import list_courses, create_workspace, delete_course as delete_workspace
from sensei.ui.components import status_badge


def render():
    """Render the home page with course list and management actions."""

    st.title("🎓 Welcome to Sensei")

    courses = list_courses()

    # --- Create course section ---
    with st.expander("➕ Create New Course", expanded=not courses):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_name = st.text_input(
                "Course name",
                key="home_new_course",
                placeholder="e.g., python-web-scraping",
            )
        with col2:
            st.write("")
            st.write("")
            create_clicked = st.button("Create", type="primary", key="home_create_btn")

        if create_clicked:
            if not new_name.strip():
                st.warning("Enter a course name.")
            else:
                try:
                    create_workspace(new_name.strip())
                    st.session_state.selected_course = new_name.strip()
                    st.session_state.mode = "new_course"
                    st.session_state.messages = []
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    # --- Course list section ---
    if not courses:
        st.info("No courses yet. Create one above to get started.")
        return

    st.subheader(f"Your Courses ({len(courses)})")

    for course in courses:
        name = course.get("name", "Unknown")
        status = course.get("status", "unknown")
        badge = status_badge(status)
        last = course.get("last_accessed", "")

        # Format timestamp
        last_display = ""
        if last:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                last_display = dt.strftime("%b %d, %Y %H:%M")
            except (ValueError, TypeError):
                last_display = last[:16]

        col1, col2, col3 = st.columns([4, 1, 1])

        with col1:
            st.markdown(
                f"**{name}** {badge}  \n"
                f"<small style='color:#888;'>Last accessed: {last_display or 'Never'}</small>",
                unsafe_allow_html=True,
            )

        with col2:
            if st.button("▶ Resume", key=f"resume_{name}", use_container_width=True):
                st.session_state.selected_course = name
                st.session_state.mode = "resume_course"
                st.session_state.messages = []
                st.rerun()

        with col3:
            if st.button("🗑 Delete", key=f"delete_{name}", use_container_width=True):
                st.session_state[f"confirm_delete_{name}"] = True

        # Confirmation dialog
        if st.session_state.get(f"confirm_delete_{name}", False):
            st.warning(f"Delete **{name}**? This cannot be undone.")
            c1, c2, _ = st.columns([1, 1, 4])
            with c1:
                if st.button("Yes, delete", key=f"yes_delete_{name}", type="primary"):
                    try:
                        delete_workspace(name)
                        del st.session_state[f"confirm_delete_{name}"]
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            with c2:
                if st.button("Cancel", key=f"cancel_delete_{name}"):
                    del st.session_state[f"confirm_delete_{name}"]
                    st.rerun()

        st.divider()
