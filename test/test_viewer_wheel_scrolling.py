"""
Tests for mouse wheel scrolling in viewers (TextViewer, DiffViewer, DirectoryDiffViewer).

Run with: PYTHONPATH=.:src:ttk pytest test/test_viewer_wheel_scrolling.py -v
"""

import os
import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton


class TestTextViewerWheelScrolling(unittest.TestCase):
    """Test mouse wheel scrolling in TextViewer"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (40, 120)
        self.mock_renderer.draw_text = Mock()
        self.mock_renderer.clear = Mock()
        
        # Import and create TextViewer
        from tfm_text_viewer import TextViewer
        
        # Create a temporary test file with content
        self.test_file = Path("/tmp/test_viewer_scroll.txt")
        test_content = "\n".join([f"Line {i}" for i in range(100)])
        self.test_file.write_text(test_content)
        
        self.viewer = TextViewer(self.mock_renderer, self.test_file)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_file.exists():
            self.test_file.unlink()
    
    def test_wheel_scroll_up(self):
        """Test scrolling up in text viewer"""
        # Set initial scroll offset
        self.viewer.scroll_offset = 10
        
        # Create wheel event (scroll up)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=10,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0  # Positive = scroll up
        )
        
        initial_offset = self.viewer.scroll_offset
        
        # Handle the event
        result = self.viewer.handle_mouse_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify scroll offset decreased (scrolled up)
        self.assertEqual(self.viewer.scroll_offset, initial_offset - 3)
    
    def test_wheel_scroll_down(self):
        """Test scrolling down in text viewer"""
        # Set initial scroll offset
        self.viewer.scroll_offset = 10
        
        # Create wheel event (scroll down)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=10,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-3.0  # Negative = scroll down
        )
        
        initial_offset = self.viewer.scroll_offset
        
        # Handle the event
        result = self.viewer.handle_mouse_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify scroll offset increased (scrolled down)
        self.assertEqual(self.viewer.scroll_offset, initial_offset + 3)
    
    def test_wheel_scroll_at_top_boundary(self):
        """Test that scrolling up at top doesn't go negative"""
        # Start at top
        self.viewer.scroll_offset = 0
        
        # Try to scroll up
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=10,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=5.0
        )
        
        self.viewer.handle_mouse_event(event)
        
        # Verify offset stayed at 0
        self.assertEqual(self.viewer.scroll_offset, 0)
    
    def test_wheel_scroll_marks_dirty(self):
        """Test that scrolling marks the viewer dirty"""
        self.viewer.scroll_offset = 10
        self.viewer._dirty = False
        
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=10,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=2.0
        )
        
        self.viewer.handle_mouse_event(event)
        
        # Verify viewer was marked dirty
        self.assertTrue(self.viewer._dirty)


class TestDiffViewerWheelScrolling(unittest.TestCase):
    """Test mouse wheel scrolling in DiffViewer"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (40, 120)
        self.mock_renderer.draw_text = Mock()
        self.mock_renderer.clear = Mock()
        
        # Import and create DiffViewer
        from tfm_diff_viewer import DiffViewer
        
        # Create temporary test files with content
        self.test_file1 = Path("/tmp/test_diff1.txt")
        self.test_file2 = Path("/tmp/test_diff2.txt")
        
        content1 = "\n".join([f"Line {i}" for i in range(50)])
        content2 = "\n".join([f"Line {i} modified" if i % 5 == 0 else f"Line {i}" for i in range(50)])
        
        self.test_file1.write_text(content1)
        self.test_file2.write_text(content2)
        
        self.viewer = DiffViewer(self.mock_renderer, self.test_file1, self.test_file2)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_file1.exists():
            self.test_file1.unlink()
        if self.test_file2.exists():
            self.test_file2.unlink()
    
    def test_wheel_scroll_up(self):
        """Test scrolling up in diff viewer"""
        self.viewer.scroll_offset = 10
        
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=10,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0
        )
        
        initial_offset = self.viewer.scroll_offset
        result = self.viewer.handle_mouse_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.viewer.scroll_offset, initial_offset - 3)
    
    def test_wheel_scroll_down(self):
        """Test scrolling down in diff viewer"""
        self.viewer.scroll_offset = 10
        
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=10,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-3.0
        )
        
        initial_offset = self.viewer.scroll_offset
        result = self.viewer.handle_mouse_event(event)
        
        self.assertTrue(result)
        # Verify scroll offset increased (may be clamped by max_scroll)
        self.assertGreaterEqual(self.viewer.scroll_offset, initial_offset)
    
    def test_wheel_scroll_marks_dirty(self):
        """Test that scrolling marks the viewer dirty"""
        self.viewer.scroll_offset = 10
        self.viewer._dirty = False
        
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=10,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=2.0
        )
        
        self.viewer.handle_mouse_event(event)
        self.assertTrue(self.viewer._dirty)


class TestDirectoryDiffViewerWheelScrolling(unittest.TestCase):
    """Test mouse wheel scrolling in DirectoryDiffViewer"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (40, 120)
        self.mock_renderer.draw_text = Mock()
        self.mock_renderer.clear = Mock()
        
        # Import and create DirectoryDiffViewer
        from tfm_directory_diff_viewer import DirectoryDiffViewer
        from tfm_path import Path as TfmPath
        
        # Create temporary test directories
        import tempfile
        import os
        
        self.temp_dir = tempfile.mkdtemp()
        self.dir1 = os.path.join(self.temp_dir, "dir1")
        self.dir2 = os.path.join(self.temp_dir, "dir2")
        
        os.makedirs(self.dir1)
        os.makedirs(self.dir2)
        
        # Create some test files
        for i in range(20):
            Path(os.path.join(self.dir1, f"file{i}.txt")).write_text(f"Content {i}")
            Path(os.path.join(self.dir2, f"file{i}.txt")).write_text(f"Content {i}")
        
        # Create viewer
        self.viewer = DirectoryDiffViewer(
            self.mock_renderer,
            TfmPath(self.dir1),
            TfmPath(self.dir2)
        )
        
        # Populate visible_nodes for testing
        self.viewer.visible_nodes = [f"node_{i}" for i in range(50)]
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        import os
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_wheel_scroll_up(self):
        """Test scrolling up in directory diff viewer"""
        self.viewer.scroll_offset = 10
        
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=10,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0
        )
        
        initial_offset = self.viewer.scroll_offset
        result = self.viewer.handle_mouse_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.viewer.scroll_offset, initial_offset - 3)
    
    def test_wheel_scroll_down(self):
        """Test scrolling down in directory diff viewer"""
        self.viewer.scroll_offset = 10
        
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=10,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-3.0
        )
        
        initial_offset = self.viewer.scroll_offset
        result = self.viewer.handle_mouse_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.viewer.scroll_offset, initial_offset + 3)
    
    def test_wheel_scroll_marks_dirty(self):
        """Test that scrolling marks the viewer dirty"""
        self.viewer.scroll_offset = 10
        self.viewer._dirty = False
        
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=10,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=2.0
        )
        
        self.viewer.handle_mouse_event(event)
        self.assertTrue(self.viewer._dirty)
