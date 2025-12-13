#!/usr/bin/env python3
"""
Verification script for TTK test interface implementation.

This script verifies that the test interface is correctly implemented
and integrated with the demo application.
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from unittest.mock import Mock
from ttk.demo.test_interface import TestInterface, create_test_interface
from ttk.input_event import InputEvent, KeyCode, ModifierKey
from ttk.renderer import TextAttribute


def verify_test_interface_creation():
    """Verify test interface can be created."""
    print("Testing test interface creation...")
    
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (40, 80)
    
    interface = TestInterface(mock_renderer)
    assert interface is not None
    assert interface.renderer == mock_renderer
    assert not interface.running
    
    print("✓ Test interface creation works")


def verify_factory_function():
    """Verify factory function works."""
    print("Testing factory function...")
    
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (40, 80)
    
    interface = create_test_interface(mock_renderer)
    assert isinstance(interface, TestInterface)
    assert interface.renderer == mock_renderer
    
    print("✓ Factory function works")


def verify_color_initialization():
    """Verify color initialization."""
    print("Testing color initialization...")
    
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (40, 80)
    
    interface = TestInterface(mock_renderer)
    interface.initialize_colors()
    
    # Should have initialized 10 color pairs
    assert mock_renderer.init_color_pair.call_count == 10
    
    print("✓ Color initialization works")


def verify_section_drawing():
    """Verify all sections can be drawn."""
    print("Testing section drawing...")
    
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (40, 80)
    
    interface = TestInterface(mock_renderer)
    
    # Test each section
    row = interface.draw_header(0)
    assert row > 0
    
    row = interface.draw_color_test(row)
    assert row > 0
    
    row = interface.draw_attribute_test(row)
    assert row > 0
    
    row = interface.draw_shape_test(row)
    assert row >= 0
    
    row = interface.draw_coordinate_info(row)
    assert row > 0
    
    row = interface.draw_input_echo(row)
    assert row >= 0
    
    print("✓ All sections can be drawn")


def verify_input_handling():
    """Verify input handling."""
    print("Testing input handling...")
    
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (40, 80)
    
    interface = TestInterface(mock_renderer)
    
    # Test printable character
    event = InputEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    result = interface.handle_input(event)
    assert result is True
    assert interface.last_input == event
    
    # Test quit command
    quit_event = InputEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
    result = interface.handle_input(quit_event)
    assert result is False
    
    # Test ESC key
    esc_event = InputEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
    result = interface.handle_input(esc_event)
    assert result is False
    
    print("✓ Input handling works")


def verify_interface_drawing():
    """Verify complete interface drawing."""
    print("Testing complete interface drawing...")
    
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (40, 80)
    
    interface = TestInterface(mock_renderer)
    interface.draw_interface()
    
    # Should have cleared and refreshed
    mock_renderer.clear.assert_called_once()
    mock_renderer.refresh.assert_called_once()
    
    # Should have drawn text
    assert mock_renderer.draw_text.called
    
    print("✓ Complete interface drawing works")


def verify_integration_with_demo():
    """Verify integration with demo application."""
    print("Testing integration with demo application...")
    
    # Import should work
    from ttk.demo.demo_ttk import DemoApplication
    
    # Should be able to import test_interface from demo
    from ttk.demo.test_interface import create_test_interface
    
    print("✓ Integration with demo application works")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("TTK Test Interface Verification")
    print("=" * 60)
    print()
    
    try:
        verify_test_interface_creation()
        verify_factory_function()
        verify_color_initialization()
        verify_section_drawing()
        verify_input_handling()
        verify_interface_drawing()
        verify_integration_with_demo()
        
        print()
        print("=" * 60)
        print("✓ All verification tests passed!")
        print("=" * 60)
        print()
        print("The test interface is correctly implemented and ready to use.")
        print()
        print("To run the demo:")
        print("  python ttk/demo/demo_ttk.py --backend curses")
        print("  python ttk/demo/demo_ttk.py --backend metal  # macOS only")
        print()
        
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print("✗ Verification failed!")
        print("=" * 60)
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ Unexpected error!")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
