"""
Color definitions and initialization for TFM (Terminal File Manager)
"""
import curses

# Color pair constants

# File type colors (normal)
COLOR_REGULAR_FILE = 1       # Regular files
COLOR_DIRECTORIES = 2        # Directories
COLOR_EXECUTABLES = 3        # Executable files

# File type colors (selected)
COLOR_REGULAR_FILE_SELECTED = 4    # Selected regular files
COLOR_DIRECTORIES_SELECTED = 5     # Selected directories
COLOR_EXECUTABLES_SELECTED = 6     # Selected executables

# File type colors (selected inactive)
COLOR_REGULAR_FILE_SELECTED_INACTIVE = 24    # Selected regular files in inactive pane
COLOR_DIRECTORIES_SELECTED_INACTIVE = 25     # Selected directories in inactive pane
COLOR_EXECUTABLES_SELECTED_INACTIVE = 26     # Selected executables in inactive pane

# Interface colors
COLOR_HEADER = 7        # File list headers (directory paths)
COLOR_FOOTER = 8        # File list footers (file counts)
COLOR_STATUS = 9        # Status bar
COLOR_BOUNDARY = 10     # Pane boundaries
COLOR_ERROR = 11        # Error messages

# Log colors
COLOR_LOG_STDOUT = 12   # Stdout log messages
COLOR_LOG_SYSTEM = 13   # System log messages
COLOR_LINE_NUMBERS = 14 # Line numbers in text viewer

# Syntax highlighting colors
COLOR_SYNTAX_KEYWORD = 15    # Keywords (def, class, if, etc.)
COLOR_SYNTAX_STRING = 16     # String literals
COLOR_SYNTAX_COMMENT = 17    # Comments
COLOR_SYNTAX_NUMBER = 18     # Numbers
COLOR_SYNTAX_OPERATOR = 19   # Operators (+, -, =, etc.)
COLOR_SYNTAX_BUILTIN = 20    # Built-in functions/types
COLOR_SYNTAX_NAME = 21       # Variable/function names

# Search highlighting colors
COLOR_SEARCH_MATCH = 22      # Search match highlighting
COLOR_SEARCH_CURRENT = 23    # Current search match highlighting

# Current color scheme
current_color_scheme = 'dark'

# Default background and foreground colors for the current scheme
default_background_color = None
default_foreground_color = None

