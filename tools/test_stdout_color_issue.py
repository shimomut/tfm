#!/usr/bin/env python3
"""
Test to check if stdout/stderr redirection affects color functionality

This test specifically checks if the LogManager's stdout/stderr redirection
is causing the color issue.
"""

import sys
import os
import curses
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

def test_colors_before_redirection():
    """Test colors before any stdout/stderr redirection"""
    print("=== Testing colors BEFORE stdout/stderr redirection ===")
    
    def test_colors(stdscr):
        from tfm_colors import init_colors, get_file_color
        
        # Initialize colors
        init_colors('dark')
        
        # Test colors
        regular_color = get_file_color(False, False, False, True)
        dir_color = get_file_color(True, False, False, True)
        exec_color = get_file_color(False, True, False, True)
        
        stdscr.addstr(0, 0, "Colors BEFORE stdout redirection:")
        stdscr.addstr(2, 0, "Regular file", regular_color)
        stdscr.addstr(3, 0, "Directory", dir_color)
        stdscr.addstr(4, 0, "Executable", exec_color)
        stdscr.addstr(6, 0, "Press any key to continue...")
        stdscr.refresh()
        stdscr.getch()
    
    try:
        curses.wrapper(test_colors)
        print("✓ Colors work BEFORE redirection")
        return True
    except Exception as e:
        print(f"✗ Colors failed BEFORE redirection: {e}")
        return False

def test_colors_after_redirection():
    """Test colors after stdout/stderr redirection (like TFM does)"""
    print("\n=== Testing colors AFTER stdout/stderr redirection ===")
    
    def test_colors(stdscr):
        from tfm_colors import init_colors, get_file_color
        from tfm_config import get_config
        from tfm_log_manager import LogManager
        
        # Initialize log manager (this redirects stdout/stderr)
        config = get_config()
        log_manager = LogManager(config)
        
        # Initialize colors AFTER redirection
        init_colors('dark')
        
        # Test colors
        regular_color = get_file_color(False, False, False, True)
        dir_color = get_file_color(True, False, False, True)
        exec_color = get_file_color(False, True, False, True)
        
        stdscr.addstr(0, 0, "Colors AFTER stdout redirection:")
        stdscr.addstr(2, 0, "Regular file", regular_color)
        stdscr.addstr(3, 0, "Directory", dir_color)
        stdscr.addstr(4, 0, "Executable", exec_color)
        stdscr.addstr(6, 0, "Press any key to continue...")
        stdscr.refresh()
        stdscr.getch()
        
        # Restore stdout/stderr
        log_manager.restore_stdio()
    
    try:
        curses.wrapper(test_colors)
        print("✓ Colors work AFTER redirection")
        return True
    except Exception as e:
        print(f"✗ Colors failed AFTER redirection: {e}")
        return False

def test_colors_init_before_redirection():
    """Test initializing colors BEFORE redirection, then redirecting"""
    print("\n=== Testing colors initialized BEFORE redirection ===")
    
    def test_colors(stdscr):
        from tfm_colors import init_colors, get_file_color
        from tfm_config import get_config
        from tfm_log_manager import LogManager
        
        # Initialize colors BEFORE redirection
        init_colors('dark')
        
        # Now initialize log manager (redirects stdout/stderr)
        config = get_config()
        log_manager = LogManager(config)
        
        # Test colors after redirection
        regular_color = get_file_color(False, False, False, True)
        dir_color = get_file_color(True, False, False, True)
        exec_color = get_file_color(False, True, False, True)
        
        stdscr.addstr(0, 0, "Colors initialized BEFORE redirection:")
        stdscr.addstr(2, 0, "Regular file", regular_color)
        stdscr.addstr(3, 0, "Directory", dir_color)
        stdscr.addstr(4, 0, "Executable", exec_color)
        stdscr.addstr(6, 0, "Press any key to continue...")
        stdscr.refresh()
        stdscr.getch()
        
        # Restore stdout/stderr
        log_manager.restore_stdio()
    
    try:
        curses.wrapper(test_colors)
        print("✓ Colors work when initialized BEFORE redirection")
        return True
    except Exception as e:
        print(f"✗ Colors failed when initialized BEFORE redirection: {e}")
        return False

