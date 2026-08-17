"""
Tests for sensei.skills.artifacts module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
from sensei.skills.courses import create_workspace
from sensei.skills.artifacts import read_artifact, write_artifact, list_artifacts


@pytest.fixture
def courses_dir(tmp_path):
    """Provide a temporary courses directory with a test course."""
    with patch("sensei.skills.courses.COURSES_DIR", tmp_path):
        with patch("sensei.path_utils.COURSES_DIR", tmp_path):
            create_workspace("test-course")
            yield tmp_path


class TestWriteArtifact:
    """Tests for write_artifact()."""

    def test_writes_file(self, courses_dir):
        write_artifact("test-course", "notes.md", "# My Notes")
        path = courses_dir / "test-course" / "artifacts" / "notes.md"
        assert path.read_text() == "# My Notes"

    def test_overwrites_existing(self, courses_dir):
        write_artifact("test-course", "notes.md", "version 1")
        write_artifact("test-course", "notes.md", "version 2")
        path = courses_dir / "test-course" / "artifacts" / "notes.md"
        assert path.read_text() == "version 2"

    def test_nonexistent_course(self, courses_dir):
        with pytest.raises(ValueError, match="doesn't exist"):
            write_artifact("nonexistent", "file.md", "content")


class TestReadArtifact:
    """Tests for read_artifact()."""

    def test_reads_file(self, courses_dir):
        write_artifact("test-course", "notes.md", "# Hello")
        content = read_artifact("test-course", "notes.md")
        assert content == "# Hello"

    def test_nonexistent_artifact(self, courses_dir):
        with pytest.raises(ValueError, match="not found"):
            read_artifact("test-course", "nonexistent.md")

    def test_initial_definition_readable(self, courses_dir):
        content = read_artifact("test-course", "definition.json")
        data = json.loads(content)
        assert "course_name" in data


class TestListArtifacts:
    """Tests for list_artifacts()."""

    def test_lists_files(self, courses_dir):
        write_artifact("test-course", "a.md", "a")
        write_artifact("test-course", "b.md", "b")
        artifacts = list_artifacts("test-course")
        assert "a.md" in artifacts
        assert "b.md" in artifacts

    def test_nonexistent_course(self, courses_dir):
        with pytest.raises(ValueError, match="doesn't exist"):
            list_artifacts("nonexistent")

    def test_includes_metadata(self, courses_dir):
        write_artifact("test-course", "test.md", "content")
        artifacts = list_artifacts("test-course")
        assert "size" in artifacts["test.md"]
        assert "modified" in artifacts["test.md"]
