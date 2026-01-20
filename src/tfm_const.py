#!/usr/bin/env python3
"""
TUI File Manager - Constants and Configuration

Note: Most key codes are now handled by TTK's KeyCode enum (ttk.input_event.KeyCode).
Standard keys like ENTER, TAB, ESCAPE, arrow keys, function keys, etc. should use
KeyCode values. Only terminal-specific key codes that aren't standardized in TTK
are defined here.
"""

# Version information
VERSION = "0.99"

# Application metadata
APP_NAME = "TUI File Manager"
APP_DESCRIPTION = "A terminal-based file manager"
GITHUB_URL = "https://github.com/shimomut/tfm"  # Update with actual repository URL

# Display constants
DEFAULT_LOG_HEIGHT_RATIO = 0.25  # Log pane takes 1/4 of screen
MIN_LOG_HEIGHT = 5
MAX_LOG_MESSAGES = 1000

# Terminal-specific key codes have been moved to TTK's curses backend
# Use KeyCode with ModifierKey.SHIFT for Shift+Arrow combinations instead

# File size formatting thresholds
SIZE_KB = 1024
SIZE_MB = 1024 * 1024
SIZE_GB = 1024 * 1024 * 1024

# Date/time formats
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
LOG_TIME_FORMAT = "%H:%M:%S"

# File list date format options
DATE_FORMAT_FULL = 'full'        # YYYY-MM-DD HH:mm:ss
DATE_FORMAT_SHORT = 'short'      # YY-MM-DD HH:mm (default)

# Pane layout constants
MIN_PANE_RATIO = 0.1  # Minimum left pane width (10%)
MAX_PANE_RATIO = 0.9  # Maximum left pane width (90%)
PANE_ADJUST_STEP = 0.05  # 5% adjustment per key press

# Vertical pane layout constants
MIN_LOG_HEIGHT_RATIO = 0.0   # Minimum log pane height (0% - can be hidden)
MAX_LOG_HEIGHT_RATIO = 0.9   # Maximum log pane height (60%)
LOG_HEIGHT_ADJUST_STEP = 0.05  # 5% adjustment per key press

# Isearch mode constants
SEARCH_KEY = ord('f')  # Key to enter isearch mode (F key)

# Text editor constants
DEFAULT_TEXT_EDITOR = 'vim'  # Default text editor to use
EDITOR_KEY = ord('e')  # Key to launch text editor (E key)

# File type detection constants for content search
# Known binary file extensions - immediately rejected from text search
BINARY_FILE_EXTENSIONS = {
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.tiff', '.tif', '.webp',
    '.psd', '.raw', '.cr2', '.nef', '.orf', '.sr2',
    # Archives
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar', '.dmg', '.iso',
    '.tgz', '.tbz2', '.txz',
    # Executables and libraries
    '.exe', '.dll', '.so', '.dylib', '.bin', '.app', '.deb', '.rpm',
    '.msi', '.pkg', '.apk',
    # Media
    '.mp3', '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4a', '.wav',
    '.flac', '.ogg', '.webm',
    # Documents (binary formats)
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods',
    # Fonts
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    # Database
    '.db', '.sqlite', '.sqlite3',
    # Python bytecode
    '.pyc', '.pyo', '.pyd',
    # Java
    '.class', '.jar', '.war', '.ear',
    # Object files
    '.o', '.obj', '.a', '.lib'
}

# Known text file extensions - immediately accepted for text search
TEXT_FILE_EXTENSIONS = {
    # Plain text and markup
    '.txt', '.md', '.rst', '.asciidoc', '.adoc',
    # Programming languages
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.cc', '.cxx',
    '.h', '.hpp', '.hh', '.hxx', '.cs', '.php', '.rb', '.go', '.rs', '.swift',
    '.kt', '.scala', '.clj', '.erl', '.ex', '.exs', '.hs', '.ml', '.fs', '.fsx',
    '.lua', '.pl', '.pm', '.r', '.m', '.mm',
    # Shell scripts
    '.sh', '.bash', '.zsh', '.fish', '.ksh', '.csh', '.tcsh',
    # Web
    '.html', '.htm', '.css', '.scss', '.sass', '.less', '.xml', '.svg',
    '.vue', '.svelte',
    # Data formats
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.config',
    '.properties', '.env',
    # SQL and query languages
    '.sql', '.graphql', '.gql',
    # Logs and data
    '.log', '.csv', '.tsv', '.psv',
    # Build and config files
    '.cmake', '.make', '.gradle', '.maven', '.sbt',
    # Version control and project files
    '.gitignore', '.gitattributes', '.dockerignore', '.editorconfig',
    '.eslintrc', '.prettierrc', '.babelrc',
    # Lock files
    '.lock',
    # Windows scripts
    '.ps1', '.psm1', '.psd1', '.bat', '.cmd',
    # Documentation
    '.tex', '.bib', '.man', '.1', '.2', '.3', '.4', '.5', '.6', '.7', '.8'
}

# Content inspection thresholds for unknown file types
TEXT_DETECTION_SAMPLE_SIZE = 8192  # Bytes to read for content inspection
TEXT_DETECTION_THRESHOLD = 0.85    # Minimum ratio of printable characters to consider text