# Color scheme definitions (RGB values 0-255)
COLOR_SCHEMES = {
    'dark': {
        'HEADER_BG': {
            'color_num': 100,
            'rgb': (51, 63, 76)     # Dark blue-gray for file list headers
        },
        'FOOTER_BG': {
            'color_num': 104,
            'rgb': (51, 63, 76)     # Dark blue-gray for file list footers
        },
        'STATUS_BG': {
            'color_num': 105,
            'rgb': (51, 63, 76)     # Dark blue-gray for status bar
        },
        'BOUNDARY_BG': {
            'color_num': 106,
            'rgb': (51, 63, 76)     # Dark blue-gray for boundaries
        },
        'DIRECTORY_FG': {
            'color_num': 101,
            'rgb': (204, 204, 120)  # Yellow for directories
        },
        'EXECUTABLE_FG': {
            'color_num': 102,
            'rgb': (51, 229, 51)    # Bright green for executables
        },
        'SELECTED_BG': {
            'color_num': 103,
            'rgb': (40, 80, 160)    # Dark blue-purple background for selected items
        },
        'SELECTED_INACTIVE_BG': {
            'color_num': 150,
            'rgb': (80, 80, 80)    # Darker blue background for selected items in inactive pane
        },
        'REGULAR_FILE_FG': {
            'color_num': 107,
            'rgb': (220, 220, 220)  # Light gray for regular files
        },
        'LOG_STDOUT_FG': {
            'color_num': 108,
            'rgb': (220, 220, 220)  # Light gray for stdout logs
        },
        'LOG_SYSTEM_FG': {
            'color_num': 109,
            'rgb': (100, 200, 255)  # Light blue for system logs
        },
        'LINE_NUMBERS_FG': {
            'color_num': 110,
            'rgb': (128, 128, 128)  # Gray for line numbers
        },
        # Syntax highlighting colors
        'SYNTAX_KEYWORD_FG': {
            'color_num': 111,
            'rgb': (255, 119, 0)    # Orange for keywords
        },
        'SYNTAX_STRING_FG': {
            'color_num': 112,
            'rgb': (0, 255, 0)      # Green for strings
        },
        'SYNTAX_COMMENT_FG': {
            'color_num': 113,
            'rgb': (128, 128, 128)  # Gray for comments
        },
        'SYNTAX_NUMBER_FG': {
            'color_num': 114,
            'rgb': (255, 255, 0)    # Yellow for numbers
        },
        'SYNTAX_OPERATOR_FG': {
            'color_num': 115,
            'rgb': (255, 0, 255)    # Magenta for operators
        },
        'SYNTAX_BUILTIN_FG': {
            'color_num': 116,
            'rgb': (0, 255, 255)    # Cyan for built-ins
        },
        'SYNTAX_NAME_FG': {
            'color_num': 117,
            'rgb': (220, 220, 220)  # Light gray for names
        },
        # Search highlighting colors
        'SEARCH_MATCH_BG': {
            'color_num': 118,
            'rgb': (30, 60, 120)    # Dark blue background for search matches
        },
        'SEARCH_CURRENT_BG': {
            'color_num': 119,
            'rgb': (40, 80, 160)    # Medium blue background for current search match
        },
        'DEFAULT_FG': {
            'color_num': 146,
            'rgb': (220, 220, 220)  # Light gray for default foreground
        },
        'DEFAULT_BG': {
            'color_num': 147,
            'rgb': (0, 0, 0)        # Black for default background
        }
    },
    'light': {
        'HEADER_BG': {
            'color_num': 120,
            'rgb': (220, 220, 220)     # Light gray for file list headers
        },
        'FOOTER_BG': {
            'color_num': 124,
            'rgb': (220, 220, 220)     # Light gray for file list footers
        },
        'STATUS_BG': {
            'color_num': 125,
            'rgb': (220, 220, 220)     # Light gray for status bar
        },
        'BOUNDARY_BG': {
            'color_num': 126,
            'rgb': (220, 220, 220)     # Light gray for boundaries
        },
        'DIRECTORY_FG': {
            'color_num': 121,
            'rgb': (160, 120, 0)  # Dark yellow/brown for directories
        },
        'EXECUTABLE_FG': {
            'color_num': 122,
            'rgb': (0, 160, 0)    # Dark green for executables
        },
        'SELECTED_BG': {
            'color_num': 123,
            'rgb': (120, 160, 255)    # Light blue background for selected items
        },
        'SELECTED_INACTIVE_BG': {
            'color_num': 151,
            'rgb': (160, 160, 160)    # Lighter blue background for selected items in inactive pane
        },
        'REGULAR_FILE_FG': {
            'color_num': 127,
            'rgb': (60, 60, 60)     # Dark gray for regular files
        },
        'LOG_STDOUT_FG': {
            'color_num': 128,
            'rgb': (60, 60, 60)     # Dark gray for stdout logs
        },
        'LOG_SYSTEM_FG': {
            'color_num': 129,
            'rgb': (50, 100, 160)  # Dark blue for system logs
        },
        'LINE_NUMBERS_FG': {
            'color_num': 130,
            'rgb': (128, 128, 128)  # Gray for line numbers
        },
        # Syntax highlighting colors
        'SYNTAX_KEYWORD_FG': {
            'color_num': 131,
            'rgb': (128, 0, 128)    # Purple for keywords
        },
        'SYNTAX_STRING_FG': {
            'color_num': 132,
            'rgb': (0, 128, 0)      # Dark green for strings
        },
        'SYNTAX_COMMENT_FG': {
            'color_num': 133,
            'rgb': (128, 128, 128)  # Gray for comments
        },
        'SYNTAX_NUMBER_FG': {
            'color_num': 134,
            'rgb': (0, 0, 200)      # Blue for numbers
        },
        'SYNTAX_OPERATOR_FG': {
            'color_num': 135,
            'rgb': (200, 0, 0)      # Red for operators
        },
        'SYNTAX_BUILTIN_FG': {
            'color_num': 136,
            'rgb': (0, 128, 128)    # Teal for built-ins
        },
        'SYNTAX_NAME_FG': {
            'color_num': 137,
            'rgb': (64, 64, 64)     # Dark gray for names
        },
        # Search highlighting colors
        'SEARCH_MATCH_BG': {
            'color_num': 138,
            'rgb': (180, 240, 255)    # Very light blue background for search matches
        },
        'SEARCH_CURRENT_BG': {
            'color_num': 139,
            'rgb': (140, 200, 255)    # Light blue background for current search match
        },
        'DEFAULT_FG': {
            'color_num': 148,
            'rgb': (0, 0, 0)        # Black for default foreground
        },
        'DEFAULT_BG': {
            'color_num': 149,
            'rgb': (255, 255, 255)  # White for default background
        }
    }
}

