#!/usr/bin/env python3
"""
Tests for archive operation conflict detection.

This module tests the conflict detection functionality for archive operations,
including detection of existing archive files and files that would be overwritten
during extraction.
"""

import tempfile
import tarfile
import zipfile
from pathlib import Path as PathlibPath
from unittest.mock import Mock, MagicMock

import pytest

from tfm_path import Path
from tfm_archive_operation_executor import ArchiveOperationExecutor, ConflictInfo
from tfm_progress_manager import ProgressManager


class TestConflictDetection:
    """Test conflict detection for archive operations"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield PathlibPath(tmpdir)
    
    @pytest.fixture
    def executor(self):
        """Create an executor instance for testing"""
        file_manager = Mock()
        file_manager.operation_cancelled = False
        progress_manager = Mock(spec=ProgressManager)
        cache_manager = Mock()
        
        return ArchiveOperationExecutor(file_manager, progress_manager, cache_manager)
    
    def test_create_conflict_archive_exists(self, executor, temp_dir):
        """Test conflict detection when archive file already exists"""
        # Create an existing archive file
        archive_path = Path(temp_dir / "test.tar.gz")
        archive_path.touch()
        
        # Create source files
        source_file = Path(temp_dir / "source.txt")
        source_file.write_text("test content")
        
        # Check for conflicts
        conflicts = executor._check_conflicts(
            'create',
            [source_file],
            archive_path
        )
        
        # Should detect one conflict
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == 'archive_exists'
        assert conflicts[0].path == archive_path
        assert conflicts[0].size is not None
        assert not conflicts[0].is_directory
    
    def test_create_no_conflict_archive_not_exists(self, executor, temp_dir):
        """Test no conflict when archive file doesn't exist"""
        # Archive file doesn't exist
        archive_path = Path(temp_dir / "test.tar.gz")
        
        # Create source files
        source_file = Path(temp_dir / "source.txt")
        source_file.write_text("test content")
        
        # Check for conflicts
        conflicts = executor._check_conflicts(
            'create',
            [source_file],
            archive_path
        )
        
        # Should detect no conflicts
        assert len(conflicts) == 0
    
    def test_extract_conflict_files_exist(self, executor, temp_dir):
        """Test conflict detection when files would be overwritten during extraction"""
        # Create a tar.gz archive with test files
        archive_path = Path(temp_dir / "test.tar.gz")
        
        # Create files to add to archive
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Create archive
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            tar.add(str(file1), arcname="file1.txt")
            tar.add(str(file2), arcname="file2.txt")
        
        # Create extraction directory with existing files
        extract_dir = Path(temp_dir / "extract")
        extract_dir.mkdir()
        
        # Create conflicting files
        (extract_dir / "file1.txt").write_text("existing content")
        (extract_dir / "file2.txt").write_text("existing content")
        
        # Check for conflicts
        conflicts = executor._check_conflicts(
            'extract',
            [archive_path],
            extract_dir
        )
        
        # Should detect two conflicts
        assert len(conflicts) == 2
        assert all(c.conflict_type == 'file_exists' for c in conflicts)
        assert {c.path.name for c in conflicts} == {"file1.txt", "file2.txt"}
    
    def test_extract_partial_conflict(self, executor, temp_dir):
        """Test conflict detection when only some files would be overwritten"""
        # Create a tar.gz archive with test files
        archive_path = Path(temp_dir / "test.tar.gz")
        
        # Create files to add to archive
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "file3.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        file3.write_text("content3")
        
        # Create archive
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            tar.add(str(file1), arcname="file1.txt")
            tar.add(str(file2), arcname="file2.txt")
            tar.add(str(file3), arcname="file3.txt")
        
        # Create extraction directory with only one existing file
        extract_dir = Path(temp_dir / "extract")
        extract_dir.mkdir()
        
        # Create only one conflicting file
        (extract_dir / "file2.txt").write_text("existing content")
        
        # Check for conflicts
        conflicts = executor._check_conflicts(
            'extract',
            [archive_path],
            extract_dir
        )
        
        # Should detect one conflict
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == 'file_exists'
        assert conflicts[0].path.name == "file2.txt"
    
    def test_extract_no_conflict_empty_directory(self, executor, temp_dir):
        """Test no conflict when extracting to empty directory"""
        # Create a tar.gz archive with test files
        archive_path = Path(temp_dir / "test.tar.gz")
        
        # Create files to add to archive
        file1 = temp_dir / "file1.txt"
        file1.write_text("content1")
        
        # Create archive
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            tar.add(str(file1), arcname="file1.txt")
        
        # Create empty extraction directory
        extract_dir = Path(temp_dir / "extract")
        extract_dir.mkdir()
        
        # Check for conflicts
        conflicts = executor._check_conflicts(
            'extract',
            [archive_path],
            extract_dir
        )
        
        # Should detect no conflicts
        assert len(conflicts) == 0
    
    def test_extract_conflict_zip_format(self, executor, temp_dir):
        """Test conflict detection with zip format archives"""
        # Create a zip archive with test files
        archive_path = Path(temp_dir / "test.zip")
        
        # Create files to add to archive
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Create archive
        with zipfile.ZipFile(str(archive_path), 'w') as zip_file:
            zip_file.write(str(file1), "file1.txt")
            zip_file.write(str(file2), "file2.txt")
        
        # Create extraction directory with existing files
        extract_dir = Path(temp_dir / "extract")
        extract_dir.mkdir()
        
        # Create conflicting files
        (extract_dir / "file1.txt").write_text("existing content")
        
        # Check for conflicts
        conflicts = executor._check_conflicts(
            'extract',
            [archive_path],
            extract_dir
        )
        
        # Should detect one conflict
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == 'file_exists'
        assert conflicts[0].path.name == "file1.txt"
    
    def test_conflict_info_dataclass(self):
        """Test ConflictInfo dataclass structure"""
        # Create a ConflictInfo instance
        path = Path("/tmp/test.txt")
        conflict = ConflictInfo(
            conflict_type='file_exists',
            path=path,
            size=1024,
            is_directory=False
        )
        
        # Verify attributes
        assert conflict.conflict_type == 'file_exists'
        assert conflict.path == path
        assert conflict.size == 1024
        assert not conflict.is_directory
    
    def test_conflict_info_defaults(self):
        """Test ConflictInfo default values"""
        # Create a ConflictInfo with minimal arguments
        path = Path("/tmp/test.txt")
        conflict = ConflictInfo(
            conflict_type='archive_exists',
            path=path
        )
        
        # Verify defaults
        assert conflict.size is None
        assert not conflict.is_directory


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
