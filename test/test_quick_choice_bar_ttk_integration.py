#!/usr/bin/env python3
"""
Tests for QuickChoiceBar TTK integration
Verifies that QuickChoiceBar uses TTK Renderer API correctly
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, call

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ttk import KeyCode, TextAttribute, InputEvent
from tfm_quick_choice_bar import QuickChoiceBar, QuickChoiceBarHelpers


class TestQuickChoiceBarTTKIntegration(unittest.TestCase):
    """Test QuickChoiceBar TTK integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.renderer = Mock()
        self.quick_choice_bar = QuickChoiceBar(self.config, self.renderer)
    
    def test_init_accepts_renderer(self):
        """Test that QuickChoiceBar accepts renderer parameter"""
        qcb = QuickChoiceBar(self.config, self.renderer)
        self.assertEqual(qcb.renderer, self.renderer)
        self.assertEqual(qcb.config, self.config)
    
    def test_show_initializes_state(self):
        """Test that show() initializes quick choice bar state"""
        choices = [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False}
        ]
        callback = Mock()
        
        self.quick_choice_bar.show("Test message?", choices, callback)
        
        self.assertTrue(self.quick_choice_bar.is_active)
        self.assertEqual(self.quick_choice_bar.message, "Test message?")
        self.assertEqual(self.quick_choice_bar.choices, choices)
        self.assertEqual(self.quick_choice_bar.callback, callback)
        self.assertEqual(self.quick_choice_bar.selected, 0)
    
    def test_handle_input_uses_input_event_escape(self):
        """Test that handle_input uses InputEvent for ESC key"""
        self.quick_choice_bar.show("Test?", [], Mock())
        
        event = InputEvent(key_code=KeyCode.ESCAPE, modifiers=0)
        result = self.quick_choice_bar.handle_input(event)
        
        self.assertEqual(result, ('cancel', None))
    
    def test_handle_input_uses_input_event_left_right(self):
        """Test that handle_input uses InputEvent for LEFT/RIGHT keys"""
        choices = [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False},
            {"text": "Cancel", "key": "c", "value": None}
        ]
        self.quick_choice_bar.show("Test?", choices, Mock())
        self.quick_choice_bar.selected = 1
        
        # Test LEFT key
        event = InputEvent(key_code=KeyCode.LEFT, modifiers=0)
        result = self.quick_choice_bar.handle_input(event)
        self.assertEqual(result, ('selection_changed', None))
        self.assertEqual(self.quick_choice_bar.selected, 0)
        
        # Test RIGHT key
        event = InputEvent(key_code=KeyCode.RIGHT, modifiers=0)
        result = self.quick_choice_bar.handle_input(event)
        self.assertEqual(result, ('selection_changed', None))
        self.assertEqual(self.quick_choice_bar.selected, 1)
    
    def test_handle_input_uses_input_event_enter(self):
        """Test that handle_input uses InputEvent for ENTER key"""
        choices = [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False}
        ]
        self.quick_choice_bar.show("Test?", choices, Mock())
        self.quick_choice_bar.selected = 0
        
        event = InputEvent(key_code=KeyCode.ENTER, modifiers=0)
        result = self.quick_choice_bar.handle_input(event)
        
        self.assertEqual(result, ('execute', True))
    
    def test_handle_input_uses_input_event_char(self):
        """Test that handle_input uses InputEvent.char for quick keys"""
        choices = [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False},
            {"text": "Cancel", "key": "c", "value": None}
        ]
        self.quick_choice_bar.show("Test?", choices, Mock())
        
        # Test 'y' key
        event = InputEvent(char='y', key_code=None, modifiers=0)
        result = self.quick_choice_bar.handle_input(event)
        self.assertEqual(result, ('execute', True))
        
        # Test 'n' key
        event = InputEvent(char='n', key_code=None, modifiers=0)
        result = self.quick_choice_bar.handle_input(event)
        self.assertEqual(result, ('execute', False))
        
        # Test 'c' key
        event = InputEvent(char='c', key_code=None, modifiers=0)
        result = self.quick_choice_bar.handle_input(event)
        self.assertEqual(result, ('execute', None))
    
    def test_draw_uses_renderer(self):
        """Test that draw() uses TTK Renderer API"""
        choices = [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False}
        ]
        self.quick_choice_bar.show("Test message?", choices, Mock())
        
        # Call draw
        self.quick_choice_bar.draw(status_y=20, width=80)
        
        # Verify renderer.draw_text was called
        self.assertTrue(self.renderer.draw_text.called)
        
        # Check that status line was filled
        calls = self.renderer.draw_text.call_args_list
        self.assertTrue(any(
            call[0][2].strip() == "" and len(call[0][2]) > 70  # Status line fill
            for call in calls
        ))
        
        # Check that message was drawn
        self.assertTrue(any(
            "Test message?" in call[0][2]
            for call in calls
        ))
    
    def test_draw_highlights_selected_choice(self):
        """Test that draw() highlights the selected choice"""
        choices = [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False}
        ]
        self.quick_choice_bar.show("Test?", choices, Mock())
        self.quick_choice_bar.selected = 1  # Select "No"
        
        # Call draw
        self.quick_choice_bar.draw(status_y=20, width=80)
        
        # Verify that selected choice is drawn with BOLD and REVERSE attributes
        calls = self.renderer.draw_text.call_args_list
        
        # Find the call that draws "[No]" with attributes
        selected_call = None
        for call_obj in calls:
            args = call_obj[0]
            if len(args) >= 3 and "[No]" in args[2]:
                selected_call = call_obj
                break
        
        self.assertIsNotNone(selected_call, "Selected choice should be drawn")
        
        # Check that it has BOLD and REVERSE attributes (5th positional arg or in kwargs)
        if len(selected_call[0]) >= 5:
            attributes = selected_call[0][4]
            self.assertTrue(
                attributes & TextAttribute.BOLD and attributes & TextAttribute.REVERSE,
                "Selected choice should have BOLD and REVERSE attributes"
            )
    
    def test_draw_shows_help_text(self):
        """Test that draw() shows help text with quick keys"""
        choices = [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False},
            {"text": "Cancel", "key": "c", "value": None}
        ]
        self.quick_choice_bar.show("Test?", choices, Mock())
        
        # Call draw
        self.quick_choice_bar.draw(status_y=20, width=120)
        
        # Verify help text is drawn
        calls = self.renderer.draw_text.call_args_list
        
        # Check for help text components
        help_text_found = False
        for call_obj in calls:
            args = call_obj[0]
            if len(args) >= 3:
                text = args[2]
                if "select" in text and "confirm" in text and "cancel" in text:
                    help_text_found = True
                    # Should also contain quick keys
                    self.assertTrue("Y/N/C" in text or "quick" in text)
                    break
        
        self.assertTrue(help_text_found, "Help text should be drawn")
    
    def test_exit_clears_state(self):
        """Test that exit() clears quick choice bar state"""
        choices = [{"text": "Yes", "key": "y", "value": True}]
        self.quick_choice_bar.show("Test?", choices, Mock())
        
        self.quick_choice_bar.exit()
        
        self.assertFalse(self.quick_choice_bar.is_active)
        self.assertEqual(self.quick_choice_bar.message, "")
        self.assertEqual(self.quick_choice_bar.choices, [])
        self.assertIsNone(self.quick_choice_bar.callback)
        self.assertEqual(self.quick_choice_bar.selected, 0)
    
    def test_no_curses_imports(self):
        """Test that QuickChoiceBar doesn't import curses"""
        import tfm_quick_choice_bar as qcb_module
        from ttk.input_event import InputEvent, KeyCode, ModifierKey
        
        # Check module doesn't import curses
        self.assertFalse(hasattr(qcb_module, 'curses'))
        
        # Check that curses is not in the module's globals
        module_globals = dir(qcb_module)
        self.assertNotIn('curses', module_globals)


