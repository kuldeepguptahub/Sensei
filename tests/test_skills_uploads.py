"""
Tests for sensei.skills.uploads module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from sensei.skills.courses import create_workspace
from sensei.skills.uploads import save_upload, read_upload, list_uploads


@pytest.fixture
def courses_dir(tmp_path):
    """Provide a temporary courses directory with a test course."""
    with patch("sensei.skills.courses.COURSES_DIR", tmp_path):
        with patch("sensei.path_utils.COURSES_DIR", tmp_path):
            create_workspace("test-course")
            yield tmp_path


class TestSaveUpload:
    """Tests for save_upload()."""

    def test_saves_file(self, courses_dir):
        save_upload("test-course", "notes.pdf", b"file content")
        path = courses_dir / "test-course" / "uploads" / "notes.pdf"
        assert path.read_bytes() == b"file content"

    def test_overwrites_existing(self, courses_dir):
        save_upload("test-course", "file.bin", b"version 1")
        save_upload("test-course", "file.bin", b"version 2")
        path = courses_dir / "test-course" / "uploads" / "file.bin"
        assert path.read_bytes() == b"version 2"

    def test_nonexistent_course(self, courses_dir):
        with pytest.raises(ValueError, match="doesn't exist"):
            save_upload("nonexistent", "file.bin", b"data")


class TestReadUpload:
    """Tests for read_upload()."""

    def test_reads_file(self, courses_dir):
        save_upload("test-course", "doc.pdf", b"content")
        content = read_upload("test-course", "doc.pdf")
        assert content == b"content"

    def test_nonexistent_file(self, courses_dir):
        with pytest.raises(ValueError, match="not found"):
            read_upload("test-course", "missing.bin")


class TestListUploads:
    """Tests for list_uploads()."""

    def test_lists_files(self, courses_dir):
        save_upload("test-course", "a.pdf", b"a")
        save_upload("test-course", "b.pdf", b"b")
        uploads = list_uploads("test-course")
        assert "a.pdf" in uploads
        assert "b.pdf" in uploads

    def test_nonexistent_course(self, courses_dir):
        with pytest.raises(ValueError, match="doesn't exist"):
            list_uploads("nonexistent")

    def test_includes_metadata(self, courses_dir):
        save_upload("test-course", "test.bin", b"data")
        uploads = list_uploads("test-course")
        assert "size" in uploads["test.bin"]
        assert "modified" in uploads["test.bin"]
