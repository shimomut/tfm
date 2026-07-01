#!/usr/bin/env python3
"""
Test that terminal-specific Shift+Arrow codes have been moved to TTK curses backend
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_constants_removed_from_tfm():
    """Test that terminal-specific key constants are no longer in TFM"""
    print("Testing that terminal-specific key constants removed from TFM...")
    
    try:
        # These constants should no longer be in tfm_const
        from tfm_const import KEY_SHIFT_UP_1
        print("  ✗ KEY_SHIFT_UP_1 should not be in tfm_const (moved to TTK backend)")
        return False
    except (ImportError, AttributeError):
        pass  # Expected - constants moved to TTK
    
    print("  ✓ Terminal-specific key constants removed from TFM")
    return True


def test_tfm_uses_standard_keys():
    """Test that TFM now uses standard KeyCode with SHIFT modifier"""
    print("Testing that TFM uses standard KeyCode with SHIFT modifier...")
    
    # Read the main file and verify it doesn't use the old constants
    tfm_main_path = Path(__file__).parent.parent.parent / 'src' / 'tfm_main.py'
    with open(tfm_main_path, 'r') as f:
        content = f.read()
    
    # Check that old constants are not used
    old_constants = ['KEY_SHIFT_UP_1', 'KEY_SHIFT_DOWN_1', 'KEY_SHIFT_LEFT_1', 'KEY_SHIFT_RIGHT_1']
    for const in old_constants:
        if const in content:
            print(f"  ✗ Found {const} in tfm_main.py - should use KeyCode with SHIFT modifier")
            return False
    
    # Check that new pattern is used
    if 'KeyCode.UP and event.modifiers & ModifierKey.SHIFT' not in content:
        print("  ✗ Expected pattern 'KeyCode.UP and event.modifiers & ModifierKey.SHIFT' not found")
        return False
    
    print("  ✓ TFM uses standard KeyCode with SHIFT modifier")
    return True


def test_backend_has_translation():
    """Test that curses backend has shift key translation logic"""
    print("Testing that curses backend has shift key translation...")
    
    backend_path = Path(__file__).parent.parent / 'backends' / 'curses_backend.py'
    with open(backend_path, 'r') as f:
        content = f.read()
    
    # Check for the private constants
    if '_KEY_SHIFT_UP_1' not in content:
        print("  ✗ _KEY_SHIFT_UP_1 not found in curses backend")
        return False
    
    # Check for translation logic
    if 'if key in (_KEY_SHIFT_UP_1, _KEY_SHIFT_UP_2):' not in content:
        print("  ✗ Shift key translation logic not found in curses backend")
        return False
    
    # Check that it returns KeyEvent with SHIFT modifier
    if 'return KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.SHIFT)' not in content:
        print("  ✗ Expected KeyEvent with SHIFT modifier not found")
        return False
    
    print("  ✓ Curses backend has shift key translation logic")
    return True


def main():
    """Run all tests"""
    print("=" * 70)
    print("TTK Curses Backend Shift+Arrow Key Refactoring Test")
    print("=" * 70)
    print()
    
    tests = [
        test_constants_removed_from_tfm,
        test_tfm_uses_standard_keys,
        test_backend_has_translation,
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"  ✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 70)
    if passed == len(tests):
        print(f"✓ All {len(tests)} tests passed!")
        print("\nRefactoring complete:")
        print("  • Terminal-specific key codes moved from TFM to TTK curses backend")
        print("  • TFM now uses standard KeyCode with ModifierKey.SHIFT")
        print("  • Curses backend translates terminal codes to standard events")
        return True
    else:
        print(f"✗ {len(tests) - passed} test(s) failed!")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
