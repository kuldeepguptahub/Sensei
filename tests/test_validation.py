"""
Tests for sensei.validation module.
"""

import json
import pytest
from sensei.validation import (
    validate_course_name,
    validate_artifact_name,
    validate_file_name,
    validate_state_json,
)


class TestValidateCourseName:
    """Tests for validate_course_name()."""

    def test_valid_names(self):
        assert validate_course_name("python-basics") == "python-basics"
        assert validate_course_name("web_dev") == "web_dev"
        assert validate_course_name("Course123") == "Course123"
        assert validate_course_name("a") == "a"

    def test_strips_whitespace(self):
        assert validate_course_name("  my-course  ") == "my-course"

    def test_empty_string(self):
        with pytest.raises(ValueError, match="empty"):
            validate_course_name("")

    def test_whitespace_only(self):
        with pytest.raises(ValueError, match="empty"):
            validate_course_name("   ")

    def test_too_long(self):
        with pytest.raises(ValueError, match="too long"):
            validate_course_name("x" * 101)

    def test_max_length_accepted(self):
        assert validate_course_name("x" * 100) == "x" * 100

    def test_rejects_spaces(self):
        # Spaces are now allowed and converted to hyphens
        assert validate_course_name("my course") == "my-course"

    def test_rejects_special_chars(self):
        with pytest.raises(ValueError, match="Invalid course name"):
            validate_course_name("course@name!")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="Invalid course name"):
            validate_course_name("../../etc")

    def test_rejects_backslash(self):
        with pytest.raises(ValueError, match="Invalid course name"):
            validate_course_name("course\\name")

    def test_rejects_dots(self):
        with pytest.raises(ValueError, match="Invalid course name"):
            validate_course_name("my.course")


class TestValidateArtifactName:
    """Tests for validate_artifact_name()."""

    def test_valid_names(self):
        assert validate_artifact_name("notes.md") == "notes.md"
        assert validate_artifact_name("definition.json") == "definition.json"
        assert validate_artifact_name("my-artifact.txt") == "my-artifact.txt"

    def test_allows_dots(self):
        assert validate_artifact_name("file.v2.md") == "file.v2.md"

    def test_empty_string(self):
        with pytest.raises(ValueError, match="empty"):
            validate_artifact_name("")

    def test_too_long(self):
        with pytest.raises(ValueError, match="too long"):
            validate_artifact_name("a" * 256)

    def test_rejects_slash(self):
        with pytest.raises(ValueError, match="Invalid artifact name"):
            validate_artifact_name("dir/file.json")

    def test_rejects_backslash(self):
        with pytest.raises(ValueError, match="Invalid artifact name"):
            validate_artifact_name("dir\\file.json")

    def test_rejects_double_dots(self):
        with pytest.raises(ValueError, match="Invalid artifact name"):
            validate_artifact_name("../file.json")

    def test_rejects_spaces(self):
        with pytest.raises(ValueError, match="Invalid artifact name"):
            validate_artifact_name("my file.md")


class TestValidateFileName:
    """Tests for validate_file_name()."""

    def test_valid_names(self):
        assert validate_file_name("notes.pdf") == "notes.pdf"
        assert validate_file_name("data.csv") == "data.csv"

    def test_empty_string(self):
        with pytest.raises(ValueError, match="empty"):
            validate_file_name("")

    def test_rejects_slash(self):
        with pytest.raises(ValueError, match="Invalid file name"):
            validate_file_name("../../etc/passwd")

    def test_rejects_backslash(self):
        with pytest.raises(ValueError, match="Invalid file name"):
            validate_file_name("dir\\file.txt")


class TestValidateStateJson:
    """Tests for validate_state_json()."""

    def test_valid_state(self):
        state = json.dumps({
            "current_module": 0,
            "current_lesson": 0,
            "progress": 0.0,
            "status": "planning",
        })
        result = validate_state_json(state)
        assert result["status"] == "planning"

    def test_invalid_json(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            validate_state_json("not json")

    def test_not_dict(self):
        with pytest.raises(ValueError, match="JSON object"):
            validate_state_json('["not", "a", "dict"]')

    def test_missing_field(self):
        state = json.dumps({"current_module": 0, "current_lesson": 0})
        with pytest.raises(ValueError, match="missing required field"):
            validate_state_json(state)

    def test_wrong_type(self):
        state = json.dumps({
            "current_module": "0",
            "current_lesson": 0,
            "progress": 0.0,
            "status": "planning",
        })
        with pytest.raises(ValueError, match="must be"):
            validate_state_json(state)

    def test_invalid_status(self):
        state = json.dumps({
            "current_module": 0,
            "current_lesson": 0,
            "progress": 0.0,
            "status": "unknown",
        })
        with pytest.raises(ValueError, match="Invalid status"):
            validate_state_json(state)

    def test_invalid_progress_negative(self):
        state = json.dumps({
            "current_module": 0,
            "current_lesson": 0,
            "progress": -0.1,
            "status": "planning",
        })
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            validate_state_json(state)

    def test_invalid_progress_over_one(self):
        state = json.dumps({
            "current_module": 0,
            "current_lesson": 0,
            "progress": 1.5,
            "status": "planning",
        })
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            validate_state_json(state)

    def test_all_valid_statuses(self):
        for status in ["planning", "active", "paused", "completed"]:
            state = json.dumps({
                "current_module": 0,
                "current_lesson": 0,
                "progress": 0.0,
                "status": status,
            })
            result = validate_state_json(state)
            assert result["status"] == status