# Backward compatibility - use current scheme's colors
def get_current_rgb_colors():
    """Get RGB colors for the current color scheme"""
    return COLOR_SCHEMES.get(current_color_scheme, COLOR_SCHEMES['dark'])

# Fallback color schemes for terminals without RGB support
FALLBACK_COLOR_SCHEMES = {
    'dark': {
        'HEADER_BG': curses.COLOR_BLUE,         # Dark blue-gray → blue
        'FOOTER_BG': curses.COLOR_BLUE,         # Dark blue-gray → blue
        'STATUS_BG': curses.COLOR_BLUE,         # Dark blue-gray → blue
        'BOUNDARY_BG': curses.COLOR_BLUE,       # Dark blue-gray → blue
        'DIRECTORY_FG': curses.COLOR_YELLOW,    # (204,204,120) yellowish → yellow
        'EXECUTABLE_FG': curses.COLOR_GREEN,    # (51,229,51) bright green → green
        'SELECTED_BG': curses.COLOR_BLUE,       # (40,80,160) dark blue → blue
        'SELECTED_INACTIVE_BG': curses.COLOR_BLACK,  # (80,80,80) dark gray → black
        'REGULAR_FILE_FG': curses.COLOR_WHITE,  # (220,220,220) light gray → white
        'LOG_STDOUT_FG': curses.COLOR_WHITE,    # (220,220,220) light gray → white
        'LOG_SYSTEM_FG': curses.COLOR_CYAN,     # (100,200,255) light blue → cyan
        'LINE_NUMBERS_FG': curses.COLOR_WHITE,  # (128,128,128) gray → white
        # Syntax highlighting fallback colors
        'SYNTAX_KEYWORD_FG': curses.COLOR_YELLOW,   # (255,119,0) orange → yellow
        'SYNTAX_STRING_FG': curses.COLOR_GREEN,     # (0,255,0) green → green
        'SYNTAX_COMMENT_FG': curses.COLOR_WHITE,    # (128,128,128) gray → white
        'SYNTAX_NUMBER_FG': curses.COLOR_YELLOW,    # (255,255,0) yellow → yellow
        'SYNTAX_OPERATOR_FG': curses.COLOR_MAGENTA, # (255,0,255) magenta → magenta
        'SYNTAX_BUILTIN_FG': curses.COLOR_CYAN,     # (0,255,255) cyan → cyan
        'SYNTAX_NAME_FG': curses.COLOR_WHITE,       # (220,220,220) light gray → white
        # Search highlighting fallback colors
        'SEARCH_MATCH_BG': curses.COLOR_BLUE,       # (30,60,120) dark blue → blue
        'SEARCH_CURRENT_BG': curses.COLOR_BLUE,     # (40,80,160) blue → blue
        # Default colors
        'DEFAULT_FG': curses.COLOR_WHITE,           # (220,220,220) light gray → white
        'DEFAULT_BG': curses.COLOR_BLACK            # (0,0,0) black → black
    },
    'light': {
        'HEADER_BG': curses.COLOR_WHITE,        # (220,220,220) light gray → white
        'FOOTER_BG': curses.COLOR_WHITE,        # (220,220,220) light gray → white
        'STATUS_BG': curses.COLOR_WHITE,        # (220,220,220) light gray → white
        'BOUNDARY_BG': curses.COLOR_WHITE,      # (220,220,220) light gray → white
        'DIRECTORY_FG': curses.COLOR_YELLOW,    # (160,120,0) brown/yellow → yellow
        'EXECUTABLE_FG': curses.COLOR_GREEN,    # (0,160,0) dark green → green
        'SELECTED_BG': curses.COLOR_CYAN,       # (120,160,255) light blue → cyan
        'SELECTED_INACTIVE_BG': curses.COLOR_WHITE,  # (160,160,160) gray → white (closest available)
        'REGULAR_FILE_FG': curses.COLOR_BLACK,  # (60,60,60) dark gray → black
        'LOG_STDOUT_FG': curses.COLOR_BLACK,    # (60,60,60) dark gray → black
        'LOG_SYSTEM_FG': curses.COLOR_BLUE,     # (50,100,160) dark blue → blue
        'LINE_NUMBERS_FG': curses.COLOR_BLACK,  # (128,128,128) gray → black (closest available)
        # Syntax highlighting fallback colors
        'SYNTAX_KEYWORD_FG': curses.COLOR_MAGENTA,  # (128,0,128) purple → magenta
        'SYNTAX_STRING_FG': curses.COLOR_GREEN,     # (0,128,0) dark green → green
        'SYNTAX_COMMENT_FG': curses.COLOR_BLACK,    # (128,128,128) gray → black
        'SYNTAX_NUMBER_FG': curses.COLOR_BLUE,      # (0,0,200) blue → blue
        'SYNTAX_OPERATOR_FG': curses.COLOR_RED,     # (200,0,0) red → red
        'SYNTAX_BUILTIN_FG': curses.COLOR_CYAN,     # (0,128,128) teal → cyan
        'SYNTAX_NAME_FG': curses.COLOR_BLACK,       # (64,64,64) dark gray → black
        # Search highlighting fallback colors
        'SEARCH_MATCH_BG': curses.COLOR_CYAN,       # (180,240,255) very light blue → cyan
        'SEARCH_CURRENT_BG': curses.COLOR_CYAN,     # (140,200,255) light blue → cyan
        # Default colors
        'DEFAULT_FG': curses.COLOR_BLACK,           # (0,0,0) black → black
        'DEFAULT_BG': curses.COLOR_WHITE            # (255,255,255) white → white
    }
}

