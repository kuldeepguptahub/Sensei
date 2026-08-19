"""
Sensei — Streamlit Web Dashboard

Launch with: streamlit run src/sensei/ui/app.py
Or via CLI:  sensei ui
"""

import sys
import streamlit as st
from pathlib import Path

# Ensure src is on path so sensei imports work
_src = str(Path(__file__).resolve().parent.parent.parent)
if _src not in sys.path:
    sys.path.insert(0, _src)

from sensei.gateway.config import config_exists
from sensei.skills.courses import list_courses, create_workspace, delete_course
from sensei.ui.components import progress_display


# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Sensei",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Provider check
# ---------------------------------------------------------------------------
if not config_exists():
    st.title("🎓 Sensei")
    st.warning("No LLM provider configured.")
    st.markdown(
        "Run the following command in your terminal to set up a provider:\n\n"
        "```bash\nsensei connect\n```"
    )
    st.stop()

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "selected_course" not in st.session_state:
    st.session_state.selected_course = None
if "mode" not in st.session_state:
    st.session_state.mode = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🎓 Sensei")

    st.divider()

    # Course list
    courses = list_courses()
    if courses:
        st.subheader("Courses")
        for course in courses:
            name = course.get("name", "Unknown")
            status = course.get("status", "unknown")

            if st.button(
                f"{name}  [{status}]",
                key=f"sb_{name}",
                use_container_width=True
            ):
                st.session_state.selected_course = name
                st.session_state.mode = "resume_course"
                st.session_state.messages = []
                st.rerun()
    else:
        st.info("No courses yet.")

    st.divider()

    # New course form
    with st.form("new_course_form", clear_on_submit=True):
        new_name = st.text_input("New course name", key="new_course_name")
        submitted = st.form_submit_button("➕ Create Course", use_container_width=True, type="primary")
        if submitted:
            if new_name.strip():
                try:
                    create_workspace(new_name.strip())
                    st.session_state.selected_course = new_name.strip()
                    st.session_state.mode = "new_course"
                    st.session_state.messages = []
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
            else:
                st.warning("Enter a course name.")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
if st.session_state.selected_course:
    # Import and run the chat page
    from sensei.ui.views import chat
    chat.render(
        course_name=st.session_state.selected_course,
        mode=st.session_state.mode,
    )
else:
    # Home page
    from sensei.ui.views import home
    home.render()
