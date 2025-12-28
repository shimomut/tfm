#!/usr/bin/env python3
"""
Test that single-character keys match regardless of modifiers.

This verifies Requirement 2.6 from the key-bindings-enhancement spec:
"WHEN a key expression is a single character, THE system SHALL compare it 
with KeyEvent.char (existing behavior)"

The key insight is that characters like "?" are actually produced by 
Shift-Slash on the keyboard, but the system should match them based on 
the char field, not the modifiers. This maintains backward compatibility
with the existing behavior.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_config import KeyBindings
from ttk import KeyEvent, KeyCode, ModifierKey


class TestSingleCharModifierIndependence(unittest.TestCase):
    """Test that single-character keys ignore modifiers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'help': ['?'],
            'quit': ['q', 'Q'],
            'search': ['/'],
            'toggle_hidden': ['.'],
        }
        self.kb = KeyBindings(self.config)
    
    def test_question_mark_with_shift(self):
        """Test that '?' matches even though it has Shift modifier."""
        # "?" is produced by Shift-Slash
        event = KeyEvent(
            key_code=KeyCode.SLASH,
            modifiers=ModifierKey.SHIFT,
            char='?'
        )
        action = self.kb.find_action_for_event(event, False)
        self.assertEqual(action, 'help', 
                        "Single-char '?' should match regardless of Shift modifier")
    
    def test_slash_without_modifiers(self):
        """Test that '/' matches without modifiers."""
        event = KeyEvent(
            key_code=KeyCode.SLASH,
            modifiers=0,
            char='/'
        )
        action = self.kb.find_action_for_event(event, False)
        self.assertEqual(action, 'search',
                        "Single-char '/' should match without modifiers")
    
    def test_period_matches_regardless_of_modifiers(self):
        """Test that '.' matches regardless of modifiers."""
        # Period without modifiers
        event_no_mod = KeyEvent(
            key_code=KeyCode.PERIOD,
            modifiers=0,
            char='.'
        )
        action = self.kb.find_action_for_event(event_no_mod, False)
        self.assertEqual(action, 'toggle_hidden',
                        "Single-char '.' should match without modifiers")
    
    def test_uppercase_letter_with_shift(self):
        """Test that uppercase letters match even with Shift modifier."""
        # 'Q' is produced by Shift-Q
        event = KeyEvent(
            key_code=KeyCode.Q,
            modifiers=ModifierKey.SHIFT,
            char='Q'
        )
        action = self.kb.find_action_for_event(event, False)
        self.assertEqual(action, 'quit',
                        "Single-char 'Q' should match regardless of Shift modifier")
    
    def test_lowercase_letter_without_shift(self):
        """Test that lowercase letters match without Shift."""
        event = KeyEvent(
            key_code=KeyCode.Q,
            modifiers=0,
            char='q'
        )
        action = self.kb.find_action_for_event(event, False)
        self.assertEqual(action, 'quit',
                        "Single-char 'q' should match without modifiers")
    
    def test_multi_char_keys_respect_modifiers(self):
        """Test that multi-character keys DO respect modifiers."""
        config = {
            'page_up': ['PAGE_UP', 'Shift-UP'],
            'move_up': ['UP'],
        }
        kb = KeyBindings(config)
        
        # UP without Shift should match 'move_up'
        event_up = KeyEvent(key_code=KeyCode.UP, modifiers=0, char=None)
        action = kb.find_action_for_event(event_up, False)
        self.assertEqual(action, 'move_up',
                        "UP without Shift should match 'move_up'")
        
        # UP with Shift should match 'page_up'
        event_shift_up = KeyEvent(
            key_code=KeyCode.UP,
            modifiers=ModifierKey.SHIFT,
            char=None
        )
        action = kb.find_action_for_event(event_shift_up, False)
        self.assertEqual(action, 'page_up',
                        "Shift-UP should match 'page_up', not 'move_up'")
    
    def test_single_char_vs_multi_char_distinction(self):
        """Test that the system correctly distinguishes single vs multi-char keys."""
        config = {
            'action_a': ['a'],  # Single char - ignores modifiers
            'action_b': ['Shift-A'],  # Multi-char expression - respects modifiers
        }
        kb = KeyBindings(config)
        
        # 'a' (single char) should match action_a regardless of modifiers
        event_a = KeyEvent(key_code=KeyCode.A, modifiers=0, char='a')
        action = kb.find_action_for_event(event_a, False)
        self.assertEqual(action, 'action_a')
        
        # 'A' with Shift should still match action_a (single char ignores modifiers)
        event_A = KeyEvent(key_code=KeyCode.A, modifiers=ModifierKey.SHIFT, char='A')
        action = kb.find_action_for_event(event_A, False)
        self.assertEqual(action, 'action_a',
                        "Single-char binding should match regardless of actual modifiers")


if __name__ == '__main__':
    unittest.main()