# Backward compatibility - use current scheme's fallback colors
def get_current_fallback_colors():
    """Get fallback colors for the current color scheme"""
    return FALLBACK_COLOR_SCHEMES.get(current_color_scheme, FALLBACK_COLOR_SCHEMES['dark'])

def init_colors(color_scheme=None):
    """Initialize all color pairs for the application"""
    global current_color_scheme
    
    # Set color scheme from parameter or use current
    if color_scheme:
        current_color_scheme = color_scheme
    
    curses.start_color()
    
    # Get colors for current scheme
    rgb_colors = get_current_rgb_colors()
    fallback_colors = get_current_fallback_colors()
    
    # Check if terminal supports RGB colors
    can_change_color = curses.can_change_color()
    
    # Initialize custom RGB colors if supported
    if can_change_color:
        rgb_success = True
        try:
            # Define all custom RGB colors from current scheme
            for color_name, color_def in rgb_colors.items():
                color_num = color_def['color_num']
                r, g, b = color_def['rgb']
                
                # Convert RGB (0-255) to curses scale (0-1000)
                r_curses = int((r / 255.0) * 1000)
                g_curses = int((g / 255.0) * 1000)
                b_curses = int((b / 255.0) * 1000)
                
                curses.init_color(color_num, r_curses, g_curses, b_curses)
            
            # Use custom RGB colors
            header_bg = rgb_colors['HEADER_BG']['color_num']
            footer_bg = rgb_colors['FOOTER_BG']['color_num']
            status_bg = rgb_colors['STATUS_BG']['color_num']
            boundary_bg = rgb_colors['BOUNDARY_BG']['color_num']
            directory_fg = rgb_colors['DIRECTORY_FG']['color_num']
            executable_fg = rgb_colors['EXECUTABLE_FG']['color_num']
            selected_bg = rgb_colors['SELECTED_BG']['color_num']
            selected_inactive_bg = rgb_colors['SELECTED_INACTIVE_BG']['color_num']
            regular_file_fg = rgb_colors['REGULAR_FILE_FG']['color_num']
            log_stdout_fg = rgb_colors['LOG_STDOUT_FG']['color_num']
            log_system_fg = rgb_colors['LOG_SYSTEM_FG']['color_num']
            line_numbers_fg = rgb_colors['LINE_NUMBERS_FG']['color_num']
            # Syntax highlighting colors
            syntax_keyword_fg = rgb_colors['SYNTAX_KEYWORD_FG']['color_num']
            syntax_string_fg = rgb_colors['SYNTAX_STRING_FG']['color_num']
            syntax_comment_fg = rgb_colors['SYNTAX_COMMENT_FG']['color_num']
            syntax_number_fg = rgb_colors['SYNTAX_NUMBER_FG']['color_num']
            syntax_operator_fg = rgb_colors['SYNTAX_OPERATOR_FG']['color_num']
            syntax_builtin_fg = rgb_colors['SYNTAX_BUILTIN_FG']['color_num']
            syntax_name_fg = rgb_colors['SYNTAX_NAME_FG']['color_num']
            # Search highlighting colors
            search_match_bg = rgb_colors['SEARCH_MATCH_BG']['color_num']
            search_current_bg = rgb_colors['SEARCH_CURRENT_BG']['color_num']
            # Default colors
            default_fg = rgb_colors['DEFAULT_FG']['color_num']
            default_bg = rgb_colors['DEFAULT_BG']['color_num']
            
            # Print success message for RGB colors
            print(f"Using RGB colors for {current_color_scheme} scheme ({len(rgb_colors)} colors defined)")
            
        except curses.error:
            rgb_success = False
    
    # Use fallback colors if RGB not supported or failed
    if not can_change_color or not rgb_success:
        # Print message about using fallback colors
        if not can_change_color:
            print(f"Terminal does not support RGB colors - using fallback colors for {current_color_scheme} scheme")
        else:
            print(f"RGB color initialization failed - using fallback colors for {current_color_scheme} scheme")
        
        # For light scheme, force use of standard curses colors to avoid RGB issues
        if current_color_scheme == 'light':
            print("Light scheme: Using standard curses colors for better compatibility")
        header_bg = fallback_colors['HEADER_BG']
        footer_bg = fallback_colors['FOOTER_BG']
        status_bg = fallback_colors['STATUS_BG']
        boundary_bg = fallback_colors['BOUNDARY_BG']
        directory_fg = fallback_colors['DIRECTORY_FG']
        executable_fg = fallback_colors['EXECUTABLE_FG']
        selected_bg = fallback_colors['SELECTED_BG']
        selected_inactive_bg = fallback_colors['SELECTED_INACTIVE_BG']
        regular_file_fg = fallback_colors['REGULAR_FILE_FG']
        log_stdout_fg = fallback_colors['LOG_STDOUT_FG']
        log_system_fg = fallback_colors['LOG_SYSTEM_FG']
        line_numbers_fg = fallback_colors['LINE_NUMBERS_FG']
        # Syntax highlighting fallback colors
        syntax_keyword_fg = fallback_colors['SYNTAX_KEYWORD_FG']
        syntax_string_fg = fallback_colors['SYNTAX_STRING_FG']
        syntax_comment_fg = fallback_colors['SYNTAX_COMMENT_FG']
        syntax_number_fg = fallback_colors['SYNTAX_NUMBER_FG']
        syntax_operator_fg = fallback_colors['SYNTAX_OPERATOR_FG']
        syntax_builtin_fg = fallback_colors['SYNTAX_BUILTIN_FG']
        syntax_name_fg = fallback_colors['SYNTAX_NAME_FG']
        # Search highlighting fallback colors
        search_match_bg = fallback_colors['SEARCH_MATCH_BG']
        search_current_bg = fallback_colors['SEARCH_CURRENT_BG']
        # Default colors
        default_fg = fallback_colors['DEFAULT_FG']
        default_bg = fallback_colors['DEFAULT_BG']
    
    # Use scheme-specific default colors
    bg_color = default_bg
    header_text_color = default_fg
    
    # Initialize color pairs
    
    # File type colors (normal)
    curses.init_pair(COLOR_REGULAR_FILE, regular_file_fg, bg_color)
    curses.init_pair(COLOR_DIRECTORIES, directory_fg, bg_color)
    curses.init_pair(COLOR_EXECUTABLES, executable_fg, bg_color)
    
    # File type colors (selected)
    curses.init_pair(COLOR_REGULAR_FILE_SELECTED, regular_file_fg, selected_bg)
    curses.init_pair(COLOR_DIRECTORIES_SELECTED, directory_fg, selected_bg)
    curses.init_pair(COLOR_EXECUTABLES_SELECTED, executable_fg, selected_bg)
    
    # File type colors (selected inactive) - use dedicated background and underline
    curses.init_pair(COLOR_REGULAR_FILE_SELECTED_INACTIVE, regular_file_fg, selected_inactive_bg)
    curses.init_pair(COLOR_DIRECTORIES_SELECTED_INACTIVE, directory_fg, selected_inactive_bg)
    curses.init_pair(COLOR_EXECUTABLES_SELECTED_INACTIVE, executable_fg, selected_inactive_bg)
    
    # Interface colors
    curses.init_pair(COLOR_HEADER, header_text_color, header_bg)
    curses.init_pair(COLOR_FOOTER, header_text_color, footer_bg)
    curses.init_pair(COLOR_STATUS, header_text_color, status_bg)
    curses.init_pair(COLOR_BOUNDARY, header_text_color, boundary_bg)
    curses.init_pair(COLOR_ERROR, curses.COLOR_RED, bg_color)
    
    # Log colors
    curses.init_pair(COLOR_LOG_STDOUT, log_stdout_fg, bg_color)
    curses.init_pair(COLOR_LOG_SYSTEM, log_system_fg, bg_color)
    curses.init_pair(COLOR_LINE_NUMBERS, line_numbers_fg, bg_color)
    # Syntax highlighting color pairs
    curses.init_pair(COLOR_SYNTAX_KEYWORD, syntax_keyword_fg, bg_color)
    curses.init_pair(COLOR_SYNTAX_STRING, syntax_string_fg, bg_color)
    curses.init_pair(COLOR_SYNTAX_COMMENT, syntax_comment_fg, bg_color)
    curses.init_pair(COLOR_SYNTAX_NUMBER, syntax_number_fg, bg_color)
    curses.init_pair(COLOR_SYNTAX_OPERATOR, syntax_operator_fg, bg_color)
    curses.init_pair(COLOR_SYNTAX_BUILTIN, syntax_builtin_fg, bg_color)
    curses.init_pair(COLOR_SYNTAX_NAME, syntax_name_fg, bg_color)
    # Search highlighting color pairs
    search_text_color = default_fg
    curses.init_pair(COLOR_SEARCH_MATCH, search_text_color, search_match_bg)
    curses.init_pair(COLOR_SEARCH_CURRENT, search_text_color, search_current_bg)
    
    # Store the default colors globally for use by the application
    global default_background_color, default_foreground_color
    default_background_color = default_bg
    default_foreground_color = default_fg
    
    # Try multiple methods to set default colors
    default_colors_set = False
    
    # Method 1: assume_default_colors (best option)
    try:
        curses.assume_default_colors(default_fg, default_bg)
        print(f"Set terminal default colors: fg={default_fg}, bg={default_bg}")
        default_colors_set = True
    except (curses.error, AttributeError):
        pass
    
    # Method 2: Use color pair 0 (fallback)
    if not default_colors_set:
        try:
            curses.init_pair(0, default_fg, default_bg)
            print(f"Set default color pair 0: fg={default_fg}, bg={default_bg}")
            default_colors_set = True
        except curses.error:
            pass
    
    # Method 3: Create a dedicated background color pair
    if not default_colors_set:
        try:
            # Use a high color pair number for background
            BACKGROUND_COLOR_PAIR = 63  # Usually safe, most terminals have 64+ pairs
            curses.init_pair(BACKGROUND_COLOR_PAIR, default_fg, default_bg)
            print(f"Created background color pair {BACKGROUND_COLOR_PAIR}: fg={default_fg}, bg={default_bg}")
            print("Note: Application will need to explicitly use this color pair for backgrounds")
            default_colors_set = True
        except curses.error:
            pass
    
    if not default_colors_set:
        print("Warning: Could not set terminal default background color")
        print("Blank spaces may not match the color scheme background")
        print("Try using a different terminal emulator for better color support")

