#!/usr/bin/env python3
"""
Test for dialog redraw fix - ensures dialogs remain visible after main screen redraws
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_main import FileManager

class TestDialogRedrawFix(unittest.TestCase):
    """Test that dialogs are properly redrawn after main screen updates"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock curses and stdscr
        self.mock_stdscr = Mock()
        self.mock_stdscr.getmaxyx.return_value = (24, 80)
        self.mock_stdscr.getch.return_value = -1  # Timeout
        
        # Mock all the required components
        with patch('tfm_main.get_config'), \
             patch('tfm_main.init_colors'), \
             patch('tfm_main.LogManager'), \
             patch('tfm_main.get_state_manager'), \
             patch('tfm_main.PaneManager'), \
             patch('tfm_main.FileOperations'), \
             patch('tfm_main.ListDialog'), \
             patch('tfm_main.InfoDialog'), \
             patch('tfm_main.SearchDialog'), \
             patch('tfm_main.JumpDialog'), \
             patch('tfm_main.BatchRenameDialog'), \
             patch('tfm_main.QuickChoiceBar'), \
             patch('tfm_main.GeneralPurposeDialog'), \
             patch('tfm_main.ExternalProgramManager'), \
             patch('tfm_main.ProgressManager'), \
             patch('tfm_main.curses'):
            
            self.file_manager = FileManager(self.mock_stdscr)
            
            # Mock dialog components
            self.file_manager.general_dialog = Mock()
            self.file_manager.list_dialog = Mock()
            self.file_manager.info_dialog = Mock()
            self.file_manager.search_dialog = Mock()
            self.file_manager.jump_dialog = Mock()
            self.file_manager.batch_rename_dialog = Mock()
            
            # Set up default states
            self.file_manager.general_dialog.is_active = False
            self.file_manager.list_dialog.is_active = False
            self.file_manager.info_dialog.is_active = False
            self.file_manager.search_dialog.is_active = False
            self.file_manager.jump_dialog.is_active = False
            self.file_manager.batch_rename_dialog.is_active = False
            
            # Mock other required methods
            self.file_manager.refresh_files = Mock()
            self.file_manager.clear_screen_with_background = Mock()
            self.file_manager.draw_header = Mock()
            self.file_manager.draw_files = Mock()
            self.file_manager.draw_log_pane = Mock()
            self.file_manager.draw_status = Mock()
            self.file_manager.get_current_pane = Mock(return_value={'files': []})
            self.file_manager.log_manager = Mock()
            self.file_manager.log_manager.has_log_updates.return_value = False
    
    def test_dialog_redrawn_when_full_redraw_needed(self):
        """Test that active dialogs are redrawn when full redraw is needed"""
        # Set up a list dialog as active
        self.file_manager.list_dialog.is_active = True
        self.file_manager.list_dialog.needs_redraw.return_value = False  # Content hasn't changed
        
        # Trigger a main screen redraw
        self.file_manager.needs_full_redraw = True
        
        # Call _draw_dialogs_if_needed
        result = self.file_manager._draw_dialogs_if_needed()
        
        # Verify dialog was drawn because full redraw was needed
        self.assertTrue(result)
        self.file_manager.list_dialog.draw.assert_called_once()
    
    def test_dialog_not_drawn_when_inactive_and_no_full_redraw(self):
        """Test that inactive dialogs are not drawn when no full redraw is needed"""
        # All dialogs inactive
        self.file_manager.general_dialog.is_active = False
        self.file_manager.list_dialog.is_active = False
        self.file_manager.info_dialog.is_active = False
        self.file_manager.search_dialog.is_active = False
        self.file_manager.jump_dialog.is_active = False
        self.file_manager.batch_rename_dialog.is_active = False
        
        # No full redraw needed
        self.file_manager.needs_full_redraw = False
        
        # Call _draw_dialogs_if_needed
        result = self.file_manager._draw_dialogs_if_needed()
        
        # Verify no dialog was drawn
        self.assertFalse(result)
        self.file_manager.list_dialog.draw.assert_not_called()
        self.file_manager.info_dialog.draw.assert_not_called()
        self.file_manager.search_dialog.draw.assert_not_called()
        self.file_manager.jump_dialog.draw.assert_not_called()
        self.file_manager.batch_rename_dialog.draw.assert_not_called()
    
    def test_general_dialog_redrawn_when_content_changed(self):
        """Test that general dialog is redrawn when content changes"""
        # Set up general dialog as active
        self.file_manager.general_dialog.is_active = True
        self.file_manager.general_dialog.needs_redraw.return_value = True  # Content has changed
        
        # Call _draw_dialogs_if_needed
        result = self.file_manager._draw_dialogs_if_needed()
        
        # Verify general dialog was drawn
        self.assertTrue(result)
        self.file_manager.general_dialog.draw.assert_called_once()
    
    def test_info_dialog_redrawn_when_full_redraw(self):
        """Test that info dialog is redrawn when full redraw is needed"""
        # Set up info dialog as active
        self.file_manager.info_dialog.is_active = True
        self.file_manager.info_dialog.needs_redraw.return_value = False  # Content hasn't changed
        self.file_manager.needs_full_redraw = True  # But full redraw is needed
        
        # Call _draw_dialogs_if_needed
        result = self.file_manager._draw_dialogs_if_needed()
        
        # Verify info dialog was drawn
        self.assertTrue(result)
        self.file_manager.info_dialog.draw.assert_called_once()
    
    def test_search_dialog_redrawn_when_content_changed(self):
        """Test that search dialog is redrawn when content changes"""
        # Set up search dialog as active
        self.file_manager.search_dialog.is_active = True
        self.file_manager.search_dialog.needs_redraw.return_value = True  # Content has changed
        
        # Call _draw_dialogs_if_needed
        result = self.file_manager._draw_dialogs_if_needed()
        
        # Verify search dialog was drawn
        self.assertTrue(result)
        self.file_manager.search_dialog.draw.assert_called_once()
    
    def test_jump_dialog_redrawn_when_full_redraw(self):
        """Test that jump dialog is redrawn when full redraw is needed"""
        # Set up jump dialog as active
        self.file_manager.jump_dialog.is_active = True
        self.file_manager.jump_dialog.needs_redraw.return_value = False  # Content hasn't changed
        self.file_manager.needs_full_redraw = True  # But full redraw is needed
        
        # Call _draw_dialogs_if_needed
        result = self.file_manager._draw_dialogs_if_needed()
        
        # Verify jump dialog was drawn
        self.assertTrue(result)
        self.file_manager.jump_dialog.draw.assert_called_once()
    
    def test_batch_rename_dialog_redrawn_when_content_changed(self):
        """Test that batch rename dialog is redrawn when content changes"""
        # Set up batch rename dialog as active
        self.file_manager.batch_rename_dialog.is_active = True
        self.file_manager.batch_rename_dialog.needs_redraw.return_value = True  # Content has changed
        
        # Call _draw_dialogs_if_needed
        result = self.file_manager._draw_dialogs_if_needed()
        
        # Verify batch rename dialog was drawn
        self.assertTrue(result)
        self.file_manager.batch_rename_dialog.draw.assert_called_once()
    
    def test_screen_refreshed_when_dialog_drawn(self):
        """Test that screen is refreshed when a dialog is drawn"""
        # Set up a dialog as active
        self.file_manager.list_dialog.is_active = True
        self.file_manager.list_dialog.needs_redraw.return_value = False
        
        # Call _draw_dialogs_if_needed
        self.file_manager._draw_dialogs_if_needed()
        
        # Verify screen was refreshed
        self.mock_stdscr.refresh.assert_called()
    
    def test_multiple_dialogs_only_one_active_drawn(self):
        """Test that only the active dialog is drawn when multiple could be active"""
        # Set up multiple dialogs, but only one should be drawn (general dialog has priority)
        self.file_manager.general_dialog.is_active = True
        self.file_manager.list_dialog.is_active = True  # This should be ignored
        
        # Trigger full redraw
        self.file_manager.needs_full_redraw = True
        
        # Call _draw_dialogs_if_needed
        result = self.file_manager._draw_dialogs_if_needed()
        
        # Verify only general dialog was drawn
        self.assertTrue(result)
        self.file_manager.general_dialog.draw.assert_called_once()
        self.file_manager.list_dialog.draw.assert_not_called()
    
    def test_dialog_not_constantly_redrawn(self):
        """Test that dialogs are not constantly redrawn when active but content unchanged and no full redraw"""
        # Set up a dialog as active
        self.file_manager.list_dialog.is_active = True
        self.file_manager.list_dialog.needs_redraw.return_value = False  # Content hasn't changed
        self.file_manager.needs_full_redraw = False  # No full redraw needed
        
        # Call _draw_dialogs_if_needed
        result = self.file_manager._draw_dialogs_if_needed()
        
        # Verify dialog was NOT drawn (performance optimization)
        self.assertFalse(result)
        self.file_manager.list_dialog.draw.assert_not_called()


if __name__ == '__main__':
    unittest.main()