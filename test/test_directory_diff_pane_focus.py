"""
Test pane focus functionality in DirectoryDiffViewer.

This test verifies that:
1. DirectoryDiffViewer initializes with left pane focused
2. Tab key switches focus between left and right panes
3. Focus indicator is displayed correctly in header
4. Cursor position remains synchronized between panes
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from ttk import KeyEvent, KeyCode, ModifierKey


@pytest.fixture
def mock_renderer():
    """Create a mock renderer for testing."""
    renderer = Mock()
    renderer.get_dimensions.return_value = (40, 120)
    renderer.clear = Mock()
    renderer.draw_text = Mock()
    return renderer


@pytest.fixture
def temp_directories(tmp_path):
    """Create temporary test directories."""
    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"
    left_dir.mkdir()
    right_dir.mkdir()
    
    # Create some test files
    (left_dir / "file1.txt").write_text("content1")
    (right_dir / "file1.txt").write_text("content1")
    (left_dir / "file2.txt").write_text("content2")
    
    return left_dir, right_dir


def test_initial_focus_is_left(mock_renderer, temp_directories):
    """Test that DirectoryDiffViewer initializes with left pane focused."""
    from src.tfm_directory_diff_viewer import DirectoryDiffViewer
    from tfm_path import Path as TFMPath
    
    left_dir, right_dir = temp_directories
    
    # Create viewer
    viewer = DirectoryDiffViewer(
        mock_renderer,
        TFMPath(str(left_dir)),
        TFMPath(str(right_dir))
    )
    
    # Verify initial focus is on left pane
    assert viewer.active_pane == 'left'


def test_tab_switches_pane_focus(mock_renderer, temp_directories):
    """Test that Tab key switches focus between panes."""
    from src.tfm_directory_diff_viewer import DirectoryDiffViewer
    from tfm_path import Path as TFMPath
    
    left_dir, right_dir = temp_directories
    
    # Create viewer
    viewer = DirectoryDiffViewer(
        mock_renderer,
        TFMPath(str(left_dir)),
        TFMPath(str(right_dir))
    )
    
    # Initial focus should be left
    assert viewer.active_pane == 'left'
    
    # Press Tab to switch to right
    tab_event = KeyEvent(key_code=KeyCode.TAB, modifiers=ModifierKey.NONE, char=None)
    result = viewer.handle_key_event(tab_event)
    
    assert result is True
    assert viewer.active_pane == 'right'
    
    # Press Tab again to switch back to left
    result = viewer.handle_key_event(tab_event)
    
    assert result is True
    assert viewer.active_pane == 'left'


def test_left_right_keys_switch_pane_focus(mock_renderer, temp_directories):
    """Test that Left/Right keys switch focus between panes."""
    from src.tfm_directory_diff_viewer import DirectoryDiffViewer
    from tfm_path import Path as TFMPath
    
    left_dir, right_dir = temp_directories
    
    # Create viewer
    viewer = DirectoryDiffViewer(
        mock_renderer,
        TFMPath(str(left_dir)),
        TFMPath(str(right_dir))
    )
    
    # Initial focus should be left
    assert viewer.active_pane == 'left'
    
    # Press Right to switch to right pane
    right_event = KeyEvent(key_code=KeyCode.RIGHT, modifiers=ModifierKey.NONE, char=None)
    result = viewer.handle_key_event(right_event)
    
    assert result is True
    assert viewer.active_pane == 'right'
    
    # Press Left to switch back to left pane
    left_event = KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE, char=None)
    result = viewer.handle_key_event(left_event)
    
    assert result is True
    assert viewer.active_pane == 'left'
    
    # Press Right again
    result = viewer.handle_key_event(right_event)
    assert result is True
    assert viewer.active_pane == 'right'


def test_focus_indicator_in_header(mock_renderer, temp_directories):
    """Test that focus indicator is displayed in header with bold text."""
    from src.tfm_directory_diff_viewer import DirectoryDiffViewer
    from tfm_path import Path as TFMPath
    from ttk import TextAttribute
    
    left_dir, right_dir = temp_directories
    
    # Create viewer
    viewer = DirectoryDiffViewer(
        mock_renderer,
        TFMPath(str(left_dir)),
        TFMPath(str(right_dir))
    )
    
    # Wait for initial scan to complete
    import time
    timeout = 2.0
    start_time = time.time()
    while viewer.scan_in_progress and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    
    # Render with left pane focused
    viewer.render(mock_renderer)
    
    # Check that header was rendered with bold attribute for left pane
    # The header should have bold attribute for the focused pane
    header_calls = [call for call in mock_renderer.draw_text.call_args_list 
                   if call[0][0] == 0]  # Row 0 is the header
    
    assert len(header_calls) > 0
    
    # Check that at least one header call has BOLD attribute
    has_bold = False
    for call in header_calls:
        if len(call[0]) > 3:  # Has attributes parameter
            attrs = call[0][3]
            if attrs & TextAttribute.BOLD:
                has_bold = True
                break
    
    assert has_bold, "Left pane header should have BOLD attribute when focused"
    
    # Switch to right pane
    from ttk import KeyEvent, KeyCode, ModifierKey
    tab_event = KeyEvent(key_code=KeyCode.TAB, modifiers=ModifierKey.NONE, char=None)
    viewer.handle_key_event(tab_event)
    
    # Clear previous calls
    mock_renderer.draw_text.reset_mock()
    
    # Render with right pane focused
    viewer.render(mock_renderer)
    
    # Check header again - should still have bold attribute (for right pane now)
    header_calls = [call for call in mock_renderer.draw_text.call_args_list 
                   if call[0][0] == 0]
    
    assert len(header_calls) > 0
    
    # Check that at least one header call has BOLD attribute
    has_bold = False
    for call in header_calls:
        if len(call[0]) > 3:
            attrs = call[0][3]
            if attrs & TextAttribute.BOLD:
                has_bold = True
                break
    
    assert has_bold, "Right pane header should have BOLD attribute when focused"


def test_cursor_position_synchronized(mock_renderer, temp_directories):
    """Test that cursor position remains synchronized between panes."""
    from src.tfm_directory_diff_viewer import DirectoryDiffViewer
    from tfm_path import Path as TFMPath
    
    left_dir, right_dir = temp_directories
    
    # Create viewer
    viewer = DirectoryDiffViewer(
        mock_renderer,
        TFMPath(str(left_dir)),
        TFMPath(str(right_dir))
    )
    
    # Wait for initial scan to complete
    import time
    timeout = 2.0
    start_time = time.time()
    while viewer.scan_in_progress and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    
    # Move cursor down
    down_event = KeyEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.NONE, char=None)
    viewer.handle_key_event(down_event)
    
    cursor_pos_left = viewer.cursor_position
    
    # Switch to right pane
    tab_event = KeyEvent(key_code=KeyCode.TAB, modifiers=ModifierKey.NONE, char=None)
    viewer.handle_key_event(tab_event)
    
    # Cursor position should remain the same
    assert viewer.cursor_position == cursor_pos_left
    
    # Move cursor down in right pane
    viewer.handle_key_event(down_event)
    
    cursor_pos_right = viewer.cursor_position
    
    # Switch back to left pane
    viewer.handle_key_event(tab_event)
    
    # Cursor position should still be synchronized
    assert viewer.cursor_position == cursor_pos_right


def test_status_bar_shows_tab_hint():
    """Test that status bar code includes Tab key hint."""
    # Read the source file and verify Tab hint is in the status bar code
    import os
    source_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'tfm_directory_diff_viewer.py')
    
    with open(source_file, 'r') as f:
        content = f.read()
    
    # Verify that the status bar includes Tab hint
    assert 'Tab:switch-pane' in content
    assert 'left_status = ' in content
    
    # Verify the active_pane state variable exists
    assert "self.active_pane = 'left'" in content
