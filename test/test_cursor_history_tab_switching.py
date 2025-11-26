#!/usr/bin/env python3

import sys
import tempfile
import time
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_state_manager import TFMStateManager
from tfm_pane_manager import PaneManager
from tfm_main import FileManager
from tfm_config import DefaultConfig


class TestConfig(DefaultConfig):
    """Test configuration with minimal settings"""
    def __init__(self):
        super().__init__()
        self.MAX_CURSOR_HISTORY_ENTRIES = 10


def test_cursor_history_tab_switching():
    """Test TAB key switching between left and right pane histories in cursor history dialog"""
    print("Testing cursor history TAB switching...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directories and files
        test_dirs = []
        for i in range(3):
            test_dir = Path(temp_dir) / f"dir_{i}"
            test_dir.mkdir()
            for j in range(3):
                (test_dir / f"file_{j}.txt").touch()
            test_dirs.append(test_dir)
        
        # Create state manager and pane manager
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_tab_switching")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        config = TestConfig()
        pane_manager = PaneManager(config, test_dirs[0], test_dirs[1], state_manager)
        
        # Build separate histories for left and right panes
        print("Building left pane history:")
        for i, test_dir in enumerate(test_dirs):
            pane_manager.left_pane['path'] = test_dir
            pane_manager.left_pane['files'] = [test_dir / f"file_{i}.txt"]
            pane_manager.left_pane['selected_index'] = 0
            pane_manager.save_cursor_position(pane_manager.left_pane)
            print(f"  {i+1}. {test_dir} -> file_{i}.txt")
            time.sleep(0.01)
        
        print("Building right pane history:")
        for i, test_dir in enumerate(reversed(test_dirs)):
            pane_manager.right_pane['path'] = test_dir
            pane_manager.right_pane['files'] = [test_dir / f"file_{i}.txt"]
            pane_manager.right_pane['selected_index'] = 0
            pane_manager.save_cursor_position(pane_manager.right_pane)
            print(f"  {i+1}. {test_dir} -> file_{i}.txt")
            time.sleep(0.01)
        
        # Test that histories are separate
        left_history = state_manager.get_ordered_pane_history('left')
        right_history = state_manager.get_ordered_pane_history('right')
        
        assert len(left_history) == 3, f"Expected 3 left history entries, got {len(left_history)}"
        assert len(right_history) == 3, f"Expected 3 right history entries, got {len(right_history)}"
        
        # Verify histories are different
        left_paths = [entry['path'] for entry in left_history]
        right_paths = [entry['path'] for entry in right_history]
        
        print(f"Left pane history: {[Path(p).name for p in left_paths]}")
        print(f"Right pane history: {[Path(p).name for p in right_paths]}")
        
        # They should be in reverse order
        assert left_paths != right_paths, "Left and right histories should be different"
        
        # Test the cursor history dialog functionality
        # Create a mock TFM main instance to test the dialog
        class MockTFMMain:
            def __init__(self, pane_manager, state_manager):
                self.pane_manager = pane_manager
                self.state_manager = state_manager
                self.needs_full_redraw = False
                
                # Mock list dialog
                class MockListDialog:
                    def __init__(self):
                        self.is_active = False
                        self.title = ""
                        self.items = []
                        self.callback = None
                        self.custom_key_handler = None
                        self.custom_help_text = None
                        self.last_shown_data = None
                    
                    def show(self, title, items, callback, custom_key_handler=None, custom_help_text=None):
                        self.is_active = True
                        self.title = title
                        self.items = items
                        self.callback = callback
                        self.custom_key_handler = custom_key_handler
                        self.custom_help_text = custom_help_text
                        self.last_shown_data = {
                            'title': title,
                            'items': items.copy(),
                            'has_custom_handler': custom_key_handler is not None,
                            'custom_help_text': custom_help_text
                        }
                    
                    def exit(self):
                        self.is_active = False
                        self.title = ""
                        self.items = []
                        self.callback = None
                        self.custom_key_handler = None
                        self.custom_help_text = None
                
                self.list_dialog = MockListDialog()
            
            def get_current_pane(self):
                return self.pane_manager.left_pane
            
            def _force_immediate_redraw(self):
                pass
            
            def navigate_to_history_path(self, path):
                pass
            
            def _show_cursor_history_for_pane(self, pane_name):
                # Copy the implementation from TFMMain
                history = self.state_manager.get_ordered_pane_history(pane_name)
                
                history_paths = []
                seen_paths = set()
                
                if history:
                    for entry in reversed(history):
                        path = entry['path']
                        if path not in seen_paths:
                            history_paths.append(path)
                            seen_paths.add(path)
                
                if not history_paths:
                    history_paths = [f"No history available for {pane_name} pane"]
                
                def on_history_selected(selected_path):
                    if selected_path and not selected_path.startswith("No history available"):
                        self.navigate_to_history_path(selected_path)
                
                def handle_custom_keys(key):
                    if key == 9:  # TAB key
                        other_pane = 'right' if pane_name == 'left' else 'left'
                        self.list_dialog.exit()
                        self._show_cursor_history_for_pane(other_pane)
                        self.needs_full_redraw = True
                        return True
                    return False
                
                title = f"History - {pane_name.title()}"
                other_pane_name = 'Right' if pane_name == 'left' else 'Left'
                help_text = f"↑↓:select  Enter:choose  TAB:switch to {other_pane_name}  Type:search  ESC:cancel"
                self.list_dialog.show(title, history_paths, on_history_selected, handle_custom_keys, help_text)
                self.needs_full_redraw = True
        
        mock_tfm = MockTFMMain(pane_manager, state_manager)
        
        # Test showing left pane history
        print("\nTesting left pane history dialog:")
        mock_tfm._show_cursor_history_for_pane('left')
        
        assert mock_tfm.list_dialog.is_active == True
        assert mock_tfm.list_dialog.title == "History - Left"
        assert "TAB:switch to Right" in mock_tfm.list_dialog.custom_help_text
        assert mock_tfm.list_dialog.custom_key_handler is not None
        assert len(mock_tfm.list_dialog.items) == 3
        
        left_dialog_items = mock_tfm.list_dialog.items.copy()
        print(f"Left dialog items: {[Path(p).name for p in left_dialog_items]}")
        
        # Test TAB key switching to right pane
        print("\nTesting TAB key switching to right pane:")
        tab_handled = mock_tfm.list_dialog.custom_key_handler(9)  # TAB key
        
        assert tab_handled == True, "TAB key should be handled by custom handler"
        assert mock_tfm.list_dialog.title == "History - Right"
        assert "TAB:switch to Left" in mock_tfm.list_dialog.custom_help_text
        assert len(mock_tfm.list_dialog.items) == 3
        
        right_dialog_items = mock_tfm.list_dialog.items.copy()
        print(f"Right dialog items: {[Path(p).name for p in right_dialog_items]}")
        
        # Verify the items are different (different pane histories)
        assert left_dialog_items != right_dialog_items, "Left and right dialog items should be different"
        
        # Test TAB key switching back to left pane
        print("\nTesting TAB key switching back to left pane:")
        tab_handled = mock_tfm.list_dialog.custom_key_handler(9)  # TAB key
        
        assert tab_handled == True, "TAB key should be handled by custom handler"
        assert mock_tfm.list_dialog.title == "History - Left"
        assert "TAB:switch to Right" in mock_tfm.list_dialog.custom_help_text
        
        back_to_left_items = mock_tfm.list_dialog.items.copy()
        assert back_to_left_items == left_dialog_items, "Should return to original left pane items"
        
        print("✅ TAB switching between pane histories works correctly")
        
        # Test with empty history
        print("\nTesting with empty history:")
        state_manager.clear_pane_history('left')
        mock_tfm._show_cursor_history_for_pane('left')
        
        assert len(mock_tfm.list_dialog.items) == 1
        assert mock_tfm.list_dialog.items[0].startswith("No history available")
        
        print("✅ Empty history handling works correctly")
        
        # Clean up
        state_manager.cleanup_session()
        print("✅ Cursor history TAB switching test completed\n")


if __name__ == "__main__":
    test_cursor_history_tab_switching()
    print("All cursor history TAB switching tests passed!")