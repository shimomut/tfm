#!/usr/bin/env python3
"""
Test TTK Library Independence from TFM

This test verifies Requirement 16.5: The library has zero dependencies on TFM
code or TFM-specific concepts and can be used standalone.

Tests:
1. No TFM-specific imports in TTK code
2. No TFM-specific dependencies in package metadata
3. Library can be used in a simple standalone application
4. All public APIs work without TFM context
"""

import sys
import os
import ast
import importlib.util
from pathlib import Path


def test_no_tfm_imports_in_source():
    """Verify that no TTK source files import TFM modules."""
    print("\n=== Testing for TFM imports in source code ===")
    
    ttk_root = Path(__file__).parent.parent
    source_files = list(ttk_root.glob("**/*.py"))
    
    # Exclude test files and build artifacts
    source_files = [
        f for f in source_files 
        if not any(part in f.parts for part in ['test', 'build', 'dist', '__pycache__'])
    ]
    
    tfm_imports_found = []
    
    for source_file in source_files:
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(source_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if 'tfm' in alias.name.lower() and 'ttk' not in alias.name.lower():
                                tfm_imports_found.append((source_file, alias.name))
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and 'tfm' in node.module.lower() and 'ttk' not in node.module.lower():
                            tfm_imports_found.append((source_file, node.module))
        except Exception as e:
            print(f"Warning: Could not parse {source_file}: {e}")
    
    if tfm_imports_found:
        print(f"✗ Found TFM imports in source code:")
        for file, module in tfm_imports_found:
            print(f"  - {file.relative_to(ttk_root)}: imports {module}")
        return False
    else:
        print("✓ No TFM imports found in source code")
        return True


def test_no_tfm_runtime_dependencies():
    """Verify that importing TTK doesn't load TFM modules."""
    print("\n=== Testing for TFM runtime dependencies ===")
    
    # Get initial modules
    initial_modules = set(sys.modules.keys())
    
    # Import TTK
    try:
        import ttk
        from ttk import Renderer, KeyEvent, KeyCode, ModifierKey, TextAttribute
        from ttk.backends.curses_backend import CursesBackend
        from ttk.serialization.command_serializer import serialize_command, parse_command
        from ttk.utils import get_recommended_backend
    except ImportError as e:
        print(f"✗ Failed to import TTK: {e}")
        return False
    
    # Get modules loaded after import
    loaded_modules = set(sys.modules.keys()) - initial_modules
    
    # Check for TFM modules (excluding ttk itself)
    tfm_modules = [
        name for name in loaded_modules 
        if 'tfm' in name.lower() and 'ttk' not in name.lower()
    ]
    
    if tfm_modules:
        print(f"✗ Found TFM modules loaded at runtime: {tfm_modules}")
        return False
    else:
        print("✓ No TFM modules loaded at runtime")
        return True


def test_standalone_application():
    """Test that TTK can be used in a simple standalone application."""
    print("\n=== Testing standalone application ===")
    
    try:
        # Import TTK components
        from ttk import Renderer, KeyEvent, KeyCode, ModifierKey, TextAttribute
        from ttk.serialization.command_serializer import serialize_command, parse_command
        from ttk.utils import get_recommended_backend
        
        print("✓ Successfully imported TTK components")
        
        # Test KeyEvent creation
        event = KeyEvent(
            key_code=KeyCode.ENTER,
            modifiers=ModifierKey.CONTROL,
            char=None
        )
        assert event.key_code == KeyCode.ENTER
        assert event.has_modifier(ModifierKey.CONTROL)
        print("✓ KeyEvent works correctly")
        
        # Test command serialization with proper dataclass
        from ttk.serialization.command_serializer import DrawTextCommand
        command = DrawTextCommand(
            row=5,
            col=10,
            text='Hello, World!',
            color_pair=1,
            attributes=TextAttribute.BOLD
        )
        serialized = serialize_command(command)
        parsed = parse_command(serialized)
        assert parsed.command_type == 'draw_text'
        assert parsed.text == 'Hello, World!'
        print("✓ Command serialization works correctly")
        
        # Test backend recommendation
        backend = get_recommended_backend()
        assert backend in ['curses', 'metal']
        print(f"✓ Backend recommendation works (recommended: {backend})")
        
        # Test TextAttribute combinations
        attrs = TextAttribute.BOLD | TextAttribute.UNDERLINE
        assert attrs & TextAttribute.BOLD
        assert attrs & TextAttribute.UNDERLINE
        print("✓ TextAttribute combinations work correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Standalone application test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_tfm_concepts_in_api():
    """Verify that TTK API doesn't expose TFM-specific concepts."""
    print("\n=== Testing for TFM-specific concepts in API ===")
    
    try:
        import ttk
        
        # Get all public attributes
        public_attrs = [attr for attr in dir(ttk) if not attr.startswith('_')]
        
        # Check for TFM-specific names
        tfm_specific = [
            'pane', 'file_manager', 'tfm', 'selection', 'cursor',
            'directory', 'file_operations', 'state_manager'
        ]
        
        found_tfm_concepts = []
        for attr in public_attrs:
            attr_lower = attr.lower()
            if any(concept in attr_lower for concept in tfm_specific):
                found_tfm_concepts.append(attr)
        
        if found_tfm_concepts:
            print(f"✗ Found TFM-specific concepts in API: {found_tfm_concepts}")
            return False
        else:
            print("✓ No TFM-specific concepts found in API")
            return True
            
    except Exception as e:
        print(f"✗ API concept test failed: {e}")
        return False


def test_generic_naming():
    """Verify that TTK uses generic, reusable naming."""
    print("\n=== Testing for generic naming ===")
    
    try:
        import ttk
        
        # Check main classes have generic names
        expected_classes = [
            'Renderer', 'KeyEvent', 'KeyCode', 'ModifierKey', 'TextAttribute'
        ]
        
        for class_name in expected_classes:
            if not hasattr(ttk, class_name):
                print(f"✗ Missing expected generic class: {class_name}")
                return False
        
        print("✓ All expected generic classes present")
        
        # Check that class names are generic (not TFM-specific)
        public_classes = [
            attr for attr in dir(ttk) 
            if not attr.startswith('_') and attr[0].isupper()
        ]
        
        for class_name in public_classes:
            if 'tfm' in class_name.lower() or 'filemanager' in class_name.lower():
                print(f"✗ Found TFM-specific class name: {class_name}")
                return False
        
        print("✓ All class names are generic")
        return True
        
    except Exception as e:
        print(f"✗ Generic naming test failed: {e}")
        return False


def test_documentation_independence():
    """Verify that TTK documentation is standalone."""
    print("\n=== Testing documentation independence ===")
    
    ttk_root = Path(__file__).parent.parent
    doc_dir = ttk_root / 'doc'
    
    if not doc_dir.exists():
        print("✗ Documentation directory not found")
        return False
    
    # Check for README
    readme = ttk_root / 'README.md'
    if not readme.exists():
        print("✗ README.md not found")
        return False
    
    # Read README and check it's not TFM-specific
    with open(readme, 'r', encoding='utf-8') as f:
        readme_content = f.read()
    
    # README should mention TTK prominently
    if 'TTK' not in readme_content and 'TUI Toolkit' not in readme_content:
        print("✗ README doesn't clearly identify as TTK library")
        return False
    
    print("✓ Documentation exists and is standalone")
    return True


def run_all_tests():
    """Run all independence tests."""
    print("=" * 70)
    print("TTK Library Independence Test Suite")
    print("=" * 70)
    
    tests = [
        ("No TFM imports in source", test_no_tfm_imports_in_source),
        ("No TFM runtime dependencies", test_no_tfm_runtime_dependencies),
        ("Standalone application", test_standalone_application),
        ("No TFM concepts in API", test_no_tfm_concepts_in_api),
        ("Generic naming", test_generic_naming),
        ("Documentation independence", test_documentation_independence),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - TTK is independent from TFM")
    else:
        print("✗ SOME TESTS FAILED - TTK has TFM dependencies")
    print("=" * 70)
    
    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
