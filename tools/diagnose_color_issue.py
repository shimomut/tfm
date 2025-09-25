#!/usr/bin/env python3
"""
Diagnostic script to help identify why colors work in --color-test but not in main TFM

This script can be run to compare different initialization scenarios and identify
the specific cause of color issues.
"""

import sys
import os
import curses
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

def test_scenario_1_basic_colors():
    """Test 1: Basic color support without any TFM code"""
    print("=== Test 1: Basic Color Support ===")
    
    def test_basic(stdscr):
        curses.start_color()
        
        # Test basic colors
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        
        stdscr.addstr(0, 0, "Red text", curses.color_pair(1))
        stdscr.addstr(1, 0, "Green text", curses.color_pair(2))
        stdscr.addstr(2, 0, "Blue text", curses.color_pair(3))
        stdscr.addstr(4, 0, "Press any key...")
        stdscr.refresh()
        stdscr.getch()
    
    try:
        curses.wrapper(test_basic)
        print("✓ Basic colors work")
    except Exception as e:
        print(f"✗ Basic colors failed: {e}")

def test_scenario_2_tfm_colors_only():
    """Test 2: TFM color system without other TFM components"""
    print("\n=== Test 2: TFM Color System Only ===")
    
    def test_tfm_colors(stdscr):
        from tfm_colors import init_colors, get_file_color
        
        # Initialize TFM colors
        init_colors('dark')
        
        # Test TFM colors
        regular_color = get_file_color(False, False, False, True)
        dir_color = get_file_color(True, False, False, True)
        exec_color = get_file_color(False, True, False, True)
        selected_color = get_file_color(False, False, True, True)
        
        stdscr.addstr(0, 0, "Regular file", regular_color)
        stdscr.addstr(1, 0, "Directory", dir_color)
        stdscr.addstr(2, 0, "Executable", exec_color)
        stdscr.addstr(3, 0, "Selected file", selected_color)
        stdscr.addstr(5, 0, "Press any key...")
        stdscr.refresh()
        stdscr.getch()
    
    try:
        curses.wrapper(test_tfm_colors)
        print("✓ TFM colors work")
    except Exception as e:
        print(f"✗ TFM colors failed: {e}")

def test_scenario_3_with_config():
    """Test 3: TFM colors with config system"""
    print("\n=== Test 3: TFM Colors + Config ===")
    
    def test_with_config(stdscr):
        from tfm_colors import init_colors, get_file_color
        from tfm_config import get_config
        
        # Load config like TFM does
        config = get_config()
        color_scheme = getattr(config, 'COLOR_SCHEME', 'dark')
        
        # Initialize colors with config
        init_colors(color_scheme)
        
        # Test colors
        regular_color = get_file_color(False, False, False, True)
        dir_color = get_file_color(True, False, False, True)
        
        stdscr.addstr(0, 0, f"Using scheme: {color_scheme}")
        stdscr.addstr(1, 0, "Regular file", regular_color)
        stdscr.addstr(2, 0, "Directory", dir_color)
        stdscr.addstr(4, 0, "Press any key...")
        stdscr.refresh()
        stdscr.getch()
    
    try:
        curses.wrapper(test_with_config)
        print("✓ TFM colors + config work")
    except Exception as e:
        print(f"✗ TFM colors + config failed: {e}")

def test_scenario_4_with_log_manager():
    """Test 4: TFM colors with log manager (stdout/stderr redirection)"""
    print("\n=== Test 4: TFM Colors + Log Manager ===")
    
    def test_with_log_manager(stdscr):
        from tfm_colors import init_colors, get_file_color
        from tfm_config import get_config
        from tfm_log_manager import LogManager
        
        # Load config
        config = get_config()
        color_scheme = getattr(config, 'COLOR_SCHEME', 'dark')
        
        # Initialize log manager (this redirects stdout/stderr)
        log_manager = LogManager(config)
        
        # Initialize colors after log manager
        init_colors(color_scheme)
        
        # Test colors
        regular_color = get_file_color(False, False, False, True)
        dir_color = get_file_color(True, False, False, True)
        
        stdscr.addstr(0, 0, "With log manager active")
        stdscr.addstr(1, 0, "Regular file", regular_color)
        stdscr.addstr(2, 0, "Directory", dir_color)
        stdscr.addstr(4, 0, "Press any key...")
        stdscr.refresh()
        stdscr.getch()
        
        # Restore stdout/stderr
        log_manager.restore_stdio()
    
    try:
        curses.wrapper(test_with_log_manager)
        print("✓ TFM colors + log manager work")
    except Exception as e:
        print(f"✗ TFM colors + log manager failed: {e}")

