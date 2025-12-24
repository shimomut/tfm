#!/usr/bin/env python3
"""
TFM Color Testing Module

Provides comprehensive color debugging and testing functionality to help diagnose
color rendering issues across different terminals and environments.

SPECIAL NOTE: This is a diagnostic/testing tool that requires direct curses access
for low-level terminal color testing. It is not part of the core TFM application
and is only used via the --color-test command-line option. This is the only TFM
source file that retains a curses import for diagnostic purposes.
"""

import sys
import os
import time
from tfm_path import Path

# Special case: This diagnostic tool requires direct curses access for testing
import curses

# Import TFM color modules
from tfm_colors import (
    init_colors, get_color_capabilities, get_current_color_scheme,
    get_available_color_schemes, set_color_scheme, toggle_fallback_mode,
    is_fallback_mode, set_fallback_mode, print_color_support_info,
    get_file_color, get_header_color, get_footer_color, get_status_color,
    get_error_color, get_boundary_color, COLOR_SCHEMES
)

# Import logging
from tfm_log_manager import getLogger

# Initialize module-level logger
logger = getLogger("ColorTest")

def print_basic_info():
    """Print basic color information without curses initialization"""
    logger.info("TFM Color Testing - Basic Information")
    logger.info("=" * 50)
    logger.info("")
    
    # Terminal environment info
    logger.info("Terminal Environment:")
    logger.info(f"  TERM: {os.environ.get('TERM', 'not set')}")
    logger.info(f"  COLORTERM: {os.environ.get('COLORTERM', 'not set')}")
    logger.info(f"  TERM_PROGRAM: {os.environ.get('TERM_PROGRAM', 'not set')}")
    logger.info(f"  TERM_PROGRAM_VERSION: {os.environ.get('TERM_PROGRAM_VERSION', 'not set')}")
    logger.info("")
    
    # Available color schemes
    logger.info("Available Color Schemes:")
    for scheme in get_available_color_schemes():
        marker = " (current)" if scheme == get_current_color_scheme() else ""
        logger.info(f"  - {scheme}{marker}")
    logger.info("")
    
    # RGB color definitions
    logger.info("RGB Color Definitions:")
    for scheme_name, colors in COLOR_SCHEMES.items():
        logger.info(f"  {scheme_name.upper()} scheme: {len(colors)} colors defined")
    logger.info("")
    
    # Note: Fallback color schemes are no longer needed with TTK
    # TTK always supports full RGB colors
    logger.info("Note: TTK always supports full RGB colors (no fallback needed)")
    logger.info("")