def get_file_color(is_dir, is_executable, is_selected, is_active):
    """Get the appropriate color for a file based on its properties"""
    # Handle selected files with common background color
    if is_selected and is_active:
        if is_dir:
            return curses.color_pair(COLOR_DIRECTORIES_SELECTED)
        elif is_executable:
            return curses.color_pair(COLOR_EXECUTABLES_SELECTED)
        else:
            return curses.color_pair(COLOR_REGULAR_FILE_SELECTED)
    
    # Handle inactive selection with dedicated colors
    if is_selected:
        if is_dir:
            return curses.color_pair(COLOR_DIRECTORIES_SELECTED_INACTIVE)
        elif is_executable:
            return curses.color_pair(COLOR_EXECUTABLES_SELECTED_INACTIVE)
        else:
            return curses.color_pair(COLOR_REGULAR_FILE_SELECTED_INACTIVE)
    
    # Normal (unselected) files
    if is_dir:
        return curses.color_pair(COLOR_DIRECTORIES)
    elif is_executable:
        return curses.color_pair(COLOR_EXECUTABLES)
    else:
        return curses.color_pair(COLOR_REGULAR_FILE)

def get_header_color(is_active=False):
    """Get header color with optional bold for active panes"""
    if is_active:
        return curses.color_pair(COLOR_HEADER) | curses.A_BOLD
    else:
        return curses.color_pair(COLOR_HEADER)

