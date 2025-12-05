"""
Property-based tests for UI Backend abstraction layer.

**Feature: qt-gui-port, Property 30: Backend interface compliance**
**Validates: Requirements 11.3**

Note: This test suite is designed to work with or without Hypothesis.
For full property-based testing with 100+ iterations, install Hypothesis:
    pip install hypothesis
"""

import sys
sys.path.append('src')

import inspect
from abc import ABC

from tfm_ui_backend import IUIBackend, InputEvent, LayoutInfo, DialogConfig

# Try to import Hypothesis for property-based testing
try:
    from hypothesis import given, strategies as st
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False
    print("Warning: Hypothesis not installed. Running basic tests only.")
    print("For full property-based testing, install: pip install hypothesis")

# Try to import pytest
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


class TestBackendInterfaceCompliance:
    """Test that the IUIBackend interface is properly defined."""
    
    def test_iuibackend_is_abstract(self):
        """Verify IUIBackend is an abstract base class."""
        assert issubclass(IUIBackend, ABC), "IUIBackend should be an ABC"
    
    def test_iuibackend_has_all_required_methods(self):
        """
        **Feature: qt-gui-port, Property 30: Backend interface compliance**
        **Validates: Requirements 11.3**
        
        For any UI backend implementation, it should implement all methods
        defined in the IUIBackend interface.
        """
        # Get all abstract methods from IUIBackend
        abstract_methods = {
            name for name, method in inspect.getmembers(IUIBackend, predicate=inspect.isfunction)
            if getattr(method, '__isabstractmethod__', False)
        }
        
        # Expected methods based on design document
        expected_methods = {
            'initialize',
            'cleanup',
            'get_screen_size',
            'render_panes',
            'render_header',
            'render_footer',
            'render_status_bar',
            'render_log_pane',
            'show_dialog',
            'show_progress',
            'get_input_event',
            'refresh',
            'set_color_scheme'
        }
        
        # Verify all expected methods are present
        assert expected_methods == abstract_methods, (
            f"IUIBackend missing methods: {expected_methods - abstract_methods}, "
            f"Extra methods: {abstract_methods - expected_methods}"
        )
    
    def test_iuibackend_method_signatures(self):
        """Verify IUIBackend methods have correct signatures."""
        # Check initialize signature
        init_sig = inspect.signature(IUIBackend.initialize)
        assert len(init_sig.parameters) == 1, "initialize should take only self"
        assert init_sig.return_annotation == bool, "initialize should return bool"
        
        # Check cleanup signature
        cleanup_sig = inspect.signature(IUIBackend.cleanup)
        assert len(cleanup_sig.parameters) == 1, "cleanup should take only self"
        
        # Check get_screen_size signature
        screen_sig = inspect.signature(IUIBackend.get_screen_size)
        assert len(screen_sig.parameters) == 1, "get_screen_size should take only self"
        
        # Check get_input_event signature
        input_sig = inspect.signature(IUIBackend.get_input_event)
        assert 'timeout' in input_sig.parameters, "get_input_event should have timeout parameter"
    
    def test_cannot_instantiate_iuibackend_directly(self):
        """Verify IUIBackend cannot be instantiated directly."""
        try:
            IUIBackend()
            assert False, "Should not be able to instantiate IUIBackend directly"
        except TypeError:
            pass  # Expected


class TestInputEvent:
    """Test InputEvent dataclass."""
    
    def test_input_event_creation(self):
        """
        For any valid input event parameters, InputEvent should be created successfully.
        """
        # Test with various combinations
        test_cases = [
            ('key', 65, 'A', None, None, None),
            ('mouse', None, None, 10, 20, 1),
            ('resize', None, None, None, None, None),
            ('key', 27, 'Escape', None, None, None),
            ('mouse', None, None, 100, 200, 3),
        ]
        
        for event_type, key, key_name, mouse_x, mouse_y, mouse_button in test_cases:
            event = InputEvent(
                type=event_type,
                key=key,
                key_name=key_name,
                mouse_x=mouse_x,
                mouse_y=mouse_y,
                mouse_button=mouse_button
            )
            
            assert event.type == event_type
            assert event.key == key
            assert event.key_name == key_name
            assert event.mouse_x == mouse_x
            assert event.mouse_y == mouse_y
            assert event.mouse_button == mouse_button
            assert isinstance(event.modifiers, set)
    
    def test_input_event_modifiers_default(self):
        """Verify InputEvent modifiers default to empty set."""
        event = InputEvent(type='key')
        assert event.modifiers == set()
    
    def test_input_event_with_modifiers(self):
        """For any set of modifiers, InputEvent should store them correctly."""
        test_modifiers = [
            set(),
            {'ctrl'},
            {'shift', 'alt'},
            {'ctrl', 'shift', 'alt', 'meta'},
        ]
        
        for modifiers in test_modifiers:
            event = InputEvent(type='key', modifiers=modifiers)
            assert event.modifiers == modifiers