def test_color_capabilities(stdscr):
    """Test and display terminal color capabilities"""
    stdscr.clear()
    
    # Initialize colors first
    init_colors()
    
    # Get capabilities
    caps = get_color_capabilities()
    
    y = 0
    stdscr.addstr(y, 0, "TFM Color Capabilities Test", curses.A_BOLD)
    y += 2
    
    stdscr.addstr(y, 0, f"Colors available: {caps['colors']}")
    y += 1
    stdscr.addstr(y, 0, f"Color pairs: {caps['color_pairs']}")
    y += 1
    stdscr.addstr(y, 0, f"RGB support: {'Yes' if caps['can_change_color'] else 'No'}")
    y += 1
    stdscr.addstr(y, 0, f"Current scheme: {get_current_color_scheme()}")
    y += 1
    stdscr.addstr(y, 0, f"Fallback mode: {'Enabled' if is_fallback_mode() else 'Disabled'}")
    y += 2
    
    # Test basic colors
    stdscr.addstr(y, 0, "Basic Color Test:")
    y += 1
    
    basic_colors = [
        (curses.COLOR_BLACK, "BLACK"),
        (curses.COLOR_RED, "RED"),
        (curses.COLOR_GREEN, "GREEN"),
        (curses.COLOR_YELLOW, "YELLOW"),
        (curses.COLOR_BLUE, "BLUE"),
        (curses.COLOR_MAGENTA, "MAGENTA"),
        (curses.COLOR_CYAN, "CYAN"),
        (curses.COLOR_WHITE, "WHITE")
    ]
    
    for i, (color, name) in enumerate(basic_colors):
        try:
            curses.init_pair(50 + i, color, curses.COLOR_BLACK)
            stdscr.addstr(y, i * 10, f"{name:8}", curses.color_pair(50 + i))
        except curses.error:
            stdscr.addstr(y, i * 10, f"{name:8}")
    
    y += 2
    
    # Test TFM file colors
    stdscr.addstr(y, 0, "TFM File Colors Test:")
    y += 1
    
    file_tests = [
        (False, False, False, True, "Regular file (active)"),
        (True, False, False, True, "Directory (active)"),
        (False, True, False, True, "Executable (active)"),
        (False, False, True, True, "Selected file (active)"),
        (True, False, True, True, "Selected directory (active)"),
        (False, True, True, True, "Selected executable (active)"),
        (False, False, True, False, "Selected file (inactive)"),
        (True, False, True, False, "Selected directory (inactive)"),
        (False, True, True, False, "Selected executable (inactive)"),
    ]
    
    for is_dir, is_exec, is_selected, is_active, description in file_tests:
        try:
            color = get_file_color(is_dir, is_exec, is_selected, is_active)
            stdscr.addstr(y, 0, f"{description:30}", color)
        except curses.error:
            stdscr.addstr(y, 0, f"{description:30} [ERROR]")
        y += 1
    
    y += 1
    
    # Test interface colors
    stdscr.addstr(y, 0, "Interface Colors Test:")
    y += 1
    
    interface_tests = [
        (get_header_color(True), "Header (active)"),
        (get_header_color(False), "Header (inactive)"),
        (get_footer_color(True), "Footer (active)"),
        (get_footer_color(False), "Footer (inactive)"),
        (get_status_color(), "Status bar"),
        (get_error_color(), "Error message"),
        (get_boundary_color(), "Boundary"),
    ]
    
    for color_func, description in interface_tests:
        try:
            stdscr.addstr(y, 0, f"{description:20}", color_func)
        except curses.error:
            stdscr.addstr(y, 0, f"{description:20} [ERROR]")
        y += 1
    
    y += 2
    stdscr.addstr(y, 0, "Press any key to continue...")
    stdscr.refresh()
    stdscr.getch()

def test_color_schemes(stdscr):
    """Test all available color schemes"""
    schemes = get_available_color_schemes()
    current_scheme_index = 0
    
    while True:
        stdscr.clear()
        
        # Set current scheme
        current_scheme = schemes[current_scheme_index]
        set_color_scheme(current_scheme)
        init_colors()
        
        y = 0
        stdscr.addstr(y, 0, f"Color Scheme Test: {current_scheme.upper()}", curses.A_BOLD)
        y += 1
        stdscr.addstr(y, 0, f"Scheme {current_scheme_index + 1} of {len(schemes)}")
        y += 2
        
        # Show sample file listing
        stdscr.addstr(y, 0, "Sample File Listing:", curses.A_UNDERLINE)
        y += 1
        
        sample_files = [
            ("Documents/", True, False, False),
            ("script.py", False, True, False),
            ("readme.txt", False, False, False),
            ("config.json", False, False, True),  # Selected
            ("Photos/", True, False, True),       # Selected directory
            ("backup.sh", False, True, True),     # Selected executable
        ]
        
        for i, (filename, is_dir, is_exec, is_selected) in enumerate(sample_files):
            # Test both active and inactive selection
            for is_active in [True, False]:
                if is_selected:
                    color = get_file_color(is_dir, is_exec, is_selected, is_active)
                    marker = ">" if is_active else " "
                    pane_label = "active" if is_active else "inactive"
                    stdscr.addstr(y, 0, f"{marker} {filename:15} ({pane_label})", color)
                    y += 1
                elif is_active:  # Only show unselected files once
                    color = get_file_color(is_dir, is_exec, is_selected, is_active)
                    stdscr.addstr(y, 0, f"  {filename:15}", color)
                    y += 1
        
        y += 1
        
        # Show interface elements
        stdscr.addstr(y, 0, "Interface Elements:", curses.A_UNDERLINE)
        y += 1
        
        try:
            stdscr.addstr(y, 0, "/home/user/documents", get_header_color(True))
            stdscr.addstr(y, 25, "│", get_boundary_color())
            stdscr.addstr(y, 26, "/home/user/downloads", get_header_color(False))
            y += 1
            
            stdscr.addstr(y, 0, "5 dirs, 12 files", get_footer_color(True))
            stdscr.addstr(y, 25, "│", get_boundary_color())
            stdscr.addstr(y, 26, "3 dirs, 8 files", get_footer_color(False))
            y += 1
            
            stdscr.addstr(y, 0, "Status: Ready", get_status_color())
            y += 1
            
            stdscr.addstr(y, 0, "Error: File not found", get_error_color())
            y += 2
        except curses.error:
            stdscr.addstr(y, 0, "[Interface color test failed]")
            y += 3
        
        # Instructions
        stdscr.addstr(y, 0, "Controls:")
        y += 1
        stdscr.addstr(y, 0, "  Left/Right arrows: Change scheme")
        y += 1
        stdscr.addstr(y, 0, "  F: Toggle fallback mode")
        y += 1
        stdscr.addstr(y, 0, "  Q: Quit")
        y += 1
        
        fallback_status = "ON" if is_fallback_mode() else "OFF"
        stdscr.addstr(y, 0, f"Fallback mode: {fallback_status}")
        
        stdscr.refresh()
        
        # Handle input
        key = stdscr.getch()
        
        if key == ord('q') or key == ord('Q'):
            break
        elif key == curses.KEY_RIGHT:
            current_scheme_index = (current_scheme_index + 1) % len(schemes)
        elif key == curses.KEY_LEFT:
            current_scheme_index = (current_scheme_index - 1) % len(schemes)
        elif key == ord('f') or key == ord('F'):
            toggle_fallback_mode()

