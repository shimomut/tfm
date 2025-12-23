"""
Tests for DirectoryDiffViewer class.

This module tests the DirectoryDiffViewer UILayer implementation,
including initialization, UILayer interface methods, and scanning.
"""

import unittest
import tempfile
import os
from pathlib import Path as StdPath
from src.tfm_directory_diff_viewer import DirectoryDiffViewer, DifferenceType
from src.tfm_path import Path


class MockRenderer:
    """Mock renderer for testing."""
    
    def __init__(self, width=80, height=24):
        self.width = width
        self.height = height
        self.drawn_text = []
    
    def get_size(self):
        return self.width, self.height
    
    def clear(self):
        self.drawn_text = []
    
    def draw_text(self, x, y, text, color=None, attrs=None):
        self.drawn_text.append((x, y, text))


class TestDirectoryDiffViewerInit(unittest.TestCase):
    """Test DirectoryDiffViewer initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.renderer = MockRenderer()
        
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.left_dir = StdPath(self.temp_dir) / "left"
        self.right_dir = StdPath(self.temp_dir) / "right"
        self.left_dir.mkdir()
        self.right_dir.mkdir()
        
        # Create some test files
        (self.left_dir / "file1.txt").write_text("content1")
        (self.right_dir / "file1.txt").write_text("content1")
        (self.left_dir / "file2.txt").write_text("content2")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init_creates_viewer(self):
        """Test that DirectoryDiffViewer can be initialized."""
        left_path = Path(str(self.left_dir))
        right_path = Path(str(self.right_dir))
        
        viewer = DirectoryDiffViewer(self.renderer, left_path, right_path)
        
        # Verify basic initialization
        self.assertIsNotNone(viewer)
        self.assertEqual(viewer.left_path, left_path)
        self.assertEqual(viewer.right_path, right_path)
        self.assertTrue(viewer.scan_in_progress)
        self.assertFalse(viewer._should_close)
        self.assertTrue(viewer._dirty)
    
    def test_is_full_screen(self):
        """Test that viewer reports as full-screen."""
        left_path = Path(str(self.left_dir))
        right_path = Path(str(self.right_dir))
        
        viewer = DirectoryDiffViewer(self.renderer, left_path, right_path)
        
        self.assertTrue(viewer.is_full_screen())
    
    def test_needs_redraw_initially_true(self):
        """Test that viewer initially needs redraw."""
        left_path = Path(str(self.left_dir))
        right_path = Path(str(self.right_dir))
        
        viewer = DirectoryDiffViewer(self.renderer, left_path, right_path)
        
        self.assertTrue(viewer.needs_redraw())
    
    def test_mark_dirty_and_clear_dirty(self):
        """Test dirty flag management."""
        left_path = Path(str(self.left_dir))
        right_path = Path(str(self.right_dir))
        
        viewer = DirectoryDiffViewer(self.renderer, left_path, right_path)
        
        # Clear dirty
        viewer.clear_dirty()
        self.assertFalse(viewer.needs_redraw())
        
        # Mark dirty
        viewer.mark_dirty()
        self.assertTrue(viewer.needs_redraw())
    
    def test_should_close_initially_false(self):
        """Test that viewer doesn't want to close initially."""
        left_path = Path(str(self.left_dir))
        right_path = Path(str(self.right_dir))
        
        viewer = DirectoryDiffViewer(self.renderer, left_path, right_path)
        
        self.assertFalse(viewer.should_close())


