#!/usr/bin/env python3
"""
TFM Text File Viewer with Syntax Highlighting

A text file viewer component for TFM that supports syntax highlighting
for popular file formats using pygments (optional dependency).
"""

import os
import traceback
from tfm_path import Path
from typing import List, Tuple, Optional, Dict, Any
import re
from ttk import KeyEvent, KeyCode, CharEvent, SystemEvent
from ttk.renderer import TextAttribute
from tfm_log_manager import getLogger
from tfm_log_manager import getLogger

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
from tfm_wide_char_utils import get_display_width, truncate_to_width, split_at_width, safe_get_display_width
from tfm_scrollbar import draw_scrollbar, calculate_scrollbar_width
from tfm_ui_layer import UILayer
from tfm_info_dialog import InfoDialog

# Module-level logger for utility functions
logger = getLogger("TextViewer")


class TextViewer(UILayer):
    """Text file viewer with syntax highlighting support"""
    
    def __init__(self, renderer, file_path: Path, layer_stack=None):
        self.logger = getLogger("TextViewer")
        self.renderer = renderer
        self.file_path = file_path
        self.layer_stack = layer_stack
        self.original_lines = []  # Original lines with tabs preserved
        self.lines = []  # List of strings (plain text lines with tabs expanded)
        self.highlighted_lines = []  # List of lists of (text, color) tuples
        self.scroll_offset = 0
        self.horizontal_offset = 0
        self.show_line_numbers = True
        self.wrap_lines = False
        self.syntax_highlighting = PYGMENTS_AVAILABLE
        self.tab_width = 4  # Number of spaces per tab
        self._should_close = False  # Flag to indicate viewer wants to close
        self._dirty = True  # Start dirty to ensure initial render
        
        # Isearch mode state
        self.isearch_mode = False
        self.isearch_pattern = ""
        self.isearch_matches = []  # List of line indices that match
        self.isearch_match_index = 0  # Current match index
        
        # Help dialog
        self.info_dialog = InfoDialog(None, renderer)
        
        # Load file content
        self.load_file()
        
    def expand_tabs(self, line: str) -> str:
        """
        Expand tab characters to spaces, respecting column positions.
        
        Args:
            line: Line of text that may contain tab characters
            
        Returns:
            Line with tabs expanded to spaces
        """
        if '\t' not in line:
            return line
        
        result = []
        col = 0
        
        for char in line:
            if char == '\t':
                # Calculate spaces needed to reach next tab stop
                spaces_to_add = self.tab_width - (col % self.tab_width)
                result.append(' ' * spaces_to_add)
                col += spaces_to_add
            else:
                result.append(char)
                # Account for wide characters in column calculation
                col += get_display_width(char)
        
        return ''.join(result)
    
    def refresh_tab_expansion(self):
        """
        Re-expand tabs in original lines with current tab width.
        This is called when tab width changes or file is first loaded.
        """
        # Expand tabs in original lines
        self.lines = [self.expand_tabs(line) for line in self.original_lines]
        
        # Apply syntax highlighting if enabled
        if self.syntax_highlighting:
            # Re-create content with expanded tabs for syntax highlighting
            expanded_content = '\n'.join(self.lines)
            self.apply_syntax_highlighting(expanded_content)
        else:
            # Create plain highlighted lines (no colors)
            self.highlighted_lines = [[(line, COLOR_REGULAR_FILE)] for line in self.lines]
    
    def load_file(self):
        """Load and process the text file"""
        try:
            # Try to read as text file with different encodings using tfm_path abstraction
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    # Use tfm_path's read_text method which works for both local and remote files
                    content = self.file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
                except (FileNotFoundError, OSError):
                    # Re-raise these as they indicate actual file access issues
                    raise
            
            if content is None:
                # If all encodings fail, try binary mode and show hex
                try:
                    # Try to read as bytes to detect if it's truly a binary file
                    binary_content = self.file_path.read_bytes()
                    # Check if it contains null bytes (common in binary files)
                    if b'\x00' in binary_content[:1024]:
                        self.original_lines = ["[Binary file - cannot display as text]"]
                        self.lines = ["[Binary file - cannot display as text]"]
                        self.highlighted_lines = [[("[Binary file - cannot display as text]", COLOR_REGULAR_FILE)]]
                        return
                    else:
                        # Try to decode as latin-1 as a last resort (it can decode any byte sequence)
                        content = binary_content.decode('latin-1', errors='replace')
                except Exception:
                    self.original_lines = ["[Binary file - cannot display as text]"]
                    self.lines = ["[Binary file - cannot display as text]"]
                    self.highlighted_lines = [[("[Binary file - cannot display as text]", COLOR_REGULAR_FILE)]]
                    return
                
            # Store original lines with tabs preserved
            self.original_lines = content.splitlines()
            
            # Expand tabs for display
            self.refresh_tab_expansion()
                
        except FileNotFoundError:
            error_msg = f"File not found: {self.file_path}"
            self.original_lines = [error_msg]
            self.lines = [error_msg]
            self.highlighted_lines = [[(error_msg, COLOR_ERROR)]]
        except PermissionError:
            error_msg = f"Permission denied: {self.file_path}"
            self.original_lines = [error_msg]
            self.lines = [error_msg]
            self.highlighted_lines = [[(error_msg, COLOR_ERROR)]]
        except OSError as e:
            error_msg = f"Error reading file: {e}"
            self.original_lines = [error_msg]
            self.lines = [error_msg]
            self.highlighted_lines = [[(error_msg, COLOR_ERROR)]]
        except Exception as e:
            error_msg = f"Unexpected error reading file: {e}"
            self.original_lines = [error_msg]
            self.lines = [error_msg]
            self.highlighted_lines = [[(error_msg, COLOR_ERROR)]]
    
    def apply_syntax_highlighting(self, content: str):
        """Apply syntax highlighting using pygments and TTK colors"""
        if not PYGMENTS_AVAILABLE:
            # Create plain highlighted lines (no colors)
            self.highlighted_lines = [[(line, COLOR_REGULAR_FILE)] for line in self.lines]
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
            
        except Exception as e:
            # If highlighting fails, create plain highlighted lines
            self.logger.warning(f"Syntax highlighting failed: {e}")
            self.highlighted_lines = [[(line, COLOR_REGULAR_FILE)] for line in self.lines]
    
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
    
    def wrap_highlighted_line(self, highlighted_line: List[Tuple[str, int]], max_width: int) -> List[List[Tuple[str, int]]]:
        """
        Wrap a highlighted line to fit within max_width display columns.
        
        Args:
            highlighted_line: List of (text, color) tuples representing a line
            max_width: Maximum display width for wrapped lines
            
        Returns:
            List of wrapped lines, each being a list of (text, color) tuples
        """
        if not highlighted_line or max_width <= 0:
            return [highlighted_line] if highlighted_line else [[]]
        
        wrapped_lines = []
        current_line = []
        current_width = 0
        
        for text, color in highlighted_line:
            if not text:
                continue
                
            # Process this text segment, potentially splitting it across lines
            remaining_text = text
            
            while remaining_text:
                # Calculate how much space is left on current line
                space_left = max_width - current_width
                
                if space_left <= 0:
                    # Current line is full, start a new line
                    if current_line:
                        wrapped_lines.append(current_line)
                    current_line = []
                    current_width = 0
                    space_left = max_width
                
                # Split the remaining text to fit in available space
                if get_display_width(remaining_text) <= space_left:
                    # Entire remaining text fits
                    current_line.append((remaining_text, color))
                    current_width += get_display_width(remaining_text)
                    remaining_text = ""
                else:
                    # Need to split the text
                    fit_text, remaining_text = split_at_width(remaining_text, space_left)
                    
                    if fit_text:
                        current_line.append((fit_text, color))
                        current_width += get_display_width(fit_text)
                    
                    # If no text fit and we have space, there might be a wide character
                    # that doesn't fit - in this case, start a new line
                    if not fit_text and space_left > 0:
                        if current_line:
                            wrapped_lines.append(current_line)
                        current_line = []
                        current_width = 0
        
        # Add the final line if it has content
        if current_line:
            wrapped_lines.append(current_line)
        
        # Ensure we return at least one line (even if empty)
        if not wrapped_lines:
            wrapped_lines = [[]]
        
        return wrapped_lines
    
    def get_wrapped_lines(self) -> List[List[Tuple[str, int]]]:
        """
        Get all lines with wrapping applied if wrap_lines is enabled.
        
        Returns:
            List of display lines, each being a list of (text, color) tuples
        """
        if not self.wrap_lines:
            return self.highlighted_lines
        
        # Calculate available width for content
        start_y, start_x, display_height, display_width = self.get_display_dimensions()
        
        # Account for line numbers if enabled
        line_num_width = 0
        if self.show_line_numbers and self.lines:
            line_num_width = len(str(len(self.lines))) + 2
        
        content_width = display_width - line_num_width
        
        if content_width <= 0:
            return self.highlighted_lines
        
        wrapped_lines = []
        for highlighted_line in self.highlighted_lines:
            wrapped_segments = self.wrap_highlighted_line(highlighted_line, content_width)
            wrapped_lines.extend(wrapped_segments)
        
        return wrapped_lines
    
    def get_wrapped_lines_with_mapping(self) -> Tuple[List[List[Tuple[str, int]]], List[int]]:
        """
        Get all lines with wrapping applied and a mapping to original line numbers.
        
        Returns:
            Tuple of (display_lines, line_mapping) where:
            - display_lines: List of display lines, each being a list of (text, color) tuples
            - line_mapping: List mapping each display line index to its original line number (1-based)
        """
        if not self.wrap_lines:
            # No wrapping - simple 1:1 mapping
            return self.highlighted_lines, list(range(1, len(self.highlighted_lines) + 1))
        
        # Calculate available width for content
        start_y, start_x, display_height, display_width = self.get_display_dimensions()
        
        # Account for line numbers if enabled
        line_num_width = 0
        if self.show_line_numbers and self.lines:
            line_num_width = len(str(len(self.lines))) + 2
        
        content_width = display_width - line_num_width
        
        if content_width <= 0:
            return self.highlighted_lines, list(range(1, len(self.highlighted_lines) + 1))
        
        wrapped_lines = []
        line_mapping = []
        
        for original_line_num, highlighted_line in enumerate(self.highlighted_lines, start=1):
            wrapped_segments = self.wrap_highlighted_line(highlighted_line, content_width)
            wrapped_lines.extend(wrapped_segments)
            # Map all wrapped segments to the same original line number
            line_mapping.extend([original_line_num] * len(wrapped_segments))
        
        return wrapped_lines, line_mapping
    
    def find_matches(self, pattern: str) -> List[int]:
        """Find all lines that match the search pattern (case-insensitive)"""
        if not pattern:
            return []
        
        matches = []
        pattern_lower = pattern.lower()
        
        for i, line in enumerate(self.lines):
            if pattern_lower in line.lower():
                matches.append(i)
        
        return matches
    
    def update_isearch_matches(self):
        """Update isearch matches and move to nearest match"""
        self.isearch_matches = self.find_matches(self.isearch_pattern)
        
        if self.isearch_matches:
            # Find the closest match to current position
            current_line = self.scroll_offset
            best_match = 0
            min_distance = abs(self.isearch_matches[0] - current_line)
            
            for i, match_line in enumerate(self.isearch_matches):
                distance = abs(match_line - current_line)
                if distance < min_distance:
                    min_distance = distance
                    best_match = i
            
            self.isearch_match_index = best_match
            self.jump_to_match()
    
    def jump_to_match(self):
        """Jump to the current search match"""
        if self.isearch_matches and 0 <= self.isearch_match_index < len(self.isearch_matches):
            match_line = self.isearch_matches[self.isearch_match_index]
            
            # Center the match on screen if possible
            start_y, start_x, display_height, display_width = self.get_display_dimensions()
            center_offset = display_height // 2
            
            self.scroll_offset = max(0, match_line - center_offset)
            
            # Ensure we don't scroll past the end
            max_scroll = max(0, len(self.lines) - display_height)
            self.scroll_offset = min(self.scroll_offset, max_scroll)
    
    def enter_isearch_mode(self):
        """Enter isearch mode"""
        self.isearch_mode = True
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
        self.mark_dirty()  # Redraw to show isearch interface
    
    def exit_isearch_mode(self):
        """Exit isearch mode"""
        self.isearch_mode = False
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
        self.mark_dirty()  # Redraw to remove isearch interface
    
    def _show_help_dialog(self) -> None:
        """Show help dialog with keyboard shortcuts."""
        title = "Text Viewer - Help"
        help_lines = [
            "NAVIGATION",
            "  ↑/↓           Scroll up/down one line",
            "  ←/→           Scroll left/right (when not wrapping)",
            "  PgUp/PgDn     Scroll one page up/down",
            "  Home/End      Jump to beginning/end of file",
            "",
            "SEARCH",
            "  f             Enter incremental search mode",
            "  (in search)   Type to search, ↑/↓ to navigate matches",
            "  (in search)   ESC or Enter to exit search",
            "",
            "DISPLAY OPTIONS",
            "  n             Toggle line numbers",
            "  w             Toggle line wrapping",
            "  s             Toggle syntax highlighting",
            "  t             Cycle tab width (2/4/8 spaces)",
            "",
            "GENERAL",
            "  ?             Show this help",
            "  q/ESC/Enter   Close viewer",
        ]
        
        self.info_dialog.show(title, help_lines)
        if self.layer_stack:
            self.layer_stack.push(self.info_dialog)
        self._dirty = True
    
    def handle_isearch_input(self, event: KeyEvent) -> bool:
        """Handle input while in isearch mode. Returns True if key was handled."""
        # Handle None event
        if event is None:
            return False
        
        # Handle CharEvent - text input for search pattern
        if isinstance(event, CharEvent):
            self.isearch_pattern += event.char
            self.update_isearch_matches()
            return True
        
        # Handle KeyEvent - navigation and control commands
        if isinstance(event, KeyEvent):
            if event.key_code == KeyCode.ESCAPE:
                self.exit_isearch_mode()
                return True
            elif event.key_code == KeyCode.ENTER:
                # Enter - exit isearch mode and keep current position
                self.exit_isearch_mode()
                return True
            elif event.key_code == KeyCode.BACKSPACE:
                # Backspace - remove last character
                if self.isearch_pattern:
                    self.isearch_pattern = self.isearch_pattern[:-1]
                    self.update_isearch_matches()
                return True
            elif event.key_code == KeyCode.UP:
                # Up arrow - go to previous match
                if self.isearch_matches:
                    self.isearch_match_index = (self.isearch_match_index - 1) % len(self.isearch_matches)
                    self.jump_to_match()
                return True
            elif event.key_code == KeyCode.DOWN:
                # Down arrow - go to next match
                if self.isearch_matches:
                    self.isearch_match_index = (self.isearch_match_index + 1) % len(self.isearch_matches)
                    self.jump_to_match()
                return True
            else:
                # For other KeyEvents, return False so backend can generate CharEvent
                return False
        
        return False
    
    def get_display_dimensions(self) -> Tuple[int, int, int, int]:
        """Get the dimensions for the text display area"""
        try:
            dimensions = self.renderer.get_dimensions()
            
            # Ensure we got a tuple of two integers
            if not isinstance(dimensions, tuple) or len(dimensions) != 2:
                self.logger.warning(f"get_dimensions() returned unexpected value: {dimensions} (type: {type(dimensions)})")
                # Fallback to reasonable defaults
                height, width = 24, 80
            else:
                height, width = dimensions
            
            # Ensure height and width are integers
            if not isinstance(height, int) or not isinstance(width, int):
                self.logger.warning(f"get_dimensions() returned non-integer values: height={height} (type: {type(height)}), width={width} (type: {type(width)})")
                height, width = 24, 80
            
            # Reserve space for header (1 line) and status bar (1 line)
            # When isearch is active, it uses a 2nd header line temporarily
            header_lines = 2 if self.isearch_mode else 1
            start_y = header_lines
            display_height = max(1, height - header_lines - 1)  # Header + status bar, ensure at least 1
            start_x = 0
            display_width = max(1, width)  # Ensure at least 1
            
            # Final validation - ensure all return values are integers
            assert isinstance(start_y, int), f"start_y is not int: {type(start_y)}"
            assert isinstance(start_x, int), f"start_x is not int: {type(start_x)}"
            assert isinstance(display_height, int), f"display_height is not int: {type(display_height)}"
            assert isinstance(display_width, int), f"display_width is not int: {type(display_width)}"
            
            return start_y, start_x, display_height, display_width
            
        except Exception as e:
            self.logger.error(f"Error in get_display_dimensions: {e}")
            traceback.print_exc()
            # Return safe defaults based on isearch mode
            if self.isearch_mode:
                return 2, 0, 21, 80
            else:
                return 1, 0, 22, 80
    
    def draw_header(self):
        """Draw the viewer header"""
        height, width = self.renderer.get_dimensions()
        
        # Get header color
        header_color_pair, header_attrs = get_header_color()
        
        # Clear header area with colored background - only 1 line normally
        self.renderer.draw_text(0, 0, " " * width, header_color_pair, header_attrs)
        
        # File path and info - use polymorphic display methods
        display_prefix = self.file_path.get_display_prefix()
        display_title = self.file_path.get_display_title()
        
        # Combine prefix and title for display
        if display_prefix:
            file_info = f"{display_prefix}{display_title}"
        else:
            file_info = f"File: {display_title}"
            
        # Truncate using display width (accounts for wide characters)
        max_width = width - 4
        if get_display_width(file_info) > max_width:
            file_info = truncate_to_width(file_info, max_width, ellipsis="…")
        
        self.renderer.draw_text(0, 2, file_info, header_color_pair, header_attrs)
        
        # Show isearch interface on 2nd line when active
        if self.isearch_mode:
            # Clear 2nd line
            self.renderer.draw_text(1, 0, " " * width, header_color_pair, header_attrs)
            
            # Show isearch interface
            isearch_prompt = f"Isearch: {self.isearch_pattern}"
            if self.isearch_matches:
                match_info = f" ({self.isearch_match_index + 1}/{len(self.isearch_matches)})"
                isearch_prompt += match_info
            isearch_prompt += " [ESC:exit ↑↓:navigate]"
            
            search_color_pair, search_attrs = get_search_color()
            self.renderer.draw_text(1, 2, isearch_prompt[:width-4], search_color_pair, search_attrs)
    
    def draw_status_bar(self):
        """Draw the status bar at the bottom of the viewer"""
        height, width = self.renderer.get_dimensions()
        status_y = height - 1  # Bottom line
        
        # Get status color
        status_color_pair, status_attrs = get_status_color()
        
        # Clear status bar area with colored background - fill entire width
        self.renderer.draw_text(status_y, 0, " " * width, status_color_pair, status_attrs)
        
        # Left side: navigation hints
        left_status = " ?:help  q:quit "
        
        # Right side: file type and options status
        right_parts = []
        
        # File format/type
        ext = self.file_path.suffix.lower()
        if ext:
            right_parts.append(ext[1:].upper())  # Remove dot and uppercase
        else:
            right_parts.append("TEXT")
        
        # Show active options
        options = []
        if self.show_line_numbers:
            options.append("NUM")
        if self.wrap_lines:
            options.append("WRAP")
        if PYGMENTS_AVAILABLE and self.syntax_highlighting:
            options.append("SYNTAX")
        options.append(f"TAB:{self.tab_width}")
        
        if options:
            right_parts.extend(options)
        
        right_status = f" {' | '.join(right_parts)} "
        
        # Draw left status
        self.renderer.draw_text(status_y, 0, left_status, status_color_pair, status_attrs)
        
        # Draw right status (right-aligned)
        right_x = width - len(right_status)
        if right_x > len(left_status):
            self.renderer.draw_text(status_y, right_x, right_status, status_color_pair, status_attrs)
    
    def draw_content(self):
        """Draw the file content with syntax highlighting and wide character support"""
        start_y, start_x, display_height, display_width = self.get_display_dimensions()
        
        # Get the lines to display with mapping to original line numbers
        display_lines, line_mapping = self.get_wrapped_lines_with_mapping()
        
        # Calculate line number width if showing line numbers
        line_num_width = 0
        if self.show_line_numbers and self.lines:
            # Use original line count for line number width calculation
            line_num_width = len(str(len(self.lines))) + 2
        
        # Reserve space for scroll bar if needed
        scroll_bar_width = calculate_scrollbar_width(len(display_lines), display_height)
        
        # Available width for content (account for line numbers and scroll bar)
        content_width = display_width - line_num_width - scroll_bar_width
        
        # Get background color for filling empty areas
        bg_color_pair, bg_attrs = get_background_color_pair()
        
        # Draw visible lines
        for i in range(display_height):
            line_index = self.scroll_offset + i
            y_pos = start_y + i
            
            # Fill the entire line with background color - fill entire width
            self.renderer.draw_text(y_pos, start_x, ' ' * display_width, bg_color_pair, bg_attrs)
            
            if line_index >= len(display_lines):
                continue
            
            # Draw line number if enabled
            x_pos = start_x
            if self.show_line_numbers:
                # Get the original line number for this display line
                original_line_num = line_mapping[line_index] if line_index < len(line_mapping) else line_index + 1
                
                # Only show line number for the first wrapped segment of each original line
                # Check if this is the first occurrence of this line number in the visible range
                is_first_segment = True
                if self.wrap_lines and line_index > 0:
                    prev_line_num = line_mapping[line_index - 1] if line_index - 1 < len(line_mapping) else 0
                    if prev_line_num == original_line_num:
                        is_first_segment = False
                
                if is_first_segment:
                    line_num = f"{original_line_num:>{line_num_width-1}} "
                else:
                    # Show blank space for continuation lines
                    line_num = " " * line_num_width
                
                line_num_color_pair, line_num_attrs = get_line_number_color()
                self.renderer.draw_text(y_pos, x_pos, line_num, line_num_color_pair, line_num_attrs)
                x_pos += line_num_width
            
            # Get the highlighted line (list of (text, color) tuples)
            highlighted_line = display_lines[line_index]
            
            # Check if this line is an isearch match
            original_line_index = line_mapping[line_index] - 1 if line_index < len(line_mapping) else line_index
            is_search_match = (self.isearch_mode and 
                             self.isearch_matches and 
                             original_line_index in self.isearch_matches)
            
            # Check if this is the current search match
            is_current_match = (is_search_match and 
                              self.isearch_matches and
                              0 <= self.isearch_match_index < len(self.isearch_matches) and
                              original_line_index == self.isearch_matches[self.isearch_match_index])
            
            # Apply horizontal scrolling using display width calculations
            current_display_col = 0
            display_x = x_pos
            
            for text, color in highlighted_line:
                if not text:
                    continue
                
                text_display_width = get_display_width(text)
                
                # Skip text that's before the horizontal offset
                if current_display_col + text_display_width <= self.horizontal_offset:
                    current_display_col += text_display_width
                    continue
                
                # Calculate visible portion of this text segment
                start_offset_cols = max(0, self.horizontal_offset - current_display_col)
                
                # Split text to handle horizontal scrolling with wide characters
                if start_offset_cols > 0:
                    # Need to skip some characters from the beginning
                    visible_text = ""
                    skip_width = 0
                    char_index = 0
                    for char in text:
                        char_width = get_display_width(char)
                        if skip_width + char_width > start_offset_cols:
                            visible_text = text[char_index:]
                            break
                        skip_width += char_width
                        char_index += 1
                    if not visible_text:
                        current_display_col += text_display_width
                        continue
                else:
                    visible_text = text
                
                # Check if we have room to display this text
                remaining_width = content_width - (display_x - x_pos)
                if remaining_width <= 0:
                    break
                
                # Truncate if necessary using wide character aware truncation
                visible_text_width = get_display_width(visible_text)
                if visible_text_width > remaining_width:
                    visible_text = truncate_to_width(visible_text, remaining_width, "")
                
                # Draw the text with its color
                if visible_text:
                    # Use search highlight color for matches
                    if is_current_match:
                        display_color_pair, display_attrs = get_search_current_color()
                    elif is_search_match:
                        display_color_pair, display_attrs = get_search_match_color()
                    else:
                        # color is a color pair constant, need to get attributes
                        display_color_pair, display_attrs = get_color_with_attrs(color)
                    
                    self.renderer.draw_text(y_pos, display_x, visible_text, display_color_pair, display_attrs)
                    display_x += get_display_width(visible_text)
                
                current_display_col += text_display_width
                
                # Stop if we've filled the line
                if display_x - x_pos >= content_width:
                    break
        
        # Draw scroll bar on the right side using unified implementation
        draw_scrollbar(self.renderer, start_y, display_width - 1, display_height, 
                      len(display_lines), self.scroll_offset)
    
    def get_original_line_number(self, display_line_index: int) -> int:
        """
        Get the original line number for a display line index when wrapping is enabled.
        
        Args:
            display_line_index: Index in the wrapped display lines
            
        Returns:
            Original line number (1-based)
        """
        if not self.wrap_lines:
            return display_line_index + 1
        
        # Use the mapping from get_wrapped_lines_with_mapping
        _, line_mapping = self.get_wrapped_lines_with_mapping()
        
        if display_line_index < len(line_mapping):
            return line_mapping[display_line_index]
        
        # Fallback if index is out of range
        return len(self.lines) if self.lines else 1
    
    def draw(self):
        """Draw the viewer (called by FileManager's main loop)"""
        self.draw_header()
        self.draw_content()
        self.draw_status_bar()
    
    def handle_key_event(self, event) -> bool:
        """
        Handle a key event (UILayer interface method).
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed, False to propagate to next layer
        """
        # Handle None event
        if event is None:
            return False
        
        start_y, start_x, display_height, display_width = self.get_display_dimensions()
        
        # Handle isearch mode input first
        if self.isearch_mode:
            result = self.handle_isearch_input(event)
            if result:
                self._dirty = True
            return result
        
        # CharEvents should only be handled in isearch mode
        # Return False for unhandled CharEvents so backend generates them
        if isinstance(event, CharEvent):
            return False
        
        # Check for character-based commands (only from KeyEvent)
        if isinstance(event, KeyEvent) and event.char:
            char_lower = event.char.lower()
            if char_lower == 'q':
                # Quit viewer
                self._should_close = True
                self._dirty = True
                return True
            elif event.char == '?':
                # Show help dialog
                self._show_help_dialog()
                return True
            elif char_lower == 'n':
                self.show_line_numbers = not self.show_line_numbers
                self._dirty = True
                return True
            elif char_lower == 'w':
                # When toggling wrap mode, adjust scroll position to maintain context
                old_scroll = self.scroll_offset
                self.wrap_lines = not self.wrap_lines
                
                # Reset horizontal offset when enabling wrap mode
                if self.wrap_lines:
                    self.horizontal_offset = 0
                
                # Try to maintain approximate scroll position
                if self.wrap_lines:
                    # When enabling wrap, we might need to adjust scroll position
                    # since wrapped lines will be longer
                    display_lines, _ = self.get_wrapped_lines_with_mapping()
                    max_scroll = max(0, len(display_lines) - display_height)
                    self.scroll_offset = min(old_scroll, max_scroll)
                self._dirty = True
                return True
            elif char_lower == 's':
                if PYGMENTS_AVAILABLE:
                    self.syntax_highlighting = not self.syntax_highlighting
                    # Re-apply highlighting without reloading the file
                    if self.syntax_highlighting:
                        content = '\n'.join(self.lines)
                        self.apply_syntax_highlighting(content)
                    else:
                        # Create plain highlighted lines (no colors)
                        self.highlighted_lines = [[(line, COLOR_REGULAR_FILE)] for line in self.lines]
                    self._dirty = True
                    return True
            elif char_lower == 'f':
                # Enter isearch mode
                self.enter_isearch_mode()
                self._dirty = True
                return True
            elif char_lower == 't':
                # Cycle through tab widths: 2, 4, 8
                if self.tab_width == 2:
                    self.tab_width = 4
                elif self.tab_width == 4:
                    self.tab_width = 8
                else:
                    self.tab_width = 2
                
                # Re-expand tabs with new tab width
                self.refresh_tab_expansion()
                self._dirty = True
                return True
        
        # Check for special keys
        if event.key_code == KeyCode.ESCAPE:
            self._should_close = True
            self._dirty = True
            return True
        elif event.key_code == KeyCode.ENTER:
            self._should_close = True
            self._dirty = True
            return True
        elif event.key_code == KeyCode.UP:
            if self.scroll_offset > 0:
                self.scroll_offset -= 1
                self._dirty = True
            return True
        elif event.key_code == KeyCode.DOWN:
            # Use display lines for scrolling when wrapping is enabled
            display_lines, _ = self.get_wrapped_lines_with_mapping()
            max_scroll = max(0, len(display_lines) - display_height)
            if self.scroll_offset < max_scroll:
                self.scroll_offset += 1
                self._dirty = True
            return True
        elif event.key_code == KeyCode.LEFT:
            # Use display width units for horizontal scrolling
            if self.horizontal_offset > 0:
                self.horizontal_offset = max(0, self.horizontal_offset - 1)
                self._dirty = True
            return True
        elif event.key_code == KeyCode.RIGHT:
            # Increment horizontal offset by display width units
            self.horizontal_offset += 1
            self._dirty = True
            return True
        elif event.key_code == KeyCode.PAGE_UP:
            self.scroll_offset = max(0, self.scroll_offset - display_height)
            self._dirty = True
            return True
        elif event.key_code == KeyCode.PAGE_DOWN:
            # Use display lines for page scrolling when wrapping is enabled
            display_lines, _ = self.get_wrapped_lines_with_mapping()
            max_scroll = max(0, len(display_lines) - display_height)
            self.scroll_offset = min(max_scroll, self.scroll_offset + display_height)
            self._dirty = True
            return True
        elif event.key_code == KeyCode.HOME:
            self.scroll_offset = 0
            self.horizontal_offset = 0
            self._dirty = True
            return True
        elif event.key_code == KeyCode.END:
            # Use display lines for end positioning when wrapping is enabled
            display_lines, _ = self.get_wrapped_lines_with_mapping()
            max_scroll = max(0, len(display_lines) - display_height)
            self.scroll_offset = max_scroll
            self._dirty = True
            return True
            
        return True
    
    def handle_char_event(self, event) -> bool:
        """
        Handle a character event (UILayer interface method).
        
        Character events are handled in isearch mode for text input.
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if event was handled, False otherwise
        """
        # Handle character input in isearch mode
        if self.isearch_mode:
            result = self.handle_isearch_input(event)
            if result:
                self._dirty = True
            return result
        
        # Outside isearch mode, don't handle character events
        return False
    
    def handle_system_event(self, event) -> bool:
        """
        Handle a system event (UILayer interface method).
        
        Handles window resize and close events for the text viewer.
        
        Args:
            event: SystemEvent to handle
        
        Returns:
            True if event was handled, False otherwise
        """
        if event.is_resize():
            # Mark dirty to trigger redraw with new dimensions
            self._dirty = True
            return True
        elif event.is_close():
            # Close the viewer
            self._should_close = True
            self._dirty = True
            return True
        return False
    
    def handle_mouse_event(self, event) -> bool:
        """
        Handle a mouse event (UILayer interface method).
        
        Mouse events are not yet implemented for the text viewer.
        
        Args:
            event: MouseEvent to handle
        
        Returns:
            False (not yet implemented)
        """
        return False
    
    def render(self, renderer) -> None:
        """
        Render the layer's content (UILayer interface method).
        
        Args:
            renderer: TTK renderer instance for drawing
        """
        self.draw()
    
    def is_full_screen(self) -> bool:
        """
        Query if this layer occupies the full screen (UILayer interface method).
        
        Returns:
            True (viewers occupy full screen)
        """
        return True
    
    def needs_redraw(self) -> bool:
        """
        Query if this layer has dirty content that needs redrawing (UILayer interface method).
        
        Returns:
            True if the layer needs redrawing, False otherwise
        """
        return self._dirty
    
    def mark_dirty(self) -> None:
        """
        Mark this layer as needing a redraw (UILayer interface method).
        """
        self._dirty = True
    
    def clear_dirty(self) -> None:
        """
        Clear the dirty flag after rendering (UILayer interface method).
        """
        self._dirty = False
    
    def should_close(self) -> bool:
        """
        Query if this layer wants to close (UILayer interface method).
        
        Returns:
            True if the layer should be closed, False otherwise
        """
        return self._should_close
    
    def on_activate(self) -> None:
        """
        Called when this layer becomes the top layer (UILayer interface method).
        
        Hides cursor when viewer becomes active and marks dirty for initial render.
        """
        # Hide cursor when viewer becomes active
        self.renderer.set_cursor_visibility(False)
        self._dirty = True
    
    def on_deactivate(self) -> None:
        """
        Called when this layer is no longer the top layer (UILayer interface method).
        
        Viewer is being covered or closed - no special cleanup needed.
        """
        pass
    

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
    
    # Try to read first few bytes to detect binary files using tfm_path abstraction
    try:
        # Use tfm_path's read_bytes method which works for both local and remote files
        chunk = file_path.read_bytes()
        
        # For large files, only read first 1024 bytes for detection
        if len(chunk) > 1024:
            chunk = chunk[:1024]
            
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
            
    except FileNotFoundError:
        logger.warning(f"File not found for text detection: {file_path}")
        return False
    except PermissionError:
        logger.warning(f"Permission denied for text detection: {file_path}")
        return False
    except OSError as e:
        logger.warning(f"Could not read file for text detection {file_path}: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error in text file detection: {e}")
        return False


def create_text_viewer(renderer, file_path: Path, layer_stack=None):
    """
    Create a text viewer instance
    
    Args:
        renderer: TTK renderer object
        file_path: Path to the file to view
        layer_stack: Optional UILayerStack for pushing dialogs
        
    Returns:
        TextViewer instance or None if file cannot be viewed
    """
    if not file_path.exists() or not file_path.is_file():
        return None
        
    if not is_text_file(file_path):
        return None
    
    try:
        return TextViewer(renderer, file_path, layer_stack)
    except (OSError, IOError) as e:
        logger.error(f"Could not open text file {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating text viewer for {file_path}: {e}")
        traceback.print_exc()
        return None