def test_rgb_colors(stdscr):
    """Test RGB color functionality"""
    stdscr.clear()
    
    # Force RGB mode
    set_fallback_mode(False)
    init_colors()
    
    y = 0
    stdscr.addstr(y, 0, "RGB Color Test (Forced RGB Mode)", curses.A_BOLD)
    y += 2
    
    caps = get_color_capabilities()
    stdscr.addstr(y, 0, f"RGB support: {'Yes' if caps['can_change_color'] else 'No'}")
    y += 1
    stdscr.addstr(y, 0, f"Fallback mode: {'Enabled' if is_fallback_mode() else 'Disabled'}")
    y += 2
    
    if not caps['can_change_color']:
        stdscr.addstr(y, 0, "WARNING: Terminal does not support RGB colors!", get_error_color())
        y += 1
        stdscr.addstr(y, 0, "This test will show fallback colors instead.")
        y += 2
    
    # Test RGB gradient
    stdscr.addstr(y, 0, "RGB Gradient Test:")
    y += 1
    
    try:
        # Create a simple gradient
        for i in range(16):
            color_num = 200 + i
            r = int((i / 15.0) * 255)
            g = 128
            b = int(((15 - i) / 15.0) * 255)
            
            # Convert to curses scale
            r_curses = int((r / 255.0) * 1000)
            g_curses = int((g / 255.0) * 1000)
            b_curses = int((b / 255.0) * 1000)
            
            try:
                curses.init_color(color_num, r_curses, g_curses, b_curses)
                curses.init_pair(60 + i, color_num, curses.COLOR_BLACK)
                stdscr.addstr(y, i * 2, "██", curses.color_pair(60 + i))
            except curses.error:
                stdscr.addstr(y, i * 2, "XX")
        
        y += 2
    except curses.error:
        stdscr.addstr(y, 0, "RGB gradient test failed")
        y += 2
    
    # Show current scheme colors
    current_scheme = get_current_color_scheme()
    rgb_colors = COLOR_SCHEMES.get(current_scheme, {})
    
    stdscr.addstr(y, 0, f"Current scheme ({current_scheme}) RGB values:")
    y += 1
    
    key_colors = ['DIRECTORY_FG', 'EXECUTABLE_FG', 'REGULAR_FILE_FG', 'SELECTED_BG']
    for color_name in key_colors:
        if color_name in rgb_colors:
            rgb = rgb_colors[color_name]['rgb']
            stdscr.addstr(y, 0, f"  {color_name:20}: RGB{rgb}")
            y += 1
    
    y += 1
    stdscr.addstr(y, 0, "Press any key to continue...")
    stdscr.refresh()
    stdscr.getch()

