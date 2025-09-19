"""
Color definitions and initialization for TFM (Terminal File Manager)
"""
import curses

# Color pair constants
COLOR_DIRECTORIES = 1
COLOR_EXECUTABLES = 2
COLOR_SELECTED = 3
COLOR_ERROR = 4
COLOR_HEADER = 5        # File list headers (directory paths)
COLOR_FOOTER = 6        # File list footers (file counts)
COLOR_STATUS = 7        # Status bar
COLOR_BOUNDARY = 8      # Pane boundaries
COLOR_REGULAR_FILE = 9  # Regular files
COLOR_LOG_STDOUT = 10   # Stdout log messages
COLOR_LOG_SYSTEM = 11   # System log messages
COLOR_LINE_NUMBERS = 12 # Line numbers in text viewer
# Syntax highlighting colors
COLOR_SYNTAX_KEYWORD = 13    # Keywords (def, class, if, etc.)
COLOR_SYNTAX_STRING = 14     # String literals
COLOR_SYNTAX_COMMENT = 15    # Comments
COLOR_SYNTAX_NUMBER = 16     # Numbers
COLOR_SYNTAX_OPERATOR = 17   # Operators (+, -, =, etc.)
COLOR_SYNTAX_BUILTIN = 18    # Built-in functions/types
COLOR_SYNTAX_NAME = 19       # Variable/function names

# Custom RGB color definitions (RGB values 0-255)
RGB_COLORS = {
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
    'SELECTED_FG': {
        'color_num': 103,
        'rgb': (255, 229, 0)    # Bright yellow for selected items
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
    }
}

# Fallback color numbers for terminals without RGB support
FALLBACK_COLORS = {
    'HEADER_BG': 23,         # Blue for headers
    'FOOTER_BG': 17,         # Dark blue for footers  
    'STATUS_BG': 18,         # Darker blue for status
    'BOUNDARY_BG': 19,       # Medium blue for boundaries
    'DIRECTORY_FG': curses.COLOR_CYAN,
    'EXECUTABLE_FG': curses.COLOR_GREEN,
    'SELECTED_FG': curses.COLOR_YELLOW,
    'REGULAR_FILE_FG': curses.COLOR_WHITE,
    'LOG_STDOUT_FG': curses.COLOR_WHITE,
    'LOG_SYSTEM_FG': curses.COLOR_BLUE,
    'LINE_NUMBERS_FG': curses.COLOR_WHITE,
    # Syntax highlighting fallback colors
    'SYNTAX_KEYWORD_FG': curses.COLOR_YELLOW,
    'SYNTAX_STRING_FG': curses.COLOR_GREEN,
    'SYNTAX_COMMENT_FG': curses.COLOR_BLUE,
    'SYNTAX_NUMBER_FG': curses.COLOR_CYAN,
    'SYNTAX_OPERATOR_FG': curses.COLOR_MAGENTA,
    'SYNTAX_BUILTIN_FG': curses.COLOR_CYAN,
    'SYNTAX_NAME_FG': curses.COLOR_WHITE
}

