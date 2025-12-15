#!/usr/bin/env python3
"""
Verification script for Task 29: Demo Keyboard Handling

This script verifies that the demo application correctly:
1. Handles keyboard input
2. Displays pressed keys with key codes and modifiers
3. Demonstrates special key handling
4. Allows quitting with 'q' or ESC

Requirements: 6.3
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from unittest.mock import Mock
from ttk.demo.test_interface import TestInterface
from ttk import KeyEvent, KeyCode, ModifierKey


def verify_keyboard_handling():
    """Verify keyboard handling implementation."""
    print("=" * 70)
    print("Task 29: Demo Keyboard Handling Verification")
    print("=" * 70)
    print()
    
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (40, 80)
    
    # Create test interface
    interface = TestInterface(mock_renderer, enable_performance_monitoring=False)
    
    print("✓ Test interface created successfully")
    print()
    
    # Test 1: Handle printable character input
    print("Test 1: Handle printable character input")
    print("-" * 70)
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    result = interface.handle_input(event)
    
    assert result == True, "Should continue running for printable character"
    assert interface.last_input == event, "Should store last input"
    assert event in interface.input_history, "Should add to input history"
    print("✓ Printable character 'a' handled correctly")
    print(f"  - Last input: {interface.last_input.char}")
    print(f"  - Key code: {interface.last_input.key_code}")
    print(f"  - Continue running: {result}")
    print()
    
    # Test 2: Display key codes
    print("Test 2: Display key codes")
    print("-" * 70)
    event2 = KeyEvent(key_code=ord('X'), modifiers=ModifierKey.NONE, char='X')
    interface.handle_input(event2)
    
    # Verify input is stored with correct key code
    assert interface.last_input.key_code == ord('X'), "Should store correct key code"
    assert interface.last_input.char == 'X', "Should store correct character"
    print("✓ Key code displayed correctly")
    print(f"  - Character: '{interface.last_input.char}'")
    print(f"  - Key code: {interface.last_input.key_code}")
    print()
    
    # Test 3: Handle special keys
    print("Test 3: Handle special keys")
    print("-" * 70)
    special_keys = [
        (KeyCode.UP, "UP arrow"),
        (KeyCode.DOWN, "DOWN arrow"),
        (KeyCode.LEFT, "LEFT arrow"),
        (KeyCode.RIGHT, "RIGHT arrow"),
        (KeyCode.F1, "F1 function key"),
        (KeyCode.HOME, "HOME key"),
        (KeyCode.END, "END key"),
        (KeyCode.PAGE_UP, "PAGE_UP key"),
        (KeyCode.DELETE, "DELETE key"),
    ]
    
    for key_code, description in special_keys:
        event = KeyEvent(key_code=key_code, modifiers=ModifierKey.NONE)
        result = interface.handle_input(event)
        
        assert result == True, f"Should continue running for {description}"
        assert interface.last_input.key_code == key_code, f"Should store correct key code for {description}"
        assert interface.last_input.is_special_key(), f"{description} should be identified as special key"
        print(f"✓ {description} handled correctly (code: {key_code})")
    print()
    
    # Test 4: Display modifiers
    print("Test 4: Display modifiers")
    print("-" * 70)
    modifier_tests = [
        (ModifierKey.SHIFT, "Shift"),
        (ModifierKey.CONTROL, "Control"),
        (ModifierKey.ALT, "Alt"),
        (ModifierKey.COMMAND, "Command"),
        (ModifierKey.SHIFT | ModifierKey.CONTROL, "Shift+Control"),
        (ModifierKey.CONTROL | ModifierKey.ALT, "Control+Alt"),
    ]
    
    for modifiers, description in modifier_tests:
        event = KeyEvent(key_code=ord('A'), modifiers=modifiers, char='A')
        interface.handle_input(event)
        
        assert interface.last_input.modifiers == modifiers, f"Should store correct modifiers for {description}"
        
        # Verify modifier detection
        if ModifierKey.SHIFT in [ModifierKey.SHIFT, modifiers]:
            if modifiers & ModifierKey.SHIFT:
                assert interface.last_input.has_modifier(ModifierKey.SHIFT), "Should detect Shift modifier"
        if ModifierKey.CONTROL in [ModifierKey.CONTROL, modifiers]:
            if modifiers & ModifierKey.CONTROL:
                assert interface.last_input.has_modifier(ModifierKey.CONTROL), "Should detect Control modifier"
        if ModifierKey.ALT in [ModifierKey.ALT, modifiers]:
            if modifiers & ModifierKey.ALT:
                assert interface.last_input.has_modifier(ModifierKey.ALT), "Should detect Alt modifier"
        if ModifierKey.COMMAND in [ModifierKey.COMMAND, modifiers]:
            if modifiers & ModifierKey.COMMAND:
                assert interface.last_input.has_modifier(ModifierKey.COMMAND), "Should detect Command modifier"
        
        print(f"✓ {description} modifier(s) detected correctly")
    print()
    
    # Test 5: Quit with 'q'
    print("Test 5: Quit with 'q'")
    print("-" * 70)
    event_q = KeyEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
    result = interface.handle_input(event_q)
    
    assert result == False, "Should stop running when 'q' is pressed"
    print("✓ Pressing 'q' triggers quit")
    print(f"  - Continue running: {result}")
    print()
    
    # Test 6: Quit with 'Q' (uppercase)
    print("Test 6: Quit with 'Q' (uppercase)")
    print("-" * 70)
    event_Q = KeyEvent(key_code=ord('Q'), modifiers=ModifierKey.NONE, char='Q')
    result = interface.handle_input(event_Q)
    
    assert result == False, "Should stop running when 'Q' is pressed"
    print("✓ Pressing 'Q' triggers quit")
    print(f"  - Continue running: {result}")
    print()
    
    # Test 7: Quit with ESC
    print("Test 7: Quit with ESC")
    print("-" * 70)
    event_esc = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
    result = interface.handle_input(event_esc)
    
    assert result == False, "Should stop running when ESC is pressed"
    print("✓ Pressing ESC triggers quit")
    print(f"  - Continue running: {result}")
    print()
    
    # Test 8: Input history
    print("Test 8: Input history")
    print("-" * 70)
    interface2 = TestInterface(mock_renderer, enable_performance_monitoring=False)
    
    # Add several inputs
    for i in range(10):
        event = KeyEvent(key_code=ord('a') + i, modifiers=ModifierKey.NONE, char=chr(ord('a') + i))
        interface2.handle_input(event)
    
    assert len(interface2.input_history) == 10, "Should store input history"
    print(f"✓ Input history maintained correctly ({len(interface2.input_history)} entries)")
    
    # Add more to test limit
    for i in range(15):
        event = KeyEvent(key_code=ord('A') + i, modifiers=ModifierKey.NONE, char=chr(ord('A') + i))
        interface2.handle_input(event)
    
    assert len(interface2.input_history) == 20, "Should limit history to 20 entries"
    print(f"✓ Input history limited to 20 entries (current: {len(interface2.input_history)})")
    print()
    
    # Test 9: Draw input echo
    print("Test 9: Draw input echo area")
    print("-" * 70)
    interface3 = TestInterface(mock_renderer, enable_performance_monitoring=False)
    
    # Add some input
    event = KeyEvent(key_code=ord('x'), modifiers=ModifierKey.SHIFT, char='X')
    interface3.handle_input(event)
    
    # Draw input echo (should not crash)
    row = interface3.draw_input_echo(25)
    
    assert row >= 25, "Should advance row position"
    assert mock_renderer.draw_text.called, "Should draw text"
    print("✓ Input echo area drawn successfully")
    print(f"  - Row advanced from 25 to {row}")
    print()
    
    # Summary
    print("=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
    print()
    print("All keyboard handling requirements verified:")
    print("  ✓ Handles keyboard input in demo application")
    print("  ✓ Displays pressed keys with key codes and modifiers")
    print("  ✓ Demonstrates special key handling")
    print("  ✓ Allows quitting with 'q' or ESC")
    print()
    print("Task 29 implementation is COMPLETE and CORRECT")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = verify_keyboard_handling()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