def test_fallback_colors(stdscr):
    """Test fallback color functionality"""
    stdscr.clear()
    
    # Force fallback mode
    set_fallback_mode(True)
    init_colors()
    
    y = 0
    stdscr.addstr(y, 0, "Fallback Color Test (Forced Fallback Mode)", curses.A_BOLD)
    y += 2
    
    caps = get_color_capabilities()
    stdscr.addstr(y, 0, f"RGB support: {'Yes' if caps['can_change_color'] else 'No'}")
    y += 1
    stdscr.addstr(y, 0, f"Fallback mode: {'Enabled' if is_fallback_mode() else 'Disabled'}")
    y += 2
    
    stdscr.addstr(y, 0, "This test forces the use of fallback colors even if RGB is supported.")
    y += 2
    
    # Note: Fallback colors are no longer used with TTK
    current_scheme = get_current_color_scheme()
    
    stdscr.addstr(y, 0, f"Current scheme ({current_scheme}) - TTK uses full RGB (no fallback)")
    y += 1
    
    color_names = {
        curses.COLOR_BLACK: "BLACK",
        curses.COLOR_RED: "RED",
        curses.COLOR_GREEN: "GREEN",
        curses.COLOR_YELLOW: "YELLOW",
        curses.COLOR_BLUE: "BLUE",
        curses.COLOR_MAGENTA: "MAGENTA",
        curses.COLOR_CYAN: "CYAN",
        curses.COLOR_WHITE: "WHITE"
    }
    
    key_colors = ['DIRECTORY_FG', 'EXECUTABLE_FG', 'REGULAR_FILE_FG', 'SELECTED_BG']
    for color_name in key_colors:
        if color_name in fallback_colors:
            color_val = fallback_colors[color_name]
            color_str = color_names.get(color_val, f"COLOR_{color_val}")
            stdscr.addstr(y, 0, f"  {color_name:20}: {color_str}")
            y += 1
    
    y += 1
    
    # Test file colors with fallback
    stdscr.addstr(y, 0, "File color test with fallback colors:")
    y += 1
    
    sample_files = [
        ("regular.txt", False, False, False, False),
        ("directory/", True, False, False, False),
        ("script.py", False, True, False, False),
        ("selected.txt", False, False, True, True),
        ("sel_dir/", True, False, True, True),
        ("sel_script.sh", False, True, True, True),
    ]
    
    for filename, is_dir, is_exec, is_selected, is_active in sample_files:
        try:
            color = get_file_color(is_dir, is_exec, is_selected, is_active)
            stdscr.addstr(y, 0, f"  {filename:15}", color)
        except curses.error:
            stdscr.addstr(y, 0, f"  {filename:15} [ERROR]")
        y += 1
    
    y += 1
    stdscr.addstr(y, 0, "Press any key to continue...")
    stdscr.refresh()
    stdscr.getch()

