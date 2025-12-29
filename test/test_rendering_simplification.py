"""
Test that rendering methods have been simplified to use UILayerStack.

This test verifies that the old if-elif chains for dialog rendering have been
removed and replaced with UILayerStack delegation.

Run with: PYTHONPATH=.:src:ttk pytest test/test_rendering_simplification.py -v
"""

import pytest
import inspect
from src.tfm_main import FileManager


class TestRenderingSimplification:
    """Test that rendering methods have been simplified"""
    
    def test_check_dialog_content_changed_removed(self):
        """Verify _check_dialog_content_changed method has been removed"""
        assert not hasattr(FileManager, '_check_dialog_content_changed'), \
            "_check_dialog_content_changed should be removed (dead code)"
    
    def test_draw_dialogs_if_needed_removed(self):
        """Verify _draw_dialogs_if_needed method has been removed"""
        assert not hasattr(FileManager, '_draw_dialogs_if_needed'), \
            "_draw_dialogs_if_needed should be removed (dead code)"
    
    def test_force_immediate_redraw_simplified(self):
        """Verify _force_immediate_redraw has been simplified"""
        # Get the method source code
        source = inspect.getsource(FileManager._force_immediate_redraw)
        
        # Should not contain if-elif chains for dialogs
        assert 'if self.list_dialog.is_active:' not in source, \
            "_force_immediate_redraw should not have if-elif chains for dialogs"
        assert 'elif self.info_dialog.is_active:' not in source, \
            "_force_immediate_redraw should not have if-elif chains for dialogs"
        assert 'elif self.search_dialog.is_active:' not in source, \
            "_force_immediate_redraw should not have if-elif chains for dialogs"
        
        # Should delegate to ui_layer_stack
        assert 'ui_layer_stack.render' in source, \
            "_force_immediate_redraw should delegate to ui_layer_stack.render()"
    
    def test_draw_interface_delegates_to_layer_stack(self):
        """Verify draw_interface delegates to UILayerStack"""
        source = inspect.getsource(FileManager.draw_interface)
        
        # Should delegate to ui_layer_stack
        assert 'ui_layer_stack.render' in source, \
            "draw_interface should delegate to ui_layer_stack.render()"
        
        # Should not have complex rendering logic
        assert 'if self.list_dialog.is_active:' not in source, \
            "draw_interface should not have dialog-specific rendering logic"
    
    def test_needs_dialog_redraw_flag_removed(self):
        """Verify needs_dialog_redraw flag has been removed from initialization"""
        source = inspect.getsource(FileManager.__init__)
        
        # Should not initialize needs_dialog_redraw flag
        assert 'needs_dialog_redraw' not in source, \
            "needs_dialog_redraw flag should be removed (replaced by layer dirty tracking)"

