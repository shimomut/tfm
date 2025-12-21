#!/usr/bin/env python3
"""
Demo: Recursion Fix for FileManagerLayer

This demo verifies that the recursion issue in FileManagerLayer.handle_key_event()
has been fixed. The issue was that FileManagerLayer was calling file_manager.handle_input(),
which then called back into the layer stack, creating infinite recursion.

The fix extracts the main screen key handling logic into a separate method
handle_main_screen_key_event() that can be called without recursion.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ttk import KeyEvent, KeyCode, ModifierKey
from src.tfm_ui_layer import FileManagerLayer
from unittest.mock import Mock


def test_down_key_no_recursion():
    """Test that DOWN key doesn't cause recursion."""
    print("Testing DOWN key handling without recursion...")
    
    # Create a mock FileManager with minimal required attributes
    mock_fm = Mock()
    mock_fm.needs_full_redraw = False
    mock_fm.pane_manager = Mock()
    mock_fm.pane_manager.active_pane = 'left'
    mock_fm.pane_manager.left_pane = {
        'focused_index': 0,
        'files': ['file1.txt', 'file2.txt', 'file3.txt'],
        'scroll_offset': 0
    }
    mock_fm.log_manager = Mock()
    mock_fm.log_manager.scroll_log_up = Mock(return_value=False)
    mock_fm.log_manager.scroll_log_down = Mock(return_value=False)
    mock_fm.config = Mock()
    mock_fm.key_bindings = {}
    
    def get_current_pane():
        return mock_fm.pane_manager.left_pane
    
    mock_fm.get_current_pane = get_current_pane
    mock_fm.is_key_for_action = Mock(return_value=False)
    
    # Import the actual handle_main_screen_key_event method
    from src.tfm_main import FileManager
    mock_fm.handle_main_screen_key_event = FileManager.handle_main_screen_key_event.__get__(mock_fm, type(mock_fm))
    
    # Create FileManagerLayer
    layer = FileManagerLayer(mock_fm)
    
    # Create DOWN key event
    down_event = KeyEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.NONE)
    
    # Test handling - this should NOT cause recursion
    print("  Handling DOWN key event...")
    result = layer.handle_key_event(down_event)
    
    print(f"  Result: {result}")
    print(f"  Focused index: {mock_fm.pane_manager.left_pane['focused_index']}")
    print(f"  Layer marked dirty: {layer._dirty}")
    
    # Verify the key was handled
    assert result is True, "DOWN key should be consumed"
    assert mock_fm.pane_manager.left_pane['focused_index'] == 1, "Focused index should increment"
    assert layer._dirty is True, "Layer should be marked dirty"
    
    print("✓ DOWN key handled successfully without recursion!")
    return True


def test_up_key_no_recursion():
    """Test that UP key doesn't cause recursion."""
    print("\nTesting UP key handling without recursion...")
    
    # Create a mock FileManager
    mock_fm = Mock()
    mock_fm.needs_full_redraw = False
    mock_fm.pane_manager = Mock()
    mock_fm.pane_manager.active_pane = 'left'
    mock_fm.pane_manager.left_pane = {
        'focused_index': 2,  # Start at index 2
        'files': ['file1.txt', 'file2.txt', 'file3.txt'],
        'scroll_offset': 0
    }
    mock_fm.log_manager = Mock()
    mock_fm.log_manager.scroll_log_up = Mock(return_value=False)
    mock_fm.log_manager.scroll_log_down = Mock(return_value=False)
    mock_fm.config = Mock()
    mock_fm.key_bindings = {}
    
    def get_current_pane():
        return mock_fm.pane_manager.left_pane
    
    mock_fm.get_current_pane = get_current_pane
    mock_fm.is_key_for_action = Mock(return_value=False)
    
    # Import the actual handle_main_screen_key_event method
    from src.tfm_main import FileManager
    mock_fm.handle_main_screen_key_event = FileManager.handle_main_screen_key_event.__get__(mock_fm, type(mock_fm))
    
    # Create FileManagerLayer
    layer = FileManagerLayer(mock_fm)
    layer._dirty = False  # Clear initial dirty flag
    
    # Create UP key event
    up_event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
    
    # Test handling
    print("  Handling UP key event...")
    result = layer.handle_key_event(up_event)
    
    print(f"  Result: {result}")
    print(f"  Focused index: {mock_fm.pane_manager.left_pane['focused_index']}")
    print(f"  Layer marked dirty: {layer._dirty}")
    
    # Verify the key was handled
    assert result is True, "UP key should be consumed"
    assert mock_fm.pane_manager.left_pane['focused_index'] == 1, "Focused index should decrement"
    assert layer._dirty is True, "Layer should be marked dirty"
    
    print("✓ UP key handled successfully without recursion!")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("FileManagerLayer Recursion Fix Demo")
    print("=" * 70)
    print()
    print("This demo verifies that the recursion bug has been fixed.")
    print("Previously, FileManagerLayer.handle_key_event() called")
    print("file_manager.handle_input(), which called back into the layer")
    print("stack, creating infinite recursion.")
    print()
    print("The fix extracts main screen key handling into a separate method")
    print("handle_main_screen_key_event() that doesn't cause recursion.")
    print()
    
    try:
        test_down_key_no_recursion()
        test_up_key_no_recursion()
        
        print()
        print("=" * 70)
        print("✓ All tests passed! Recursion issue is fixed.")
        print("=" * 70)
        return 0
    except Exception as e:
        print()
        print("=" * 70)
        print(f"✗ Test failed: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
