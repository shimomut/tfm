"""
Property-based tests for CursesBackend implementation.

**Feature: qt-gui-port, Property 30: Backend interface compliance**
**Validates: Requirements 11.3**

This test verifies that CursesBackend correctly implements the IUIBackend interface.
"""

import sys
sys.path.append('src')

import inspect
from unittest.mock import Mock, MagicMock, patch

from tfm_ui_backend import IUIBackend, InputEvent, LayoutInfo, DialogConfig
from tfm_curses_backend import CursesBackend


class TestCursesBackendCompliance:
    """
    Test that CursesBackend implements IUIBackend interface correctly.
    
    **Feature: qt-gui-port, Property 30: Backend interface compliance**
    **Validates: Requirements 11.3**
    """
    
    def test_curses_backend_implements_iuibackend(self):
        """
        For any UI backend implementation, it should implement all methods
        defined in the IUIBackend interface.
        
        Verify CursesBackend is a subclass of IUIBackend.
        """
        assert issubclass(CursesBackend, IUIBackend), \
            "CursesBackend should be a subclass of IUIBackend"
    
    def test_curses_backend_has_all_required_methods(self):
        """
        Verify CursesBackend implements all abstract methods from IUIBackend.
        """
        # Get all abstract methods from IUIBackend
        abstract_methods = {
            name for name, method in inspect.getmembers(IUIBackend, predicate=inspect.isfunction)
            if getattr(method, '__isabstractmethod__', False)
        }
        
        # Get all methods from CursesBackend (use inspect.isfunction for unbound methods)
        backend_methods = {
            name for name, method in inspect.getmembers(CursesBackend, predicate=lambda m: inspect.isfunction(m) or inspect.ismethod(m))
        }
        
        # Verify all abstract methods are implemented
        missing_methods = abstract_methods - backend_methods
        assert not missing_methods, \
            f"CursesBackend missing methods: {missing_methods}"
    
    def test_curses_backend_can_be_instantiated(self):
        """
        Verify CursesBackend can be instantiated with a mock stdscr.
        """
        mock_stdscr = Mock()
        backend = CursesBackend(mock_stdscr)
        
        assert isinstance(backend, IUIBackend)
        assert isinstance(backend, CursesBackend)
        assert backend.stdscr is mock_stdscr
    
    def test_initialize_returns_bool(self):
        """
        Verify initialize() returns a boolean value.
        """
        mock_stdscr = Mock()
        backend = CursesBackend(mock_stdscr)
        
        with patch('curses.curs_set'), \
             patch('tfm_colors.init_colors'):
            result = backend.initialize()
            assert isinstance(result, bool)
    
    def test_get_screen_size_returns_tuple(self):
        """
        Verify get_screen_size() returns a tuple of (height, width).
        """
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        
        backend = CursesBackend(mock_stdscr)
        result = backend.get_screen_size()
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result == (24, 80)
    
    def test_get_screen_size_handles_error(self):
        """
        Verify get_screen_size() returns default size on error.
        """
        import curses
        
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.side_effect = curses.error("Test error")
        
        backend = CursesBackend(mock_stdscr)
        result = backend.get_screen_size()
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result == (24, 80)  # Default size
    
    def test_refresh_calls_stdscr_refresh(self):
        """
        Verify refresh() calls stdscr.refresh().
        """
        mock_stdscr = Mock()
        backend = CursesBackend(mock_stdscr)
        
        backend.refresh()
        
        mock_stdscr.refresh.assert_called_once()
    
    def test_set_color_scheme_stores_scheme(self):
        """
        Verify set_color_scheme() stores the color scheme.
        """
        mock_stdscr = Mock()
        backend = CursesBackend(mock_stdscr)
        
        with patch('tfm_colors.init_colors'):
            backend.set_color_scheme('light')
            assert backend.color_scheme == 'light'
            
            backend.set_color_scheme('dark')
            assert backend.color_scheme == 'dark'
    
    def test_get_input_event_returns_input_event_or_none(self):
        """
        Verify get_input_event() returns InputEvent or None.
        """
        mock_stdscr = Mock()
        backend = CursesBackend(mock_stdscr)
        
        # Test with no input (timeout)
        mock_stdscr.getch.return_value = -1
        result = backend.get_input_event(timeout=0)
        assert result is None
        
        # Test with key input
        mock_stdscr.getch.return_value = 65  # 'A'
        result = backend.get_input_event()
        assert isinstance(result, InputEvent)
        assert result.type == 'key'
        assert result.key == 65
    
    def test_convert_curses_key_handles_special_keys(self):
        """
        Verify _convert_curses_key() correctly converts special keys.
        """
        import curses
        
        mock_stdscr = Mock()
        backend = CursesBackend(mock_stdscr)
        
        # Test special keys
        test_cases = [
            (curses.KEY_UP, 'Up'),
            (curses.KEY_DOWN, 'Down'),
            (curses.KEY_LEFT, 'Left'),
            (curses.KEY_RIGHT, 'Right'),
            (curses.KEY_HOME, 'Home'),
            (curses.KEY_END, 'End'),
            (27, 'Escape'),
            (9, 'Tab'),
            (10, 'Enter'),
        ]
        
        for key_code, expected_name in test_cases:
            event = backend._convert_curses_key(key_code)
            assert isinstance(event, InputEvent)
            assert event.type == 'key'
            assert event.key == key_code
            assert event.key_name == expected_name
    
    def test_convert_curses_key_handles_printable_ascii(self):
        """
        Verify _convert_curses_key() correctly converts printable ASCII.
        """
        mock_stdscr = Mock()
        backend = CursesBackend(mock_stdscr)
        
        # Test printable ASCII characters
        for key_code in range(32, 127):
            event = backend._convert_curses_key(key_code)
            assert isinstance(event, InputEvent)
            assert event.type == 'key'
            assert event.key == key_code
            assert event.key_name == chr(key_code)
    
    def test_render_methods_dont_crash(self):
        """
        Verify all render methods can be called without crashing.
        """
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        mock_stdscr.addstr = Mock()  # Mock addstr to avoid curses errors
        backend = CursesBackend(mock_stdscr)
        
        # Create test data
        layout = LayoutInfo.calculate(24, 80, 0.2)
        left_pane = {'path': '/', 'files': [], 'selected_index': 0, 
                    'scroll_offset': 0, 'selected_files': set()}
        right_pane = {'path': '/', 'files': [], 'selected_index': 0,
                     'scroll_offset': 0, 'selected_files': set()}
        
        # Test render methods (should not crash)
        # Patch color functions to avoid curses initialization
        with patch('tfm_colors.get_header_color', return_value=0), \
             patch('tfm_colors.get_boundary_color', return_value=0), \
             patch('tfm_colors.get_footer_color', return_value=0), \
             patch('tfm_colors.get_status_color', return_value=0), \
             patch('tfm_colors.get_log_color', return_value=0):
            try:
                backend.render_header('/left', '/right', 'left')
                backend.render_panes(left_pane, right_pane, 'left', layout)
                backend.render_footer('left info', 'right info', 'left')
                backend.render_status_bar('message', [{'key': 'F1', 'label': 'Help'}])
                backend.render_log_pane(['message1', 'message2'], 0, 0.2)
            except Exception as e:
                assert False, f"Render methods should not crash: {e}"


