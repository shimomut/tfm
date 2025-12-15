#!/usr/bin/env python3
"""
Test suite for DrivesDialog TTK integration
Tests the migration from curses to TTK API
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import threading
import time
from unittest.mock import Mock, MagicMock, patch
from ttk import KeyCode, TextAttribute, KeyEvent
from tfm_drives_dialog import DrivesDialog, DriveEntry, DrivesDialogHelpers


@pytest.fixture
def mock_renderer():
    """Create a mock TTK renderer"""
    renderer = Mock()
    renderer.get_dimensions.return_value = (40, 120)
    renderer.draw_text = Mock()
    renderer.draw_hline = Mock()
    renderer.draw_vline = Mock()
    renderer.clear = Mock()
    renderer.refresh = Mock()
    return renderer


@pytest.fixture
def config():
    """Create a test configuration"""
    config = Mock()
    config.DRIVES_DIALOG_WIDTH_RATIO = 0.7
    config.DRIVES_DIALOG_HEIGHT_RATIO = 0.8
    config.DRIVES_DIALOG_MIN_WIDTH = 50
    config.DRIVES_DIALOG_MIN_HEIGHT = 18
    config.SEARCH_ANIMATION_ENABLED = True
    config.SEARCH_ANIMATION_STYLE = 'dots'
    return config


@pytest.fixture
def drives_dialog(config, mock_renderer):
    """Create a DrivesDialog instance with mock renderer"""
    dialog = DrivesDialog(config, mock_renderer)
    return dialog


class TestDrivesDialogInitialization:
    """Test DrivesDialog initialization with TTK"""
    
    def test_init_accepts_renderer(self, config, mock_renderer):
        """Test that DrivesDialog accepts renderer parameter"""
        dialog = DrivesDialog(config, mock_renderer)
        assert dialog.renderer is mock_renderer
    
    def test_init_without_renderer(self, config):
        """Test that DrivesDialog can be initialized without renderer"""
        dialog = DrivesDialog(config)
        assert dialog.renderer is None
    
    def test_init_state(self, drives_dialog):
        """Test that DrivesDialog initializes with correct state"""
        assert drives_dialog.drives == []
        assert drives_dialog.filtered_drives == []
        assert drives_dialog.loading_s3 is False
        assert drives_dialog.content_changed is True
        assert drives_dialog.s3_thread is None


class TestDrivesDialogInputHandling:
    """Test DrivesDialog input handling with KeyEvent"""
    
    def test_handle_input_accepts_input_event(self, drives_dialog):
        """Test that handle_input accepts KeyEvent"""
        event = KeyEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=set())
        result = drives_dialog.handle_input(event)
        assert result is True
        assert not drives_dialog.is_active
    
    def test_handle_input_escape_cancels(self, drives_dialog):
        """Test that ESC key cancels the dialog"""
        drives_dialog.show()
        event = KeyEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=set())
        result = drives_dialog.handle_input(event)
        assert result is True
        assert not drives_dialog.is_active
    
    def test_handle_input_enter_selects(self, drives_dialog):
        """Test that ENTER key selects current drive"""
        drives_dialog.show()
        # Add a test drive
        test_drive = DriveEntry("Test Drive", "/test", "local")
        drives_dialog.drives = [test_drive]
        drives_dialog.filtered_drives = [test_drive]
        drives_dialog.selected = 0
        
        event = KeyEvent(key_code=KeyCode.ENTER, char=None, modifiers=set())
        result = drives_dialog.handle_input(event)
        assert result == ('navigate', test_drive)
    
    def test_handle_input_up_arrow(self, drives_dialog):
        """Test that UP arrow navigates up"""
        drives_dialog.show()
        drives_dialog.drives = [
            DriveEntry("Drive 1", "/test1", "local"),
            DriveEntry("Drive 2", "/test2", "local")
        ]
        drives_dialog.filtered_drives = drives_dialog.drives.copy()
        drives_dialog.selected = 1
        
        event = KeyEvent(key_code=KeyCode.UP, char=None, modifiers=set())
        result = drives_dialog.handle_input(event)
        assert result is True
        assert drives_dialog.selected == 0
    
    def test_handle_input_down_arrow(self, drives_dialog):
        """Test that DOWN arrow navigates down"""
        drives_dialog.show()
        drives_dialog.drives = [
            DriveEntry("Drive 1", "/test1", "local"),
            DriveEntry("Drive 2", "/test2", "local")
        ]
        drives_dialog.filtered_drives = drives_dialog.drives.copy()
        drives_dialog.selected = 0
        
        event = KeyEvent(key_code=KeyCode.DOWN, char=None, modifiers=set())
        result = drives_dialog.handle_input(event)
        assert result is True
        assert drives_dialog.selected == 1
    
    def test_handle_input_page_up(self, drives_dialog):
        """Test that PAGE_UP navigates up by page"""
        drives_dialog.show()
        drives_dialog.drives = [DriveEntry(f"Drive {i}", f"/test{i}", "local") for i in range(20)]
        drives_dialog.filtered_drives = drives_dialog.drives.copy()
        drives_dialog.selected = 15
        
        event = KeyEvent(key_code=KeyCode.PAGE_UP, char=None, modifiers=set())
        result = drives_dialog.handle_input(event)
        assert result is True
        assert drives_dialog.selected < 15
    
    def test_handle_input_page_down(self, drives_dialog):
        """Test that PAGE_DOWN navigates down by page"""
        drives_dialog.show()
        drives_dialog.drives = [DriveEntry(f"Drive {i}", f"/test{i}", "local") for i in range(20)]
        drives_dialog.filtered_drives = drives_dialog.drives.copy()
        drives_dialog.selected = 0
        
        event = KeyEvent(key_code=KeyCode.PAGE_DOWN, char=None, modifiers=set())
        result = drives_dialog.handle_input(event)
        assert result is True
        assert drives_dialog.selected > 0
    
    def test_handle_input_home(self, drives_dialog):
        """Test that HOME key goes to first item"""
        drives_dialog.show()
        drives_dialog.drives = [DriveEntry(f"Drive {i}", f"/test{i}", "local") for i in range(10)]
        drives_dialog.filtered_drives = drives_dialog.drives.copy()
        drives_dialog.selected = 5
        
        event = KeyEvent(key_code=KeyCode.HOME, char=None, modifiers=set())
        result = drives_dialog.handle_input(event)
        assert result is True
        assert drives_dialog.selected == 0
    
    def test_handle_input_end(self, drives_dialog):
        """Test that END key goes to last item"""
        drives_dialog.show()
        drives_dialog.drives = [DriveEntry(f"Drive {i}", f"/test{i}", "local") for i in range(10)]
        drives_dialog.filtered_drives = drives_dialog.drives.copy()
        drives_dialog.selected = 0
        
        event = KeyEvent(key_code=KeyCode.END, char=None, modifiers=set())
        result = drives_dialog.handle_input(event)
        assert result is True
        assert drives_dialog.selected == 9
    
    @pytest.mark.skip(reason="Depends on SingleLineTextEdit TTK migration (task 26)")
    def test_handle_input_text_filters(self, drives_dialog):
        """Test that typing text filters drives"""
        drives_dialog.show()
        drives_dialog.drives = [
            DriveEntry("Home Directory", "/home/user", "local"),
            DriveEntry("Root Directory", "/", "local"),
            DriveEntry("test-bucket", "s3://test-bucket/", "s3")
        ]
        drives_dialog.filtered_drives = drives_dialog.drives.copy()
        
        # Type 's3' to filter
        for char in "s3":
            event = KeyEvent(key_code=None, char=char, modifiers=set())
            drives_dialog.handle_input(event)
        
        assert len(drives_dialog.filtered_drives) == 1
        assert drives_dialog.filtered_drives[0].name == "test-bucket"


class TestDrivesDialogDrawing:
    """Test DrivesDialog drawing with TTK renderer"""
    
    @pytest.mark.skip(reason="Depends on SingleLineTextEdit TTK migration (task 26)")
    def test_draw_uses_renderer(self, drives_dialog):
        """Test that draw() uses renderer instead of stdscr"""
        drives_dialog.show()
        drives_dialog.drives = [DriveEntry("Test Drive", "/test", "local")]
        drives_dialog.filtered_drives = drives_dialog.drives.copy()
        
        drives_dialog.draw()
        
        # Verify renderer methods were called
        assert drives_dialog.renderer.draw_text.called
        assert drives_dialog.renderer.get_dimensions.called
    
    @pytest.mark.skip(reason="Depends on SingleLineTextEdit TTK migration (task 26)")
    def test_draw_no_stdscr_parameter(self, drives_dialog):
        """Test that draw() doesn't require stdscr parameter"""
        drives_dialog.show()
        # Should not raise an error
        drives_dialog.draw()
    
    @pytest.mark.skip(reason="Depends on SingleLineTextEdit TTK migration (task 26)")
    def test_draw_displays_drives(self, drives_dialog):
        """Test that draw() displays drive list"""
        drives_dialog.show()
        drives_dialog.drives = [
            DriveEntry("Home Directory", "/home/user", "local"),
            DriveEntry("test-bucket", "s3://test-bucket/", "s3")
        ]
        drives_dialog.filtered_drives = drives_dialog.drives.copy()
        
        drives_dialog.draw()
        
        # Verify text was drawn (check that draw_text was called multiple times)
        assert drives_dialog.renderer.draw_text.call_count > 0
    
    @pytest.mark.skip(reason="Depends on SingleLineTextEdit TTK migration (task 26)")
    def test_draw_shows_loading_indicator(self, drives_dialog):
        """Test that draw() shows loading indicator when scanning S3"""
        drives_dialog.show()
        drives_dialog.loading_s3 = True
        
        drives_dialog.draw()
        
        # Verify status text was drawn
        assert drives_dialog.renderer.draw_text.called


