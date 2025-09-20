#!/usr/bin/env python3
"""
Integration test for the progress system with TFM operations
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

# Add the src directory to the path so we can import TFM modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_progress_manager import ProgressManager, OperationType


class MockTFM:
    """Mock TFM class to test progress integration"""
    
    def __init__(self):
        self.progress_manager = ProgressManager()
        self.stdscr = Mock()
        self.needs_full_redraw = False
        
    def _progress_callback(self, progress_data):
        """Mock progress callback"""
        pass
        
    def draw_status(self):
        """Mock draw_status method"""
        pass
        
    def refresh_files(self, pane=None):
        """Mock refresh_files method"""
        pass
        
    def get_current_pane(self):
        """Mock get_current_pane method"""
        return {'selected_files': set()}
        
    def perform_copy_operation(self, files_to_copy, destination_dir, overwrite=False):
        """Mock copy operation with progress tracking"""
        copied_count = 0
        error_count = 0
        
        # Start progress tracking for copy operation
        total_files = len(files_to_copy)
        if total_files > 1:  # Only show progress for multiple files
            self.progress_manager.start_operation(
                OperationType.COPY, 
                total_files, 
                f"to {destination_dir.name}",
                self._progress_callback
            )
        
        try:
            for i, source_file in enumerate(files_to_copy):
                # Update progress
                if total_files > 1:
                    self.progress_manager.update_progress(source_file.name, i)
                
                try:
                    # Simulate copy operation
                    dest_path = destination_dir / source_file.name
                    if source_file.is_file():
                        shutil.copy2(source_file, dest_path)
                    elif source_file.is_dir():
                        shutil.copytree(source_file, dest_path, dirs_exist_ok=True)
                    
                    copied_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if total_files > 1:
                        self.progress_manager.increment_errors()
        
        finally:
            # Finish progress tracking
            if total_files > 1:
                self.progress_manager.finish_operation()
        
        return copied_count, error_count


def test_progress_integration():
    """Test progress system integration with file operations"""
    print("Testing progress system integration...")
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create test files
        test_files = []
        for i in range(5):
            test_file = source_dir / f"test_file_{i}.txt"
            test_file.write_text(f"Content of file {i}")
            test_files.append(test_file)
        
        # Create mock TFM instance
        tfm = MockTFM()
        
        # Test copy operation with progress
        copied_count, error_count = tfm.perform_copy_operation(test_files, dest_dir)
        
        # Verify operation completed successfully
        assert copied_count == 5
        assert error_count == 0
        
        # Verify progress manager is no longer active
        assert not tfm.progress_manager.is_operation_active()
        
        # Verify files were actually copied
        for i in range(5):
            dest_file = dest_dir / f"test_file_{i}.txt"
            assert dest_file.exists()
            assert dest_file.read_text() == f"Content of file {i}"
    
    print("✅ Progress integration test passed!")


def test_progress_display_integration():
    """Test progress display integration"""
    print("Testing progress display integration...")
    
    tfm = MockTFM()
    
    # Test that progress manager integrates with status display
    assert not tfm.progress_manager.is_operation_active()
    
    # Start an operation
    tfm.progress_manager.start_operation(
        OperationType.MOVE,
        10,
        "to Archive",
        tfm._progress_callback
    )
    
    # Verify operation is active
    assert tfm.progress_manager.is_operation_active()
    
    # Test progress updates
    for i in range(10):
        tfm.progress_manager.update_progress(f"file_{i}.txt", i)
        
        # Verify progress state
        operation = tfm.progress_manager.get_current_operation()
        assert operation['processed_items'] == i
        assert operation['current_item'] == f"file_{i}.txt"
        
        # Test progress text generation
        progress_text = tfm.progress_manager.get_progress_text(80)
        assert "Moving" in progress_text
        assert f"{i}/10" in progress_text
        assert f"file_{i}.txt" in progress_text
    
    # Finish operation
    tfm.progress_manager.finish_operation()
    assert not tfm.progress_manager.is_operation_active()
    
    print("✅ Progress display integration test passed!")


def test_legacy_compatibility():
    """Test that legacy archive progress method still works"""
    print("Testing legacy compatibility...")
    
    tfm = MockTFM()
    
    # Add the legacy method
    def update_archive_progress(self, current_file, processed, total):
        """Legacy method that delegates to ProgressManager"""
        if self.progress_manager.is_operation_active():
            self.progress_manager.update_progress(current_file, processed)
        
        try:
            self.draw_status()
            self.stdscr.refresh()
        except:
            pass
    
    # Bind the method to our mock TFM
    tfm.update_archive_progress = update_archive_progress.__get__(tfm, MockTFM)
    
    # Start an archive operation
    tfm.progress_manager.start_operation(
        OperationType.ARCHIVE_CREATE,
        5,
        "ZIP: backup.zip",
        tfm._progress_callback
    )
    
    # Test legacy method calls
    for i in range(1, 6):
        tfm.update_archive_progress(f"file_{i}.txt", i, 5)
        
        # Verify progress was updated
        operation = tfm.progress_manager.get_current_operation()
        assert operation['processed_items'] == i
        assert operation['current_item'] == f"file_{i}.txt"
    
    # Finish operation
    tfm.progress_manager.finish_operation()
    assert not tfm.progress_manager.is_operation_active()
    
    print("✅ Legacy compatibility test passed!")


if __name__ == "__main__":
    test_progress_integration()
    test_progress_display_integration()
    test_legacy_compatibility()
    print("\n🎉 All progress integration tests passed!")