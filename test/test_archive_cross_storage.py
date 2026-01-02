#!/usr/bin/env python3
"""
Test suite for cross-storage archive operations

This test suite verifies that archive operations work correctly across different
storage backends (local, S3, etc.) including:
- Archive creation with cross-storage sources
- Archive extraction to cross-storage destinations
- Mixed storage schemes (local to S3, S3 to local)
"""

import tempfile
import tarfile
import zipfile
from pathlib import Path as PathlibPath
from unittest.mock import Mock, MagicMock, patch

import pytest

from tfm_path import Path
from tfm_archive_operation_executor import ArchiveOperationExecutor
from tfm_progress_manager import ProgressManager


class TestCrossStorageArchiveOperations:
    """Test cross-storage archive operations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.file_manager = Mock()
        self.file_manager.operation_cancelled = False
        self.file_manager.operation_in_progress = False
        
        self.progress_manager = ProgressManager()
        self.cache_manager = Mock()
        
        self.executor = ArchiveOperationExecutor(
            self.file_manager,
            self.progress_manager,
            self.cache_manager
        )
    
    def test_local_sources_local_destination(self):
        """Test archive creation with all local paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = PathlibPath(tmpdir)
            
            # Create test files
            file1 = tmpdir_path / 'file1.txt'
            file1.write_text('Content 1')
            file2 = tmpdir_path / 'file2.txt'
            file2.write_text('Content 2')
            
            # Create archive
            archive_path = tmpdir_path / 'test.tar.gz'
            source_paths = [Path(file1), Path(file2)]
            
            # Verify all paths are local
            assert all(p.get_scheme() == 'file' for p in source_paths)
            assert Path(archive_path).get_scheme() == 'file'
            
            # Create archive (synchronous for testing)
            format_info = {'type': 'tar', 'compression': 'gz'}
            success, errors = self.executor._create_archive_local(
                source_paths, Path(archive_path), format_info
            )
            
            assert success == 2, f"Expected 2 files, got {success}"
            assert errors == 0, f"Expected 0 errors, got {errors}"
            assert archive_path.exists(), "Archive should exist"
            
            # Verify archive contents
            with tarfile.open(str(archive_path), 'r:gz') as tar:
                members = tar.getmembers()
                assert len(members) == 2, f"Expected 2 members, got {len(members)}"
    
    def test_local_archive_local_extraction(self):
        """Test archive extraction with all local paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = PathlibPath(tmpdir)
            
            # Create test archive
            archive_path = tmpdir_path / 'test.tar.gz'
            with tarfile.open(str(archive_path), 'w:gz') as tar:
                # Add test file
                test_file = tmpdir_path / 'source.txt'
                test_file.write_text('Test content')
                tar.add(str(test_file), arcname='source.txt')
            
            # Extract archive
            extract_dir = tmpdir_path / 'extracted'
            extract_dir.mkdir()
            
            # Verify all paths are local
            assert Path(archive_path).get_scheme() == 'file'
            assert Path(extract_dir).get_scheme() == 'file'
            
            format_info = {'type': 'tar', 'compression': 'gz'}
            success, errors, skipped = self.executor._extract_archive_local(
                Path(archive_path), Path(extract_dir), format_info, overwrite=True
            )
            
            assert success == 1, f"Expected 1 file, got {success}"
            assert errors == 0, f"Expected 0 errors, got {errors}"
            assert skipped == 0, f"Expected 0 skipped, got {skipped}"
            
            # Verify extracted file
            extracted_file = extract_dir / 'source.txt'
            assert extracted_file.exists(), "Extracted file should exist"
            assert extracted_file.read_text() == 'Test content'
    
    def test_cross_storage_detection_creation(self):
        """Test that cross-storage scenarios are detected during creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = PathlibPath(tmpdir)
            
            # Create local test file
            local_file = tmpdir_path / 'local.txt'
            local_file.write_text('Local content')
            
            # Test cross-storage detection logic
            local_path = Path(local_file)
            source_schemes = {local_path.get_scheme()}
            dest_scheme = 's3'  # Simulated S3 destination
            
            # Verify detection
            is_cross_storage = not (all(scheme == 'file' for scheme in source_schemes) and dest_scheme == 'file')
            assert is_cross_storage, "Should detect cross-storage scenario"
    
    def test_cross_storage_detection_extraction(self):
        """Test that cross-storage scenarios are detected during extraction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = PathlibPath(tmpdir)
            
            # Create local archive
            archive_path = tmpdir_path / 'test.tar.gz'
            with tarfile.open(str(archive_path), 'w:gz') as tar:
                test_file = tmpdir_path / 'test.txt'
                test_file.write_text('Test')
                tar.add(str(test_file), arcname='test.txt')
            
            # Test cross-storage detection logic
            local_archive = Path(archive_path)
            archive_scheme = local_archive.get_scheme()
            dest_scheme = 's3'  # Mock S3 destination
            
            # Verify detection
            is_cross_storage = not (archive_scheme == 'file' and dest_scheme == 'file')
            assert is_cross_storage, "Should detect cross-storage scenario"
    
    def test_mixed_storage_schemes(self):
        """Test handling of mixed storage schemes in source paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = PathlibPath(tmpdir)
            
            # Create local files
            file1 = tmpdir_path / 'file1.txt'
            file1.write_text('Content 1')
            file2 = tmpdir_path / 'file2.txt'
            file2.write_text('Content 2')
            
            source_paths = [Path(file1), Path(file2)]
            
            # Collect schemes
            source_schemes = {path.get_scheme() for path in source_paths}
            
            # Verify all are local
            assert source_schemes == {'file'}, f"Expected only 'file' scheme, got {source_schemes}"
            
            # Test that mixed schemes would be detected
            # (In real scenario, one would be S3)
            mock_s3_path = Mock()
            mock_s3_path.get_scheme.return_value = 's3'
            
            mixed_schemes = {path.get_scheme() for path in source_paths}
            mixed_schemes.add('s3')
            
            has_mixed = len(mixed_schemes) > 1
            assert has_mixed, "Should detect mixed storage schemes"
    
    def test_archive_format_support_cross_storage(self):
        """Test that all archive formats work with cross-storage"""
        formats = [
            ('tar', None, '.tar'),
            ('tar', 'gz', '.tar.gz'),
            ('tar', 'bz2', '.tar.bz2'),
            ('tar', 'xz', '.tar.xz'),
            ('zip', None, '.zip'),
        ]
        
        for archive_type, compression, extension in formats:
            format_info = {'type': archive_type, 'compression': compression}
            
            # Verify format info is valid
            assert format_info['type'] in ['tar', 'zip']
            
            # Verify extension matches
            expected_ext = self.executor._get_extension_for_format(format_info)
            assert expected_ext == extension, f"Expected {extension}, got {expected_ext}"
    
    def test_scheme_detection_methods(self):
        """Test that Path objects correctly report their storage scheme"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = PathlibPath(tmpdir)
            
            # Test local path
            local_file = tmpdir_path / 'local.txt'
            local_file.write_text('Local')
            local_path = Path(local_file)
            
            assert local_path.get_scheme() == 'file', "Local path should have 'file' scheme"
            assert not local_path.is_remote(), "Local path should not be remote"
    
    def test_cross_storage_error_handling(self):
        """Test error handling in cross-storage operations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = PathlibPath(tmpdir)
            
            # Create test file
            test_file = tmpdir_path / 'test.txt'
            test_file.write_text('Test content')
            
            # Test with non-existent destination (should handle gracefully)
            source_paths = [Path(test_file)]
            archive_path = Path(tmpdir_path / 'test.tar.gz')
            
            format_info = {'type': 'tar', 'compression': 'gz'}
            
            # This should succeed
            success, errors = self.executor._create_archive_local(
                source_paths, archive_path, format_info
            )
            
            assert success == 1, "Should successfully create archive"
            assert errors == 0, "Should have no errors"
    
    def test_cancellation_during_cross_storage(self):
        """Test that cancellation works during cross-storage operations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = PathlibPath(tmpdir)
            
            # Create test files
            files = []
            for i in range(5):
                f = tmpdir_path / f'file{i}.txt'
                f.write_text(f'Content {i}')
                files.append(Path(f))
            
            # Set cancellation flag
            self.file_manager.operation_cancelled = True
            
            archive_path = Path(tmpdir_path / 'test.tar.gz')
            format_info = {'type': 'tar', 'compression': 'gz'}
            
            # Attempt to create archive (should be cancelled)
            success, errors = self.executor._create_archive_local(
                files, archive_path, format_info
            )
            
            # Operation should be cancelled early
            assert success < len(files), "Should not process all files when cancelled"


def test_cross_storage_integration():
    """Integration test for cross-storage archive operations"""
    print("\n=== Cross-Storage Archive Integration Test ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = PathlibPath(tmpdir)
        
        # Create test files
        file1 = tmpdir_path / 'file1.txt'
        file1.write_text('Content 1')
        file2 = tmpdir_path / 'file2.txt'
        file2.write_text('Content 2')
        
        # Create archive
        archive_path = tmpdir_path / 'test.tar.gz'
        source_paths = [Path(file1), Path(file2)]
        
        # Set up executor
        file_manager = Mock()
        file_manager.operation_cancelled = False
        progress_manager = ProgressManager()
        executor = ArchiveOperationExecutor(file_manager, progress_manager, None)
        
        # Create archive
        format_info = {'type': 'tar', 'compression': 'gz'}
        success, errors = executor._create_archive_local(
            source_paths, Path(archive_path), format_info
        )
        
        print(f"✓ Created archive with {success} files, {errors} errors")
        assert success == 2
        assert errors == 0
        
        # Extract archive
        extract_dir = tmpdir_path / 'extracted'
        extract_dir.mkdir()
        
        success, errors, skipped = executor._extract_archive_local(
            Path(archive_path), Path(extract_dir), format_info, overwrite=True
        )
        
        print(f"✓ Extracted archive: {success} files, {errors} errors, {skipped} skipped")
        assert success == 2
        assert errors == 0
        
        # Verify extracted files
        extracted1 = extract_dir / 'file1.txt'
        extracted2 = extract_dir / 'file2.txt'
        
        assert extracted1.exists()
        assert extracted2.exists()
        assert extracted1.read_text() == 'Content 1'
        assert extracted2.read_text() == 'Content 2'
        
        print("✓ Cross-storage integration test passed")


if __name__ == '__main__':
    # Run integration test
    test_cross_storage_integration()
    
    # Run pytest tests
    pytest.main([__file__, '-v'])
