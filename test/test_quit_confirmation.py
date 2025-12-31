#!/usr/bin/env python3
"""
Test quit confirmation dialog uses Yes/No choices only
"""

import unittest
from unittest.mock import Mock
from tfm_quick_choice_bar import QuickChoiceBarHelpers


class TestQuitConfirmation(unittest.TestCase):
    """Test quit confirmation dialog behavior"""
    
    def test_yes_no_choices_has_two_options(self):
        """Test that Yes/No choices returns exactly 2 options"""
        choices = QuickChoiceBarHelpers.create_yes_no_choices()
        
        self.assertEqual(len(choices), 2)
        self.assertEqual(choices[0]["text"], "Yes")
        self.assertEqual(choices[0]["key"], "y")
        self.assertEqual(choices[0]["value"], True)
        self.assertEqual(choices[1]["text"], "No")
        self.assertEqual(choices[1]["key"], "n")
        self.assertEqual(choices[1]["value"], False)
    
    def test_show_yes_no_confirmation(self):
        """Test showing Yes/No confirmation dialog"""
        qcb = Mock()
        callback = Mock()
        
        QuickChoiceBarHelpers.show_yes_no_confirmation(qcb, "Quit?", callback)
        
        qcb.show.assert_called_once()
        call_args = qcb.show.call_args
        
        # Verify message
        self.assertEqual(call_args[0][0], "Quit?")
        
        # Verify choices (2 options only)
        choices = call_args[0][1]
        self.assertEqual(len(choices), 2)
        self.assertEqual(choices[0]["text"], "Yes")
        self.assertEqual(choices[1]["text"], "No")
        
        # Verify callback
        self.assertEqual(call_args[0][2], callback)


if __name__ == '__main__':
    unittest.main()
