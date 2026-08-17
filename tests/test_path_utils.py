"""
Tests for sensei.path_utils module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from sensei.path_utils import (
    safe_course_path,
    safe_artifact_path,
    safe_upload_path,
    safe_uploads_dir,
    safe_artifacts_dir,
)


class TestSafeCoursePath:
    """Tests for safe_course_path()."""

    def test_valid_name(self):
        path = safe_course_path("test-course")
        assert path.name == "test-course"

    def test_rejects_traversal(self):
        with pytest.raises(ValueError, match="Invalid course name"):
            safe_course_path("../../etc")

    def test_rejects_backslash(self):
        with pytest.raises(ValueError, match="Invalid course name"):
            safe_course_path("course\\name")

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            safe_course_path("")


class TestSafeArtifactPath:
    """Tests for safe_artifact_path()."""

    def test_valid_names(self):
        path = safe_artifact_path("test-course", "notes.md")
        assert path.name == "notes.md"
        assert path.parent.name == "artifacts"

    def test_rejects_course_traversal(self):
        with pytest.raises(ValueError):
            safe_artifact_path("../../etc", "file.md")

    def test_rejects_artifact_traversal(self):
        with pytest.raises(ValueError):
            safe_artifact_path("test-course", "../file.md")

    def test_rejects_artifact_slash(self):
        with pytest.raises(ValueError, match="Invalid artifact name"):
            safe_artifact_path("test-course", "dir/file.json")


class TestSafeUploadPath:
    """Tests for safe_upload_path()."""

    def test_valid_names(self):
        path = safe_upload_path("test-course", "notes.pdf")
        assert path.name == "notes.pdf"
        assert path.parent.name == "uploads"

    def test_rejects_traversal(self):
        with pytest.raises(ValueError):
            safe_upload_path("test-course", "../../etc/passwd")


class TestSafeDirs:
    """Tests for safe_uploads_dir and safe_artifacts_dir."""

    def test_uploads_dir(self):
        path = safe_uploads_dir("test-course")
        assert path.name == "uploads"

    def test_artifacts_dir(self):
        path = safe_artifacts_dir("test-course")
        assert path.name == "artifacts"

    def test_uploads_dir_rejects_traversal(self):
        with pytest.raises(ValueError):
            safe_uploads_dir("../../etc")

    def test_artifacts_dir_rejects_traversal(self):
        with pytest.raises(ValueError):
            safe_artifacts_dir("../../etc")