class TestDrivesDialogFiltering:
    """Test DrivesDialog filtering functionality"""
    
    def test_filter_by_name(self, drives_dialog):
        """Test filtering drives by name"""
        drives_dialog.drives = [
            DriveEntry("Home Directory", "/home/user", "local"),
            DriveEntry("Root Directory", "/", "local"),
            DriveEntry("test-bucket", "s3://test-bucket/", "s3")
        ]
        drives_dialog.text_editor.text = "home"
        drives_dialog._filter_drives()
        
        assert len(drives_dialog.filtered_drives) == 1
        assert drives_dialog.filtered_drives[0].name == "Home Directory"
    
    def test_filter_by_path(self, drives_dialog):
        """Test filtering drives by path"""
        drives_dialog.drives = [
            DriveEntry("Home Directory", "/home/user", "local"),
            DriveEntry("Root Directory", "/", "local"),
            DriveEntry("test-bucket", "s3://test-bucket/", "s3")
        ]
        drives_dialog.text_editor.text = "s3://"
        drives_dialog._filter_drives()
        
        assert len(drives_dialog.filtered_drives) == 1
        assert drives_dialog.filtered_drives[0].drive_type == "s3"
    
    def test_filter_case_insensitive(self, drives_dialog):
        """Test that filtering is case-insensitive"""
        drives_dialog.drives = [
            DriveEntry("Home Directory", "/home/user", "local"),
            DriveEntry("test-bucket", "s3://test-bucket/", "s3")
        ]
        drives_dialog.text_editor.text = "HOME"
        drives_dialog._filter_drives()
        
        assert len(drives_dialog.filtered_drives) == 1
        assert drives_dialog.filtered_drives[0].name == "Home Directory"
    
    def test_filter_empty_shows_all(self, drives_dialog):
        """Test that empty filter shows all drives"""
        drives_dialog.drives = [
            DriveEntry("Home Directory", "/home/user", "local"),
            DriveEntry("Root Directory", "/", "local"),
            DriveEntry("test-bucket", "s3://test-bucket/", "s3")
        ]
        drives_dialog.text_editor.text = ""
        drives_dialog._filter_drives()
        
        assert len(drives_dialog.filtered_drives) == 3


