#!/usr/bin/env python3
"""
TFM User Configuration

This file contains your personal TFM configuration.
You can modify any of these settings to customize TFM behavior.
"""

import platform
import sys

# Import tfm_tool function and tfm_python variable for external program configuration
from tfm_external_programs import tfm_tool, tfm_python

# Import backend detector for runtime backend detection
from tfm_backend_detector import is_desktop_mode

class Config:
    """User configuration for TFM"""

    # --- Desktop (GUI) mode fonts (ignored in TUI mode) ----------------------
    # UI_FONT_NAME   : proportional default face (file names, labels,
    #                  dialogs, markdown prose).
    # MONO_FONT_NAME : monospaced face for aligned content (size/date
    #                  columns, viewer, diffs); also grounds the layout
    #                  grid, so it must be monospaced.
    # FONT_SIZE      : point size applied to BOTH faces.
    # Missing glyphs use the OS's native font substitution.
    #
    # None = the OS system default face -- already a matched pair per platform:
    #   macOS   -> San Francisco + SF Mono
    #   Windows -> Segoe UI + Consolas
    #
    # To use named fonts, uncomment ONE block below (it runs after the defaults
    # and overrides them). `sys` is already imported at the top of this file.

    # Default: the system pair on every platform (recommended).
    UI_FONT_NAME = None
    MONO_FONT_NAME = None

    # Example -- a sans-serif pairing:
    # if sys.platform == 'darwin':        # macOS
    #     UI_FONT_NAME = 'Helvetica Neue'
    #     MONO_FONT_NAME = 'Menlo'
    # elif sys.platform == 'win32':       # Windows
    #     UI_FONT_NAME = 'Segoe UI'
    #     MONO_FONT_NAME = 'Consolas'
    # else:                               # other
    #     UI_FONT_NAME = None
    #     MONO_FONT_NAME = None

    # Example -- a serif pairing (serif UI + serif/slab monospace):
    # if sys.platform == 'darwin':        # macOS
    #     UI_FONT_NAME = 'Georgia'
    #     MONO_FONT_NAME = 'PT Mono'
    # elif sys.platform == 'win32':       # Windows
    #     UI_FONT_NAME = 'Georgia'
    #     MONO_FONT_NAME = 'Courier New'
    # else:                               # other
    #     UI_FONT_NAME = None
    #     MONO_FONT_NAME = None

    FONT_SIZE = 12  # point size for both faces (8-72)

    # Display settings
    SHOW_HIDDEN_FILES = False
    DEFAULT_LEFT_PANE_RATIO = 0.5  # 0.1 to 0.9
    DEFAULT_LOG_HEIGHT_RATIO = 0.25  # 0.1 to 0.5
    DATE_FORMAT = 'short'  # 'short' (YY-MM-DD HH:mm) or 'full' (YYYY-MM-DD HH:mm:ss)
    
    # Sorting settings
    DEFAULT_SORT_MODE = 'name'  # 'name', 'size', 'date'
    DEFAULT_SORT_REVERSE = False
    
    # -----------------------------------------------------------------------
    # Custom themes (optional)
    # -----------------------------------------------------------------------
    # Register your own named themes here. Each one is added to the theme picker
    # (View > Theme) and the T-key cycle alongside the built-ins — Dark+, Monokai,
    # Dracula, Nord, Solarized, Gruvbox Dark, Light+, Solarized Light — so you can
    # switch between them at run time. TFM starts on Dark+ and remembers whichever
    # theme you last switched to across restarts.
    #
    # THEMES maps a display name to a dict of color overrides. A theme inherits a
    # base and overrides only what differs: set 'base' to any built-in (or another
    # theme you defined above) to inherit it; with no 'base' it builds on the theme
    # of the same name if one exists (so {'Dark+': {...}} tweaks the built-in), else
    # on 'Dark+'. A name matching an existing theme replaces it in place.
    #
    # Every available key (all optional). Colors are (R, G, B) tuples, 0-255:
    #
    #   'base':          'Dark+'          # theme to inherit (see above for default)
    #   # --- base palette ---
    #   'background':    (30, 30, 30)     # content surface / editor background
    #   'foreground':    (212, 212, 212)  # primary text
    #   'muted':         (157, 157, 157)  # secondary text, dividers
    #   'accent':        (0, 122, 204)    # focus ring, selection fill, default bars
    #   'accent2':       (78, 201, 176)   # secondary accent (i-search base, recipes)
    #   'surface':       (48, 48, 52)     # raised panels (pane header / popup)
    #   'selection':     (10, 105, 178)   # active selection fill
    #   # --- chrome bars (a solid color for the whole bar) ---
    #   'status':        (0, 122, 204)    # bottom status bar (also the viewers')
    #   'footer':        (0, 122, 204)    # per-pane info bar
    #   # --- file panes: per-type name colors (a sub-dict, like 'syntax';
    #   #     override only the types you name) ---
    #   'file_types': {'directory': (204, 204, 120),  # dirs  (default: soft yellow)
    #                  'file':      (212, 212, 212),  # files (default: foreground)
    #                  'link':      (86, 194, 214)}   # symlinks (default: cyan)
    #   #   ('directory' may also be given as a flat top-level key — shorthand for
    #   #    file_types['directory']. A symlink is colored as a link even when it
    #   #    points at a directory.)
    #   # --- file pane cursor cue (a sub-dict; the row outline / [ ] bracket,
    #   #     distinct from the selection fill) ---
    #   'cursor': {'active':   (231, 76, 76),  # focused pane (default: red)
    #              'inactive': (140, 92, 94)}  # blurred pane (default: muted red)
    #   # --- incremental search ---
    #   'isearch_match': (78, 201, 176)   # match-highlight base (default: accent2)
    #   # --- text / diff viewer syntax colors (override only the tokens you name) ---
    #   'syntax': {'keyword': (86, 156, 214), 'string': (206, 145, 120),
    #              'comment': (106, 153, 85), 'number': (181, 206, 168),
    #              'operator': (212, 212, 212), 'builtin': (78, 201, 176),
    #              'name': (156, 220, 254)}
    #   # --- recommended post-processing effect (GUI backend only) ---
    #   #   A full-screen CRT / phosphor "look" composited over the rendered
    #   #   frame. TFM turns it on when this theme becomes active and off when you
    #   #   switch away. Only the GUI backend (`tfm.py --backend gui`) renders it;
    #   #   a terminal has no pixels to filter and silently ignores it.
    #   #     'post_effect': 'crt'       # preset: glow + bloom + scanlines + vignette + roll
    #   #     'post_effect': {'bloom': 0.3, 'vignette': 0.15, 'glow': 0.22,
    #   #                     'scanline': 0.15, 'roll': 0.1}  # custom (override any)
    #   # --- background behind the UI (GUI backend only) ---
    #   #   One background of two kinds (else the plain theme color). On/off with the
    #   #   theme, like post_effect; a terminal has no pixels and ignores it. NOTE the
    #   #   'background' key above is the base *color* — these choose the content:
    #   #   * animation — a slow moving scene drawn in this theme's own colors
    #   #     (foreground line, background backdrop) so it stays on-palette:
    #   #       'starfield'     stars streaming toward you, fading in with depth
    #   #       'rain'          falling streaks with fading tails
    #   #       'constellation' drifting nodes linked to their near neighbours
    #   #       'grid'          flying through a wireframe corridor, the camera
    #   #                       slowly drifting and turning as it goes
    #   #     Written as a bare type, or a dict to retune speed / line opacity:
    #   #       'animation': 'starfield'                     # the tuned default
    #   #       'animation': {'type': 'rain', 'speed': 1.0, 'opacity': 0.8}
    #   #     ('cube', a spinning wireframe, also works — it is the UI toolkit's
    #   #      own reference scene rather than one of TFM's.)
    #   #   * wallpaper — a single image scaled to fill the window:
    #   #       'wallpaper': '~/Pictures/bg.png'
    #   #       'wallpaper': {'image': '~/bg.png', 'fit': 'fit', 'opacity': 0.8}
    #   #       fit: 'fill' (cover, default) | 'fit' (contain) | 'stretch' | 'center'
    #   # --- surface opacity (GUI backend only) ---
    #   #   How opaque the UI's pane/row backgrounds are (0..1); below 1 the
    #   #   background behind them shows through. A single per-theme value, separate
    #   #   from the background so it applies to any kind. 1 = fully opaque UI.
    #   #     'opacity': 0.6
    #
    # Example:
    #
    # THEMES = {
    #     'Ocean': {                       # builds on Dark+
    #         'accent': (38, 139, 210),
    #         'file_types': {'directory': (120, 200, 220), 'link': (90, 200, 180)},
    #         'syntax': {'keyword': (0, 175, 215)},
    #     },
    #     'Paper': {                       # a light theme, from a light base
    #         'base': 'Light+',
    #         'file_types': {'directory': (150, 110, 0)},
    #     },
    # }
    THEMES = {
        # Phosphor: a monochrome phosphor-green CRT terminal — every color is a
        # shade of green on a near-black screen. A ready-made example of a full
        # custom theme; select it from View > Theme or with the T key. On the GUI
        # backend the 'post_effect' below adds a real CRT glow over the green.
        'Phosphor': {
            'post_effect': 'crt',            # CRT glow/bloom/scanlines (GUI backend)
            'animation': 'rain',             # falling phosphor streaks (GUI backend)
            'opacity': 0.6,                  # chrome opacity; < 1 lets the rain show through
            'background': (4, 15, 7),        # dark CRT green-black
            'foreground': (51, 245, 121),    # phosphor green
            'muted':      (33, 138, 74),     # dim green (secondary text / dividers)
            'accent':     (60, 235, 122),    # focus ring / selection accent
            'accent2':    (124, 255, 168),   # pale mint (i-search match base)
            'surface':    (11, 38, 20),      # raised panels (header / popup)
            'selection':  (24, 105, 54),     # active selection fill
            'status':     (9, 30, 16),       # status bar (dark green panel)
            'footer':     (9, 30, 16),       # per-pane info bar
            'file_types': {
                'directory': (150, 255, 150),  # directories (brightest green)
                'link':      (124, 255, 168),  # symlinks (pale mint)
            },
            'cursor': {                        # keep the cue on-palette, not red
                'active':   (180, 255, 180),   # bright green frame (focused pane)
                'inactive': (60, 150, 90),     # dim green frame (blurred pane)
            },
            'syntax': {
                'keyword':  (130, 255, 150),
                'string':   (90, 220, 120),
                'comment':  (36, 140, 78),
                'number':   (150, 255, 130),
                'operator': (70, 210, 110),
                'builtin':  (150, 255, 170),
                'name':     (60, 235, 120),
            },
        },
    }

    # Behavior settings
    CONFIRM_DELETE = True   # Show confirmation dialog before deleting files/directories
    CONFIRM_QUIT = True     # Show confirmation dialog before quitting TFM
    CONFIRM_COPY = True     # Show confirmation dialog before copying files/directories
    CONFIRM_MOVE = True     # Show confirmation dialog before moving files/directories
    CONFIRM_DUPLICATE = True  # Show confirmation dialog before duplicating files/directories
    CONFIRM_EXTRACT_ARCHIVE = True  # Show confirmation dialog before extracting archives
    CONFIRM_ARCHIVE_CREATE = True   # Show confirmation dialog before creating archives
    
    # Key bindings - customize your shortcuts
    # Each action can have multiple keys assigned to it
    # 
    # Supported formats:
    # 1. Simple format: 'action': ['key1', 'key2']
    #    - Works regardless of selection status
    #    - Keys can be characters ('a', 'Q') or special key names ('HOME', 'END')
    # 
    # 2. Extended format: 'action': {'keys': ['key1', 'key2'], 'selection': 'any|required|none'}
    #    - 'any': works regardless of selection status (default)
    #    - 'required': only works when at least one item is explicitly selected
    #    - 'none': only works when no items are explicitly selected
    #
    # Special key names (use these strings in the keys list):
    #   'HOME', 'END', 'PPAGE', 'NPAGE', 'UP', 'DOWN',
    #   'LEFT', 'RIGHT', 'BACKSPACE', 'DELETE', 'INSERT',
    #   'F1' through 'F12'
    #
    KEY_BINDINGS = {
        # === Application Control ===
        'quit': ['Q'],                         # Exit TFM application
        'help': ['?'],                         # Show help dialog with all key bindings
        'redraw': ['F5'],                      # Additional redraw trigger (Ctrl-L is always hardcoded)
        
        # === Navigation ===
        'cursor_up': ['UP'],                   # Move cursor up one item
        'cursor_down': ['DOWN'],               # Move cursor down one item
        'page_up': ['PAGE_UP'],                # Move cursor up one page
        'page_down': ['PAGE_DOWN'],            # Move cursor down one page
        'open_item': ['ENTER'],                # Open file/directory or enter directory
        'open_with_os': ['Command-ENTER'],     # Open file(s) with OS default application
        'reveal_in_os': ['Alt-ENTER'],         # Reveal focused file in OS file manager
        'go_parent': ['BACKSPACE'],            # Go to parent directory
        'switch_pane': ['TAB'],                # Switch between left and right panes
        'nav_left': ['LEFT'],                  # Left pane: go to parent, Right pane: switch to left pane
        'nav_right': ['RIGHT'],                # Right pane: go to parent, Left pane: switch to right pane
        
        # === File Selection ===
        'select_file': ['SPACE'],              # Toggle selection of current file
        'select_file_up': ['Shift-SPACE'],     # Toggle selection and move up
        'select_all': ['HOME'],                # Select all items (Home key)
        'unselect_all': ['END'],               # Unselect all items (End key)
        'select_all_files': ['A'],             # Toggle selection of all files in current pane
        'select_all_items': ['Shift-A'],       # Toggle selection of all items (files + dirs)
        
        # === Clipboard (copy names/paths to the system clipboard) ===
        'copy_names': ['Command-Shift-C'],     # Copy selected/focused file name(s) to clipboard
        'copy_paths': ['Command-Shift-P'],     # Copy selected/focused full path(s) to clipboard

        # === File Operations ===
        'copy_files': {'keys': ['C'], 'selection': 'required'},  # Copy selected files to other pane
        'move_files': {'keys': ['M'], 'selection': 'required'},  # Move selected files to other pane
        'delete_files': {'keys': ['K', 'DELETE'], 'selection': 'required'}, # Delete selected files/directories
        'rename_file': ['R'],                  # Rename selected file/directory
        'create_file': ['Shift-E'],            # Create new file (prompts for filename)
        'create_directory': {'keys': ['M'], 'selection': 'none'},  # Create new directory (only when no files selected)
        
        # === File Viewing & Editing ===
        'view_file': ['V'],                    # View file using configured viewer
        'edit_file': ['E'],                    # Edit selected file with configured text editor
        'file_details': ['I'],                 # Show detailed file information dialog
        
        # === File Comparison ===
        'diff_files': ['EQUAL'],               # Compare two selected files side-by-side
        'diff_directories': ['Shift-EQUAL'],   # Compare directories recursively
        
        # === Archive Operations ===
        'create_archive': {'keys': ['P'], 'selection': 'required'}, # Create archive from selected files
        'extract_archive': ['U'],              # Extract selected archive file
        
        # === Search & Filter ===
        'search': ['F'],                       # Enter incremental search mode (isearch)
        'search_dialog': ['Shift-F'],          # Show filename search dialog
        'search_content': ['Shift-G'],         # Show content search dialog (grep)
        'filter': [';'],                       # Enter filter mode to show only matching files
        'clear_filter': [':'],                 # Clear current file filter
        
        # === Sorting ===
        'sort_menu': ['S'],                    # Show sort options menu
        'quick_sort_name': ['1'],              # Quick sort by filename
        'quick_sort_ext': ['2'],               # Quick sort by file extension
        'quick_sort_size': ['3'],              # Quick sort by file size
        'quick_sort_date': ['4'],              # Quick sort by modification date
        
        # === Directory Navigation ===
        'favorites': ['J'],                    # Show favorite directories dialog
        'jump_to_path': ['Shift-J'],           # Jump to path
        'history': ['H'],                      # Show history for current pane
        'drives_dialog': ['D'],                # Show drives/volumes dialog
        
        # === Pane Management ===
        'sync_current_to_other': ['O'],        # Sync current pane directory to other pane
        'sync_other_to_current': ['Shift-O'],  # Sync other pane directory to current pane
        'compare_selection': ['W'],            # Show file and directory comparison options
        'adjust_pane_left': ['['],             # Make left pane smaller (move boundary left)
        'adjust_pane_right': [']'],            # Make left pane larger (move boundary right)
        'reset_pane_boundary': ['-'],          # Reset pane split to 50% | 50%
        
        # === Log Pane Control ===
        'adjust_log_up': ['{'],                # Make log pane larger (Shift+[)
        'adjust_log_down': ['}'],              # Make log pane smaller (Shift+])
        'reset_log_height': ['_'],             # Reset log pane height to default (Shift+-)
        'scroll_log_up': ['Shift-UP'],         # Scroll log pane up one line
        'scroll_log_down': ['Shift-DOWN'],     # Scroll log pane down one line
        'scroll_log_page_up': ['Shift-LEFT'],  # Scroll log pane up one page (to older messages)
        'scroll_log_page_down': ['Shift-RIGHT'], # Scroll log pane down one page (to newer messages)
        
        # === Text / Diff Viewer ===
        # Viewer-only actions. 'search' (F, above) opens incremental search inside
        # the viewers too. 'toggle_wrap' intentionally shares 'W' with
        # 'compare_selection': they never apply in the same context (file list vs.
        # open viewer), and each context matches its own action by name via
        # KeyBindings.is_action_for_event, so the shared key is unambiguous.
        'toggle_wrap': ['W'],                  # Text viewer: toggle line wrapping
        # 'M' likewise shares with 'move_files' / 'create_directory' (file list
        # only); in an open viewer it toggles the raw text view and the file
        # type's rich renderer (Markdown for *.md), matched by name in-context.
        'toggle_view_mode': ['M'],             # Text viewer: toggle rendered (Markdown) / raw text

        # === Display & Appearance ===
        'toggle_hidden': ['.'],                # Toggle visibility of hidden files (dotfiles)
        'toggle_color_scheme': ['T'],          # Switch between dark and light color schemes
        'toggle_fallback_colors': ['Shift-T'], # Toggle fallback color mode for compatibility
        'view_options': ['Z'],                 # Show view options menu
        'settings_menu': ['Shift-Z'],          # Show settings and configuration menu
        
        # === External Programs ===
        'programs': ['X'],                     # Show external programs menu
        'subshell': ['Shift-X'],               # Enter subshell (command line) mode

        # === Configuration ===
        # Unbound by default (reachable via the Tools menu). Assign a key here to
        # open/reload this file without leaving TFM, e.g. 'edit_config': ['Y'].
        'edit_config': [],                     # Edit this config.py in TEXT_EDITOR, then reload
        'reload_config': [],                   # Re-read this config.py and apply live
    }

    # Windows has no Command key, and Alt-Enter is the platform fullscreen-toggle
    # convention — so the Mac-centric defaults above are unreachable there. Remap
    # them to Ctrl equivalents on Windows.
    if sys.platform == 'win32':
        KEY_BINDINGS['open_with_os'] = ['Ctrl-ENTER']    # Open file(s) with OS default application
        KEY_BINDINGS['reveal_in_os'] = ['Ctrl-Shift-E']  # Reveal focused file in Explorer
        KEY_BINDINGS['copy_names'] = ['Ctrl-Shift-C']    # Copy selected/focused file name(s) to clipboard
        KEY_BINDINGS['copy_paths'] = ['Ctrl-Shift-P']    # Copy selected/focused full path(s) to clipboard


    # Favorite directories - customize your frequently used directories
    # Each entry should have 'name' and 'path' keys
    FAVORITE_DIRECTORIES = [
        {'name': 'Home', 'path': '~'},
        {'name': 'Documents', 'path': '~/Documents'},
        {'name': 'Downloads', 'path': '~/Downloads'},
        {'name': 'Desktop', 'path': '~/Desktop'},
        {'name': 'Projects', 'path': '~/Projects'},
        {'name': 'Root', 'path': '/'},
        {'name': 'Temp', 'path': '/tmp'},
        {'name': 'Config', 'path': '~/.config'},
        # Add your own favorites here:
        # {'name': 'Work', 'path': '/path/to/work'},
        # {'name': 'Scripts', 'path': '~/bin'},
    ]
    
    # Performance settings
    MAX_LOG_MESSAGES = 1000

    # History settings
    MAX_HISTORY_ENTRIES = 100  # Maximum number of history entries to keep
    
    # Progress animation settings
    PROGRESS_ANIMATION_PATTERN = 'spinner'  # 'spinner', 'dots', 'progress', 'bounce', 'pulse', 'wave', 'clock', 'arrow'
    PROGRESS_ANIMATION_SPEED = 0.2  # Animation frame update interval in seconds
    
    # File display settings
    SEPARATE_EXTENSIONS = True  # Show file extensions separately from basenames
    MAX_EXTENSION_LENGTH = 5    # Maximum extension length to show separately
    
    # Text editor settings
    # Supports both string and list formats:
    # - String format: 'vim' (single command, no arguments)
    # - List format: ['code', '--wait'] (command with arguments)
    # Automatically set based on actual running backend mode:
    # - Terminal mode (curses): vim
    # - Desktop mode (coregraphics): code (VS Code)
    TEXT_EDITOR = 'code' if is_desktop_mode() else 'vim'
    
    # Text diff tool settings
    # Tool invoked when pressing 'E' (edit_file) key in DiffViewer or DirectoryDiffViewer
    # Supports both string and list formats:
    # - String format: 'vimdiff' (single command, no arguments)
    # - List format: ['code', '--diff'] (command with arguments)
    # Automatically set based on actual running backend mode:
    # - Terminal mode (curses): vimdiff (string format example)
    # - Desktop mode (coregraphics): code --diff (list format example)
    TEXT_DIFF = ['code', '--diff'] if is_desktop_mode() else 'vimdiff'
    
    # S3 settings
    S3_CACHE_TTL = 60  # S3 cache TTL in seconds (default: 60 seconds)
    
    # SSH/SFTP cache settings
    SSH_CACHE_TTL = 30        # SSH cache TTL in seconds for successful results (default: 30 seconds)
    SSH_CACHE_ERROR_TTL = 300  # SSH cache TTL in seconds for cached errors (default: 300 seconds / 5 minutes)
    
    # Archive cache settings
    ARCHIVE_CACHE_MAX_OPEN = 5   # Maximum number of archives to keep open simultaneously
    ARCHIVE_CACHE_TTL = 300       # Archive cache TTL in seconds (default: 300 seconds / 5 minutes)
    
    # File monitoring settings
    FILE_MONITORING_ENABLED = True                      # Enable/disable automatic file list reloading
    FILE_MONITORING_COALESCE_DELAY_MS = 200            # Event coalescing window in milliseconds
    FILE_MONITORING_MAX_RELOADS_PER_SECOND = 5         # Maximum reloads per second (rate limiting)
    FILE_MONITORING_FALLBACK_POLL_INTERVAL_S = 5       # Polling interval for fallback mode (seconds)
    
    # File extension associations
    # Maps file patterns to programs for different actions (open, view, edit)
    # 
    # Compact Format Features:
    # 1. Multiple patterns in one entry: ['*.jpg', '*.jpeg', '*.png']
    # 2. Combined actions: 'open|view' assigns same command to both actions
    # 3. Commands: List ['open', '-a', 'Preview'] or string 'open -a Preview'
    # 4. None: Action not available
    #
    # Format:
    # {
    #     'pattern': '*.pdf' or ['*.jpg', '*.png'],  # Single or multiple fnmatch patterns
    #     'open|view': ['command'],  # Same command for open and view
    #     'edit': ['command']        # Different command for edit
    # }
    FILE_ASSOCIATIONS = [
        # PDF files
        {
            'pattern': '*.pdf',
            'open|view': ['open', '-a', 'Preview'],
            'edit': None,
        },
        # Image files
        {
            'pattern': ['*.jpg', '*.jpeg', '*.png', '*.gif'],
            'open|view': ['open', '-a', 'Preview'],
            'edit': ['open', '-a', 'GIMP'],
        },
        # Video files
        {
            'pattern': ['*.mp4', '*.mov'],
            'open|view': ['open', '-a', 'QuickTime Player'],
            'edit': None,
        },
        # Audio files
        {
            'pattern': ['*.mp3', '*.wav'],
            'open': ['open', '-a', 'Music'],
            'edit': None,
        },
        # Microsoft Word documents
        {
            'pattern': ['*.doc', '*.docx'],
            'open|view|edit': ['open', '-a', 'Microsoft Word'],
        },
        # Microsoft Excel spreadsheets
        {
            'pattern': ['*.xls', '*.xlsx'],
            'open|view|edit': ['open', '-a', 'Microsoft Excel'],
        },
        # Microsoft PowerPoint presentations
        {
            'pattern': ['*.ppt', '*.pptx'],
            'open|view|edit': ['open', '-a', 'Microsoft PowerPoint'],
        },
        # Add your own file associations here:
        # {
        #     'pattern': ['*.ext1', '*.ext2'],
        #     'open|view': ['command', 'args'],
        #     'edit': ['command', 'args']
        # },
    ]
    
    # External programs - each item has "name", "command", and optional "options" fields
    # The "command" field is a list for safe subprocess execution
    # Relative paths in the first element are resolved relative to the TFM root directory (where tfm.py is located)
    # Use tfm_tool('tool_name') to search for tools in:
    #   1. ~/.tfm/tools/ (user-specific tools, highest priority)
    #   2. {tfm.py directory}/tools/ (system tools, fallback)
    # The "options" field is a dictionary with program-specific options:
    #   - auto_return: if True, automatically returns to TFM without waiting for user input
    PROGRAMS = [
        {'name': 'Compare Files (BeyondCompare)', 'command': [tfm_python, tfm_tool('bcompare_files.py')], 'options': {'auto_return': True}},
        {'name': 'Compare Directories (BeyondCompare)', 'command': [tfm_python, tfm_tool('bcompare_dirs.py')], 'options': {'auto_return': True}},
        {'name': 'Open in VSCode', 'command': [tfm_python, tfm_tool('vscode.py')], 'options': {'auto_return': True}},
        {'name': 'Open in Kiro', 'command': [tfm_python, tfm_tool('kiro.py')], 'options': {'auto_return': True}},

        # Add your own programs here:
        # {'name': 'My Custom Tool', 'command': [tfm_python, tfm_tool('my_custom_tool.py')], 'options': {'auto_return': True}},
        # {'name': 'My Script (direct path)', 'command': [tfm_python, '/path/to/script.py']},
        # {'name': 'Python REPL', 'command': ['python3']},
        # {'name': 'Quick Command', 'command': ['ls', '-la'], 'options': {'auto_return': True}},
    ]