def interactive_color_tester(stdscr):
    """Interactive color testing interface"""
    current_scheme_index = 0
    schemes = get_available_color_schemes()
    fallback_mode = False
    
    while True:
        stdscr.clear()
        
        # Apply current settings
        current_scheme = schemes[current_scheme_index]
        set_color_scheme(current_scheme)
        set_fallback_mode(fallback_mode)
        init_colors()
        
        y = 0
        stdscr.addstr(y, 0, "TFM Interactive Color Tester", curses.A_BOLD)
        y += 2
        
        # Current settings
        stdscr.addstr(y, 0, f"Color scheme: {current_scheme}")
        y += 1
        stdscr.addstr(y, 0, f"Fallback mode: {'ON' if fallback_mode else 'OFF'}")
        y += 1
        
        caps = get_color_capabilities()
        stdscr.addstr(y, 0, f"Terminal RGB support: {'Yes' if caps['can_change_color'] else 'No'}")
        y += 1
        stdscr.addstr(y, 0, f"Colors available: {caps['colors']}")
        y += 2
        
        # Sample display
        stdscr.addstr(y, 0, "Sample File Manager Display:", curses.A_UNDERLINE)
        y += 1
        
        # Header
        try:
            stdscr.addstr(y, 0, "/home/user/documents", get_header_color(True))
            stdscr.addstr(y, 25, "│", get_boundary_color())
            stdscr.addstr(y, 27, "/home/user/projects", get_header_color(False))
            y += 1
        except curses.error:
            y += 1
        
        # File listing
        sample_files = [
            ("../", True, False, False, True, "Parent directory"),
            ("Documents/", True, False, False, True, "Directory"),
            ("Photos/", True, False, True, True, "Selected directory"),
            ("script.py", False, True, False, True, "Executable file"),
            ("readme.txt", False, False, False, True, "Regular file"),
            ("config.json", False, False, True, True, "Selected file"),
            ("backup.sh", False, True, True, False, "Selected executable (inactive)"),
        ]
        
        for filename, is_dir, is_exec, is_selected, is_active, description in sample_files:
            try:
                color = get_file_color(is_dir, is_exec, is_selected, is_active)
                marker = ">" if is_selected and is_active else " "
                stdscr.addstr(y, 0, f"{marker} {filename:15}", color)
                stdscr.addstr(y, 20, f"({description})")
            except curses.error:
                stdscr.addstr(y, 0, f"  {filename:15} [ERROR]")
            y += 1
        
        # Footer
        try:
            stdscr.addstr(y, 0, "3 dirs, 4 files (2 selected)", get_footer_color(True))
            stdscr.addstr(y, 25, "│", get_boundary_color())
            stdscr.addstr(y, 27, "2 dirs, 3 files", get_footer_color(False))
            y += 1
        except curses.error:
            y += 1
        
        # Status bar
        try:
            stdscr.addstr(y, 0, "Status: Color test mode active", get_status_color())
            y += 1
        except curses.error:
            y += 1
        
        y += 1
        
        # Controls
        stdscr.addstr(y, 0, "Controls:", curses.A_UNDERLINE)
        y += 1
        stdscr.addstr(y, 0, "  S: Next color scheme")
        y += 1
        stdscr.addstr(y, 0, "  F: Toggle fallback mode")
        y += 1
        stdscr.addstr(y, 0, "  I: Show detailed info")
        y += 1
        stdscr.addstr(y, 0, "  D: Diagnose color issues")
        y += 1
        stdscr.addstr(y, 0, "  Q: Quit")
        y += 1
        
        # Additional info
        y += 1
        if fallback_mode:
            stdscr.addstr(y, 0, "Note: Fallback mode forces basic colors", get_error_color())
        elif not caps['can_change_color']:
            stdscr.addstr(y, 0, "Note: Terminal doesn't support RGB, using fallback", get_error_color())
        else:
            stdscr.addstr(y, 0, "Note: Using RGB colors")
        
        stdscr.refresh()
        
        # Handle input
        key = stdscr.getch()
        
        if key == ord('q') or key == ord('Q'):
            break
        elif key == ord('s') or key == ord('S'):
            current_scheme_index = (current_scheme_index + 1) % len(schemes)
        elif key == ord('f') or key == ord('F'):
            fallback_mode = not fallback_mode
        elif key == ord('i') or key == ord('I'):
            show_detailed_info(stdscr)
        elif key == ord('d') or key == ord('D'):
            diagnose_color_initialization_issue(stdscr)

