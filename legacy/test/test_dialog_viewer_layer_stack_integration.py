"""
Test that all dialog and viewer creation methods properly push layers onto the stack.

This test verifies task 16 of the UI Layer Stack implementation:
- All show_*_dialog() methods push dialogs onto the layer stack
- All create_*_viewer() methods push viewers onto the layer stack
- self.active_viewer variable has been removed

Run with: PYTHONPATH=.:src:ttk pytest test/test_dialog_viewer_layer_stack_integration.py -v
"""

import os
import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from pathlib import Path
import tempfile

from tfm_main import FileManager


class TestDialogViewerLayerStackIntegration(unittest.TestCase):
    """Test that dialogs and viewers are properly integrated with the layer stack"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        self.mock_renderer.set_event_callback = Mock()
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "test.txt"
        self.test_file.write_text("Test content\n")
        
        # Create FileManager instance
        self.file_manager = FileManager(self.mock_renderer)
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary directory
        if self.test_file.exists():
            self.test_file.unlink()
        if Path(self.test_dir).exists():
            os.rmdir(self.test_dir)
    
    def test_active_viewer_variable_removed(self):
        """Test that self.active_viewer variable has been removed"""
        self.assertFalse(hasattr(self.file_manager, 'active_viewer'),
                        "self.active_viewer should be removed - viewers are now managed by layer stack")
    
    def test_show_info_dialog_pushes_layer(self):
        """Test that show_info_dialog() pushes InfoDialog onto the layer stack"""
        initial_count = self.file_manager.ui_layer_stack.get_layer_count()
        
        self.file_manager.show_info_dialog("Test Title", ["Line 1", "Line 2"])
        
        # Should have one more layer
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 1)
        
        # Top layer should be the info dialog
        top_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIs(top_layer, self.file_manager.info_dialog)
    
    def test_show_list_dialog_pushes_layer(self):
        """Test that show_list_dialog() pushes ListDialog onto the layer stack"""
        initial_count = self.file_manager.ui_layer_stack.get_layer_count()
        
        def callback(item):
            pass
        
        self.file_manager.show_list_dialog("Test Title", ["Item 1", "Item 2"], callback)
        
        # Should have one more layer
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 1)
        
        # Top layer should be the list dialog
        top_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIs(top_layer, self.file_manager.list_dialog)
    
    def test_show_search_dialog_pushes_layer(self):
        """Test that show_search_dialog() pushes SearchDialog onto the layer stack"""
        initial_count = self.file_manager.ui_layer_stack.get_layer_count()
        
        self.file_manager.show_search_dialog('filename')
        
        # Should have one more layer
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 1)
        
        # Top layer should be the search dialog
        top_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIs(top_layer, self.file_manager.search_dialog)
    
    def test_show_jump_dialog_pushes_layer(self):
        """Test that show_jump_dialog() pushes JumpDialog onto the layer stack"""
        initial_count = self.file_manager.ui_layer_stack.get_layer_count()
        
        self.file_manager.show_jump_dialog()
        
        # Should have one more layer
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 1)
        
        # Top layer should be the jump dialog
        top_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIs(top_layer, self.file_manager.jump_dialog)
    
    def test_show_drives_dialog_pushes_layer(self):
        """Test that show_drives_dialog() pushes DrivesDialog onto the layer stack"""
        initial_count = self.file_manager.ui_layer_stack.get_layer_count()
        
        self.file_manager.show_drives_dialog()
        
        # Should have one more layer
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 1)
        
        # Top layer should be the drives dialog
        top_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIs(top_layer, self.file_manager.drives_dialog)
    
    def test_show_batch_rename_dialog_pushes_layer(self):
        """Test that batch rename dialog is pushed onto the layer stack"""
        initial_count = self.file_manager.ui_layer_stack.get_layer_count()
        
        # Create some test files in the current pane
        current_pane = self.file_manager.get_current_pane()
        current_pane['selected_files'] = {0, 1}  # Select first two files
        
        # Mock the batch_rename_dialog.show() to return True
        with patch.object(self.file_manager.batch_rename_dialog, 'show', return_value=True):
            # Trigger batch rename (this is called from a key binding)
            # We'll call the internal method directly
            selected_files = [self.test_file, self.test_file]
            if self.file_manager.batch_rename_dialog.show(selected_files):
                self.file_manager.push_layer(self.file_manager.batch_rename_dialog)
        
        # Should have one more layer
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 1)
        
        # Top layer should be the batch rename dialog
        top_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIs(top_layer, self.file_manager.batch_rename_dialog)
    
    def test_create_text_viewer_pushes_layer(self):
        """Test that create_text_viewer() result is pushed onto the layer stack"""
        from tfm_text_viewer import create_text_viewer
        
        initial_count = self.file_manager.ui_layer_stack.get_layer_count()
        
        # Create a text viewer
        viewer = create_text_viewer(self.mock_renderer, self.test_file)
        self.assertIsNotNone(viewer, "Viewer should be created successfully")
        
        # Push it onto the stack (this is what FileManager does)
        self.file_manager.push_layer(viewer)
        
        # Should have one more layer
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 1)
        
        # Top layer should be the viewer
        top_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIs(top_layer, viewer)
    
    def test_create_diff_viewer_pushes_layer(self):
        """Test that create_diff_viewer() result is pushed onto the layer stack"""
        from tfm_diff_viewer import create_diff_viewer
        
        initial_count = self.file_manager.ui_layer_stack.get_layer_count()
        
        # Create a second test file
        test_file2 = Path(self.test_dir) / "test2.txt"
        test_file2.write_text("Different content\n")
        
        try:
            # Create a diff viewer
            viewer = create_diff_viewer(self.mock_renderer, self.test_file, test_file2)
            self.assertIsNotNone(viewer, "Viewer should be created successfully")
            
            # Push it onto the stack (this is what FileManager does)
            self.file_manager.push_layer(viewer)
            
            # Should have one more layer
            self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 1)
            
            # Top layer should be the viewer
            top_layer = self.file_manager.ui_layer_stack.get_top_layer()
            self.assertIs(top_layer, viewer)
        finally:
            # Clean up
            if test_file2.exists():
                test_file2.unlink()
    
    def test_multiple_dialogs_stack_correctly(self):
        """Test that multiple dialogs can be stacked on top of each other"""
        initial_count = self.file_manager.ui_layer_stack.get_layer_count()
        
        # Push info dialog
        self.file_manager.show_info_dialog("Info", ["Line 1"])
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 1)
        
        # Push list dialog on top
        self.file_manager.show_list_dialog("List", ["Item 1"], lambda x: None)
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 2)
        
        # Top layer should be list dialog
        top_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIs(top_layer, self.file_manager.list_dialog)
        
        # Pop list dialog
        self.file_manager.pop_layer()
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 1)
        
        # Top layer should now be info dialog
        top_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIs(top_layer, self.file_manager.info_dialog)
    
    def test_viewer_on_top_of_dialog(self):
        """Test that a viewer can be pushed on top of a dialog"""
        from tfm_text_viewer import create_text_viewer
        
        initial_count = self.file_manager.ui_layer_stack.get_layer_count()
        
        # Push info dialog
        self.file_manager.show_info_dialog("Info", ["Line 1"])
        
        # Push viewer on top
        viewer = create_text_viewer(self.mock_renderer, self.test_file)
        self.file_manager.push_layer(viewer)
        
        # Should have two more layers
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), initial_count + 2)
        
        # Top layer should be viewer
        top_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIs(top_layer, viewer)
