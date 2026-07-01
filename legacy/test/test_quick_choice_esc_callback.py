#!/usr/bin/env python3
"""
Test that ESC key in quick choice bar calls callback with None
"""

import unittest
from unittest.mock import Mock
from tfm_quick_choice_bar import QuickChoiceBar, QuickChoiceBarHelpers
from ttk import KeyCode, KeyEvent, ModifierKey


class TestQuickChoiceEscCallback(unittest.TestCase):
    """Test ESC key behavior in quick choice bar"""
    
    def test_esc_returns_cancel_action(self):
        """Test that ESC key returns cancel action"""
        qcb = QuickChoiceBar(config=Mock())
        choices = QuickChoiceBarHelpers.create_yes_no_choices()
        callback = Mock()
        
        qcb.show("Test?", choices, callback)
        
        # Simulate ESC key
        esc_event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE, char=None)
        result = qcb.handle_input(esc_event)
        
        # Should return cancel action
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], 'cancel')
        self.assertIsNone(result[1])
    
    def test_yes_no_confirmation_with_esc(self):
        """Test that Yes/No confirmation can be canceled with ESC"""
        qcb = QuickChoiceBar(config=Mock())
        callback = Mock()
        
        QuickChoiceBarHelpers.show_yes_no_confirmation(qcb, "Quit?", callback)
        
        # Verify only 2 choices (Yes/No)
        self.assertEqual(len(qcb.choices), 2)
        self.assertEqual(qcb.choices[0]["text"], "Yes")
        self.assertEqual(qcb.choices[1]["text"], "No")
        
        # ESC should still work to cancel
        esc_event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE, char=None)
        result = qcb.handle_input(esc_event)
        
        self.assertEqual(result[0], 'cancel')


if __name__ == '__main__':
    unittest.main()
