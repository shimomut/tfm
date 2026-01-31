"""Test task cancellation with ESC key and action blocking during task execution."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from ttk import KeyEvent, KeyCode, ModifierKey
from tfm_base_task import BaseTask


class MockTask(BaseTask):
    """Mock task for testing."""
    
    def __init__(self, file_manager):
        super().__init__(file_manager, "MockTask")
        self.state = "idle"
        self.started = False
        self.cancelled = False
    
    def start(self):
        """Start the task."""
        self.state = "running"
        self.started = True
    
    def cancel(self):
        """Cancel the task."""
        self.state = "cancelled"
        self.cancelled = True
    
    def is_active(self):
        """Check if task is active."""
        return self.state == "running"
    
    def get_state(self):
        """Get current state."""
        return self.state


@pytest.fixture
def mock_renderer():
    """Create a mock renderer."""
    renderer = Mock()
    renderer.get_dimensions.return_value = (40, 120)
    renderer.is_desktop_mode.return_value = False
    renderer.supports_mouse.return_value = False
    return renderer


@pytest.fixture
def file_manager(mock_renderer):
    """Create a FileManager instance with mocked dependencies."""
    with patch('tfm_main.get_config') as mock_config, \
         patch('tfm_main.init_colors'), \
         patch('tfm_main.get_state_manager') as mock_state_mgr, \
         patch('tfm_main.cleanup_state_manager'):
        
        # Configure mock config
        config = Mock()
        config.COLOR_SCHEME = 'dark'
        config.DEFAULT_LOG_HEIGHT_RATIO = 0.25
        config.CONFIRM_QUIT = False
        mock_config.return_value = config
        
        # Configure mock state manager
        state_mgr = Mock()
        state_mgr.load_window_layout.return_value = None
        state_mgr.load_pane_state.return_value = None
        state_mgr.load_recent_directories.return_value = []
        mock_state_mgr.return_value = state_mgr
        
        # Import and create FileManager
        from tfm_main import FileManager
        
        fm = FileManager(
            mock_renderer,
            left_dir=str(Path.cwd()),
            right_dir=str(Path.home()),
            no_log_pane=True
        )
        
        return fm


def test_esc_cancels_active_task(file_manager):
    """Test that ESC key cancels an active task."""
    # Create and start a mock task
    task = MockTask(file_manager)
    file_manager.start_task(task)
    
    assert task.is_active()
    assert not task.cancelled
    
    # Press ESC key
    esc_event = KeyEvent(KeyCode.ESCAPE, '', set())
    result = file_manager.handle_main_screen_key_event(esc_event)
    
    # Verify task was cancelled
    assert result is True
    assert task.cancelled
    assert task.state == "cancelled"


def test_esc_ignored_when_no_task(file_manager):
    """Test that ESC key is ignored when no task is active."""
    # No task active
    assert file_manager.current_task is None
    
    # Press ESC key
    esc_event = KeyEvent(KeyCode.ESCAPE, '', set())
    result = file_manager.handle_main_screen_key_event(esc_event)
    
    # Verify ESC was not handled (returns False)
    assert result is False


def test_actions_blocked_during_task(file_manager):
    """Test that actions are blocked while a task is active."""
    # Create and start a mock task
    task = MockTask(file_manager)
    file_manager.start_task(task)
    
    assert task.is_active()
    
    # Try various actions - they should all be blocked
    test_keys = [
        KeyEvent(KeyCode.ENTER, '', set()),  # open_item
        KeyEvent(KeyCode.F5, '', set()),  # copy_files
        KeyEvent(KeyCode.F6, '', set()),  # move_files
        KeyEvent(KeyCode.F8, '', set()),  # delete_files
        KeyEvent(KeyCode.UP, '', set()),  # cursor_up
        KeyEvent(KeyCode.DOWN, '', set()),  # cursor_down
    ]
    
    for key_event in test_keys:
        result = file_manager.handle_main_screen_key_event(key_event)
        # All actions should be blocked (return True = consumed)
        assert result is True, f"Action for {key_event.key_code} was not blocked"


def test_actions_allowed_when_no_task(file_manager):
    """Test that actions work normally when no task is active."""
    # No task active
    assert file_manager.current_task is None
    
    # Mock find_action_for_event to return an action
    with patch('tfm_main.find_action_for_event', return_value='cursor_up'):
        # Try cursor movement - should work
        up_event = KeyEvent(KeyCode.UP, '', set())
        
        # Set up pane with files
        current_pane = file_manager.get_current_pane()
        mock_files = []
        for i in range(5):
            mock_file = Mock()
            mock_file.name = f"file{i}.txt"
            mock_file.is_dir.return_value = False
            mock_files.append(mock_file)
        current_pane['files'] = mock_files
        current_pane['focused_index'] = 2
        
        result = file_manager.handle_main_screen_key_event(up_event)
        
        # Action should be processed
        assert result is True
        assert current_pane['focused_index'] == 1


def test_task_completion_allows_actions(file_manager):
    """Test that actions are allowed after task completes."""
    # Create and start a mock task
    task = MockTask(file_manager)
    file_manager.start_task(task)
    
    assert task.is_active()
    
    # Complete the task
    task.state = "completed"
    assert not task.is_active()
    
    # Mock find_action_for_event to return an action
    with patch('tfm_main.find_action_for_event', return_value='cursor_up'):
        # Try cursor movement - should work now
        up_event = KeyEvent(KeyCode.UP, '', set())
        
        # Set up pane with files
        current_pane = file_manager.get_current_pane()
        mock_files = []
        for i in range(5):
            mock_file = Mock()
            mock_file.name = f"file{i}.txt"
            mock_file.is_dir.return_value = False
            mock_files.append(mock_file)
        current_pane['files'] = mock_files
        current_pane['focused_index'] = 2
        
        result = file_manager.handle_main_screen_key_event(up_event)
        
        # Action should be processed
        assert result is True
        assert current_pane['focused_index'] == 1


def test_esc_during_task_logs_message(file_manager):
    """Test that cancelling a task logs an appropriate message."""
    # Create and start a mock task
    task = MockTask(file_manager)
    file_manager.start_task(task)
    
    # Mock the logger to capture messages
    with patch.object(file_manager.logger, 'info') as mock_info:
        # Press ESC key
        esc_event = KeyEvent(KeyCode.ESCAPE, '', set())
        file_manager.handle_main_screen_key_event(esc_event)
        
        # Verify log message
        mock_info.assert_called_once_with("Cancelling task...")


def test_blocked_action_logs_warning(file_manager):
    """Test that blocked actions log a warning message."""
    # Create and start a mock task
    task = MockTask(file_manager)
    file_manager.start_task(task)
    
    # Mock the logger to capture messages
    with patch.object(file_manager.logger, 'warning') as mock_warning:
        # Try an action
        enter_event = KeyEvent(KeyCode.ENTER, '', set())
        file_manager.handle_main_screen_key_event(enter_event)
        
        # Verify warning message
        mock_warning.assert_called_once_with("Action blocked: task in progress (press ESC to cancel)")