def diagnose_color_initialization_issue(stdscr):
    """Diagnose potential color initialization issues"""
    stdscr.clear()
    
    y = 0
    stdscr.addstr(y, 0, "Color Initialization Issue Diagnosis", curses.A_BOLD)
    y += 2
    
    stdscr.addstr(y, 0, "This test helps diagnose why colors work in --color-test but not in main TFM")
    y += 2
    
    # Test 1: Basic curses color support
    stdscr.addstr(y, 0, "Test 1: Basic curses color support")
    y += 1
    
    try:
        if curses.has_colors():
            stdscr.addstr(y, 0, "  ✓ Terminal supports colors")
        else:
            stdscr.addstr(y, 0, "  ✗ Terminal does NOT support colors")
        y += 1
        
        if curses.can_change_color():
            stdscr.addstr(y, 0, "  ✓ Terminal supports RGB color changes")
        else:
            stdscr.addstr(y, 0, "  ✗ Terminal does NOT support RGB color changes")
        y += 1
        
        stdscr.addstr(y, 0, f"  Colors available: {curses.COLORS}")
        y += 1
        stdscr.addstr(y, 0, f"  Color pairs available: {curses.COLOR_PAIRS}")
        y += 1
        
    except Exception as e:
        stdscr.addstr(y, 0, f"  Error checking color support: {e}")
        y += 1
    
    y += 1
    
    # Test 2: Color initialization timing
    stdscr.addstr(y, 0, "Test 2: Color initialization timing")
    y += 1
    
    # Test colors before init_colors
    try:
        curses.init_pair(90, curses.COLOR_RED, curses.COLOR_BLACK)
        stdscr.addstr(y, 0, "  Before init_colors: ", curses.color_pair(90))
        stdscr.addstr(y, 22, "Basic color works", curses.color_pair(90))
        y += 1
    except Exception as e:
        stdscr.addstr(y, 0, f"  Before init_colors: Basic color failed ({e})")
        y += 1
    
    # Initialize colors
    try:
        init_colors('dark')
        stdscr.addstr(y, 0, "  ✓ init_colors('dark') completed")
        y += 1
    except Exception as e:
        stdscr.addstr(y, 0, f"  ✗ init_colors failed: {e}")
        y += 1
    
    # Test colors after init_colors
    try:
        color = get_file_color(True, False, False, True)  # Directory color
        stdscr.addstr(y, 0, "  After init_colors: ", color)
        stdscr.addstr(y, 21, "Directory color works", color)
        y += 1
    except Exception as e:
        stdscr.addstr(y, 0, f"  After init_colors: TFM color failed ({e})")
        y += 1
    
    y += 1
    
    # Test 3: Check for color pair conflicts
    stdscr.addstr(y, 0, "Test 3: Color pair usage analysis")
    y += 1
    
    # Check which color pairs are in use
    used_pairs = []
    for i in range(1, min(64, curses.COLOR_PAIRS)):
        try:
            # Try to get color pair info (this might not work on all systems)
            used_pairs.append(i)
        except:
            pass
    
    stdscr.addstr(y, 0, f"  Color pairs potentially in use: {len(used_pairs)}")
    y += 1
    
    # Test 4: Environment variables that might affect colors
    stdscr.addstr(y, 0, "Test 4: Environment variables")
    y += 1
    
    env_vars = {
        'TERM': 'Terminal type',
        'COLORTERM': 'Color support indicator', 
        'TERM_PROGRAM': 'Terminal program',
        'NO_COLOR': 'Disable colors flag',
        'FORCE_COLOR': 'Force colors flag',
        'CLICOLOR': 'CLI color support',
        'CLICOLOR_FORCE': 'Force CLI colors'
    }
    
    for var, description in env_vars.items():
        value = os.environ.get(var, 'not set')
        if value != 'not set':
            stdscr.addstr(y, 0, f"  {var}: {value}")
            y += 1
    
    y += 1
    
    # Test 5: Check for potential interference
    stdscr.addstr(y, 0, "Test 5: Potential interference checks")
    y += 1
    
    # Check if stdout/stderr redirection might affect colors
    if not sys.stdout.isatty():
        stdscr.addstr(y, 0, "  ⚠ stdout is not a TTY (might affect colors)")
        y += 1
    else:
        stdscr.addstr(y, 0, "  ✓ stdout is a TTY")
        y += 1
    
    if not sys.stderr.isatty():
        stdscr.addstr(y, 0, "  ⚠ stderr is not a TTY (might affect colors)")
        y += 1
    else:
        stdscr.addstr(y, 0, "  ✓ stderr is a TTY")
        y += 1
    
    y += 2
    
    # Recommendations
    stdscr.addstr(y, 0, "Recommendations:", curses.A_UNDERLINE)
    y += 1
    
    recommendations = [
        "1. If colors work here but not in main TFM:",
        "   - Check if TFM's stdout/stderr redirection affects colors",
        "   - Look for code that calls curses functions after init_colors",
        "   - Check if background color setting interferes",
        "",
        "2. Try running main TFM with different settings:",
        "   - Set TERM=xterm-256color",
        "   - Unset NO_COLOR if it's set",
        "   - Try different terminal emulator",
        "",
        "3. Compare this output with main TFM behavior"
    ]
    
    for rec in recommendations:
        if y < stdscr.getmaxyx()[0] - 2:
            stdscr.addstr(y, 0, rec)
            y += 1
    
    y += 1
    stdscr.addstr(y, 0, "Press any key to continue...")
    stdscr.refresh()
    stdscr.getch()

