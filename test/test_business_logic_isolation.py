"""
Property-Based Test for Business Logic Isolation

**Feature: qt-gui-port, Property 4: Business logic isolation**
**Validates: Requirements 2.1, 2.5**

This test verifies that business logic modules do not have direct dependencies
on UI libraries (curses or Qt). This ensures that business logic can work with
any UI backend.

Note: This test uses hypothesis for property-based testing. Install with:
    pip install hypothesis pytest
"""

import ast
import os
from pathlib import Path

# Try to import hypothesis for property-based testing
try:
    from hypothesis import given, strategies as st, settings
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False
    print("Warning: hypothesis not installed. Property-based tests will be skipped.")
    print("Install with: pip install hypothesis")

# Try to import pytest
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    print("Warning: pytest not installed. Using basic assertions.")
    print("Install with: pip install pytest")


# Business logic modules that should be UI-agnostic
BUSINESS_LOGIC_MODULES = [
    'src/tfm_application.py',
    'src/tfm_pane_manager.py',
    'src/tfm_file_operations.py',
    'src/tfm_log_manager.py',
    'src/tfm_progress_manager.py',
    'src/tfm_state_manager.py',
    'src/tfm_cache_manager.py',
    'src/tfm_archive.py',
    'src/tfm_path.py',
]

# Modules that currently have curses dependencies but should be refactored
# These are excluded from strict isolation checks for now
MODULES_NEEDING_REFACTORING = [
    'src/tfm_external_programs.py',  # Uses curses for suspend/resume
    'src/tfm_config.py',  # Uses curses for key code constants
]

# UI libraries that business logic should NOT import
FORBIDDEN_UI_IMPORTS = [
    'curses',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'tkinter',
]