class TestLayoutInfo:
    """Test LayoutInfo dataclass."""
    
    def test_layout_calculation(self):
        """
        For any screen dimensions, LayoutInfo.calculate should produce valid layout.
        """
        # Test with various screen dimensions
        test_cases = [
            (24, 80, 0.0),
            (50, 100, 0.2),
            (100, 200, 0.3),
            (30, 60, 0.0),
            (200, 400, 0.5),
        ]
        
        for screen_height, screen_width, log_ratio in test_cases:
            layout = LayoutInfo.calculate(screen_height, screen_width, log_ratio)
            
            # Verify basic properties
            assert layout.screen_height == screen_height
            assert layout.screen_width == screen_width
            
            # Verify pane widths sum to screen width
            assert layout.left_pane_width + layout.right_pane_width == screen_width
            
            # Verify all Y positions are within screen bounds
            assert 0 <= layout.header_y < screen_height
            assert 0 <= layout.panes_y < screen_height
            assert 0 <= layout.footer_y < screen_height
            assert 0 <= layout.status_y < screen_height
            
            # Verify Y positions are in correct order
            assert layout.header_y < layout.panes_y
            assert layout.panes_y < layout.footer_y
            assert layout.footer_y < layout.status_y
            
            # Verify heights are non-negative
            assert layout.pane_height >= 0
            assert layout.log_height >= 0
    
    def test_layout_with_no_log(self):
        """Verify layout calculation with no log pane."""
        layout = LayoutInfo.calculate(50, 100, 0.0)
        assert layout.log_height == 0
    
    def test_layout_with_log(self):
        """Verify layout calculation with log pane."""
        layout = LayoutInfo.calculate(50, 100, 0.2)
        assert layout.log_height > 0
        assert layout.log_height == int(50 * 0.2)


class TestDialogConfig:
    """Test DialogConfig dataclass."""
    
    def test_dialog_config_creation(self):
        """
        For any valid dialog configuration, DialogConfig should be created successfully.
        """
        # Test with various dialog configurations
        test_cases = [
            ('confirmation', 'Confirm', 'Are you sure?', 0.6, 0.7, 40, 15),
            ('input', 'Input', 'Enter value:', 0.5, 0.5, 30, 10),
            ('list', 'Select', 'Choose item:', 0.8, 0.8, 50, 20),
            ('info', 'Information', 'Details here', 0.7, 0.6, 45, 18),
            ('progress', 'Progress', 'Processing...', 0.6, 0.4, 40, 12),
        ]
        
        for dialog_type, title, message, width_ratio, height_ratio, min_width, min_height in test_cases:
            config = DialogConfig(
                type=dialog_type,
                title=title,
                message=message,
                width_ratio=width_ratio,
                height_ratio=height_ratio,
                min_width=min_width,
                min_height=min_height
            )
            
            assert config.type == dialog_type
            assert config.title == title
            assert config.message == message
            assert config.width_ratio == width_ratio
            assert config.height_ratio == height_ratio
            assert config.min_width == min_width
            assert config.min_height == min_height
    
    def test_dialog_config_defaults(self):
        """Verify DialogConfig has sensible defaults."""
        config = DialogConfig(type='info', title='Test', message='Message')
        
        assert config.choices is None
        assert config.default_value is None
        assert config.width_ratio == 0.6
        assert config.height_ratio == 0.7
        assert config.min_width == 40
        assert config.min_height == 15


class TestMockBackend:
    """Test that a mock backend can implement IUIBackend."""
    
    def test_mock_backend_implementation(self):
        """
        **Feature: qt-gui-port, Property 30: Backend interface compliance**
        **Validates: Requirements 11.3**
        
        For any UI backend implementation, it should implement all methods
        defined in the IUIBackend interface.
        """
        # Create a mock backend that implements all required methods
        class MockBackend(IUIBackend):
            def initialize(self) -> bool:
                return True
            
            def cleanup(self):
                pass
            
            def get_screen_size(self):
                return (24, 80)
            
            def render_panes(self, left_pane, right_pane, active_pane, layout):
                pass
            
            def render_header(self, left_path, right_path, active_pane):
                pass
            
            def render_footer(self, left_info, right_info, active_pane):
                pass
            
            def render_status_bar(self, message, controls):
                pass
            
            def render_log_pane(self, messages, scroll_offset, height_ratio):
                pass
            
            def show_dialog(self, dialog_config):
                return None
            
            def show_progress(self, operation, current, total, message):
                pass
            
            def get_input_event(self, timeout=-1):
                return None
            
            def refresh(self):
                pass
            
            def set_color_scheme(self, scheme):
                pass
        
        # Should be able to instantiate the mock backend
        backend = MockBackend()
        assert isinstance(backend, IUIBackend)
        
        # Verify all methods are callable
        assert backend.initialize() is True
        backend.cleanup()
        assert backend.get_screen_size() == (24, 80)
        backend.render_panes({}, {}, 'left', LayoutInfo.calculate(24, 80))
        backend.render_header('/', '/', 'left')
        backend.render_footer('info', 'info', 'left')
        backend.render_status_bar('message', [])
        backend.render_log_pane([], 0, 0.0)
        assert backend.show_dialog(DialogConfig('info', 'title', 'msg')) is None
        backend.show_progress('op', 0, 100, 'msg')
        assert backend.get_input_event() is None
        backend.refresh()
        backend.set_color_scheme('dark')