def init_colors():
    """Initialize all color pairs for the application"""
    curses.start_color()
    
    # Check if terminal supports RGB colors
    can_change_color = curses.can_change_color()
    
    # Initialize custom RGB colors if supported
    if can_change_color:
        rgb_success = True
        try:
            # Define all custom RGB colors from constants
            for color_name, color_def in RGB_COLORS.items():
                color_num = color_def['color_num']
                r, g, b = color_def['rgb']
                
                # Convert RGB (0-255) to curses scale (0-1000)
                r_curses = int((r / 255.0) * 1000)
                g_curses = int((g / 255.0) * 1000)
                b_curses = int((b / 255.0) * 1000)
                
                curses.init_color(color_num, r_curses, g_curses, b_curses)
            
            # Use custom RGB colors
            header_bg = RGB_COLORS['HEADER_BG']['color_num']
            footer_bg = RGB_COLORS['FOOTER_BG']['color_num']
            status_bg = RGB_COLORS['STATUS_BG']['color_num']
            boundary_bg = RGB_COLORS['BOUNDARY_BG']['color_num']
            directory_fg = RGB_COLORS['DIRECTORY_FG']['color_num']
            executable_fg = RGB_COLORS['EXECUTABLE_FG']['color_num']
            selected_fg = RGB_COLORS['SELECTED_FG']['color_num']
            regular_file_fg = RGB_COLORS['REGULAR_FILE_FG']['color_num']
            log_stdout_fg = RGB_COLORS['LOG_STDOUT_FG']['color_num']
            log_system_fg = RGB_COLORS['LOG_SYSTEM_FG']['color_num']
            line_numbers_fg = RGB_COLORS['LINE_NUMBERS_FG']['color_num']
            # Syntax highlighting colors
            syntax_keyword_fg = RGB_COLORS['SYNTAX_KEYWORD_FG']['color_num']
            syntax_string_fg = RGB_COLORS['SYNTAX_STRING_FG']['color_num']
            syntax_comment_fg = RGB_COLORS['SYNTAX_COMMENT_FG']['color_num']
            syntax_number_fg = RGB_COLORS['SYNTAX_NUMBER_FG']['color_num']
            syntax_operator_fg = RGB_COLORS['SYNTAX_OPERATOR_FG']['color_num']
            syntax_builtin_fg = RGB_COLORS['SYNTAX_BUILTIN_FG']['color_num']
            syntax_name_fg = RGB_COLORS['SYNTAX_NAME_FG']['color_num']
            
        except curses.error:
            rgb_success = False
    
    # Use fallback colors if RGB not supported or failed
    if not can_change_color or not rgb_success:
        header_bg = FALLBACK_COLORS['HEADER_BG']
        footer_bg = FALLBACK_COLORS['FOOTER_BG']
        status_bg = FALLBACK_COLORS['STATUS_BG']
        boundary_bg = FALLBACK_COLORS['BOUNDARY_BG']
        directory_fg = FALLBACK_COLORS['DIRECTORY_FG']
        executable_fg = FALLBACK_COLORS['EXECUTABLE_FG']
        selected_fg = FALLBACK_COLORS['SELECTED_FG']
        regular_file_fg = FALLBACK_COLORS['REGULAR_FILE_FG']
        log_stdout_fg = FALLBACK_COLORS['LOG_STDOUT_FG']
        log_system_fg = FALLBACK_COLORS['LOG_SYSTEM_FG']
        line_numbers_fg = FALLBACK_COLORS['LINE_NUMBERS_FG']
        # Syntax highlighting fallback colors
        syntax_keyword_fg = FALLBACK_COLORS['SYNTAX_KEYWORD_FG']
        syntax_string_fg = FALLBACK_COLORS['SYNTAX_STRING_FG']
        syntax_comment_fg = FALLBACK_COLORS['SYNTAX_COMMENT_FG']
        syntax_number_fg = FALLBACK_COLORS['SYNTAX_NUMBER_FG']
        syntax_operator_fg = FALLBACK_COLORS['SYNTAX_OPERATOR_FG']
        syntax_builtin_fg = FALLBACK_COLORS['SYNTAX_BUILTIN_FG']
        syntax_name_fg = FALLBACK_COLORS['SYNTAX_NAME_FG']
    
    # Initialize color pairs
    curses.init_pair(COLOR_DIRECTORIES, directory_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_EXECUTABLES, executable_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SELECTED, selected_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_ERROR, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(COLOR_HEADER, curses.COLOR_WHITE, header_bg)
    curses.init_pair(COLOR_FOOTER, curses.COLOR_WHITE, footer_bg)
    curses.init_pair(COLOR_STATUS, curses.COLOR_WHITE, status_bg)
    curses.init_pair(COLOR_BOUNDARY, curses.COLOR_WHITE, boundary_bg)
    curses.init_pair(COLOR_REGULAR_FILE, regular_file_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_LOG_STDOUT, log_stdout_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_LOG_SYSTEM, log_system_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_LINE_NUMBERS, line_numbers_fg, curses.COLOR_BLACK)
    # Syntax highlighting color pairs
    curses.init_pair(COLOR_SYNTAX_KEYWORD, syntax_keyword_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SYNTAX_STRING, syntax_string_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SYNTAX_COMMENT, syntax_comment_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SYNTAX_NUMBER, syntax_number_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SYNTAX_OPERATOR, syntax_operator_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SYNTAX_BUILTIN, syntax_builtin_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SYNTAX_NAME, syntax_name_fg, curses.COLOR_BLACK)

def get_file_color(is_dir, is_executable, is_selected, is_active):
    """Get the appropriate color for a file based on its properties"""
    if is_dir:
        base_color = curses.color_pair(COLOR_DIRECTORIES) | curses.A_BOLD
    elif is_executable:
        base_color = curses.color_pair(COLOR_EXECUTABLES)
    else:
        # Regular files now use custom RGB color instead of A_NORMAL
        base_color = curses.color_pair(COLOR_REGULAR_FILE)
    
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
    return RGB_COLORS

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