class TestDriveEntry:
    """Test DriveEntry class"""
    
    def test_local_drive_display(self):
        """Test display text for local drive"""
        drive = DriveEntry("Home Directory", "/home/user", "local", "User home")
        display = drive.get_display_text()
        assert "Home" in display
        assert "User home" in display
    
    def test_s3_drive_display(self):
        """Test display text for S3 drive"""
        drive = DriveEntry("test-bucket", "s3://test-bucket/", "s3")
        display = drive.get_display_text()
        assert "s3://test-bucket" in display
    
    def test_s3_error_display(self):
        """Test display text for S3 error entry"""
        drive = DriveEntry("S3 (No Credentials)", "", "s3", "Configure AWS credentials")
        display = drive.get_display_text()
        assert "S3 (No Credentials)" in display
        assert "Configure AWS credentials" in display


class TestDrivesDialogThreadSafety:
    """Test DrivesDialog thread safety"""
    
    def test_s3_scan_thread_safety(self, drives_dialog):
        """Test that S3 scanning is thread-safe"""
        drives_dialog.show()
        
        # Simulate S3 scan starting
        drives_dialog.loading_s3 = True
        
        # Access filtered_drives from main thread while "scanning"
        with drives_dialog.s3_lock:
            filtered = drives_dialog.filtered_drives.copy()
        
        assert isinstance(filtered, list)
    
    def test_cancel_s3_scan(self, drives_dialog):
        """Test cancelling S3 scan"""
        drives_dialog.show()
        
        # Start a mock S3 scan
        drives_dialog.loading_s3 = True
        drives_dialog.s3_thread = threading.Thread(target=lambda: time.sleep(0.1))
        drives_dialog.s3_thread.start()
        
        # Cancel the scan
        drives_dialog._cancel_current_s3_scan()
        
        assert drives_dialog.loading_s3 is False
        assert drives_dialog.cancel_s3_scan.is_set()


