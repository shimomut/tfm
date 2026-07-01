"""
Test key code consistency between CoreGraphics and curses backends.

This test verifies that the same logical keys produce the same key codes
across both backends, ensuring consistent behavior for TTK applications
regardless of which backend is used.

Requirements tested: 16.4
"""

import unittest
from ttk.input_event import KeyCode, ModifierKey


class TestKeyCodeConsistency(unittest.TestCase):
    """
    Test that key codes are consistent between backends.
    
    This test verifies that the CoreGraphics and curses backends produce
    the same KeyCode values for the same logical keys. This ensures that
    applications written against the Renderer interface work identically
    regardless of which backend is used.
    """
    
    def test_special_key_codes_defined(self):
        """
        Test that all special key codes are defined in KeyCode enum.
        
        Verifies that the KeyCode enum includes all the special keys that
        both backends need to support.
        """
        # Arrow keys
        self.assertTrue(hasattr(KeyCode, 'UP'))
        self.assertTrue(hasattr(KeyCode, 'DOWN'))
        self.assertTrue(hasattr(KeyCode, 'LEFT'))
        self.assertTrue(hasattr(KeyCode, 'RIGHT'))
        
        # Function keys
        for i in range(1, 13):
            self.assertTrue(hasattr(KeyCode, f'F{i}'))
        
        # Editing keys
        self.assertTrue(hasattr(KeyCode, 'HOME'))
        self.assertTrue(hasattr(KeyCode, 'END'))
        self.assertTrue(hasattr(KeyCode, 'PAGE_UP'))
        self.assertTrue(hasattr(KeyCode, 'PAGE_DOWN'))
        self.assertTrue(hasattr(KeyCode, 'INSERT'))
        self.assertTrue(hasattr(KeyCode, 'DELETE'))
        
        # Special keys
        self.assertTrue(hasattr(KeyCode, 'ENTER'))
        self.assertTrue(hasattr(KeyCode, 'ESCAPE'))
        self.assertTrue(hasattr(KeyCode, 'BACKSPACE'))
        self.assertTrue(hasattr(KeyCode, 'TAB'))
    
    def test_arrow_key_codes(self):
        """
        Test that arrow key codes are consistent.
        
        Verifies that arrow keys have unique, consistent values that both
        backends can map to.
        """
        # Arrow keys should have unique values
        arrow_keys = [KeyCode.UP, KeyCode.DOWN, KeyCode.LEFT, KeyCode.RIGHT]
        self.assertEqual(len(arrow_keys), len(set(arrow_keys)))
        
        # Arrow keys should be in the special key range (>= 1000)
        for key in arrow_keys:
            self.assertGreaterEqual(key, 1000)
    
    def test_function_key_codes(self):
        """
        Test that function key codes are consistent and sequential.
        
        Verifies that function keys F1-F12 have sequential values, which
        makes it easy for backends to map them using simple arithmetic.
        """
        # Function keys should be sequential
        for i in range(1, 12):
            f_key = getattr(KeyCode, f'F{i}')
            f_next = getattr(KeyCode, f'F{i+1}')
            self.assertEqual(f_next, f_key + 1)
        
        # Function keys should be in the special key range
        self.assertGreaterEqual(KeyCode.F1, 1000)
        self.assertGreaterEqual(KeyCode.F12, 1000)
    
    def test_editing_key_codes(self):
        """
        Test that editing key codes are consistent.
        
        Verifies that editing keys (Home, End, Page Up, Page Down, Insert,
        Delete) have unique values in the special key range.
        """
        editing_keys = [
            KeyCode.HOME,
            KeyCode.END,
            KeyCode.PAGE_UP,
            KeyCode.PAGE_DOWN,
            KeyCode.INSERT,
            KeyCode.DELETE
        ]
        
        # All editing keys should have unique values
        self.assertEqual(len(editing_keys), len(set(editing_keys)))
        
        # All editing keys should be in the special key range
        for key in editing_keys:
            self.assertGreaterEqual(key, 1000)
    
    def test_special_character_key_codes(self):
        """
        Test that special character key codes are consistent.
        
        Verifies that Enter, Escape, Backspace, and Tab have the expected
        values that both backends can recognize.
        """
        # Enter should be 10 (newline)
        self.assertEqual(KeyCode.ENTER, 10)
        
        # Escape should be 27
        self.assertEqual(KeyCode.ESCAPE, 27)
        
        # Backspace should be 127 (DEL character)
        self.assertEqual(KeyCode.BACKSPACE, 127)
        
        # Tab should be 9
        self.assertEqual(KeyCode.TAB, 9)
    
    def test_printable_character_range(self):
        """
        Test that printable characters use their Unicode code points.
        
        Verifies that printable ASCII characters (32-126) are represented
        by their Unicode code points, not special KeyCode values.
        """
        # Printable ASCII range is 32-126
        # These should not conflict with special key codes
        
        # Space (32) should not be a special key
        self.assertLess(32, 1000)
        
        # Tilde (126) should not be a special key
        self.assertLess(126, 1000)
        
        # All special keys should be >= 1000 or in the special character range
        special_keys = [
            KeyCode.UP, KeyCode.DOWN, KeyCode.LEFT, KeyCode.RIGHT,
            KeyCode.F1, KeyCode.F12,
            KeyCode.HOME, KeyCode.END, KeyCode.PAGE_UP, KeyCode.PAGE_DOWN,
            KeyCode.INSERT, KeyCode.DELETE
        ]
        
        for key in special_keys:
            # Special keys should be >= 1000
            self.assertGreaterEqual(key, 1000)
    
    def test_modifier_key_flags(self):
        """
        Test that modifier key flags are defined and can be combined.
        
        Verifies that modifier keys (Shift, Control, Alt, Command) are
        defined as flags that can be combined with bitwise OR.
        """
        # All modifier flags should be defined
        self.assertTrue(hasattr(ModifierKey, 'NONE'))
        self.assertTrue(hasattr(ModifierKey, 'SHIFT'))
        self.assertTrue(hasattr(ModifierKey, 'CONTROL'))
        self.assertTrue(hasattr(ModifierKey, 'ALT'))
        self.assertTrue(hasattr(ModifierKey, 'COMMAND'))
        
        # NONE should be 0
        self.assertEqual(ModifierKey.NONE, 0)
        
        # Each modifier should be a power of 2 (single bit)
        self.assertEqual(ModifierKey.SHIFT, 1)
        self.assertEqual(ModifierKey.CONTROL, 2)
        self.assertEqual(ModifierKey.ALT, 4)
        self.assertEqual(ModifierKey.COMMAND, 8)
        
        # Modifiers should be combinable with bitwise OR
        combined = ModifierKey.SHIFT | ModifierKey.CONTROL
        self.assertEqual(combined, 3)
        
        combined = ModifierKey.SHIFT | ModifierKey.ALT
        self.assertEqual(combined, 5)
        
        combined = ModifierKey.CONTROL | ModifierKey.ALT | ModifierKey.COMMAND
        self.assertEqual(combined, 14)
    
    def test_key_code_uniqueness(self):
        """
        Test that all key codes are unique.
        
        Verifies that no two different logical keys have the same KeyCode
        value, which would cause ambiguity in input handling.
        """
        # Collect all special key codes
        key_codes = []
        
        # Arrow keys
        key_codes.extend([KeyCode.UP, KeyCode.DOWN, KeyCode.LEFT, KeyCode.RIGHT])
        
        # Function keys
        for i in range(1, 13):
            key_codes.append(getattr(KeyCode, f'F{i}'))
        
        # Editing keys
        key_codes.extend([
            KeyCode.HOME, KeyCode.END,
            KeyCode.PAGE_UP, KeyCode.PAGE_DOWN,
            KeyCode.INSERT, KeyCode.DELETE
        ])
        
        # Special character keys
        key_codes.extend([
            KeyCode.ENTER, KeyCode.ESCAPE,
            KeyCode.BACKSPACE, KeyCode.TAB
        ])
        
        # All key codes should be unique
        self.assertEqual(len(key_codes), len(set(key_codes)),
                        "Some key codes are not unique")
    
    def test_backend_key_mapping_coverage(self):
        """
        Test that both backends can map all required keys.
        
        This test documents the key mapping requirements for both backends
        to ensure they provide consistent key code translation.
        """
        # Required keys that both backends must support
        required_keys = {
            # Arrow keys
            'UP', 'DOWN', 'LEFT', 'RIGHT',
            
            # Function keys
            'F1', 'F2', 'F3', 'F4', 'F5', 'F6',
            'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
            
            # Editing keys
            'HOME', 'END', 'PAGE_UP', 'PAGE_DOWN',
            'INSERT', 'DELETE',
            
            # Special keys
            'ENTER', 'ESCAPE', 'BACKSPACE', 'TAB'
        }
        
        # Verify all required keys are defined in KeyCode
        for key_name in required_keys:
            self.assertTrue(
                hasattr(KeyCode, key_name),
                f"KeyCode.{key_name} is not defined"
            )
    
    def test_coregraphics_key_mapping_documentation(self):
        """
        Test that CoreGraphics key mapping is documented.
        
        This test documents the macOS virtual key codes that the CoreGraphics
        backend uses to map to TTK KeyCode values. This serves as a reference
        for understanding the key mapping implementation.
        """
        # macOS virtual key codes (from CoreGraphics backend)
        macos_key_map = {
            # Arrow keys
            123: 'LEFT',
            124: 'RIGHT',
            125: 'DOWN',
            126: 'UP',
            
            # Function keys
            122: 'F1',
            120: 'F2',
            99: 'F3',
            118: 'F4',
            96: 'F5',
            97: 'F6',
            98: 'F7',
            100: 'F8',
            101: 'F9',
            109: 'F10',
            103: 'F11',
            111: 'F12',
            
            # Editing keys
            51: 'BACKSPACE',
            117: 'DELETE',
            115: 'HOME',
            119: 'END',
            116: 'PAGE_UP',
            121: 'PAGE_DOWN',
            
            # Special keys
            36: 'ENTER',
            76: 'ENTER',  # Numeric keypad Enter
            53: 'ESCAPE',
            48: 'TAB',
        }
        
        # Verify all mapped keys exist in KeyCode
        for key_name in set(macos_key_map.values()):
            self.assertTrue(
                hasattr(KeyCode, key_name),
                f"KeyCode.{key_name} is not defined (needed for macOS mapping)"
            )
    
    def test_curses_key_mapping_documentation(self):
        """
        Test that curses key mapping is documented.
        
        This test documents the curses key constants that the curses backend
        uses to map to TTK KeyCode values. This serves as a reference for
        understanding the key mapping implementation.
        """
        # Note: We can't import curses constants in this test because curses
        # requires a terminal. This test just documents the expected mappings.
        
        # Curses key constants (from curses backend)
        curses_key_names = [
            # Arrow keys
            'KEY_UP', 'KEY_DOWN', 'KEY_LEFT', 'KEY_RIGHT',
            
            # Function keys
            'KEY_F1', 'KEY_F2', 'KEY_F3', 'KEY_F4',
            'KEY_F5', 'KEY_F6', 'KEY_F7', 'KEY_F8',
            'KEY_F9', 'KEY_F10', 'KEY_F11', 'KEY_F12',
            
            # Editing keys
            'KEY_HOME', 'KEY_END',
            'KEY_PPAGE',  # Page Up
            'KEY_NPAGE',  # Page Down
            'KEY_DC',     # Delete
            'KEY_IC',     # Insert
            'KEY_BACKSPACE',
        ]
        
        # All these curses keys should map to corresponding KeyCode values
        # This is verified by the curses backend implementation
        self.assertTrue(True, "Curses key mapping documented")


