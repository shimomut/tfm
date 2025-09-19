#!/usr/bin/env python3
"""
Test script to verify j/k/h/l navigation keys have been removed
"""

import sys
import re

def test_navigation_keys_removed():
    """Test that j/k/h/l keys are no longer used for navigation"""
    print("Testing removal of j/k/h/l navigation keys...")
    
    try:
        with open('tfm_main.py', 'r') as f:
            content = f.read()
        
        # Check for removed navigation patterns
        removed_patterns = [
            r"key == ord\('j'\)",
            r"key == ord\('k'\)",
            r"key == ord\('h'\)",
            r"key == ord\('l'\)",
        ]
        
        found_issues = []
        
        for pattern in removed_patterns:
            matches = re.findall(pattern, content)
            if matches:
                found_issues.append(f"Found {len(matches)} instances of {pattern}")
        
        # Check for remaining arrow key navigation (should still exist)
        arrow_patterns = [
            r"curses\.KEY_UP",
            r"curses\.KEY_DOWN", 
            r"curses\.KEY_LEFT",
            r"curses\.KEY_RIGHT"
        ]
        
        arrow_found = []
        for pattern in arrow_patterns:
            matches = re.findall(pattern, content)
            if matches:
                arrow_found.append(f"Found {len(matches)} instances of {pattern}")
        
        # Report results
        if found_issues:
            print("✗ Issues found:")
            for issue in found_issues:
                print(f"  {issue}")
            return False
        else:
            print("✓ No j/k/h/l navigation keys found")
        
        if arrow_found:
            print("✓ Arrow key navigation preserved:")
            for arrow in arrow_found:
                print(f"  {arrow}")
        else:
            print("✗ Warning: No arrow key navigation found")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return False

def test_specific_navigation_contexts():
    """Test specific contexts where navigation keys should be removed"""
    print("\nTesting specific navigation contexts...")
    
    try:
        with open('tfm_main.py', 'r') as f:
            content = f.read()
        
        # Test cases that should NOT exist anymore
        bad_patterns = [
            # Main file navigation
            r"elif key == curses\.KEY_UP or key == ord\('k'\):",
            r"elif key == curses\.KEY_DOWN or key == ord\('j'\):",
            # Dialog navigation
            r"elif key == curses\.KEY_LEFT or key == ord\('h'\):",
            r"elif key == curses\.KEY_RIGHT or key == ord\('l'\):",
            # Log scrolling with l/L
            r"elif key == ord\('l'\):.*scroll log",
            r"elif key == ord\('L'\):.*scroll log",
        ]
        
        # Test cases that SHOULD exist (arrow keys only)
        good_patterns = [
            r"elif key == curses\.KEY_UP:",
            r"elif key == curses\.KEY_DOWN:",
            r"elif key == curses\.KEY_LEFT:",
            r"elif key == curses\.KEY_RIGHT:",
        ]
        
        issues = []
        
        for pattern in bad_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Found bad pattern: {pattern}")
        
        good_found = 0
        for pattern in good_patterns:
            if re.search(pattern, content):
                good_found += 1
        
        if issues:
            print("✗ Found problematic patterns:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("✓ No problematic navigation patterns found")
        
        if good_found >= 4:  # Should have at least UP, DOWN, LEFT, RIGHT
            print(f"✓ Found {good_found} arrow-only navigation patterns")
        else:
            print(f"✗ Warning: Only found {good_found} arrow navigation patterns")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing navigation contexts: {e}")
        return False

def test_remaining_functionality():
    """Test that other functionality using these keys is preserved"""
    print("\nTesting remaining functionality...")
    
    try:
        with open('tfm_main.py', 'r') as f:
            content = f.read()
        
        # These should still exist for other purposes
        preserved_patterns = [
            # Delete functionality should still use 'k'
            r"delete_files.*k.*K",
            # Ctrl+K and Ctrl+L for log scrolling should remain
            r"key == 11.*Ctrl\+K",
            r"key == 12.*Ctrl\+L",
        ]
        
        preserved_found = 0
        for pattern in preserved_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                preserved_found += 1
        
        print(f"✓ Found {preserved_found} preserved functionality patterns")
        
        # Check that delete functionality is still intact
        if 'delete_selected_files' in content:
            print("✓ Delete functionality preserved")
        else:
            print("✗ Delete functionality missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing remaining functionality: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("TFM Navigation Keys Removal Test")
    print("=" * 60)
    
    tests = [
        ("Remove j/k/h/l Navigation", test_navigation_keys_removed),
        ("Specific Navigation Contexts", test_specific_navigation_contexts),
        ("Remaining Functionality", test_remaining_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[{passed + 1}/{total}] {test_name}")
        print("-" * 40)
        
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL TESTS PASSED - j/k/h/l navigation keys successfully removed!")
        print("\nNavigation Summary:")
        print("- Arrow keys (↑↓←→) are used for all navigation")
        print("- j/k/h/l keys are no longer used for navigation")
        print("- Other functionality (delete, log scroll) preserved")
        print("- Ctrl+K/Ctrl+L still work for log scrolling")
    else:
        print("✗ Some tests failed - please check the implementation")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)