class TestQuickChoiceBarHelpers(unittest.TestCase):
    """Test QuickChoiceBarHelpers utility functions"""
    
    def test_create_yes_no_cancel_choices(self):
        """Test creating Yes/No/Cancel choices"""
        choices = QuickChoiceBarHelpers.create_yes_no_cancel_choices()
        
        self.assertEqual(len(choices), 3)
        self.assertEqual(choices[0]["text"], "Yes")
        self.assertEqual(choices[0]["key"], "y")
        self.assertEqual(choices[0]["value"], True)
        self.assertEqual(choices[1]["text"], "No")
        self.assertEqual(choices[2]["text"], "Cancel")
    
    def test_create_ok_cancel_choices(self):
        """Test creating OK/Cancel choices"""
        choices = QuickChoiceBarHelpers.create_ok_cancel_choices()
        
        self.assertEqual(len(choices), 2)
        self.assertEqual(choices[0]["text"], "OK")
        self.assertEqual(choices[0]["key"], "o")
        self.assertEqual(choices[1]["text"], "Cancel")
    
    def test_create_overwrite_choices(self):
        """Test creating overwrite choices"""
        choices = QuickChoiceBarHelpers.create_overwrite_choices()
        
        self.assertEqual(len(choices), 4)
        self.assertEqual(choices[0]["text"], "Overwrite")
        self.assertEqual(choices[1]["text"], "Skip")
        self.assertEqual(choices[2]["text"], "Rename")
        self.assertEqual(choices[3]["text"], "Cancel")
    
    def test_show_confirmation(self):
        """Test showing confirmation dialog"""
        qcb = Mock()
        callback = Mock()
        
        QuickChoiceBarHelpers.show_confirmation(qcb, "Are you sure?", callback)
        
        qcb.show.assert_called_once()
        args = qcb.show.call_args[0]
        self.assertEqual(args[0], "Are you sure?")
        self.assertEqual(len(args[1]), 3)  # Yes/No/Cancel
        self.assertEqual(args[2], callback)
    
    def test_show_delete_confirmation_single_item(self):
        """Test showing delete confirmation for single item"""
        qcb = Mock()
        callback = Mock()
        
        QuickChoiceBarHelpers.show_delete_confirmation(qcb, ["file.txt"], callback)
        
        qcb.show.assert_called_once()
        args = qcb.show.call_args[0]
        self.assertIn("file.txt", args[0])
    
    def test_show_delete_confirmation_multiple_items(self):
        """Test showing delete confirmation for multiple items"""
        qcb = Mock()
        callback = Mock()
        
        QuickChoiceBarHelpers.show_delete_confirmation(qcb, ["file1.txt", "file2.txt"], callback)
        
        qcb.show.assert_called_once()
        args = qcb.show.call_args[0]
        self.assertIn("2", args[0])
        self.assertIn("selected items", args[0])


if __name__ == '__main__':
    unittest.main()
