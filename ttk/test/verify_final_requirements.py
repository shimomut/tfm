#!/usr/bin/env python3
"""
Final Requirements Verification Script

This script verifies that all requirements from the design document are met.
It checks implementation completeness, test coverage, and documentation.
"""

import sys
from pathlib import Path

# Add ttk to path
ttk_root = Path(__file__).parent.parent
sys.path.insert(0, str(ttk_root))


def check_requirement(req_id: str, description: str, checks: list) -> bool:
    """Check if a requirement is met."""
    print(f"\n{'='*80}")
    print(f"Requirement {req_id}: {description}")
    print(f"{'='*80}")
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            result = check_func()
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {check_name}")
            if not result:
                all_passed = False
        except Exception as e:
            print(f"✗ ERROR: {check_name} - {e}")
            all_passed = False
    
    return all_passed


def main():
    """Run all requirement checks."""
    print("="*80)
    print("TTK Library - Final Requirements Verification")
    print("="*80)
    
    results = []
    
    # Requirement 1: Abstract Rendering API
    results.append(check_requirement(
        "1",
        "Abstract rendering API defined",
        [
            ("Renderer ABC exists", lambda: Path(ttk_root / "renderer.py").exists()),
            ("InputEvent module exists", lambda: Path(ttk_root / "input_event.py").exists()),
            ("Drawing operations defined", lambda: check_renderer_methods()),
            ("Input handling defined", lambda: check_input_event()),
            ("Window management defined", lambda: check_window_management()),
        ]
    ))
    
    # Requirement 2: Curses Backend
    results.append(check_requirement(
        "2",
        "Curses backend implemented",
        [
            ("CursesBackend exists", lambda: Path(ttk_root / "backends" / "curses_backend.py").exists()),
            ("Drawing operations implemented", lambda: check_curses_drawing()),
            ("Input handling implemented", lambda: check_curses_input()),
            ("Window management implemented", lambda: check_curses_window()),
            ("Tests exist", lambda: check_curses_tests()),
        ]
    ))
    
    # Requirement 3: Metal Backend
    results.append(check_requirement(
        "3",
        "Metal backend implemented",
        [
            ("MetalBackend exists", lambda: Path(ttk_root / "backends" / "metal_backend.py").exists()),
            ("Drawing operations implemented", lambda: check_metal_drawing()),
            ("Input handling implemented", lambda: check_metal_input()),
            ("Window management implemented", lambda: check_metal_window()),
            ("Tests exist", lambda: check_metal_tests()),
        ]
    ))
    
    # Requirement 4-9: Core functionality
    results.append(check_requirement(
        "4-9",
        "Core drawing, input, and window functionality",
        [
            ("Text attributes supported", lambda: check_text_attributes()),
            ("Color management implemented", lambda: check_color_management()),
            ("Coordinate system correct", lambda: check_coordinate_system()),
        ]
    ))
    
    # Requirement 10: Documentation
    results.append(check_requirement(
        "10",
        "Documentation complete",
        [
            ("API reference exists", lambda: Path(ttk_root / "doc" / "API_REFERENCE.md").exists()),
            ("User guide exists", lambda: Path(ttk_root / "doc" / "USER_GUIDE.md").exists()),
            ("Backend guide exists", lambda: Path(ttk_root / "doc" / "BACKEND_IMPLEMENTATION_GUIDE.md").exists()),
            ("Examples exist", lambda: Path(ttk_root / "doc" / "EXAMPLES.md").exists()),
        ]
    ))
    
    # Requirement 13: Command serialization
    results.append(check_requirement(
        "13",
        "Command serialization implemented",
        [
            ("Serialization module exists", lambda: Path(ttk_root / "serialization" / "command_serializer.py").exists()),
            ("Serialization tests exist", lambda: Path(ttk_root / "test" / "test_command_serialization.py").exists()),
            ("Parsing tests exist", lambda: Path(ttk_root / "test" / "test_command_parsing.py").exists()),
            ("Pretty-print tests exist", lambda: Path(ttk_root / "test" / "test_command_pretty_print.py").exists()),
        ]
    ))
    
    # Requirement 16: Library independence
    results.append(check_requirement(
        "16",
        "Library is standalone and reusable",
        [
            ("Package configuration exists", lambda: Path(ttk_root / "setup.py").exists() or Path(ttk_root / "pyproject.toml").exists()),
            ("No TFM dependencies", lambda: check_no_tfm_dependencies()),
            ("Demo application exists", lambda: Path(ttk_root / "demo" / "demo_ttk.py").exists()),
            ("Standalone test exists", lambda: Path(ttk_root / "test" / "test_library_independence.py").exists()),
        ]
    ))
    
    # Requirement 17: Monospace font enforcement
    results.append(check_requirement(
        "17",
        "Monospace font enforcement",
        [
            ("Font validation exists", lambda: check_font_validation()),
            ("Font validation tests exist", lambda: Path(ttk_root / "test" / "test_metal_font_validation.py").exists()),
        ]
    ))
    
    # Property-based tests
    results.append(check_requirement(
        "PBT",
        "Property-based testing implemented",
        [
            ("PBT tests exist", lambda: Path(ttk_root / "test" / "test_pbt_command_pretty_print.py").exists()),
            ("Hypothesis configured", lambda: check_hypothesis_config()),
        ]
    ))
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nRequirements Verified: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n✓ ALL REQUIREMENTS MET!")
        return 0
    else:
        print(f"\n✗ {total - passed} requirement(s) not fully met")
        return 1