def get_imports_from_file(file_path: str) -> set:
    """
    Extract all import statements from a Python file.
    
    Args:
        file_path: Path to the Python file
    
    Returns:
        Set of imported module names
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
        
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        return imports
    
    except (SyntaxError, FileNotFoundError, UnicodeDecodeError) as e:
        if HAS_PYTEST:
            pytest.fail(f"Failed to parse {file_path}: {e}")
        else:
            raise AssertionError(f"Failed to parse {file_path}: {e}")
        return set()


def test_business_logic_modules_exist():
    """Verify that all business logic modules exist."""
    workspace_root = Path(__file__).parent.parent
    
    for module_path in BUSINESS_LOGIC_MODULES:
        full_path = workspace_root / module_path
        assert full_path.exists(), f"Business logic module not found: {module_path}"


if HAS_HYPOTHESIS:
    @settings(max_examples=100)
    @given(st.sampled_from(BUSINESS_LOGIC_MODULES))
    def test_business_logic_isolation(module_path: str):
        """
        Property 4: Business logic isolation
        
        For any business logic module, analyzing its imports should show no direct
        dependencies on curses or Qt libraries.
        
        This property ensures that business logic can work with any UI backend.
        """
        workspace_root = Path(__file__).parent.parent
        full_path = workspace_root / module_path
        
        # Get all imports from the module
        imports = get_imports_from_file(str(full_path))
        
        # Check for forbidden UI imports
        forbidden_found = imports.intersection(FORBIDDEN_UI_IMPORTS)
        
        assert not forbidden_found, (
            f"Business logic module '{module_path}' has forbidden UI imports: {forbidden_found}. "
            f"Business logic should not directly import UI libraries. "
            f"Use the IUIBackend abstraction instead."
        )


def test_all_business_logic_modules_are_ui_agnostic():
    """
    Comprehensive test that checks all business logic modules at once.
    
    This is a non-property-based test that provides a clear overview of
    which modules (if any) violate the business logic isolation principle.
    """
    workspace_root = Path(__file__).parent.parent
    violations = {}
    
    for module_path in BUSINESS_LOGIC_MODULES:
        full_path = workspace_root / module_path
        
        if not full_path.exists():
            violations[module_path] = ["Module file not found"]
            continue
        
        imports = get_imports_from_file(str(full_path))
        forbidden_found = imports.intersection(FORBIDDEN_UI_IMPORTS)
        
        if forbidden_found:
            violations[module_path] = list(forbidden_found)
    
    if violations:
        error_msg = "Business logic isolation violations found:\n"
        for module, forbidden_imports in violations.items():
            error_msg += f"  {module}: {', '.join(forbidden_imports)}\n"
        error_msg += "\nBusiness logic modules should not import UI libraries directly."
        if HAS_PYTEST:
            pytest.fail(error_msg)
        else:
            raise AssertionError(error_msg)


def test_tfm_application_uses_ui_backend():
    """
    Verify that TFMApplication uses IUIBackend abstraction.
    
    This test checks that the main application controller properly uses
    the UI backend abstraction instead of direct UI calls.
    """
    workspace_root = Path(__file__).parent.parent
    app_path = workspace_root / 'src' / 'tfm_application.py'
    
    assert app_path.exists(), "TFMApplication module not found"
    
    # Read the file content
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that IUIBackend is imported
    assert 'from tfm_ui_backend import IUIBackend' in content or 'import tfm_ui_backend' in content, \
        "TFMApplication should import IUIBackend"
    
    # Check that the class accepts ui_backend parameter
    assert 'ui_backend: IUIBackend' in content or 'ui_backend:IUIBackend' in content, \
        "TFMApplication should accept IUIBackend parameter"
    
    # Check that it stores the UI backend
    assert 'self.ui = ui_backend' in content or 'self.ui=ui_backend' in content, \
        "TFMApplication should store UI backend reference"


def test_pane_manager_is_ui_agnostic():
    """
    Verify that PaneManager is UI-agnostic.
    
    PaneManager should only manage pane state, not perform any rendering.
    """
    workspace_root = Path(__file__).parent.parent
    pane_manager_path = workspace_root / 'src' / 'tfm_pane_manager.py'
    
    assert pane_manager_path.exists(), "PaneManager module not found"
    
    imports = get_imports_from_file(str(pane_manager_path))
    forbidden_found = imports.intersection(FORBIDDEN_UI_IMPORTS)
    
    assert not forbidden_found, (
        f"PaneManager has forbidden UI imports: {forbidden_found}. "
        f"PaneManager should only manage pane state, not perform rendering."
    )


def test_file_operations_is_ui_agnostic():
    """
    Verify that FileOperations is UI-agnostic.
    
    FileOperations should only perform file operations, not UI updates.
    """
    workspace_root = Path(__file__).parent.parent
    file_ops_path = workspace_root / 'src' / 'tfm_file_operations.py'
    
    assert file_ops_path.exists(), "FileOperations module not found"
    
    imports = get_imports_from_file(str(file_ops_path))
    forbidden_found = imports.intersection(FORBIDDEN_UI_IMPORTS)
    
    assert not forbidden_found, (
        f"FileOperations has forbidden UI imports: {forbidden_found}. "
        f"FileOperations should only perform file operations, not UI updates."
    )


if __name__ == '__main__':
    if HAS_PYTEST:
        pytest.main([__file__, '-v'])
    else:
        # Run tests manually
        print("Running business logic isolation tests...")
        print()
        
        try:
            test_business_logic_modules_exist()
            print("✓ test_business_logic_modules_exist PASSED")
        except AssertionError as e:
            print(f"✗ test_business_logic_modules_exist FAILED: {e}")
        
        try:
            test_all_business_logic_modules_are_ui_agnostic()
            print("✓ test_all_business_logic_modules_are_ui_agnostic PASSED")
        except AssertionError as e:
            print(f"✗ test_all_business_logic_modules_are_ui_agnostic FAILED: {e}")
        
        try:
            test_tfm_application_uses_ui_backend()
            print("✓ test_tfm_application_uses_ui_backend PASSED")
        except AssertionError as e:
            print(f"✗ test_tfm_application_uses_ui_backend FAILED: {e}")
        
        try:
            test_pane_manager_is_ui_agnostic()
            print("✓ test_pane_manager_is_ui_agnostic PASSED")
        except AssertionError as e:
            print(f"✗ test_pane_manager_is_ui_agnostic FAILED: {e}")
        
        try:
            test_file_operations_is_ui_agnostic()
            print("✓ test_file_operations_is_ui_agnostic PASSED")
        except AssertionError as e:
            print(f"✗ test_file_operations_is_ui_agnostic FAILED: {e}")
        
        print()
        print("Tests complete!")
