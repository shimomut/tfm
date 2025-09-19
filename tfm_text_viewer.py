#!/usr/bin/env python3
"""
TFM Text File Viewer with Syntax Highlighting

A text file viewer component for TFM that supports syntax highlighting
for popular file formats using pygments (optional dependency).
"""

import curses
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import re

# Try to import pygments for syntax highlighting
try:
    from pygments import lex
    from pygments.lexers import get_lexer_for_filename, get_lexer_by_name, TextLexer
    from pygments.token import Token
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

from tfm_colors import *
from tfm_const import *


class TextViewer:
    """Text file viewer with syntax highlighting support"""
    
    def __init__(self, stdscr, file_path: Path):
        self.stdscr = stdscr
        self.file_path = file_path
        self.lines = []  # List of strings (plain text lines)
        self.highlighted_lines = []  # List of lists of (text, color) tuples
        self.scroll_offset = 0
        self.horizontal_offset = 0
        self.show_line_numbers = True
        self.wrap_lines = False
        self.syntax_highlighting = PYGMENTS_AVAILABLE
        
        # Load file content
        self.load_file()
        
    def load_file(self):
        """Load and process the text file"""
        try:
            # Try to read as text file with different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(self.file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                # If all encodings fail, try binary mode and show hex
                self.lines = ["[Binary file - cannot display as text]"]
                self.highlighted_lines = [[("[Binary file - cannot display as text]", curses.color_pair(COLOR_REGULAR_FILE))]]
                return
                
            # Split into lines
            self.lines = content.splitlines()
            
            # Apply syntax highlighting if enabled
            if self.syntax_highlighting:
                self.apply_syntax_highlighting(content)
            else:
                # Create plain highlighted lines (no colors)
                self.highlighted_lines = [[(line, curses.color_pair(COLOR_REGULAR_FILE))] for line in self.lines]
                
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.lines = [error_msg]
            self.highlighted_lines = [[(error_msg, curses.color_pair(COLOR_ERROR))]]
    
    def apply_syntax_highlighting(self, content: str):
        """Apply syntax highlighting using pygments and curses colors"""
        if not PYGMENTS_AVAILABLE:
            # Create plain highlighted lines (no colors)
            self.highlighted_lines = [[(line, curses.color_pair(COLOR_REGULAR_FILE))] for line in self.lines]
            return
            
        try:
            # Get appropriate lexer for the file
            lexer = None
            
            # Try to get lexer by filename
            try:
                lexer = get_lexer_for_filename(self.file_path.name)
            except ClassNotFound:
                # Try by file extension
                ext = self.file_path.suffix.lower()
                lexer_map = {
                    '.py': 'python',
                    '.js': 'javascript', 
                    '.json': 'json',
                    '.md': 'markdown',
                    '.yml': 'yaml',
                    '.yaml': 'yaml',
                    '.xml': 'xml',
                    '.html': 'html',
                    '.css': 'css',
                    '.sh': 'bash',
                    '.bash': 'bash',
                    '.zsh': 'zsh',
                    '.c': 'c',
                    '.cpp': 'cpp',
                    '.h': 'c',
                    '.hpp': 'cpp',
                    '.java': 'java',
                    '.go': 'go',
                    '.rs': 'rust',
                    '.php': 'php',
                    '.rb': 'ruby',
                    '.sql': 'sql',
                    '.ini': 'ini',
                    '.cfg': 'ini',
                    '.conf': 'ini',
                    '.toml': 'toml',
                }
                
                if ext in lexer_map:
                    try:
                        lexer = get_lexer_by_name(lexer_map[ext])
                    except ClassNotFound:
                        pass
            
            # Fallback to text lexer
            if lexer is None:
                lexer = TextLexer()
            
            # Tokenize the content
            tokens = list(lexer.get_tokens(content))
            
            # Convert tokens to highlighted lines
            self.highlighted_lines = self.tokens_to_highlighted_lines(tokens)
            
        except Exception:
            # If highlighting fails, create plain highlighted lines
            self.highlighted_lines = [[(line, curses.color_pair(COLOR_REGULAR_FILE))] for line in self.lines]
    
    def tokens_to_highlighted_lines(self, tokens) -> List[List[Tuple[str, int]]]:
        """Convert pygments tokens to lines of (text, color) tuples"""
        highlighted_lines = []
        current_line = []
        
        for token_type, text in tokens:
            # Get the appropriate curses color for this token type
            color = get_syntax_color(token_type)
            
            # Handle newlines - split tokens that contain newlines
            if '\n' in text:
                parts = text.split('\n')
                
                # Add the first part to current line
                if parts[0]:
                    current_line.append((parts[0], color))
                
                # Finish current line
                highlighted_lines.append(current_line)
                
                # Add intermediate complete lines
                for part in parts[1:-1]:
                    if part:
                        highlighted_lines.append([(part, color)])
                    else:
                        highlighted_lines.append([])  # Empty line
                
                # Start new line with last part
                current_line = []
                if parts[-1]:
                    current_line.append((parts[-1], color))
            else:
                # No newlines, just add to current line
                if text:
                    current_line.append((text, color))
        
        # Add final line if not empty
        if current_line:
            highlighted_lines.append(current_line)
        
        return highlighted_lines
    
    def get_display_dimensions(self) -> Tuple[int, int, int, int]:
        """Get the dimensions for the text display area"""
        height, width = self.stdscr.getmaxyx()
        
        # Reserve space for header (2 lines) and footer (1 line)
        start_y = 2
        display_height = height - 3
        start_x = 0
        display_width = width
        
        return start_y, start_x, display_height, display_width
    
    def draw_header(self):
        """Draw the viewer header"""
        height, width = self.stdscr.getmaxyx()
        
        # Clear header area
        try:
            self.stdscr.addstr(0, 0, " " * (width - 1), get_header_color())
            self.stdscr.addstr(1, 0, " " * (width - 1), get_header_color())
        except curses.error:
            pass
        
        # File path and info
        file_info = f"File: {self.file_path.name}"
        if len(file_info) > width - 4:
            file_info = "..." + file_info[-(width-7):]
        
        try:
            self.stdscr.addstr(0, 2, file_info, get_header_color())
        except curses.error:
            pass
        
        # Status line with controls
        status_parts = []
        if self.syntax_highlighting:
            status_parts.append("Syntax: ON")
        else:
            status_parts.append("Syntax: OFF")
            
        if self.show_line_numbers:
            status_parts.append("Lines: ON")
        else:
            status_parts.append("Lines: OFF")
            
        if self.wrap_lines:
            status_parts.append("Wrap: ON")
        else:
            status_parts.append("Wrap: OFF")
        
        status_left = " | ".join(status_parts)
        controls = "q:quit ↑↓:scroll ←→:h-scroll n:numbers w:wrap s:syntax"
        
        try:
            self.stdscr.addstr(1, 2, status_left, get_status_color())
            
            # Right-align controls if there's space
            if len(status_left) + len(controls) + 6 < width:
                controls_x = width - len(controls) - 2
                self.stdscr.addstr(1, controls_x, controls, get_status_color())
        except curses.error:
            pass
    
    def draw_content(self):
        """Draw the file content with syntax highlighting"""
        start_y, start_x, display_height, display_width = self.get_display_dimensions()
        
        # Calculate line number width if showing line numbers
        line_num_width = 0
        if self.show_line_numbers and self.lines:
            line_num_width = len(str(len(self.lines))) + 2
        
        # Available width for content
        content_width = display_width - line_num_width
        
        # Draw visible lines
        for i in range(display_height):
            line_index = self.scroll_offset + i
            y_pos = start_y + i
            
            # Clear the line
            try:
                self.stdscr.addstr(y_pos, start_x, " " * (display_width - 1))
            except curses.error:
                pass
            
            if line_index >= len(self.highlighted_lines):
                continue
            
            # Draw line number if enabled
            x_pos = start_x
            if self.show_line_numbers:
                line_num = f"{line_index + 1:>{line_num_width-1}} "
                try:
                    self.stdscr.addstr(y_pos, x_pos, line_num, get_line_number_color())
                except curses.error:
                    pass
                x_pos += line_num_width
            
            # Get the highlighted line (list of (text, color) tuples)
            highlighted_line = self.highlighted_lines[line_index]
            
            # Apply horizontal scrolling
            current_col = 0
            display_x = x_pos
            
            for text, color in highlighted_line:
                # Skip text that's before the horizontal offset
                if current_col + len(text) <= self.horizontal_offset:
                    current_col += len(text)
                    continue
                
                # Calculate visible portion of this text segment
                start_offset = max(0, self.horizontal_offset - current_col)
                visible_text = text[start_offset:]
                
                # Check if we have room to display this text
                remaining_width = content_width - (display_x - x_pos)
                if remaining_width <= 0:
                    break
                
                # Truncate if necessary
                if len(visible_text) > remaining_width:
                    visible_text = visible_text[:remaining_width]
                
                # Draw the text with its color
                if visible_text:
                    try:
                        self.stdscr.addstr(y_pos, display_x, visible_text, color)
                        display_x += len(visible_text)
                    except curses.error:
                        pass
                
                current_col += len(text)
                
                # Stop if we've filled the line
                if display_x - x_pos >= content_width:
                    break
    
    def handle_key(self, key) -> bool:
        """Handle key input. Returns True if viewer should continue, False to exit"""
        start_y, start_x, display_height, display_width = self.get_display_dimensions()
        
        if key == ord('q') or key == ord('Q') or key == 27:  # q, Q, or ESC
            return False
            
        elif key == curses.KEY_UP or key == ord('k'):
            if self.scroll_offset > 0:
                self.scroll_offset -= 1
                
        elif key == curses.KEY_DOWN or key == ord('j'):
            max_scroll = max(0, len(self.lines) - display_height)
            if self.scroll_offset < max_scroll:
                self.scroll_offset += 1
                
        elif key == curses.KEY_LEFT or key == ord('h'):
            if self.horizontal_offset > 0:
                self.horizontal_offset -= 1
                
        elif key == curses.KEY_RIGHT or key == ord('l'):
            self.horizontal_offset += 1
            
        elif key == curses.KEY_PPAGE:  # Page Up
            self.scroll_offset = max(0, self.scroll_offset - display_height)
            
        elif key == curses.KEY_NPAGE:  # Page Down
            max_scroll = max(0, len(self.lines) - display_height)
            self.scroll_offset = min(max_scroll, self.scroll_offset + display_height)
            
        elif key == curses.KEY_HOME:
            self.scroll_offset = 0
            self.horizontal_offset = 0
            
        elif key == curses.KEY_END:
            max_scroll = max(0, len(self.lines) - display_height)
            self.scroll_offset = max_scroll
            
        elif key == ord('n') or key == ord('N'):
            self.show_line_numbers = not self.show_line_numbers
            
        elif key == ord('w') or key == ord('W'):
            self.wrap_lines = not self.wrap_lines
            
        elif key == ord('s') or key == ord('S'):
            if PYGMENTS_AVAILABLE:
                self.syntax_highlighting = not self.syntax_highlighting
                # Re-apply highlighting without reloading the file
                if self.syntax_highlighting:
                    content = '\n'.join(self.lines)
                    self.apply_syntax_highlighting(content)
                else:
                    # Create plain highlighted lines (no colors)
                    self.highlighted_lines = [[(line, curses.color_pair(COLOR_REGULAR_FILE))] for line in self.lines]
            
        return True
    
    def run(self):
        """Main viewer loop"""
        curses.curs_set(0)  # Hide cursor
        
        while True:
            # Clear screen
            self.stdscr.clear()
            
            # Draw components
            self.draw_header()
            self.draw_content()
            
            # Refresh screen
            self.stdscr.refresh()
            
            # Handle input
            try:
                key = self.stdscr.getch()
                if not self.handle_key(key):
                    break
            except KeyboardInterrupt:
                break


