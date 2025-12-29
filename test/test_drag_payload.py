"""
Tests for drag payload builder.

Run with: PYTHONPATH=.:src:ttk pytest test/test_drag_payload.py -v
"""

import pytest

from tfm_drag_payload import DragPayloadBuilder


class TestDragPayloadBuilder:
    """Test DragPayloadBuilder class."""
    
    def test_build_payload_with_selected_files(self, tmp_path):
        """Test building payload with selected files."""
        builder = DragPayloadBuilder()
        
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Build payload
        urls = builder.build_payload(
            selected_files=[file1, file2],
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify
        assert urls is not None
        assert len(urls) == 2
        assert all(url.startswith("file://") for url in urls)
        assert str(file1.resolve().as_posix()) in urls[0]
        assert str(file2.resolve().as_posix()) in urls[1]
    
    def test_build_payload_with_focused_item(self, tmp_path):
        """Test building payload with focused item when no selection."""
        builder = DragPayloadBuilder()
        
        # Create test file
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")
        
        # Build payload
        urls = builder.build_payload(
            selected_files=[],
            focused_item=file1,
            current_directory=tmp_path
        )
        
        # Verify
        assert urls is not None
        assert len(urls) == 1
        assert urls[0].startswith("file://")
        assert str(file1.resolve().as_posix()) in urls[0]
    
    def test_build_payload_rejects_parent_directory(self, tmp_path):
        """Test that parent directory marker is rejected."""
        builder = DragPayloadBuilder()
        
        # Create parent directory marker
        parent = tmp_path / ".."
        
        # Build payload
        urls = builder.build_payload(
            selected_files=[],
            focused_item=parent,
            current_directory=tmp_path
        )
        
        # Verify rejection
        assert urls is None
    
    def test_build_payload_rejects_remote_files(self, tmp_path):
        """Test that remote files are rejected."""
        builder = DragPayloadBuilder()
        
        # Create mock remote path
        remote_path = Path("s3://bucket/file.txt")
        
        # Build payload
        urls = builder.build_payload(
            selected_files=[remote_path],
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify rejection
        assert urls is None
    
    def test_build_payload_rejects_archive_content(self, tmp_path):
        """Test that archive contents are rejected."""
        builder = DragPayloadBuilder()
        
        # Create mock archive path
        archive_path = Path("/path/to/file.zip/internal/file.txt")
        
        # Build payload
        urls = builder.build_payload(
            selected_files=[archive_path],
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify rejection
        assert urls is None
    
    def test_build_payload_rejects_nonexistent_files(self, tmp_path):
        """Test that nonexistent files are rejected."""
        builder = DragPayloadBuilder()
        
        # Create path to nonexistent file
        nonexistent = tmp_path / "does_not_exist.txt"
        
        # Build payload
        urls = builder.build_payload(
            selected_files=[nonexistent],
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify rejection
        assert urls is None
    
    def test_build_payload_rejects_too_many_files(self, tmp_path):
        """Test that file count limit is enforced."""
        builder = DragPayloadBuilder()
        
        # Create more files than the limit
        files = []
        for i in range(builder.MAX_FILES + 1):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)
        
        # Build payload
        urls = builder.build_payload(
            selected_files=files,
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify rejection
        assert urls is None
    
    def test_build_payload_with_no_files(self, tmp_path):
        """Test that empty selection is rejected."""
        builder = DragPayloadBuilder()
        
        # Build payload with no files
        urls = builder.build_payload(
            selected_files=[],
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify rejection
        assert urls is None
    
    def test_file_url_encoding(self, tmp_path):
        """Test that file URLs are properly encoded."""
        builder = DragPayloadBuilder()
        
        # Create file with spaces and special characters
        file = tmp_path / "file with spaces.txt"
        file.write_text("content")
        
        # Build payload
        urls = builder.build_payload(
            selected_files=[file],
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify URL encoding
        assert urls is not None
        assert len(urls) == 1
        assert "file%20with%20spaces" in urls[0]
        assert urls[0].startswith("file://")