class TestDirectoryDiffViewerEvents(unittest.TestCase):
    """Test DirectoryDiffViewer event handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.renderer = MockRenderer()
        
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.left_dir = StdPath(self.temp_dir) / "left"
        self.right_dir = StdPath(self.temp_dir) / "right"
        self.left_dir.mkdir()
        self.right_dir.mkdir()
        
        left_path = Path(str(self.left_dir))
        right_path = Path(str(self.right_dir))
        
        self.viewer = DirectoryDiffViewer(self.renderer, left_path, right_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_handle_key_event_escape_closes(self):
        """Test that ESC key sets should_close flag."""
        from ttk import KeyEvent, KeyCode, ModifierKey
        
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)  # Event consumed
        self.assertTrue(self.viewer.should_close())
    
    def test_handle_char_event_returns_false(self):
        """Test that char events are not handled yet."""
        from ttk import CharEvent
        
        event = CharEvent(char='a')
        result = self.viewer.handle_char_event(event)
        
        self.assertFalse(result)  # Event not consumed
    
    def test_handle_system_event_resize_marks_dirty(self):
        """Test that resize event marks viewer dirty."""
        from ttk import SystemEvent, SystemEventType
        
        # Clear dirty flag first
        self.viewer.clear_dirty()
        self.assertFalse(self.viewer.needs_redraw())
        
        # Send resize event
        event = SystemEvent(event_type=SystemEventType.RESIZE)
        result = self.viewer.handle_system_event(event)
        
        self.assertTrue(result)  # Event consumed
        self.assertTrue(self.viewer.needs_redraw())


class TestDirectoryDiffViewerRendering(unittest.TestCase):
    """Test DirectoryDiffViewer rendering."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.renderer = MockRenderer()
        
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.left_dir = StdPath(self.temp_dir) / "left"
        self.right_dir = StdPath(self.temp_dir) / "right"
        self.left_dir.mkdir()
        self.right_dir.mkdir()
        
        left_path = Path(str(self.left_dir))
        right_path = Path(str(self.right_dir))
        
        self.viewer = DirectoryDiffViewer(self.renderer, left_path, right_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_render_draws_header(self):
        """Test that render draws header with directory paths."""
        self.viewer.render(self.renderer)
        
        # Check that header was drawn
        drawn_texts = [text for x, y, text in self.renderer.drawn_text]
        header_found = any("Directory Diff" in text for text in drawn_texts)
        
        self.assertTrue(header_found)
    
    def test_render_shows_scanning_status(self):
        """Test that render shows scanning status when scan in progress."""
        self.viewer.scan_in_progress = True
        self.viewer.scan_status = "Scanning left directory..."
        
        self.viewer.render(self.renderer)
        
        # Check that scanning status was drawn
        drawn_texts = [text for x, y, text in self.renderer.drawn_text]
        status_found = any("Scanning..." in text for text in drawn_texts)
        
        self.assertTrue(status_found)
    
    def test_render_shows_help_text(self):
        """Test that render shows help text."""
        self.viewer.render(self.renderer)
        
        # Check that help text was drawn
        drawn_texts = [text for x, y, text in self.renderer.drawn_text]
        help_found = any("ESC" in text or "close" in text for text in drawn_texts)
        
        self.assertTrue(help_found)


class TestDirectoryDiffViewerLifecycle(unittest.TestCase):
    """Test DirectoryDiffViewer lifecycle methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.renderer = MockRenderer()
        
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.left_dir = StdPath(self.temp_dir) / "left"
        self.right_dir = StdPath(self.temp_dir) / "right"
        self.left_dir.mkdir()
        self.right_dir.mkdir()
        
        left_path = Path(str(self.left_dir))
        right_path = Path(str(self.right_dir))
        
        self.viewer = DirectoryDiffViewer(self.renderer, left_path, right_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_on_activate_marks_dirty(self):
        """Test that on_activate marks viewer dirty."""
        self.viewer.clear_dirty()
        self.assertFalse(self.viewer.needs_redraw())
        
        self.viewer.on_activate()
        
        self.assertTrue(self.viewer.needs_redraw())
    
    def test_on_deactivate_cancels_scan(self):
        """Test that on_deactivate cancels ongoing scan."""
        # Ensure scan is in progress
        self.viewer.scan_in_progress = True
        
        self.viewer.on_deactivate()
        
        # Scanner should be cancelled (if it exists)
        if self.viewer.scanner:
            self.assertTrue(self.viewer.scanner._cancel_flag)


if __name__ == '__main__':
    unittest.main()
