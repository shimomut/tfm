"""
Tests for performance optimizations in Qt GUI.

This module tests the performance optimizations implemented in Task 23:
- Incremental file list updates
- Progress update throttling
"""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication

# Skip all tests in this module due to Qt segfault issues in CI
pytestmark = pytest.mark.skip(reason="Qt tests cause segfaults in CI environment")


@pytest.fixture
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def file_pane(qapp):
    """Create FilePaneWidget instance for tests."""
    from src.tfm_qt_file_pane import FilePaneWidget
    pane = FilePaneWidget()
    yield pane
    pane.deleteLater()


@pytest.fixture
def progress_dialog(qapp):
    """Create ProgressDialog instance for tests."""
    from src.tfm_qt_progress_dialog import ProgressDialog
    dialog = ProgressDialog(title="Test", operation="Testing")
    yield dialog
    dialog.deleteLater()


class TestIncrementalFileListUpdates:
    """Test incremental file list update optimization."""
    
    def test_full_update_on_first_call(self, file_pane, tmp_path):
        """Test that first update performs full rebuild."""
        # Create test files
        files = [tmp_path / f"file{i}.txt" for i in range(5)]
        for f in files:
            f.touch()
        
        # First update should do full rebuild
        file_pane.update_files(files)
        
        assert file_pane.table.rowCount() == 5
        assert len(file_pane.files) == 5
    
    def test_incremental_update_same_files(self, file_pane, tmp_path):
        """Test incremental update when files haven't changed."""
        # Create test files
        files = [tmp_path / f"file{i}.txt" for i in range(5)]
        for f in files:
            f.touch()
        
        # Initial update
        file_pane.update_files(files)
        
        # Mock _incremental_update to verify it's called
        with patch.object(file_pane, '_incremental_update') as mock_incremental:
            # Update with same files
            file_pane.update_files(files)
            
            # Should use incremental update
            mock_incremental.assert_called_once()
    
    def test_full_update_on_file_count_change(self, file_pane, tmp_path):
        """Test full update when file count changes."""
        # Create initial files
        files1 = [tmp_path / f"file{i}.txt" for i in range(5)]
        for f in files1:
            f.touch()
        
        file_pane.update_files(files1)
        
        # Create different number of files
        files2 = [tmp_path / f"file{i}.txt" for i in range(7)]
        for f in files2:
            f.touch()
        
        # Mock _full_update to verify it's called
        with patch.object(file_pane, '_full_update') as mock_full:
            file_pane.update_files(files2)
            
            # Should use full update
            mock_full.assert_called_once()
    
    def test_force_full_update(self, file_pane, tmp_path):
        """Test forcing full update even when incremental is possible."""
        # Create test files
        files = [tmp_path / f"file{i}.txt" for i in range(5)]
        for f in files:
            f.touch()
        
        file_pane.update_files(files)
        
        # Mock _full_update to verify it's called
        with patch.object(file_pane, '_full_update') as mock_full:
            # Force full update
            file_pane.update_files(files, force_full_update=True)
            
            # Should use full update
            mock_full.assert_called_once()
    
    def test_incremental_update_detects_changes(self, file_pane, tmp_path):
        """Test that incremental update detects file changes."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("initial")
        
        files = [test_file]
        file_pane.update_files(files)
        
        # Modify file
        time.sleep(0.01)  # Ensure mtime changes
        test_file.write_text("modified")
        
        # Mock _update_row to verify it's called
        with patch.object(file_pane, '_update_row') as mock_update_row:
            file_pane.update_files(files)
            
            # Should update the changed row
            mock_update_row.assert_called()
    
    def test_updates_disabled_during_full_update(self, file_pane, tmp_path):
        """Test that table updates are disabled during full rebuild."""
        # Create test files
        files = [tmp_path / f"file{i}.txt" for i in range(10)]
        for f in files:
            f.touch()
        
        # Track setUpdatesEnabled calls
        calls = []
        original_set_updates = file_pane.table.setUpdatesEnabled
        
        def track_updates(enabled):
            calls.append(enabled)
            original_set_updates(enabled)
        
        file_pane.table.setUpdatesEnabled = track_updates
        
        # Perform full update
        file_pane._full_update(files)
        
        # Should disable then re-enable updates
        assert calls == [False, True]


class TestProgressUpdateThrottling:
    """Test progress update throttling optimization."""
    
    def test_initial_update_not_throttled(self, progress_dialog):
        """Test that first update is not throttled."""
        progress_dialog.update_progress(1, 100, "File 1")
        
        assert progress_dialog.progress_bar.value() == 1
        assert progress_dialog.message_label.text() == "File 1"
    
    def test_rapid_updates_are_throttled(self, progress_dialog):
        """Test that rapid updates are throttled."""
        # Set short throttle time for testing
        progress_dialog.throttle_ms = 50
        
        # First update
        progress_dialog.update_progress(1, 100, "File 1")
        assert progress_dialog.progress_bar.value() == 1
        
        # Immediate second update should be throttled
        progress_dialog.update_progress(2, 100, "File 2")
        
        # Should still show first update (throttled)
        assert progress_dialog.progress_bar.value() == 1
        
        # Pending update should be stored
        assert progress_dialog._pending_update == (2, 100, "File 2")
    
    def test_updates_after_throttle_period(self, progress_dialog):
        """Test that updates work after throttle period."""
        # Set short throttle time for testing
        progress_dialog.throttle_ms = 50
        
        # First update
        progress_dialog.update_progress(1, 100, "File 1")
        
        # Wait for throttle period
        time.sleep(0.06)
        
        # Second update should go through
        progress_dialog.update_progress(2, 100, "File 2")
        assert progress_dialog.progress_bar.value() == 2
        assert progress_dialog.message_label.text() == "File 2"
    
    def test_force_update_bypasses_throttle(self, progress_dialog):
        """Test that forced updates bypass throttling."""
        # Set short throttle time for testing
        progress_dialog.throttle_ms = 50
        
        # First update
        progress_dialog.update_progress(1, 100, "File 1")
        
        # Immediate forced update should go through
        progress_dialog.update_progress(2, 100, "File 2", force=True)
        assert progress_dialog.progress_bar.value() == 2
        assert progress_dialog.message_label.text() == "File 2"
    
    def test_completion_update_not_throttled(self, progress_dialog):
        """Test that completion update is never throttled."""
        # Set short throttle time for testing
        progress_dialog.throttle_ms = 50
        
        # First update
        progress_dialog.update_progress(1, 100, "File 1")
        
        # Immediate completion update should go through
        progress_dialog.update_progress(100, 100, "Complete")
        assert progress_dialog.progress_bar.value() == 100
        assert progress_dialog.message_label.text() == "Complete"
    
    def test_flush_pending_update(self, progress_dialog):
        """Test flushing pending throttled updates."""
        # Set short throttle time for testing
        progress_dialog.throttle_ms = 50
        
        # First update
        progress_dialog.update_progress(1, 100, "File 1")
        
        # Immediate second update (throttled)
        progress_dialog.update_progress(2, 100, "File 2")
        assert progress_dialog._pending_update is not None
        
        # Flush pending update
        progress_dialog.flush_pending_update()
        
        # Should apply pending update
        assert progress_dialog.progress_bar.value() == 2
        assert progress_dialog.message_label.text() == "File 2"
        assert progress_dialog._pending_update is None
    
    def test_auto_close_flushes_pending(self, progress_dialog):
        """Test that auto_close flushes pending updates."""
        # Set short throttle time for testing
        progress_dialog.throttle_ms = 50
        
        # First update
        progress_dialog.update_progress(1, 100, "File 1")
        
        # Immediate second update (throttled)
        progress_dialog.update_progress(2, 100, "File 2")
        
        # Mock flush_pending_update to verify it's called
        with patch.object(progress_dialog, 'flush_pending_update') as mock_flush:
            # Mock accept to prevent actual dialog close
            with patch.object(progress_dialog, 'accept'):
                progress_dialog.auto_close()
            
            # Should flush pending updates
            mock_flush.assert_called_once()
    
    def test_throttle_with_zero_total(self, progress_dialog):
        """Test throttling with indeterminate progress (total=0)."""
        # Set short throttle time for testing
        progress_dialog.throttle_ms = 50
        
        # Update with zero total (indeterminate)
        progress_dialog.update_progress(0, 0, "Processing...")
        
        # Should set indeterminate mode
        assert progress_dialog.progress_bar.maximum() == 0
    
    def test_multiple_throttled_updates(self, progress_dialog):
        """Test that only the last throttled update is kept."""
        # Set short throttle time for testing
        progress_dialog.throttle_ms = 50
        
        # First update
        progress_dialog.update_progress(1, 100, "File 1")
        
        # Multiple rapid updates (all throttled)
        progress_dialog.update_progress(2, 100, "File 2")
        progress_dialog.update_progress(3, 100, "File 3")
        progress_dialog.update_progress(4, 100, "File 4")
        
        # Only last update should be pending
        assert progress_dialog._pending_update == (4, 100, "File 4")
        
        # Flush should apply last update
        progress_dialog.flush_pending_update()
        assert progress_dialog.progress_bar.value() == 4
        assert progress_dialog.message_label.text() == "File 4"


class TestPerformanceImprovements:
    """Test overall performance improvements."""
    
    def test_large_directory_update_performance(self, file_pane, tmp_path):
        """Test that large directory updates are reasonably fast."""
        # Create many files
        files = [tmp_path / f"file{i:04d}.txt" for i in range(1000)]
        for f in files:
            f.touch()
        
        # Measure update time
        start = time.time()
        file_pane.update_files(files)
        duration = time.time() - start
        
        # Should complete in reasonable time (< 2 seconds for 1000 files)
        assert duration < 2.0
        assert file_pane.table.rowCount() == 1000
    
    def test_incremental_update_faster_than_full(self, file_pane, tmp_path):
        """Test that incremental updates are faster than full updates."""
        # Create test files
        files = [tmp_path / f"file{i:03d}.txt" for i in range(500)]
        for f in files:
            f.touch()
        
        # Initial full update
        file_pane.update_files(files)
        
        # Measure full update time
        start = time.time()
        file_pane.update_files(files, force_full_update=True)
        full_duration = time.time() - start
        
        # Measure incremental update time
        start = time.time()
        file_pane.update_files(files)
        incremental_duration = time.time() - start
        
        # Incremental should be faster (or at least not slower)
        # Allow some margin for timing variations
        assert incremental_duration <= full_duration * 1.5
    
    def test_progress_throttling_reduces_updates(self, progress_dialog):
        """Test that throttling reduces number of UI updates."""
        # Set throttle time
        progress_dialog.throttle_ms = 50
        
        # Track actual UI updates
        update_count = 0
        original_apply = progress_dialog._apply_update
        
        def count_updates(*args, **kwargs):
            nonlocal update_count
            update_count += 1
            original_apply(*args, **kwargs)
        
        progress_dialog._apply_update = count_updates
        
        # Perform many rapid updates
        for i in range(100):
            progress_dialog.update_progress(i, 100, f"File {i}")
        
        # Should have significantly fewer actual updates than requested
        # (100 updates with 50ms throttle should result in ~20 actual updates)
        assert update_count < 50