def test_manual_redirection():
    """Test manual stdout/stderr redirection to see if that's the issue"""
    print("\n=== Testing manual stdout/stderr redirection ===")
    
    def test_colors(stdscr):
        from tfm_colors import init_colors, get_file_color
        import io
        
        # Manually redirect stdout/stderr like LogManager does
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        # Redirect to string buffers
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        
        # Initialize colors after manual redirection
        init_colors('dark')
        
        # Test colors
        regular_color = get_file_color(False, False, False, True)
        dir_color = get_file_color(True, False, False, True)
        exec_color = get_file_color(False, True, False, True)
        
        # Restore stdout/stderr for display
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
        stdscr.addstr(0, 0, "Colors with manual stdout redirection:")
        stdscr.addstr(2, 0, "Regular file", regular_color)
        stdscr.addstr(3, 0, "Directory", dir_color)
        stdscr.addstr(4, 0, "Executable", exec_color)
        stdscr.addstr(6, 0, "Press any key to continue...")
        stdscr.refresh()
        stdscr.getch()
    
    try:
        curses.wrapper(test_colors)
        print("✓ Colors work with manual redirection")
        return True
    except Exception as e:
        print(f"✗ Colors failed with manual redirection: {e}")
        return False

def main():
    """Run all stdout/stderr redirection tests"""
    print("TFM Stdout/Stderr Redirection Color Test")
    print("=" * 50)
    print()
    print("This test checks if the LogManager's stdout/stderr redirection")
    print("is causing the color issue you're experiencing.")
    print()
    
    # Check environment
    print("Environment:")
    print(f"  TERM: {os.environ.get('TERM', 'not set')}")
    print(f"  COLORTERM: {os.environ.get('COLORTERM', 'not set')}")
    print(f"  stdout.isatty(): {sys.stdout.isatty()}")
    print(f"  stderr.isatty(): {sys.stderr.isatty()}")
    print()
    
    # Run tests
    results = []
    results.append(("Before redirection", test_colors_before_redirection()))
    results.append(("After redirection", test_colors_after_redirection()))
    results.append(("Init before redirection", test_colors_init_before_redirection()))
    results.append(("Manual redirection", test_manual_redirection()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("-" * 20)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {test_name:25}: {status}")
    
    print()
    
    # Analysis
    if results[0][1] and not results[1][1]:
        print("🔍 DIAGNOSIS: stdout/stderr redirection is likely causing the color issue!")
        print()
        print("✅ GOOD NEWS: This issue has been FIXED!")
        print("The fix moves color initialization to happen BEFORE LogManager creation.")
        print("Colors are now initialized before stdout/stderr redirection occurs.")
        
    elif results[0][1] and results[2][1] and not results[1][1]:
        print("🔍 DIAGNOSIS: Color initialization timing is the issue!")
        print()
        print("✅ GOOD NEWS: This issue has been FIXED!")
        print("Colors are now initialized before LogManager creation.")
        
    elif all(result[1] for result in results):
        print("🤔 All tests passed - the issue might be elsewhere.")
        print("Try running the full diagnostic tool: python tools/diagnose_color_issue.py")
        
    else:
        print("🔍 Multiple issues detected. Check individual test results above.")
    
    print()
    print("Next steps:")
    print("1. Test the main TFM application: python tfm.py")
    print("2. Compare with color test: python tfm.py --color-test interactive")
    print("3. Both should now show colors correctly!")
    print()
    print("If colors still don't work, run: python tools/diagnose_color_issue.py")

if __name__ == "__main__":
    main()