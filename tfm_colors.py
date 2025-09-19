"""
Color definitions and initialization for TFM (Terminal File Manager)
"""
import curses

# Color pair constants
COLOR_DIRECTORIES = 1
COLOR_EXECUTABLES = 2
COLOR_SELECTED = 3
COLOR_ERROR = 4
COLOR_HEADER = 5
COLOR_STATUS = 6

def init_colors():
    """Initialize all color pairs for the application"""
    curses.start_color()
    curses.init_pair(COLOR_DIRECTORIES, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_EXECUTABLES, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SELECTED, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_ERROR, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(COLOR_HEADER, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(COLOR_STATUS, curses.COLOR_WHITE, curses.COLOR_BLUE)

def get_file_color(is_dir, is_executable, is_selected, is_active):
    """Get the appropriate color for a file based on its properties"""
    base_color = curses.A_NORMAL
    
    if is_dir:
        base_color = curses.color_pair(COLOR_DIRECTORIES) | curses.A_BOLD
    elif is_executable:
        base_color = curses.color_pair(COLOR_EXECUTABLES)
    
    # Apply selection highlighting
    if is_selected and is_active:
        return curses.color_pair(COLOR_SELECTED) | curses.A_REVERSE
    elif is_selected:
        return base_color | curses.A_UNDERLINE
    else:
        return base_color

def get_header_color(is_active=False):
    """Get header color with optional bold for active panes"""
    if is_active:
        return curses.color_pair(COLOR_HEADER) | curses.A_BOLD
    else:
        return curses.color_pair(COLOR_HEADER)

def get_status_color():
    """Get status line color"""
    return curses.color_pair(COLOR_STATUS)

def get_error_color():
    """Get error message color"""
    return curses.color_pair(COLOR_ERROR)

def get_log_color(source):
    """Get appropriate color for log messages based on source"""
    if source == "STDERR":
        return curses.color_pair(COLOR_ERROR)  # Red for stderr
    elif source == "SYSTEM":
        return curses.color_pair(COLOR_SELECTED)  # Yellow for system messages
    else:
        return curses.A_NORMAL