def show_detailed_info(stdscr):
    """Show detailed color information"""
    stdscr.clear()
    
    y = 0
    stdscr.addstr(y, 0, "Detailed Color Information", curses.A_BOLD)
    y += 2
    
    # Terminal info
    stdscr.addstr(y, 0, "Terminal Environment:")
    y += 1
    env_vars = ['TERM', 'COLORTERM', 'TERM_PROGRAM', 'TERM_PROGRAM_VERSION']
    for var in env_vars:
        value = os.environ.get(var, 'not set')
        stdscr.addstr(y, 0, f"  {var}: {value}")
        y += 1
    
    y += 1
    
    # Color capabilities
    caps = get_color_capabilities()
    stdscr.addstr(y, 0, "Color Capabilities:")
    y += 1
    stdscr.addstr(y, 0, f"  Colors: {caps['colors']}")
    y += 1
    stdscr.addstr(y, 0, f"  Color pairs: {caps['color_pairs']}")
    y += 1
    stdscr.addstr(y, 0, f"  RGB support: {'Yes' if caps['can_change_color'] else 'No'}")
    y += 1
    
    # Current settings
    y += 1
    stdscr.addstr(y, 0, "Current Settings:")
    y += 1
    stdscr.addstr(y, 0, f"  Scheme: {get_current_color_scheme()}")
    y += 1
    stdscr.addstr(y, 0, f"  Fallback mode: {'Enabled' if is_fallback_mode() else 'Disabled'}")
    y += 1
    
    # Color scheme details
    current_scheme = get_current_color_scheme()
    rgb_colors = COLOR_SCHEMES.get(current_scheme, {})
    
    y += 1
    stdscr.addstr(y, 0, f"RGB Colors in {current_scheme} scheme (TTK always uses RGB):")
    y += 1
    
    max_lines = stdscr.getmaxyx()[0] - y - 3
    color_count = 0
    
    for color_name, color_def in rgb_colors.items():
        if color_count >= max_lines:
            stdscr.addstr(y, 0, "  ... (more colors available)")
            break
        rgb = color_def['rgb']
        stdscr.addstr(y, 0, f"  {color_name:20}: RGB{rgb}")
        y += 1
        color_count += 1
    
    y += 1
    stdscr.addstr(y, 0, "Press any key to return...")
    stdscr.refresh()
    stdscr.getch()

def test_tfm_initialization_sequence(stdscr):
    """Test the exact same initialization sequence as main TFM"""
    stdscr.clear()
    
    y = 0
    stdscr.addstr(y, 0, "TFM Initialization Sequence Test", curses.A_BOLD)
    y += 2
    
    # Step 1: Import config (simulate)
    stdscr.addstr(y, 0, "Step 1: Loading configuration...")
    y += 1
    
    try:
        from tfm_config import get_config
        config = get_config()
        color_scheme = getattr(config, 'COLOR_SCHEME', 'dark')
        stdscr.addstr(y, 0, f"  Config loaded, color scheme: {color_scheme}")
        y += 1
    except Exception as e:
        stdscr.addstr(y, 0, f"  Config load failed: {e}")
        y += 1
        color_scheme = 'dark'
    
    y += 1
    
    # Step 2: Initialize colors (same as TFM)
    stdscr.addstr(y, 0, "Step 2: Initializing colors...")
    y += 1
    
    try:
        init_colors(color_scheme)
        stdscr.addstr(y, 0, f"  Colors initialized with scheme: {color_scheme}")
        y += 1
    except Exception as e:
        stdscr.addstr(y, 0, f"  Color initialization failed: {e}")
        y += 1
    
    y += 1
    
    # Step 3: Configure curses (same as TFM)
    stdscr.addstr(y, 0, "Step 3: Configuring curses...")
    y += 1
    
    try:
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)
        stdscr.addstr(y, 0, "  Curses configured successfully")
        y += 1
    except Exception as e:
        stdscr.addstr(y, 0, f"  Curses configuration failed: {e}")
        y += 1
    
    y += 2
    
    # Step 4: Test colors
    stdscr.addstr(y, 0, "Step 4: Testing colors after TFM-style initialization...")
    y += 1
    
    # Test file colors
    sample_files = [
        ("regular.txt", False, False, False, True, "Regular file"),
        ("directory/", True, False, False, True, "Directory"),
        ("script.py", False, True, False, True, "Executable"),
        ("selected.txt", False, False, True, True, "Selected file"),
    ]
    
    for filename, is_dir, is_exec, is_selected, is_active, description in sample_files:
        try:
            color = get_file_color(is_dir, is_exec, is_selected, is_active)
            stdscr.addstr(y, 0, f"  {filename:15}", color)
            stdscr.addstr(y, 20, f"({description})")
        except Exception as e:
            stdscr.addstr(y, 0, f"  {filename:15} [ERROR: {e}]")
        y += 1
    
    y += 2
    
    # Step 5: Compare with current terminal state
    stdscr.addstr(y, 0, "Step 5: Terminal state comparison...")
    y += 1
    
    caps = get_color_capabilities()
    stdscr.addstr(y, 0, f"  Colors available: {caps['colors']}")
    y += 1
    stdscr.addstr(y, 0, f"  RGB support: {'Yes' if caps['can_change_color'] else 'No'}")
    y += 1
    stdscr.addstr(y, 0, f"  Fallback mode: {'Enabled' if is_fallback_mode() else 'Disabled'}")
    y += 1
    
    # Check if colors are actually working
    try:
        # Try to use a basic color
        curses.init_pair(99, curses.COLOR_RED, curses.COLOR_BLACK)
        stdscr.addstr(y, 0, "  Basic color test: ", curses.color_pair(99))
        stdscr.addstr(y, 20, "SUCCESS", curses.color_pair(99))
        y += 1
    except Exception as e:
        stdscr.addstr(y, 0, f"  Basic color test: FAILED ({e})")
        y += 1
    
    y += 2
    stdscr.addstr(y, 0, "Analysis complete. Press any key to continue...")
    stdscr.refresh()
    stdscr.getch()