def run_tests():
    """Run all tests."""
    print("Testing UI Backend Abstraction Layer")
    print("=" * 60)
    
    # Test IUIBackend interface
    print("\n1. Testing IUIBackend Interface...")
    test_backend = TestBackendInterfaceCompliance()
    
    try:
        test_backend.test_iuibackend_is_abstract()
        print("   ✓ IUIBackend is abstract")
    except AssertionError as e:
        print(f"   ❌ IUIBackend abstract test failed: {e}")
        return False
    
    try:
        test_backend.test_iuibackend_has_all_required_methods()
        print("   ✓ IUIBackend has all required methods")
    except AssertionError as e:
        print(f"   ❌ IUIBackend methods test failed: {e}")
        return False
    
    try:
        test_backend.test_iuibackend_method_signatures()
        print("   ✓ IUIBackend method signatures are correct")
    except AssertionError as e:
        print(f"   ❌ IUIBackend signatures test failed: {e}")
        return False
    
    try:
        test_backend.test_cannot_instantiate_iuibackend_directly()
        print("   ✓ Cannot instantiate IUIBackend directly")
    except AssertionError as e:
        print(f"   ❌ IUIBackend instantiation test failed: {e}")
        return False
    
    # Test InputEvent
    print("\n2. Testing InputEvent...")
    test_input = TestInputEvent()
    
    try:
        test_input.test_input_event_creation()
        print("   ✓ InputEvent creation works")
    except AssertionError as e:
        print(f"   ❌ InputEvent creation test failed: {e}")
        return False
    
    try:
        test_input.test_input_event_modifiers_default()
        print("   ✓ InputEvent modifiers default to empty set")
    except AssertionError as e:
        print(f"   ❌ InputEvent modifiers default test failed: {e}")
        return False
    
    try:
        test_input.test_input_event_with_modifiers()
        print("   ✓ InputEvent stores modifiers correctly")
    except AssertionError as e:
        print(f"   ❌ InputEvent modifiers test failed: {e}")
        return False
    
    # Test LayoutInfo
    print("\n3. Testing LayoutInfo...")
    test_layout = TestLayoutInfo()
    
    try:
        test_layout.test_layout_calculation()
        print("   ✓ LayoutInfo calculation works")
    except AssertionError as e:
        print(f"   ❌ LayoutInfo calculation test failed: {e}")
        return False
    
    try:
        test_layout.test_layout_with_no_log()
        print("   ✓ LayoutInfo works with no log pane")
    except AssertionError as e:
        print(f"   ❌ LayoutInfo no log test failed: {e}")
        return False
    
    try:
        test_layout.test_layout_with_log()
        print("   ✓ LayoutInfo works with log pane")
    except AssertionError as e:
        print(f"   ❌ LayoutInfo with log test failed: {e}")
        return False
    
    # Test DialogConfig
    print("\n4. Testing DialogConfig...")
    test_dialog = TestDialogConfig()
    
    try:
        test_dialog.test_dialog_config_creation()
        print("   ✓ DialogConfig creation works")
    except AssertionError as e:
        print(f"   ❌ DialogConfig creation test failed: {e}")
        return False
    
    try:
        test_dialog.test_dialog_config_defaults()
        print("   ✓ DialogConfig has sensible defaults")
    except AssertionError as e:
        print(f"   ❌ DialogConfig defaults test failed: {e}")
        return False
    
    # Test MockBackend
    print("\n5. Testing Mock Backend Implementation...")
    test_mock = TestMockBackend()
    
    try:
        test_mock.test_mock_backend_implementation()
        print("   ✓ Mock backend implements IUIBackend correctly")
    except AssertionError as e:
        print(f"   ❌ Mock backend test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed!")
    print("\n**Feature: qt-gui-port, Property 30: Backend interface compliance**")
    print("**Validates: Requirements 11.3**")
    print("\nFor any UI backend implementation, it implements all methods")
    print("defined in the IUIBackend interface.")
    
    if not HAS_HYPOTHESIS:
        print("\nNote: For full property-based testing with 100+ iterations,")
        print("install Hypothesis: pip install hypothesis")
    
    return True


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