def run_tests():
    """Run all tests."""
    print("Testing CursesBackend Implementation")
    print("=" * 60)
    
    test_suite = TestCursesBackendCompliance()
    
    tests = [
        ("CursesBackend implements IUIBackend", test_suite.test_curses_backend_implements_iuibackend),
        ("CursesBackend has all required methods", test_suite.test_curses_backend_has_all_required_methods),
        ("CursesBackend can be instantiated", test_suite.test_curses_backend_can_be_instantiated),
        ("initialize() returns bool", test_suite.test_initialize_returns_bool),
        ("get_screen_size() returns tuple", test_suite.test_get_screen_size_returns_tuple),
        ("get_screen_size() handles error", test_suite.test_get_screen_size_handles_error),
        ("refresh() calls stdscr.refresh()", test_suite.test_refresh_calls_stdscr_refresh),
        ("set_color_scheme() stores scheme", test_suite.test_set_color_scheme_stores_scheme),
        ("get_input_event() returns InputEvent or None", test_suite.test_get_input_event_returns_input_event_or_none),
        ("_convert_curses_key() handles special keys", test_suite.test_convert_curses_key_handles_special_keys),
        ("_convert_curses_key() handles printable ASCII", test_suite.test_convert_curses_key_handles_printable_ascii),
        ("Render methods don't crash", test_suite.test_render_methods_dont_crash),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"   ✓ {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"   ❌ {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ {test_name}: Unexpected error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        print("\n**Feature: qt-gui-port, Property 30: Backend interface compliance**")
        print("**Validates: Requirements 11.3**")
        print("\nCursesBackend correctly implements all methods defined in")
        print("the IUIBackend interface.")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
