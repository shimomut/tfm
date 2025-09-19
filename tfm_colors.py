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

# Custom RGB color definitions (RGB values 0-255)
RGB_COLORS = {
    'HEADER_BG': {
        'color_num': 100,
        'rgb': (51, 63, 76),     # Dark blue-gray for file list headers
        'description': 'Dark blue-gray background for file list headers'
    },
    'FOOTER_BG': {
        'color_num': 104,
        'rgb': (51, 63, 76),     # Dark blue-gray for file list headers
        'description': 'Darker blue-gray background for file list footers'
    },
    'STATUS_BG': {
        'color_num': 105,
        'rgb': (51, 63, 76),     # Dark blue-gray for file list headers
        'description': 'Darkest blue-gray background for status bar'
    },
    'BOUNDARY_BG': {
        'color_num': 106,
        'rgb': (51, 63, 76),     # Dark blue-gray for file list headers
        'description': 'Medium dark blue-gray background for boundaries'
    },
    'DIRECTORY_FG': {
        'color_num': 101,
        'rgb': (0, 204, 204),    # Bright cyan for directories
        'description': 'Bright cyan for directory names'
    },
    'EXECUTABLE_FG': {
        'color_num': 102,
        'rgb': (51, 229, 51),    # Bright green for executables
        'description': 'Bright green for executable files'
    },
    'SELECTED_FG': {
        'color_num': 103,
        'rgb': (255, 229, 0),    # Bright yellow for selected items
        'description': 'Bright yellow for selected items'
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
    'SELECTED_FG': curses.COLOR_YELLOW
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
    
    # Initialize color pairs
    curses.init_pair(COLOR_DIRECTORIES, directory_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_EXECUTABLES, executable_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SELECTED, selected_fg, curses.COLOR_BLACK)
    curses.init_pair(COLOR_ERROR, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(COLOR_HEADER, curses.COLOR_WHITE, header_bg)
    curses.init_pair(COLOR_FOOTER, curses.COLOR_WHITE, footer_bg)
    curses.init_pair(COLOR_STATUS, curses.COLOR_WHITE, status_bg)
    curses.init_pair(COLOR_BOUNDARY, curses.COLOR_WHITE, boundary_bg)

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

def add_custom_rgb_color(name, color_num, rgb_tuple, description="Custom color"):
    """
    Add a new custom RGB color to the constants
    
    Args:
        name: Name for the color (e.g., 'MY_CUSTOM_COLOR')
        color_num: Color number to use (should be unique)
        rgb_tuple: (red, green, blue) tuple with values 0-255
        description: Description of the color
    """
    RGB_COLORS[name] = {
        'color_num': color_num,
        'rgb': rgb_tuple,
        'description': description
    }

def get_log_color(source):
    """Get appropriate color for log messages based on source"""
    if source == "STDERR":
        return curses.color_pair(COLOR_ERROR)  # Red for stderr
    elif source == "SYSTEM":
        return curses.color_pair(COLOR_SELECTED)  # Yellow for system messages
    else:
        return curses.A_NORMAL