def get_footer_color(is_active=False):
    """Get footer color with optional bold for active panes"""
    if is_active:
        return curses.color_pair(COLOR_FOOTER) | curses.A_BOLD
    else:
        return curses.color_pair(COLOR_FOOTER)

def get_status_color():
    """Get status line color"""
    return curses.color_pair(COLOR_STATUS)

def get_error_color():
    """Get error message color"""
    return curses.color_pair(COLOR_ERROR)

def get_boundary_color():
    """Get boundary color for pane separators"""
    return curses.color_pair(COLOR_BOUNDARY)

def get_color_capabilities():
    """Get information about terminal color capabilities"""
    info = {
        'colors': curses.COLORS if hasattr(curses, 'COLORS') else 8,
        'color_pairs': curses.COLOR_PAIRS if hasattr(curses, 'COLOR_PAIRS') else 64,
        'can_change_color': curses.can_change_color(),
    }
    return info

def get_rgb_color_info():
    """Get information about defined RGB colors"""
    return get_current_rgb_colors()

def get_available_color_schemes():
    """Get list of available color schemes"""
    return list(COLOR_SCHEMES.keys())

def get_current_color_scheme():
    """Get the current color scheme name"""
    return current_color_scheme

def set_color_scheme(scheme_name):
    """Set the color scheme (init_colors should be called separately)"""
    global current_color_scheme
    
    if scheme_name not in COLOR_SCHEMES:
        raise ValueError(f"Unknown color scheme: {scheme_name}. Available schemes: {list(COLOR_SCHEMES.keys())}")
    
    current_color_scheme = scheme_name
    return True