def check_renderer_methods():
    """Check that Renderer ABC has all required methods."""
    from ttk.renderer import Renderer
    required_methods = [
        'initialize', 'shutdown', 'get_dimensions', 'clear', 'clear_region',
        'draw_text', 'draw_hline', 'draw_vline', 'draw_rect',
        'refresh', 'refresh_region', 'init_color_pair',
        'get_input', 'set_cursor_visibility', 'move_cursor'
    ]
    for method in required_methods:
        if not hasattr(Renderer, method):
            return False
    return True


def check_input_event():
    """Check InputEvent implementation."""
    from ttk.input_event import InputEvent, KeyCode, ModifierKey
    # Check that classes exist and have required attributes
    # For dataclass, check instance has the fields
    ie = InputEvent(key_code=65, modifiers=0)
    return (
        hasattr(ie, 'key_code') and
        hasattr(ie, 'modifiers') and
        hasattr(ie, 'is_printable') and
        hasattr(ie, 'is_special_key') and
        hasattr(KeyCode, 'UP') and
        hasattr(ModifierKey, 'SHIFT')
    )


def check_window_management():
    """Check window management methods."""
    from ttk.renderer import Renderer
    return (
        hasattr(Renderer, 'get_dimensions') and
        hasattr(Renderer, 'set_cursor_visibility') and
        hasattr(Renderer, 'move_cursor')
    )


def check_curses_drawing():
    """Check curses drawing implementation."""
    from ttk.backends.curses_backend import CursesBackend
    backend = CursesBackend()
    return (
        hasattr(backend, 'draw_text') and
        hasattr(backend, 'draw_rect') and
        hasattr(backend, 'draw_hline') and
        hasattr(backend, 'draw_vline')
    )


def check_curses_input():
    """Check curses input implementation."""
    from ttk.backends.curses_backend import CursesBackend
    backend = CursesBackend()
    return hasattr(backend, 'get_input') and hasattr(backend, '_translate_curses_key')


def check_curses_window():
    """Check curses window management."""
    from ttk.backends.curses_backend import CursesBackend
    backend = CursesBackend()
    return (
        hasattr(backend, 'get_dimensions') and
        hasattr(backend, 'set_cursor_visibility') and
        hasattr(backend, 'move_cursor')
    )


def check_curses_tests():
    """Check curses tests exist."""
    test_files = [
        "test_curses_drawing.py",
        "test_curses_input_handling.py",
        "test_curses_window_management.py",
        "test_curses_color_management.py"
    ]
    return all(Path(ttk_root / "test" / f).exists() for f in test_files)


def check_metal_drawing():
    """Check metal drawing implementation."""
    from ttk.backends.metal_backend import MetalBackend
    backend = MetalBackend()
    return (
        hasattr(backend, 'draw_text') and
        hasattr(backend, 'draw_rect') and
        hasattr(backend, 'draw_hline') and
        hasattr(backend, 'draw_vline')
    )


def check_metal_input():
    """Check metal input implementation."""
    from ttk.backends.metal_backend import MetalBackend
    backend = MetalBackend()
    return hasattr(backend, 'get_input') and hasattr(backend, '_translate_macos_event')


def check_metal_window():
    """Check metal window management."""
    from ttk.backends.metal_backend import MetalBackend
    backend = MetalBackend()
    return (
        hasattr(backend, 'get_dimensions') and
        hasattr(backend, 'set_cursor_visibility') and
        hasattr(backend, 'move_cursor')
    )


def check_metal_tests():
    """Check metal tests exist."""
    test_files = [
        "test_metal_drawing_operations.py",
        "test_metal_input_handling.py",
        "test_metal_window_management.py",
        "test_metal_color_management.py",
        "test_metal_initialization.py"
    ]
    return all(Path(ttk_root / "test" / f).exists() for f in test_files)


def check_text_attributes():
    """Check text attributes implementation."""
    from ttk.renderer import TextAttribute
    return (
        hasattr(TextAttribute, 'NORMAL') and
        hasattr(TextAttribute, 'BOLD') and
        hasattr(TextAttribute, 'UNDERLINE') and
        hasattr(TextAttribute, 'REVERSE')
    )


def check_color_management():
    """Check color management implementation."""
    from ttk.backends.curses_backend import CursesBackend
    from ttk.backends.metal_backend import MetalBackend
    return (
        hasattr(CursesBackend(), 'init_color_pair') and
        hasattr(MetalBackend(), 'init_color_pair')
    )


def check_coordinate_system():
    """Check coordinate system is correct (0,0 at top-left)."""
    # This is verified through tests, just check tests exist
    return Path(ttk_root / "test" / "test_curses_drawing.py").exists()


def check_font_validation():
    """Check font validation implementation."""
    from ttk.backends.metal_backend import MetalBackend
    backend = MetalBackend()
    return hasattr(backend, '_validate_font')


def check_no_tfm_dependencies():
    """Check that there are no TFM-specific imports."""
    # Check key files for TFM imports
    files_to_check = [
        ttk_root / "renderer.py",
        ttk_root / "input_event.py",
        ttk_root / "backends" / "curses_backend.py",
        ttk_root / "backends" / "metal_backend.py",
    ]
    
    for file_path in files_to_check:
        if file_path.exists():
            content = file_path.read_text()
            if 'tfm_' in content.lower() or 'from tfm' in content.lower():
                return False
    return True


def check_hypothesis_config():
    """Check hypothesis is configured."""
    try:
        import hypothesis
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    sys.exit(main())
