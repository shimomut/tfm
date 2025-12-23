"""
Test progress feedback during directory scanning.

This test verifies that progress indicators are displayed correctly
and that scan cancellation works properly.
"""

import unittest
import tempfile
import os
from pathlib import Path as StdPath
from unittest.mock import Mock, MagicMock
from src.tfm_directory_diff_viewer import DirectoryDiffViewer, DirectoryScanner
from tfm_path import Path


class TestProgressFeedback(unittest.TestCase):
    """Test progress feedback and cancellation during scanning."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock renderer
        self.renderer = Mock()
        self.renderer.get_size.return_value = (80, 24)
        self.renderer.clear = Mock()
        self.renderer.draw_text = Mock()
        
        # Create temporary test directories
        self.temp_dir = tempfile.mkdtemp(prefix='tfm_test_progress_')
        self.left_dir = StdPath(self.temp_dir) / 'left'
        self.right_dir = StdPath(self.temp_dir) / 'right'
        self.left_dir.mkdir()
        self.right_dir.mkdir()
        
        # Create some test files
        for i in range(5):
            (self.left_dir / f'file{i}.txt').write_text(f'content {i}')
            (self.right_dir / f'file{i}.txt').write_text(f'content {i}')
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if StdPath(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_progress_callback_updates_state(self):
        """Test that progress callback updates viewer state correctly."""
        # Create viewer
        viewer = DirectoryDiffViewer(
            self.renderer,
            Path(str(self.left_dir)),
            Path(str(self.right_dir))
        )
        
        # Wait a moment for scan to start
        import time
        time.sleep(0.1)
        
        # Simulate progress callback
        viewer._on_scan_progress(5, 10, "Scanning left directory...")
        
        # Verify state was updated
        self.assertEqual(viewer.scan_current, 5)
        self.assertEqual(viewer.scan_total, 10)
        self.assertEqual(viewer.scan_status, "Scanning left directory...")
        self.assertEqual(viewer.scan_progress, 0.5)
        self.assertTrue(viewer.needs_redraw())
    
    def test_progress_callback_with_zero_total(self):
        """Test progress callback with indeterminate progress (total=0)."""
        viewer = DirectoryDiffViewer(
            self.renderer,
            Path(str(self.left_dir)),
            Path(str(self.right_dir))
        )
        
        # Simulate indeterminate progress
        viewer._on_scan_progress(5, 0, "Scanning...")
        
        # Verify state
        self.assertEqual(viewer.scan_current, 5)
        self.assertEqual(viewer.scan_total, 0)
        self.assertEqual(viewer.scan_progress, 0.0)
    
    def test_progress_screen_rendering(self):
        """Test that progress screen is rendered during scan."""
        viewer = DirectoryDiffViewer(
            self.renderer,
            Path(str(self.left_dir)),
            Path(str(self.right_dir))
        )
        
        # Set scan state
        viewer.scan_in_progress = True
        viewer.scan_progress = 0.5
        viewer.scan_current = 5
        viewer.scan_total = 10
        viewer.scan_status = "Scanning left directory..."
        
        # Render
        viewer.render(self.renderer)
        
        # Verify progress screen was rendered
        # Check that draw_text was called with progress information
        calls = self.renderer.draw_text.call_args_list
        
        # Should have header
        header_found = any("Scanning" in str(call) for call in calls)
        self.assertTrue(header_found, "Progress screen should show scanning header")
        
        # Should have progress information
        progress_found = any("Progress:" in str(call) or "items" in str(call) for call in calls)
        self.assertTrue(progress_found, "Progress screen should show progress information")
    
    def test_cancellation_screen_rendering(self):
        """Test that cancellation screen is rendered when cancelling."""
        viewer = DirectoryDiffViewer(
            self.renderer,
            Path(str(self.left_dir)),
            Path(str(self.right_dir))
        )
        
        # Set cancellation state
        viewer.scan_in_progress = True
        viewer.scan_cancelled = True
        viewer.scan_current = 5
        viewer.scan_status = "Cancelling scan..."
        
        # Render
        viewer.render(self.renderer)
        
        # Verify cancellation screen was rendered
        calls = self.renderer.draw_text.call_args_list
        
        # Should have cancellation header
        cancel_found = any("Cancelling" in str(call) for call in calls)
        self.assertTrue(cancel_found, "Cancellation screen should show cancelling header")
    
    def test_scan_cancellation_sets_flag(self):
        """Test that ESC during scan sets cancellation flag."""
        viewer = DirectoryDiffViewer(
            self.renderer,
            Path(str(self.left_dir)),
            Path(str(self.right_dir))
        )
        
        # Set scan in progress
        viewer.scan_in_progress = True
        viewer.scanner = Mock()
        viewer.scanner.cancel = Mock()
        
        # Create ESC key event
        from ttk import KeyEvent, KeyCode
        esc_event = KeyEvent(key_code=KeyCode.ESCAPE, char='', modifiers=set())
        
        # Handle event
        result = viewer.handle_key_event(esc_event)
        
        # Verify cancellation was triggered
        self.assertTrue(result, "ESC should be consumed during scan")
        self.assertTrue(viewer.scan_cancelled, "Cancellation flag should be set")
        viewer.scanner.cancel.assert_called_once()
        self.assertTrue(viewer.should_close(), "Viewer should be marked for closing")
    
    def test_directory_scanner_cancellation(self):
        """Test that DirectoryScanner respects cancellation flag."""
        # Create scanner
        scanner = DirectoryScanner(
            Path(str(self.left_dir)),
            Path(str(self.right_dir)),
            lambda c, t, s: None  # No-op progress callback
        )
        
        # Cancel immediately
        scanner.cancel()
        
        # Scan should return empty results
        left_files, right_files = scanner.scan()
        
        # Verify scan was cancelled (returns empty dicts)
        self.assertEqual(len(left_files), 0)
        self.assertEqual(len(right_files), 0)


if __name__ == '__main__':
    unittest.main()