def is_text_file(file_path: Path) -> bool:
    """Check if a file is likely to be a text file"""
    # Check by extension first
    text_extensions = {
        '.txt', '.py', '.js', '.json', '.md', '.yml', '.yaml', '.xml', 
        '.html', '.css', '.sh', '.bash', '.zsh', '.c', '.cpp', '.h', 
        '.hpp', '.java', '.go', '.rs', '.php', '.rb', '.sql', '.ini', 
        '.cfg', '.conf', '.toml', '.log', '.csv', '.tsv', '.rst', 
        '.tex', '.r', '.R', '.scala', '.kt', '.swift', '.dart',
        '.dockerfile', '.gitignore', '.gitattributes', '.editorconfig'
    }
    
    if file_path.suffix.lower() in text_extensions:
        return True
    
    # Check files without extensions that are commonly text
    text_names = {
        'readme', 'license', 'changelog', 'makefile', 'dockerfile',
        'vagrantfile', 'gemfile', 'rakefile', 'procfile'
    }
    
    if file_path.name.lower() in text_names:
        return True
    
    # Try to read first few bytes to detect binary files
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            
        # Check for null bytes (common in binary files)
        if b'\x00' in chunk:
            return False
            
        # Try to decode as UTF-8
        try:
            chunk.decode('utf-8')
            return True
        except UnicodeDecodeError:
            # Try other common encodings
            for encoding in ['latin-1', 'cp1252']:
                try:
                    chunk.decode(encoding)
                    return True
                except UnicodeDecodeError:
                    continue
            return False
            
    except Exception:
        return False


def view_text_file(stdscr, file_path: Path) -> bool:
    """
    View a text file with syntax highlighting
    
    Args:
        stdscr: curses screen object
        file_path: Path to the file to view
        
    Returns:
        True if file was viewed successfully, False otherwise
    """
    if not file_path.exists() or not file_path.is_file():
        return False
        
    if not is_text_file(file_path):
        return False
    
    try:
        viewer = TextViewer(stdscr, file_path)
        viewer.run()
        return True
    except Exception:
        return False