def test_scenario_5_background_colors():
    """Test 5: TFM colors with background color application"""
    print("\n=== Test 5: TFM Colors + Background Colors ===")
    
    def test_with_background(stdscr):
        from tfm_colors import init_colors, get_file_color
        from tfm_config import get_config
        
        # Load config and initialize colors
        config = get_config()
        color_scheme = getattr(config, 'COLOR_SCHEME', 'dark')
        init_colors(color_scheme)
        
        # Try to apply background color like TFM does
        try:
            from tfm_colors import apply_background_to_window, get_background_color_pair
            
            # Clear and apply background
            stdscr.clear()
            
            if apply_background_to_window(stdscr):
                stdscr.addstr(0, 0, "Background applied successfully")
            else:
                # Fallback method
                height, width = stdscr.getmaxyx()
                bg_color_pair = get_background_color_pair()
                
                for y in range(min(height, 10)):  # Only fill first 10 lines
                    try:
                        stdscr.addstr(y, 0, ' ' * (width - 1), bg_color_pair)
                    except curses.error:
                        pass
                
                stdscr.addstr(0, 0, "Background applied via fallback")
        except Exception as e:
            stdscr.addstr(0, 0, f"Background application failed: {e}")
        
        # Test colors after background application
        regular_color = get_file_color(False, False, False, True)
        dir_color = get_file_color(True, False, False, True)
        
        stdscr.addstr(2, 0, "Regular file", regular_color)
        stdscr.addstr(3, 0, "Directory", dir_color)
        stdscr.addstr(5, 0, "Press any key...")
        stdscr.refresh()
        stdscr.getch()
    
    try:
        curses.wrapper(test_with_background)
        print("✓ TFM colors + background work")
    except Exception as e:
        print(f"✗ TFM colors + background failed: {e}")

def test_scenario_6_full_tfm_init():
    """Test 6: Full TFM initialization sequence"""
    print("\n=== Test 6: Full TFM Initialization ===")
    
    def test_full_init(stdscr):
        from tfm_colors import init_colors, get_file_color
        from tfm_config import get_config
        from tfm_log_manager import LogManager
        
        # Replicate FileManager.__init__ sequence
        config = get_config()
        
        # Initialize log manager
        log_manager = LogManager(config)
        
        # Initialize colors
        color_scheme = getattr(config, 'COLOR_SCHEME', 'dark')
        init_colors(color_scheme)
        
        # Configure curses like TFM does
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)
        
        # Clear screen with background like TFM does
        try:
            from tfm_colors import apply_background_to_window, get_background_color_pair
            
            stdscr.clear()
            
            if not apply_background_to_window(stdscr):
                height, width = stdscr.getmaxyx()
                bg_color_pair = get_background_color_pair()
                
                for y in range(min(height, 10)):
                    try:
                        stdscr.addstr(y, 0, ' ' * (width - 1), bg_color_pair)
                    except curses.error:
                        pass
        except:
            stdscr.clear()
        
        # Test colors after full initialization
        regular_color = get_file_color(False, False, False, True)
        dir_color = get_file_color(True, False, False, True)
        exec_color = get_file_color(False, True, False, True)
        
        stdscr.addstr(0, 0, "Full TFM initialization complete")
        stdscr.addstr(2, 0, "Regular file", regular_color)
        stdscr.addstr(3, 0, "Directory", dir_color)
        stdscr.addstr(4, 0, "Executable", exec_color)
        stdscr.addstr(6, 0, "Press any key...")
        stdscr.refresh()
        stdscr.getch()
        
        # Cleanup
        log_manager.restore_stdio()
    
    try:
        curses.wrapper(test_full_init)
        print("✓ Full TFM initialization works")
    except Exception as e:
        print(f"✗ Full TFM initialization failed: {e}")

def main():
    """Run all diagnostic tests"""
    print("TFM Color Issue Diagnostic Tool")
    print("=" * 40)
    print()
    print("This tool tests different initialization scenarios to identify")
    print("why colors might work in --color-test but not in main TFM.")
    print()
    
    # Check environment
    print("Environment:")
    print(f"  TERM: {os.environ.get('TERM', 'not set')}")
    print(f"  COLORTERM: {os.environ.get('COLORTERM', 'not set')}")
    print(f"  TERM_PROGRAM: {os.environ.get('TERM_PROGRAM', 'not set')}")
    print()
    
    # Run tests in order
    test_scenario_1_basic_colors()
    test_scenario_2_tfm_colors_only()
    test_scenario_3_with_config()
    test_scenario_4_with_log_manager()
    test_scenario_5_background_colors()
    test_scenario_6_full_tfm_init()
    
    print("\n" + "=" * 40)
    print("Diagnostic complete!")
    print()
    print("If any test fails, that component is likely causing the color issue.")
    print("Compare these results with the behavior you see in:")
    print("  - python tfm.py --color-test interactive  (should work)")
    print("  - python tfm.py  (colors don't work)")

if __name__ == "__main__":
    main()