def toggle_color_scheme():
    """Toggle between dark and light color schemes"""
    global current_color_scheme
    new_scheme = 'light' if current_color_scheme == 'dark' else 'dark'
    current_color_scheme = new_scheme
    # Note: init_colors() should be called separately in the application
    return new_scheme

def print_current_color_scheme():
    """Print current color scheme information"""
    print(f"Current color scheme: {current_color_scheme}")
    
    # Get current scheme colors
    rgb_colors = get_current_rgb_colors()
    fallback_colors = get_current_fallback_colors()
    
    print(f"Available schemes: {', '.join(get_available_color_schemes())}")
    print(f"RGB colors defined: {len(rgb_colors)} colors")
    print(f"Fallback colors defined: {len(fallback_colors)} colors")
    
    # Show a few key colors as examples
    key_colors = ['DIRECTORY_FG', 'EXECUTABLE_FG', 'SELECTED_FG', 'REGULAR_FILE_FG']
    print(f"Key colors in {current_color_scheme} scheme:")
    for color_name in key_colors:
        if color_name in rgb_colors:
            rgb = rgb_colors[color_name]['rgb']
            print(f"  {color_name}: RGB{rgb}")

def print_all_color_schemes():
    """Print information about all available color schemes"""
    print("TFM Color Schemes:")
    print("=" * 40)
    
    for scheme_name in get_available_color_schemes():
        print(f"\n{scheme_name.upper()} SCHEME:")
        print("-" * 20)
        
        scheme_colors = COLOR_SCHEMES[scheme_name]
        key_colors = ['DIRECTORY_FG', 'EXECUTABLE_FG', 'SELECTED_FG', 'REGULAR_FILE_FG']
        
        for color_name in key_colors:
            if color_name in scheme_colors:
                rgb = scheme_colors[color_name]['rgb']
                print(f"  {color_name:15}: RGB{rgb}")
    
    print(f"\nCurrent active scheme: {current_color_scheme}")

def print_color_support_info():
    """Print information about terminal color support"""
    try:
        import curses
        # This will only work if curses has been initialized
        if hasattr(curses, 'COLORS'):
            colors = curses.COLORS
            pairs = curses.COLOR_PAIRS if hasattr(curses, 'COLOR_PAIRS') else 'Unknown'
            can_change = curses.can_change_color()
            
            print("Terminal Color Support:")
            print(f"  Colors available: {colors}")
            print(f"  Color pairs: {pairs}")
            print(f"  RGB support: {'Yes' if can_change else 'No'}")
            print(f"  Current scheme: {current_color_scheme}")
            
            # Check for default color support
            has_default_colors = hasattr(curses, 'assume_default_colors')
            print(f"  Default colors support: {'Yes' if has_default_colors else 'No'}")
            
            if can_change:
                print("  Status: Using RGB colors")
            else:
                print("  Status: Using fallback colors")
        else:
            print("Color support information not available (curses not initialized)")
    except Exception as e:
        print(f"Cannot determine color support: {e}")

