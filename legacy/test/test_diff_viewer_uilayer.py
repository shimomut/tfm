"""
Test suite for DiffViewer UILayer interface implementation

Run with: PYTHONPATH=.:src:ttk pytest test/test_diff_viewer_uilayer.py -v
"""

import unittest
from unittest.mock import Mock
from pathlib import Path as StdPath

from tfm_path import Path
from tfm_diff_viewer import DiffViewer
from tfm_ui_layer import UILayer
from ttk import KeyEvent, KeyCode, CharEvent


class TestDiffViewerUILayer(unittest.TestCase):
    """Test cases for DiffViewer UILayer interface implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        self.mock_renderer.set_cursor_visibility = Mock()
        
        # Create temporary test files
        self.test_dir = StdPath(__file__).parent / 'temp_diff_uilayer_test'
        self.test_dir.mkdir(exist_ok=True)
        
        self.file1_path = self.test_dir / 'file1.txt'
        self.file2_path = self.test_dir / 'file2.txt'
        
        # Write test content
        self.file1_content = "Line 1\nLine 2\nLine 3\n"
        self.file2_content = "Line 1\nLine 2 modified\nLine 3\n"
        
        self.file1_path.write_text(self.file1_content)
        self.file2_path.write_text(self.file2_content)
    
    def tearDown(self):
        """Clean up test files"""
        if self.test_dir.exists():
            for file in self.test_dir.iterdir():
                file.unlink()
            self.test_dir.rmdir()
    
    def test_diff_viewer_inherits_from_uilayer(self):
        """Test that DiffViewer inherits from UILayer"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        self.assertIsInstance(viewer, UILayer)
    
    def test_handle_key_event(self):
        """Test handle_key_event method"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Test that KeyEvent is handled
        event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0, char='')
        result = viewer.handle_key_event(event)
        self.assertTrue(result)
        
        # Test that dirty flag is set when event is consumed
        viewer._dirty = False
        event = KeyEvent(key_code=KeyCode.UP, modifiers=0, char='')
        viewer.handle_key_event(event)
        self.assertTrue(viewer._dirty)
    
    def test_handle_char_event(self):
        """Test handle_char_event method"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # DiffViewer should not handle CharEvents
        event = CharEvent(char='a')
        result = viewer.handle_char_event(event)
        self.assertFalse(result)
    
    def test_render(self):
        """Test render method"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Should call draw method without errors
        viewer.render(self.mock_renderer)
        
        # Verify renderer was used
        self.assertTrue(self.mock_renderer.draw_text.called)
    
    def test_is_full_screen(self):
        """Test is_full_screen method"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # DiffViewer is always full-screen
        self.assertTrue(viewer.is_full_screen())
    
    def test_needs_redraw(self):
        """Test needs_redraw method"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Initially dirty (starts as True)
        self.assertTrue(viewer.needs_redraw())
        
        # Clear dirty flag
        viewer._dirty = False
        self.assertFalse(viewer.needs_redraw())
    
    def test_mark_dirty(self):
        """Test mark_dirty method"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        viewer._dirty = False
        viewer.mark_dirty()
        self.assertTrue(viewer._dirty)
    
    def test_clear_dirty(self):
        """Test clear_dirty method"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        viewer._dirty = True
        viewer.clear_dirty()
        self.assertFalse(viewer._dirty)
    
    def test_should_close(self):
        """Test should_close method"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Initially should not close
        self.assertFalse(viewer.should_close())
        
        # After ESCAPE key, should close
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=0, char='')
        viewer.handle_key_event(event)
        self.assertTrue(viewer.should_close())
    
    def test_on_activate(self):
        """Test on_activate method"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Clear dirty flag first
        viewer._dirty = False
        
        # Call on_activate
        viewer.on_activate()
        
        # Should hide cursor
        self.mock_renderer.set_cursor_visibility.assert_called_with(False)
        
        # Should mark dirty
        self.assertTrue(viewer._dirty)
    
    def test_on_deactivate(self):
        """Test on_deactivate method"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Should not raise any errors
        viewer.on_deactivate()
    
    def test_dirty_tracking_on_scroll(self):
        """Test that scrolling marks layer as dirty"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Clear dirty flag
        viewer._dirty = False
        
        # Scroll down
        event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0, char='')
        viewer.handle_key_event(event)
        
        # Should be marked dirty
        self.assertTrue(viewer._dirty)
    
    def test_dirty_tracking_on_toggle(self):
        """Test that toggling options marks layer as dirty"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Clear dirty flag
        viewer._dirty = False
        
        # Toggle line numbers with 'n' key
        event = KeyEvent(key_code=None, modifiers=0, char='n')
        viewer.handle_key_event(event)
        
        # Should be marked dirty
        self.assertTrue(viewer._dirty)
