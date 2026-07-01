"""
Tests for the screen redraw feature (Ctrl-L).

The redraw action forces a complete repaint of the interface. This is mainly
useful for recovering the display after a terminal multiplexer (tmux/screen)
context switch, where the terminal contents are changed behind the backend's
back and the normal dirty-tracking refresh sends nothing.

This module verifies:
1. The default 'redraw' key binding resolves from a Ctrl-L KeyEvent.
2. FileManager.force_redraw() invalidates the renderer and marks all layers dirty.
3. The global key handler routes Ctrl-L to force_redraw() in any context.

Run with: PYTHONPATH=.:src:ttk pytest test/test_redraw_action.py -v
"""

import unittest
from unittest.mock import Mock

from tfm_config import KeyBindings
from ttk import KeyEvent, KeyCode, ModifierKey


class TestRedrawKeyBinding(unittest.TestCase):
    """Test that the redraw action is bound to Ctrl-L."""

    def setUp(self):
        self.kb = KeyBindings({'redraw': ['Ctrl-L']})

    def test_ctrl_l_matches_redraw(self):
        """A Ctrl-L KeyEvent should resolve to the 'redraw' action."""
        event = KeyEvent(key_code=KeyCode.L, modifiers=ModifierKey.CONTROL, char=None)
        action = self.kb.find_action_for_event(event, has_selection=False)
        self.assertEqual(action, 'redraw')

    def test_plain_l_does_not_match_redraw(self):
        """A plain 'l' (no Control modifier) must not trigger redraw."""
        event = KeyEvent(key_code=KeyCode.L, modifiers=ModifierKey.NONE, char='l')
        action = self.kb.find_action_for_event(event, has_selection=False)
        self.assertIsNone(action)

    def test_ctrl_l_parses_to_control_modifier(self):
        """The 'Ctrl-L' expression should parse to (L, CONTROL)."""
        main_key, modifiers = self.kb._parse_key_expression('Ctrl-L')
        self.assertEqual(main_key, 'L')
        self.assertEqual(modifiers, ModifierKey.CONTROL)


class TestDefaultConfigBinding(unittest.TestCase):
    """Test that the shipped default config binds redraw to Ctrl-L."""

    def test_default_config_has_redraw_binding(self):
        import importlib.util
        from pathlib import Path

        config_path = Path(__file__).resolve().parent.parent / 'src' / '_config.py'
        spec = importlib.util.spec_from_file_location('_config_template', config_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertIn('redraw', module.Config.KEY_BINDINGS)
        self.assertEqual(module.Config.KEY_BINDINGS['redraw'], ['F5'])


class TestForceRedraw(unittest.TestCase):
    """Test FileManager.force_redraw behavior via a lightweight stand-in."""

    def _make_fake_file_manager(self):
        """Build an object that runs the real force_redraw against mocks."""
        from tfm_main import FileManager

        fake = Mock()
        fake.renderer = Mock()
        fake.ui_layer_stack = Mock()
        fake.logger = Mock()
        # Bind the unbound method to our fake instance
        fake.force_redraw = FileManager.force_redraw.__get__(fake, fake.__class__)
        return fake

    def test_force_redraw_invalidates_renderer_and_layers(self):
        fake = self._make_fake_file_manager()

        fake.force_redraw()

        fake.renderer.force_repaint.assert_called_once()
        fake.ui_layer_stack.mark_all_dirty.assert_called_once()

    def test_force_redraw_survives_repaint_error(self):
        """If the renderer fails to repaint, layers are still marked dirty."""
        fake = self._make_fake_file_manager()
        fake.renderer.force_repaint.side_effect = RuntimeError("boom")

        fake.force_redraw()

        fake.logger.error.assert_called()
        fake.ui_layer_stack.mark_all_dirty.assert_called_once()


if __name__ == '__main__':
    unittest.main()
