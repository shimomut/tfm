"""
Test that arrow keys and navigation keys don't insert characters in file list I-Search mode.
"""
import pytest
from unittest.mock import Mock, patch
from ttk.input_event import KeyEvent, CharEvent, KeyCode, ModifierKey


def test_filelist_isearch_ignores_navigation_keys():
    """Test that navigation keys are ignored in file list I-Search mode"""
    from src.tfm_main import FileManager
    
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    mock_renderer.clear = Mock()
    mock_renderer.refresh = Mock()
    mock_renderer.draw_text = Mock()
    mock_renderer.draw_hline = Mock()
    mock_renderer.draw_vline = Mock()
    mock_renderer.set_cursor_visibility = Mock()
    mock_renderer.get_input = Mock()
    
    # Create FileManager with proper mocking
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'):
        
        fm = FileManager(mock_renderer)
        fm.log_height_ratio = 0.25
        
        # Set up isearch mode
        fm.isearch_mode = True
        fm.isearch_pattern = "test"
        fm.isearch_matches = [0, 1, 2]
        fm.isearch_match_index = 0
        
        # Mock get_current_pane
        mock_pane = {'focused_index': 0}
        fm.get_current_pane = Mock(return_value=mock_pane)
        fm.adjust_scroll_for_focus = Mock()
        fm.update_isearch_matches = Mock()
        fm.mark_dirty = Mock()
        
        # Test LEFT arrow key
        left_event = KeyEvent(KeyCode.LEFT, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(left_event)
        assert result is True
        assert fm.isearch_pattern == "test"  # Pattern unchanged
        
        # Test RIGHT arrow key
        right_event = KeyEvent(KeyCode.RIGHT, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(right_event)
        assert result is True
        assert fm.isearch_pattern == "test"  # Pattern unchanged
        
        # Test HOME key
        home_event = KeyEvent(KeyCode.HOME, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(home_event)
        assert result is True
        assert fm.isearch_pattern == "test"  # Pattern unchanged
        
        # Test END key
        end_event = KeyEvent(KeyCode.END, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(end_event)
        assert result is True
        assert fm.isearch_pattern == "test"  # Pattern unchanged
        
        # Test PAGE_UP key
        pgup_event = KeyEvent(KeyCode.PAGE_UP, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(pgup_event)
        assert result is True
        assert fm.isearch_pattern == "test"  # Pattern unchanged
        
        # Test PAGE_DOWN key
        pgdn_event = KeyEvent(KeyCode.PAGE_DOWN, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(pgdn_event)
        assert result is True
        assert fm.isearch_pattern == "test"  # Pattern unchanged
        
        # Test TAB key
        tab_event = KeyEvent(KeyCode.TAB, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(tab_event)
        assert result is True
        assert fm.isearch_pattern == "test"  # Pattern unchanged
        
        # Test DELETE key
        del_event = KeyEvent(KeyCode.DELETE, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(del_event)
        assert result is True
        assert fm.isearch_pattern == "test"  # Pattern unchanged
        
        # Test INSERT key
        ins_event = KeyEvent(KeyCode.INSERT, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(ins_event)
        assert result is True
        assert fm.isearch_pattern == "test"  # Pattern unchanged


def test_filelist_isearch_handles_printable_chars():
    """Test that printable characters are added to search pattern"""
    from src.tfm_main import FileManager
    
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    
    # Create FileManager with proper mocking
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'):
        
        fm = FileManager(mock_renderer)
        fm.log_height_ratio = 0.25
        
        # Set up isearch mode
        fm.isearch_mode = True
        fm.isearch_pattern = ""
        fm.update_isearch_matches = Mock()
        fm.mark_dirty = Mock()
        
        # Test CharEvent
        char_event = CharEvent('a')
        result = fm.handle_isearch_input(char_event)
        assert result is True
        assert fm.isearch_pattern == "a"
        
        # Test another CharEvent
        char_event2 = CharEvent('b')
        result = fm.handle_isearch_input(char_event2)
        assert result is True
        assert fm.isearch_pattern == "ab"


def test_filelist_isearch_up_down_navigation():
    """Test that UP/DOWN keys navigate through matches"""
    from src.tfm_main import FileManager
    
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    
    # Create FileManager with proper mocking
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'):
        
        fm = FileManager(mock_renderer)
        fm.log_height_ratio = 0.25
        
        # Set up isearch mode with matches
        fm.isearch_mode = True
        fm.isearch_pattern = "test"
        fm.isearch_matches = [0, 5, 10]
        fm.isearch_match_index = 0
        
        # Mock get_current_pane
        mock_pane = {'focused_index': 0}
        fm.get_current_pane = Mock(return_value=mock_pane)
        fm.adjust_scroll_for_focus = Mock()
        fm.mark_dirty = Mock()
        
        # Test DOWN arrow - should move to next match
        down_event = KeyEvent(KeyCode.DOWN, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(down_event)
        assert result is True
        assert fm.isearch_match_index == 1
        assert mock_pane['focused_index'] == 5
        
        # Test UP arrow - should move to previous match
        up_event = KeyEvent(KeyCode.UP, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(up_event)
        assert result is True
        assert fm.isearch_match_index == 0
        assert mock_pane['focused_index'] == 0


def test_filelist_isearch_backspace():
    """Test that BACKSPACE removes last character"""
    from src.tfm_main import FileManager
    
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    
    # Create FileManager with proper mocking
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'):
        
        fm = FileManager(mock_renderer)
        fm.log_height_ratio = 0.25
        
        # Set up isearch mode
        fm.isearch_mode = True
        fm.isearch_pattern = "test"
        fm.update_isearch_matches = Mock()
        fm.mark_dirty = Mock()
        
        # Test BACKSPACE
        bs_event = KeyEvent(KeyCode.BACKSPACE, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(bs_event)
        assert result is True
        assert fm.isearch_pattern == "tes"


def test_filelist_isearch_escape_enter():
    """Test that ESC and ENTER exit isearch mode"""
    from src.tfm_main import FileManager
    
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    
    # Create FileManager with proper mocking
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'):
        
        fm = FileManager(mock_renderer)
        fm.log_height_ratio = 0.25
        
        # Set up isearch mode
        fm.isearch_mode = True
        fm.isearch_pattern = "test"
        fm.exit_isearch_mode = Mock()
        
        # Test ESC
        esc_event = KeyEvent(KeyCode.ESCAPE, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(esc_event)
        assert result is True
        fm.exit_isearch_mode.assert_called_once()
        
        # Reset mock
        fm.exit_isearch_mode.reset_mock()
        
        # Test ENTER
        enter_event = KeyEvent(KeyCode.ENTER, ModifierKey.NONE, None)
        result = fm.handle_isearch_input(enter_event)
        assert result is True
        fm.exit_isearch_mode.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