def run_color_test(test_mode):
    """Main entry point for color testing"""
    if test_mode == 'info':
        print_basic_info()
        
    elif test_mode == 'schemes':
        print_basic_info()
        logger.info("\nDetailed Color Scheme Information:")
        logger.info("=" * 50)
        
        for scheme_name in get_available_color_schemes():
            logger.info(f"\n{scheme_name.upper()} SCHEME:")
            logger.info("-" * 20)
            
            # RGB colors
            rgb_colors = COLOR_SCHEMES.get(scheme_name, {})
            logger.info(f"RGB colors: {len(rgb_colors)}")
            
            # Show key colors
            key_colors = ['DIRECTORY_FG', 'EXECUTABLE_FG', 'REGULAR_FILE_FG', 'SELECTED_BG']
            for color_name in key_colors:
                if color_name in rgb_colors:
                    rgb = rgb_colors[color_name]['rgb']
                    logger.info(f"  {color_name:20}: RGB{rgb}")
            
            # Note: Fallback colors no longer used with TTK
            logger.info("Note: TTK always uses full RGB colors (no fallback)")
        
    elif test_mode == 'capabilities':
        print_basic_info()
        logger.info("\nTesting terminal capabilities...")
        
        # Test without curses first
        logger.info(f"TERM environment: {os.environ.get('TERM', 'not set')}")
        logger.info(f"COLORTERM environment: {os.environ.get('COLORTERM', 'not set')}")
        
        # Test with curses
        def test_caps(stdscr):
            test_color_capabilities(stdscr)
        
        curses.wrapper(test_caps)
        
    elif test_mode == 'rgb-test':
        logger.info("Testing RGB color support...")
        curses.wrapper(test_rgb_colors)
        
    elif test_mode == 'fallback-test':
        logger.info("Testing fallback color support...")
        curses.wrapper(test_fallback_colors)
        
    elif test_mode == 'interactive':
        logger.info("Starting interactive color tester...")
        logger.info("Use the controls shown in the interface to test different settings.")
        curses.wrapper(interactive_color_tester)
        
    elif test_mode == 'tfm-init':
        logger.info("Testing TFM initialization sequence...")
        logger.info("This test replicates the exact same initialization as main TFM.")
        curses.wrapper(test_tfm_initialization_sequence)
        
    elif test_mode == 'diagnose':
        logger.info("Diagnosing color initialization issues...")
        logger.info("This test helps identify why colors work in --color-test but not in main TFM.")
        curses.wrapper(diagnose_color_initialization_issue)
    
    else:
        logger.error(f"Unknown test mode: {test_mode}")
        sys.exit(1)

if __name__ == "__main__":
    # Allow running this module directly for testing
    import sys
    if len(sys.argv) > 1:
        run_color_test(sys.argv[1])
    else:
        logger.info("Usage: python tfm_color_tester.py <test_mode>")
        logger.info("Available modes: info, schemes, capabilities, rgb-test, fallback-test, interactive")