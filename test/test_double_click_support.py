"""
Test double-click support in TFM.

This test verifies that double-click events trigger the same actions as
pressing the Enter key in file lists and directory diff viewer.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton
from src.tfm_main import FileManager
from src.tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_path import Path


class TestFileManagerDoubleClick:
    """Test double-click support in FileManager."""
    
    def test_double_click_opens_directory(self):
        """Double-clicking a directory should navigate into it."""
        # Create mock renderer
        renderer = Mock()
        renderer.get_dimensions.return_value = (24, 80)
        renderer.supports_mouse.return_value = True
        renderer.get_supported_mouse_events.return_value = {MouseEventType.DOUBLE_CLICK}
        renderer.enable_mouse_events.return_value = True
        
        # Create FileManager
        fm = FileManager(renderer)
        fm.mark_dirty = Mock()
        
        # Set up test directory with subdirectory
        test_dir = Path("/tmp/test_dir")
        subdir = Path("/tmp/test_dir/subdir")
        
        # Mock the directory structure
        with patch.object(Path, 'iterdir') as mock_iterdir:
            mock_iterdir.return_value = [subdir]
            
            # Set up pane with subdirectory
            fm.pane_manager.left_pane['path'] = test_dir
            fm.pane_manager.left_pane['files'] = [subdir]
            fm.pane_manager.left_pane['focused_index'] = 0
            fm.pane_manager.left_pane['scroll_offset'] = 0
            fm.pane_manager.active_pane = 'left'
            
            # Mock is_dir to return True for subdirectory
            with patch.object(Path, 'is_dir', return_value=True):
                # Mock refresh_files to avoid actual filesystem operations
                fm.refresh_files = Mock()
                
                # Create double-click event on the subdirectory (row 1, column 0)
                event = MouseEvent(
                    event_type=MouseEventType.DOUBLE_CLICK,
                    column=0,
                    row=1,
                    sub_cell_x=0.5,
                    sub_cell_y=0.5,
                    button=MouseButton.LEFT
                )
                
                # Handle the event
                result = fm.handle_mouse_event(event)
                
                # Verify event was handled
                assert result is True
                
                # Verify directory was changed
                assert fm.pane_manager.left_pane['path'] == subdir
                assert fm.refresh_files.called
    
    def test_double_click_opens_file(self):
        """Double-clicking a file should trigger file opening logic."""
        # Create mock renderer
        renderer = Mock()
        renderer.get_dimensions.return_value = (24, 80)
        renderer.supports_mouse.return_value = True
        renderer.get_supported_mouse_events.return_value = {MouseEventType.DOUBLE_CLICK}
        renderer.enable_mouse_events.return_value = True
        
        # Create FileManager
        fm = FileManager(renderer)
        fm.mark_dirty = Mock()
        
        # Set up test directory with file
        test_dir = Path("/tmp/test_dir")
        test_file = Path("/tmp/test_dir/test.txt")
        
        # Set up pane with file
        fm.pane_manager.left_pane['path'] = test_dir
        fm.pane_manager.left_pane['files'] = [test_file]
        fm.pane_manager.left_pane['focused_index'] = 0
        fm.pane_manager.left_pane['scroll_offset'] = 0
        fm.pane_manager.active_pane = 'left'
        
        # Mock is_dir to return False for file
        with patch.object(Path, 'is_dir', return_value=False):
            # Mock archive check
            fm.archive_operations.is_archive = Mock(return_value=False)
            
            # Mock get_program_for_file to return None (no association)
            with patch('src.tfm_main.get_program_for_file', return_value=None):
                # Mock is_text_file to return True
                with patch('src.tfm_main.is_text_file', return_value=True):
                    # Mock create_text_viewer to return None (simpler test)
                    with patch('src.tfm_main.create_text_viewer', return_value=None):
                        # Create double-click event on the file (row 1, column 0)
                        event = MouseEvent(
                            event_type=MouseEventType.DOUBLE_CLICK,
                            column=0,
                            row=1,
                            sub_cell_x=0.5,
                            sub_cell_y=0.5,
                            button=MouseButton.LEFT
                        )
                        
                        # Handle the event
                        result = fm.handle_mouse_event(event)
                        
                        # Verify event was handled
                        assert result is True
                        
                        # Verify the file was processed (logged)
                        # The actual file opening is tested elsewhere, we just verify
                        # that handle_enter was called by checking mark_dirty was called
                        assert fm.mark_dirty.called
    
    def test_double_click_switches_pane_focus(self):
        """Double-clicking in inactive pane should switch focus."""
        # Create mock renderer
        renderer = Mock()
        renderer.get_dimensions.return_value = (24, 80)
        renderer.supports_mouse.return_value = True
        renderer.get_supported_mouse_events.return_value = {MouseEventType.DOUBLE_CLICK}
        renderer.enable_mouse_events.return_value = True
        
        # Create FileManager
        fm = FileManager(renderer)
        fm.mark_dirty = Mock()
        
        # Set up both panes with files
        test_file_left = Path("/tmp/left/file.txt")
        test_file_right = Path("/tmp/right/file.txt")
        
        fm.pane_manager.left_pane['files'] = [test_file_left]
        fm.pane_manager.left_pane['focused_index'] = 0
        fm.pane_manager.left_pane['scroll_offset'] = 0
        
        fm.pane_manager.right_pane['files'] = [test_file_right]
        fm.pane_manager.right_pane['focused_index'] = 0
        fm.pane_manager.right_pane['scroll_offset'] = 0
        
        # Start with left pane active
        fm.pane_manager.active_pane = 'left'
        
        # Mock is_dir and archive check
        with patch.object(Path, 'is_dir', return_value=False):
            fm.archive_operations.is_archive = Mock(return_value=False)
            fm.external_program_manager.open_file = Mock()
            
            # Double-click in right pane (column 40 is in right pane)
            event = MouseEvent(
                event_type=MouseEventType.DOUBLE_CLICK,
                column=40,
                row=1,
                sub_cell_x=0.5,
                sub_cell_y=0.5,
                button=MouseButton.LEFT
            )
            
            # Handle the event
            result = fm.handle_mouse_event(event)
            
            # Verify event was handled
            assert result is True
            
            # Verify focus switched to right pane
            assert fm.pane_manager.active_pane == 'right'
    
    def test_double_click_outside_file_area_ignored(self):
        """Double-clicking outside file area should be ignored."""
        # Create mock renderer
        renderer = Mock()
        renderer.get_dimensions.return_value = (24, 80)
        renderer.supports_mouse.return_value = True
        renderer.get_supported_mouse_events.return_value = {MouseEventType.DOUBLE_CLICK}
        renderer.enable_mouse_events.return_value = True
        
        # Create FileManager
        fm = FileManager(renderer)
        
        # Double-click in status bar area (row 22, near bottom)
        event = MouseEvent(
            event_type=MouseEventType.DOUBLE_CLICK,
            column=10,
            row=22,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT
        )
        
        # Handle the event
        result = fm.handle_mouse_event(event)
        
        # Verify event was not handled
        assert result is False
    
    def test_double_click_header_goes_to_parent(self):
        """Double-clicking the header should navigate to parent directory."""
        # Create mock renderer
        renderer = Mock()
        renderer.get_dimensions.return_value = (24, 80)
        renderer.supports_mouse.return_value = True
        renderer.get_supported_mouse_events.return_value = {MouseEventType.DOUBLE_CLICK}
        renderer.enable_mouse_events.return_value = True
        
        # Create FileManager
        fm = FileManager(renderer)
        fm.mark_dirty = Mock()
        
        # Set up test directory structure
        test_dir = Path("/tmp/test_dir/subdir")
        parent_dir = Path("/tmp/test_dir")
        
        # Set up left pane in subdirectory
        fm.pane_manager.left_pane['path'] = test_dir
        fm.pane_manager.left_pane['files'] = []
        fm.pane_manager.left_pane['focused_index'] = 0
        fm.pane_manager.left_pane['scroll_offset'] = 0
        fm.pane_manager.active_pane = 'left'
        
        # Mock Path.parent to return parent directory
        with patch.object(Path, 'parent', new_callable=lambda: property(lambda self: parent_dir)):
            # Mock refresh_files to avoid actual filesystem operations
            fm.refresh_files = Mock()
            fm.save_cursor_position = Mock()
            fm.restore_cursor_position = Mock()
            
            # Create double-click event on left pane header (row 0, column 10)
            event = MouseEvent(
                event_type=MouseEventType.DOUBLE_CLICK,
                column=10,
                row=0,
                sub_cell_x=0.5,
                sub_cell_y=0.5,
                button=MouseButton.LEFT
            )
            
            # Handle the event
            result = fm.handle_mouse_event(event)
            
            # Verify event was handled
            assert result is True
            
            # Verify parent directory navigation was triggered
            assert fm.refresh_files.called
    
    def test_double_click_header_switches_pane_focus(self):
        """Double-clicking inactive pane header should switch focus."""
        # Create mock renderer
        renderer = Mock()
        renderer.get_dimensions.return_value = (24, 80)
        renderer.supports_mouse.return_value = True
        renderer.get_supported_mouse_events.return_value = {MouseEventType.DOUBLE_CLICK}
        renderer.enable_mouse_events.return_value = True
        
        # Create FileManager
        fm = FileManager(renderer)
        fm.mark_dirty = Mock()
        
        # Set up both panes
        test_dir_left = Path("/tmp/left/subdir")
        test_dir_right = Path("/tmp/right/subdir")
        parent_dir = Path("/tmp/right")
        
        fm.pane_manager.left_pane['path'] = test_dir_left
        fm.pane_manager.right_pane['path'] = test_dir_right
        
        # Start with left pane active
        fm.pane_manager.active_pane = 'left'
        
        # Mock Path.parent
        with patch.object(Path, 'parent', new_callable=lambda: property(lambda self: parent_dir)):
            # Mock methods
            fm.refresh_files = Mock()
            fm.save_cursor_position = Mock()
            fm.restore_cursor_position = Mock()
            
            # Double-click on right pane header (column 50 is in right pane)
            event = MouseEvent(
                event_type=MouseEventType.DOUBLE_CLICK,
                column=50,
                row=0,
                sub_cell_x=0.5,
                sub_cell_y=0.5,
                button=MouseButton.LEFT
            )
            
            # Handle the event
            result = fm.handle_mouse_event(event)
            
            # Verify event was handled
            assert result is True
            
            # Verify focus switched to right pane
            assert fm.pane_manager.active_pane == 'right'


class TestDirectoryDiffViewerDoubleClick:
    """Test double-click support in DirectoryDiffViewer."""
    
    def test_double_click_expands_directory(self):
        """Double-clicking a collapsed directory should expand it."""
        # Create mock renderer
        renderer = Mock()
        renderer.get_dimensions.return_value = (24, 80)
        
        # Create mock paths
        left_path = Mock(spec=Path)
        right_path = Mock(spec=Path)
        
        # Create DirectoryDiffViewer
        viewer = DirectoryDiffViewer(renderer, left_path, right_path)
        viewer._dirty = False
        
        # Create a mock directory node
        mock_node = Mock()
        mock_node.is_directory = True
        mock_node.is_expanded = False
        
        # Set up visible nodes
        viewer.visible_nodes = [mock_node]
        viewer.cursor_position = 0
        viewer.scroll_offset = 0
        
        # Mock expand_node method
        viewer.expand_node = Mock()
        
        # Create double-click event on the directory (row 1)
        event = MouseEvent(
            event_type=MouseEventType.DOUBLE_CLICK,
            column=10,
            row=1,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify event was handled
        assert result is True
        
        # Verify expand_node was called
        viewer.expand_node.assert_called_once_with(0)
    
    def test_double_click_collapses_directory(self):
        """Double-clicking an expanded directory should collapse it."""
        # Create mock renderer
        renderer = Mock()
        renderer.get_dimensions.return_value = (24, 80)
        
        # Create mock paths
        left_path = Mock(spec=Path)
        right_path = Mock(spec=Path)
        
        # Create DirectoryDiffViewer
        viewer = DirectoryDiffViewer(renderer, left_path, right_path)
        viewer._dirty = False
        
        # Create a mock directory node
        mock_node = Mock()
        mock_node.is_directory = True
        mock_node.is_expanded = True
        
        # Set up visible nodes
        viewer.visible_nodes = [mock_node]
        viewer.cursor_position = 0
        viewer.scroll_offset = 0
        
        # Mock collapse_node method
        viewer.collapse_node = Mock()
        
        # Create double-click event on the directory (row 1)
        event = MouseEvent(
            event_type=MouseEventType.DOUBLE_CLICK,
            column=10,
            row=1,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify event was handled
        assert result is True
        
        # Verify collapse_node was called
        viewer.collapse_node.assert_called_once_with(0)
    
    def test_double_click_opens_file_diff(self):
        """Double-clicking a file should open the diff viewer."""
        # Create mock renderer
        renderer = Mock()
        renderer.get_dimensions.return_value = (24, 80)
        
        # Create mock paths
        left_path = Mock(spec=Path)
        right_path = Mock(spec=Path)
        
        # Create DirectoryDiffViewer
        viewer = DirectoryDiffViewer(renderer, left_path, right_path)
        viewer._dirty = False
        
        # Create a mock file node
        mock_node = Mock()
        mock_node.is_directory = False
        
        # Set up visible nodes
        viewer.visible_nodes = [mock_node]
        viewer.cursor_position = 0
        viewer.scroll_offset = 0
        
        # Mock open_file_diff method
        viewer.open_file_diff = Mock()
        
        # Create double-click event on the file (row 1)
        event = MouseEvent(
            event_type=MouseEventType.DOUBLE_CLICK,
            column=10,
            row=1,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify event was handled
        assert result is True
        
        # Verify open_file_diff was called
        viewer.open_file_diff.assert_called_once_with(0)
    
    def test_double_click_outside_tree_area_ignored(self):
        """Double-clicking outside tree area should be ignored."""
        # Create mock renderer
        renderer = Mock()
        renderer.get_dimensions.return_value = (24, 80)
        
        # Create mock paths
        left_path = Mock(spec=Path)
        right_path = Mock(spec=Path)
        
        # Create DirectoryDiffViewer
        viewer = DirectoryDiffViewer(renderer, left_path, right_path)
        
        # Double-click in header area (row 0)
        event = MouseEvent(
            event_type=MouseEventType.DOUBLE_CLICK,
            column=10,
            row=0,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify event was not handled
        assert result is False