class TestDrivesDialogHelpers:
    """Test DrivesDialogHelpers class"""
    
    def test_navigate_to_local_drive(self):
        """Test navigating to local drive"""
        drive = DriveEntry("Test Drive", "/tmp", "local")
        pane_manager = Mock()
        pane_manager.get_current_pane.return_value = {
            'path': None,
            'selected_index': 0,
            'scroll_offset': 0,
            'selected_files': set()
        }
        pane_manager.active_pane = 'left'
        print_func = Mock()
        
        DrivesDialogHelpers.navigate_to_drive(drive, pane_manager, print_func)
        
        # Verify navigation occurred
        assert print_func.called
    
    def test_navigate_to_s3_drive(self):
        """Test navigating to S3 drive"""
        drive = DriveEntry("test-bucket", "s3://test-bucket/", "s3")
        pane_manager = Mock()
        pane_manager.get_current_pane.return_value = {
            'path': None,
            'selected_index': 0,
            'scroll_offset': 0,
            'selected_files': set()
        }
        pane_manager.active_pane = 'left'
        print_func = Mock()
        
        DrivesDialogHelpers.navigate_to_drive(drive, pane_manager, print_func)
        
        # Verify navigation occurred
        assert print_func.called
    
    def test_navigate_to_invalid_drive(self):
        """Test navigating to invalid drive"""
        drive = DriveEntry("Invalid", "", "local")
        pane_manager = Mock()
        print_func = Mock()
        
        DrivesDialogHelpers.navigate_to_drive(drive, pane_manager, print_func)
        
        # Verify error message
        assert print_func.called
        call_args = print_func.call_args[0][0]
        assert "Error" in call_args or "Invalid" in call_args


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