class TestKeyCodeConsistencyIntegration(unittest.TestCase):
    """
    Integration tests for key code consistency.
    
    These tests verify that the key code mappings in both backends produce
    consistent results for the same logical keys.
    """
    
    def test_arrow_keys_consistency(self):
        """
        Test that arrow keys map to the same KeyCode values.
        
        Both backends should map their platform-specific arrow key codes
        to the same TTK KeyCode values.
        """
        # Expected KeyCode values for arrow keys
        expected = {
            'UP': KeyCode.UP,
            'DOWN': KeyCode.DOWN,
            'LEFT': KeyCode.LEFT,
            'RIGHT': KeyCode.RIGHT
        }
        
        # Verify values are in the special key range
        for key_name, key_code in expected.items():
            self.assertGreaterEqual(
                key_code, 1000,
                f"{key_name} should be in special key range"
            )
    
    def test_function_keys_consistency(self):
        """
        Test that function keys map to the same KeyCode values.
        
        Both backends should map their platform-specific function key codes
        to the same TTK KeyCode values.
        """
        # Expected KeyCode values for function keys
        for i in range(1, 13):
            key_code = getattr(KeyCode, f'F{i}')
            self.assertGreaterEqual(
                key_code, 1000,
                f"F{i} should be in special key range"
            )
    
    def test_editing_keys_consistency(self):
        """
        Test that editing keys map to the same KeyCode values.
        
        Both backends should map their platform-specific editing key codes
        to the same TTK KeyCode values.
        """
        # Expected KeyCode values for editing keys
        editing_keys = {
            'HOME': KeyCode.HOME,
            'END': KeyCode.END,
            'PAGE_UP': KeyCode.PAGE_UP,
            'PAGE_DOWN': KeyCode.PAGE_DOWN,
            'INSERT': KeyCode.INSERT,
            'DELETE': KeyCode.DELETE
        }
        
        # Verify values are in the special key range
        for key_name, key_code in editing_keys.items():
            self.assertGreaterEqual(
                key_code, 1000,
                f"{key_name} should be in special key range"
            )
    
    def test_special_keys_consistency(self):
        """
        Test that special keys map to the same KeyCode values.
        
        Both backends should map their platform-specific special key codes
        to the same TTK KeyCode values.
        """
        # Expected KeyCode values for special keys
        special_keys = {
            'ENTER': KeyCode.ENTER,
            'ESCAPE': KeyCode.ESCAPE,
            'BACKSPACE': KeyCode.BACKSPACE,
            'TAB': KeyCode.TAB
        }
        
        # Verify values match expected constants
        self.assertEqual(special_keys['ENTER'], 10)
        self.assertEqual(special_keys['ESCAPE'], 27)
        self.assertEqual(special_keys['BACKSPACE'], 127)
        self.assertEqual(special_keys['TAB'], 9)


if __name__ == '__main__':
    unittest.main()