def check_default_colors_support():
    """Check if terminal supports default color changes"""
    try:
        import curses
        return hasattr(curses, 'assume_default_colors')
    except ImportError:
        return False

def get_default_background_color():
    """Get the default background color for the current scheme"""
    return default_background_color

def get_default_foreground_color():
    """Get the default foreground color for the current scheme"""
    return default_foreground_color

def get_background_color_pair():
    """Get a color pair that can be used for background areas"""
    try:
        import curses
        # Try to return a color pair with the scheme's background
        if default_background_color is not None and default_foreground_color is not None:
            # Use color pair 63 as background pair (created in init_colors if needed)
            return curses.color_pair(63)
        else:
            # Fallback to normal colors
            return curses.color_pair(0)
    except:
        return 0

def apply_background_to_window(window):
    """Apply the color scheme background to a curses window"""
    try:
        import curses
        if default_background_color is not None:
            # Set the background character and color for the window
            bg_char = ' '  # Space character
            bg_attr = get_background_color_pair()
            window.bkgd(bg_char, bg_attr)
            return True
    except:
        pass
    return False

def define_rgb_color(color_num, red, green, blue):
    """
    Define a custom RGB color
    
    Args:
        color_num: Color number to define (usually 8-255)
        red: Red component (0-255)
        green: Green component (0-255) 
        blue: Blue component (0-255)
    
    Returns:
        True if successful, False if not supported
    """
    if not curses.can_change_color():
        return False
    
    try:
        # Convert 0-255 RGB to 0-1000 scale used by curses
        r = int((red / 255.0) * 1000)
        g = int((green / 255.0) * 1000)
        b = int((blue / 255.0) * 1000)
        
        curses.init_color(color_num, r, g, b)
        return True
    except curses.error:
        return False

def add_custom_rgb_color(name, color_num, rgb_tuple):
    """
    Add a new custom RGB color to the constants
    
    Args:
        name: Name for the color (e.g., 'MY_CUSTOM_COLOR')
        color_num: Color number to use (should be unique)
        rgb_tuple: (red, green, blue) tuple with values 0-255
    """
    RGB_COLORS[name] = {
        'color_num': color_num,
        'rgb': rgb_tuple
    }

def get_log_color(source):
    """Get appropriate color for log messages based on source"""
    if source == "STDERR":
        return curses.color_pair(COLOR_ERROR)  # Red for stderr
    elif source == "SYSTEM":
        return curses.color_pair(COLOR_LOG_SYSTEM)  # Light blue for system messages
    elif source == "STDOUT":
        return curses.color_pair(COLOR_LOG_STDOUT)  # Medium gray for stdout
    else:
        return curses.color_pair(COLOR_LOG_STDOUT)  # Default to stdout color

def get_line_number_color():
    """Get line number color for text viewer"""
    return curses.color_pair(COLOR_LINE_NUMBERS)

def get_syntax_color(token_type):
    """Get syntax highlighting color for a token type"""
    # Map pygments token types to our color pairs
    token_str = str(token_type)
    
    if 'Keyword' in token_str:
        return curses.color_pair(COLOR_SYNTAX_KEYWORD)
    elif 'String' in token_str or 'Literal.String' in token_str:
        return curses.color_pair(COLOR_SYNTAX_STRING)
    elif 'Comment' in token_str:
        return curses.color_pair(COLOR_SYNTAX_COMMENT)
    elif 'Number' in token_str or 'Literal.Number' in token_str:
        return curses.color_pair(COLOR_SYNTAX_NUMBER)
    elif 'Operator' in token_str or 'Punctuation' in token_str:
        return curses.color_pair(COLOR_SYNTAX_OPERATOR)
    elif 'Builtin' in token_str or 'Name.Builtin' in token_str:
        return curses.color_pair(COLOR_SYNTAX_BUILTIN)
    elif 'Name' in token_str:
        return curses.color_pair(COLOR_SYNTAX_NAME)
    else:
        # Default to regular text color
        return curses.color_pair(COLOR_REGULAR_FILE)

def get_search_color():
    """Get search interface color (same as status color)"""
    return curses.color_pair(COLOR_STATUS)

def get_search_match_color():
    """Get search match highlighting color"""
    return curses.color_pair(COLOR_SEARCH_MATCH)

def get_search_current_color():
    """Get current search match highlighting color"""
    return curses.color_pair(COLOR_SEARCH_CURRENT)