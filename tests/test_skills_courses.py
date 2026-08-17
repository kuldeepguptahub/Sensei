"""
Tests for sensei.skills.courses module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
from sensei.skills.courses import (
    create_workspace,
    list_courses,
    delete_course,
    rename_course,
    update_state,
)


@pytest.fixture
def courses_dir(tmp_path):
    """Provide a temporary courses directory."""
    with patch("sensei.skills.courses.COURSES_DIR", tmp_path):
        with patch("sensei.path_utils.COURSES_DIR", tmp_path):
            yield tmp_path


class TestCreateWorkspace:
    """Tests for create_workspace()."""

    def test_creates_directory_structure(self, courses_dir):
        create_workspace("test-course")
        course_dir = courses_dir / "test-course"
        assert course_dir.exists()
        assert (course_dir / "artifacts").exists()
        assert (course_dir / "uploads").exists()

    def test_creates_initial_files(self, courses_dir):
        create_workspace("test-course")
        artifacts = courses_dir / "test-course" / "artifacts"
        assert (artifacts / "definition.json").exists()
        assert (artifacts / "state.json").exists()
        assert (artifacts / "context.md").exists()
        assert (artifacts / "notes.md").exists()
        assert (artifacts / "planner.md").exists()

    def test_state_json_valid(self, courses_dir):
        create_workspace("test-course")
        state_path = courses_dir / "test-course" / "artifacts" / "state.json"
        state = json.loads(state_path.read_text())
        assert state["current_module"] == 0
        assert state["current_lesson"] == 0
        assert state["status"] == "planning"
        assert state["progress"] == 0.0

    def test_duplicate_rejected(self, courses_dir):
        create_workspace("test-course")
        with pytest.raises(ValueError, match="already exists"):
            create_workspace("test-course")

    def test_invalid_name_rejected(self, courses_dir):
        with pytest.raises(ValueError):
            create_workspace("../../etc")


class TestDeleteCourse:
    """Tests for delete_course()."""

    def test_deletes_course(self, courses_dir):
        create_workspace("test-course")
        delete_course("test-course")
        assert not (courses_dir / "test-course").exists()

    def test_nonexistent_rejected(self, courses_dir):
        with pytest.raises(ValueError, match="doesn't exist"):
            delete_course("nonexistent")

    def test_invalid_name_rejected(self, courses_dir):
        with pytest.raises(ValueError):
            delete_course("../../etc")


class TestRenameCourse:
    """Tests for rename_course()."""

    def test_renames_course(self, courses_dir):
        create_workspace("old-name")
        rename_course("old-name", "new-name")
        assert not (courses_dir / "old-name").exists()
        assert (courses_dir / "new-name").exists()

    def test_old_not_found(self, courses_dir):
        with pytest.raises(ValueError, match="doesn't exist"):
            rename_course("nonexistent", "new-name")

    def test_new_already_exists(self, courses_dir):
        create_workspace("name-1")
        create_workspace("name-2")
        with pytest.raises(ValueError, match="already exists"):
            rename_course("name-1", "name-2")

    def test_invalid_names_rejected(self, courses_dir):
        with pytest.raises(ValueError):
            rename_course("../../etc", "new-name")


class TestUpdateState:
    """Tests for update_state()."""

    def test_updates_state(self, courses_dir):
        create_workspace("test-course")
        new_state = json.dumps({
            "current_module": 1,
            "current_lesson": 2,
            "progress": 0.5,
            "status": "active"
        })
        update_state("test-course", new_state)

        state_path = courses_dir / "test-course" / "artifacts" / "state.json"
        state = json.loads(state_path.read_text())
        assert state["current_module"] == 1
        assert state["progress"] == 0.5

    def test_invalid_json_rejected(self, courses_dir):
        create_workspace("test-course")
        with pytest.raises(ValueError, match="Invalid JSON"):
            update_state("test-course", "not json")

    def test_missing_field_rejected(self, courses_dir):
        create_workspace("test-course")
        invalid_state = json.dumps({"current_module": 0})
        with pytest.raises(ValueError, match="missing required field"):
            update_state("test-course", invalid_state)

    def test_nonexistent_course(self, courses_dir):
        with pytest.raises(ValueError, match="doesn't exist"):
            update_state("nonexistent", '{"current_module": 0, "current_lesson": 0, "progress": 0.0, "status": "active"}')


class TestListCourses:
    """Tests for list_courses()."""

    def test_empty_list(self, courses_dir):
        assert list_courses() == []

    def test_lists_courses(self, courses_dir):
        create_workspace("course-a")
        create_workspace("course-b")
        courses = list_courses()
        names = [c["name"] for c in courses]
        assert "course-a" in names
        assert "course-b" in names
