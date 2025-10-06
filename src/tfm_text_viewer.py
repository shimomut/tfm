#!/usr/bin/env python3
"""
TFM Text File Viewer with Syntax Highlighting

A text file viewer component for TFM that supports syntax highlighting
for popular file formats using pygments (optional dependency).
"""

import curses
import os
from tfm_path import Path
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
from tfm_wide_char_utils import get_display_width, truncate_to_width, split_at_width, safe_get_display_width


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
        
        # Isearch mode state
        self.isearch_mode = False
        self.isearch_pattern = ""
        self.isearch_matches = []  # List of line indices that match
        self.isearch_match_index = 0  # Current match index
        
        # Load file content
        self.load_file()
        
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
                        self.lines = ["[Binary file - cannot display as text]"]
                        self.highlighted_lines = [[("[Binary file - cannot display as text]", curses.color_pair(COLOR_REGULAR_FILE))]]
                        return
                    else:
                        # Try to decode as latin-1 as a last resort (it can decode any byte sequence)
                        content = binary_content.decode('latin-1', errors='replace')
                except Exception:
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
                
        except FileNotFoundError:
            error_msg = f"File not found: {self.file_path}"
            self.lines = [error_msg]
            self.highlighted_lines = [[(error_msg, curses.color_pair(COLOR_ERROR))]]
        except PermissionError:
            error_msg = f"Permission denied: {self.file_path}"
            self.lines = [error_msg]
            self.highlighted_lines = [[(error_msg, curses.color_pair(COLOR_ERROR))]]
        except OSError as e:
            error_msg = f"Error reading file: {e}"
            self.lines = [error_msg]
            self.highlighted_lines = [[(error_msg, curses.color_pair(COLOR_ERROR))]]
        except Exception as e:
            error_msg = f"Unexpected error reading file: {e}"
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
    
    def exit_isearch_mode(self):
        """Exit isearch mode"""
        self.isearch_mode = False
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
    
    def handle_isearch_input(self, key) -> bool:
        """Handle input while in isearch mode. Returns True if key was handled."""
        if key == 27:  # ESC - exit isearch mode
            self.exit_isearch_mode()
            return True
        elif key == curses.KEY_ENTER or key == 10 or key == 13:
            # Enter - exit isearch mode and keep current position
            self.exit_isearch_mode()
            return True
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            # Backspace - remove last character
            if self.isearch_pattern:
                self.isearch_pattern = self.isearch_pattern[:-1]
                self.update_isearch_matches()
            return True
        elif key == curses.KEY_UP:
            # Up arrow - go to previous match
            if self.isearch_matches:
                self.isearch_match_index = (self.isearch_match_index - 1) % len(self.isearch_matches)
                self.jump_to_match()
            return True
        elif key == curses.KEY_DOWN:
            # Down arrow - go to next match
            if self.isearch_matches:
                self.isearch_match_index = (self.isearch_match_index + 1) % len(self.isearch_matches)
                self.jump_to_match()
            return True
        elif 32 <= key <= 126:  # Printable characters
            # Add character to isearch pattern
            self.isearch_pattern += chr(key)
            self.update_isearch_matches()
            return True
        
        return False
    
    def get_display_dimensions(self) -> Tuple[int, int, int, int]:
        """Get the dimensions for the text display area"""
        height, width = self.stdscr.getmaxyx()
        
        # Reserve space for header (2 lines) and status bar (1 line)
        start_y = 2
        display_height = height - 3  # Header (2) + status bar (1)
        start_x = 0
        display_width = width
        
        return start_y, start_x, display_height, display_width
    
    def draw_header(self):
        """Draw the viewer header"""
        height, width = self.stdscr.getmaxyx()
        
        # Clear header area with colored background
        try:
            self.stdscr.addstr(0, 0, " " * (width - 1), get_header_color())
            self.stdscr.addstr(1, 0, " " * (width - 1), get_header_color())
        except curses.error:
            pass
        
        # File path and info - show scheme for remote files
        if self.file_path.is_remote():
            scheme = self.file_path.get_scheme().upper()
            file_info = f"{scheme}: {self.file_path.name}"
        else:
            file_info = f"File: {self.file_path.name}"
            
        if len(file_info) > width - 4:
            file_info = "..." + file_info[-(width-7):]
        
        try:
            self.stdscr.addstr(0, 2, file_info, get_header_color())
        except curses.error:
            pass
        
        # Controls line or isearch interface
        if self.isearch_mode:
            # Show isearch interface
            isearch_prompt = f"Isearch: {self.isearch_pattern}"
            if self.isearch_matches:
                match_info = f" ({self.isearch_match_index + 1}/{len(self.isearch_matches)})"
                isearch_prompt += match_info
            isearch_prompt += " [ESC:exit ↑↓:navigate]"
            
            try:
                self.stdscr.addstr(1, 2, isearch_prompt[:width-4], get_search_color())
            except curses.error:
                pass
        else:
            # Show normal controls
            controls = "q:quit ↑↓:scroll ←→:h-scroll PgUp/PgDn:page f:isearch n:numbers w:wrap s:syntax"
            
            try:
                # Center the controls or left-align if too long
                if len(controls) + 4 < width:
                    controls_x = (width - len(controls)) // 2
                else:
                    controls_x = 2
                self.stdscr.addstr(1, controls_x, controls[:width-4], get_status_color())
            except curses.error:
                pass
    
    def draw_status_bar(self):
        """Draw the status bar at the bottom of the viewer"""
        height, width = self.stdscr.getmaxyx()
        status_y = height - 1  # Bottom line
        
        # Clear status bar area with colored background
        try:
            self.stdscr.addstr(status_y, 0, " " * (width - 1), get_status_color())
        except curses.error:
            pass
        
        # Calculate current position info
        if self.wrap_lines:
            # When wrapping is enabled, show display line position
            display_lines = self.get_wrapped_lines()
            current_line = self.scroll_offset + 1  # 1-based display line number
            total_lines = len(display_lines)
            original_line = self.get_original_line_number(self.scroll_offset)
        else:
            # Normal mode - show original line numbers
            current_line = self.scroll_offset + 1  # 1-based line number
            total_lines = len(self.lines)
            original_line = current_line
        
        # Calculate scroll percentage
        if total_lines <= 1:
            scroll_percent = 100
        else:
            scroll_percent = min(100, int((current_line / total_lines) * 100))
        
        # Get file size
        try:
            file_size = self.file_path.stat().st_size
            if file_size < 1024:
                size_str = f"{file_size}B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f}K"
            elif file_size < 1024 * 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f}M"
            else:
                size_str = f"{file_size / (1024 * 1024 * 1024):.1f}G"
        except FileNotFoundError:
            print(f"Warning: File not found for size calculation: {self.file_path}")
            size_str = "---"
        except PermissionError:
            print(f"Warning: Permission denied for size calculation: {self.file_path}")
            size_str = "---"
        except (OSError, AttributeError) as e:
            print(f"Warning: Could not get file size for {self.file_path}: {e}")
            size_str = "---"
        except Exception as e:
            print(f"Warning: Unexpected error getting file size: {e}")
            size_str = "---"
        
        # Build status components
        if self.wrap_lines and total_lines != len(self.lines):
            # Show both display line and original line when wrapping
            position_info = f"Line {current_line}/{total_lines} (orig: {original_line}/{len(self.lines)}) ({scroll_percent}%)"
        else:
            position_info = f"Line {current_line}/{total_lines} ({scroll_percent}%)"
        
        file_info = f"{size_str}"
        
        # Add horizontal scroll info if applicable (only when not wrapping)
        if self.horizontal_offset > 0 and not self.wrap_lines:
            position_info += f" | Col {self.horizontal_offset + 1}"
        
        # Left side: position and file info
        left_status = f" {position_info} | {file_info} "
        
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
        
        if options:
            right_parts.extend(options)
        
        right_status = f" {' | '.join(right_parts)} "
        
        # Draw left status
        try:
            self.stdscr.addstr(status_y, 0, left_status, get_status_color())
        except curses.error:
            pass
        
        # Draw right status (right-aligned)
        try:
            right_x = max(len(left_status) + 2, width - len(right_status))
            if right_x < width:
                self.stdscr.addstr(status_y, right_x, right_status, get_status_color())
        except curses.error:
            pass
    
    def draw_content(self):
        """Draw the file content with syntax highlighting and wide character support"""
        start_y, start_x, display_height, display_width = self.get_display_dimensions()
        
        # Get the lines to display (wrapped or unwrapped)
        display_lines = self.get_wrapped_lines()
        
        # Calculate line number width if showing line numbers
        line_num_width = 0
        if self.show_line_numbers and self.lines:
            # Use original line count for line number width calculation
            line_num_width = len(str(len(self.lines))) + 2
        
        # Available width for content
        content_width = display_width - line_num_width
        
        # Get background color for filling empty areas
        bg_color_pair = get_background_color_pair()
        
        # Draw visible lines
        for i in range(display_height):
            line_index = self.scroll_offset + i
            y_pos = start_y + i
            
            # Fill the entire line with background color instead of using clrtoeol()
            try:
                self.stdscr.addstr(y_pos, start_x, ' ' * (display_width - 1), bg_color_pair)
                self.stdscr.move(y_pos, start_x)
            except curses.error:
                pass
            
            if line_index >= len(display_lines):
                continue
            
            # Draw line number if enabled
            x_pos = start_x
            if self.show_line_numbers:
                # For wrapped lines, we need to map back to original line numbers
                # For now, show the display line index + 1 (this could be improved)
                original_line_num = self.get_original_line_number(line_index) if self.wrap_lines else line_index + 1
                line_num = f"{original_line_num:>{line_num_width-1}} "
                try:
                    self.stdscr.addstr(y_pos, x_pos, line_num, get_line_number_color())
                except curses.error:
                    pass
                x_pos += line_num_width
            
            # Get the highlighted line (list of (text, color) tuples)
            highlighted_line = display_lines[line_index]
            
            # Check if this line is an isearch match (for unwrapped mode)
            original_line_index = self.get_original_line_number(line_index) - 1 if self.wrap_lines else line_index
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
                    for char in text:
                        char_width = get_display_width(char)
                        if skip_width + char_width > start_offset_cols:
                            visible_text = text[text.index(char):]
                            break
                        skip_width += char_width
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
                    try:
                        # Use search highlight color for matches
                        display_color = color
                        if is_current_match:
                            display_color = get_search_current_color()
                        elif is_search_match:
                            display_color = get_search_match_color()
                        
                        self.stdscr.addstr(y_pos, display_x, visible_text, display_color)
                        display_x += get_display_width(visible_text)
                    except curses.error:
                        pass
                
                current_display_col += text_display_width
                
                # Stop if we've filled the line
                if display_x - x_pos >= content_width:
                    break
    
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
        
        # This is a simplified implementation - for a more accurate mapping,
        # we would need to track which original line each wrapped line came from
        # For now, estimate based on average wrapping
        if not self.lines:
            return 1
        
        # Calculate approximate original line
        total_display_lines = len(self.get_wrapped_lines())
        if total_display_lines == 0:
            return 1
        
        ratio = len(self.lines) / total_display_lines
        estimated_line = int(display_line_index * ratio) + 1
        
        return min(estimated_line, len(self.lines))
    
    def handle_key(self, key) -> bool:
        """Handle key input. Returns True if viewer should continue, False to exit"""
        start_y, start_x, display_height, display_width = self.get_display_dimensions()
        
        # Handle isearch mode input first
        if self.isearch_mode:
            if self.handle_isearch_input(key):
                return True  # Isearch mode handled the key
        
        if key == ord('q') or key == ord('Q') or key == 27:  # q, Q, or ESC
            return False
            
        elif key == curses.KEY_UP:
            if self.scroll_offset > 0:
                self.scroll_offset -= 1
                
        elif key == curses.KEY_DOWN:
            # Use display lines for scrolling when wrapping is enabled
            display_lines = self.get_wrapped_lines()
            max_scroll = max(0, len(display_lines) - display_height)
            if self.scroll_offset < max_scroll:
                self.scroll_offset += 1
                
        elif key == curses.KEY_LEFT:
            # Use display width units for horizontal scrolling
            if self.horizontal_offset > 0:
                self.horizontal_offset = max(0, self.horizontal_offset - 1)
                
        elif key == curses.KEY_RIGHT:
            # Increment horizontal offset by display width units
            self.horizontal_offset += 1
            
        elif key == curses.KEY_PPAGE:  # Page Up
            self.scroll_offset = max(0, self.scroll_offset - display_height)
            
        elif key == curses.KEY_NPAGE:  # Page Down
            # Use display lines for page scrolling when wrapping is enabled
            display_lines = self.get_wrapped_lines()
            max_scroll = max(0, len(display_lines) - display_height)
            self.scroll_offset = min(max_scroll, self.scroll_offset + display_height)
            
        elif key == curses.KEY_HOME:
            self.scroll_offset = 0
            self.horizontal_offset = 0
            
        elif key == curses.KEY_END:
            # Use display lines for end positioning when wrapping is enabled
            display_lines = self.get_wrapped_lines()
            max_scroll = max(0, len(display_lines) - display_height)
            self.scroll_offset = max_scroll
            
        elif key == ord('n') or key == ord('N'):
            self.show_line_numbers = not self.show_line_numbers
            
        elif key == ord('w') or key == ord('W'):
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
                display_lines = self.get_wrapped_lines()
                max_scroll = max(0, len(display_lines) - display_height)
                self.scroll_offset = min(old_scroll, max_scroll)
            
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
        
        elif key == ord('f') or key == ord('F'):
            # Enter isearch mode
            self.enter_isearch_mode()
            
        return True
    
    def run(self):
        """Main viewer loop"""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.timeout(-1)  # Block indefinitely for input
        
        # Initial draw
        self.stdscr.clear()
        self.draw_header()
        self.draw_content()
        self.draw_status_bar()
        self.stdscr.refresh()
        
        while True:
            # Handle input - this will block until a key is pressed
            try:
                key = self.stdscr.getch()
                if not self.handle_key(key):
                    break
                    
                # Only redraw after handling input - no full clear to avoid flicker
                self.draw_header()
                self.draw_content()
                self.draw_status_bar()
                self.stdscr.refresh()
                
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
        print(f"Warning: File not found for text detection: {file_path}")
        return False
    except PermissionError:
        print(f"Warning: Permission denied for text detection: {file_path}")
        return False
    except OSError as e:
        print(f"Warning: Could not read file for text detection {file_path}: {e}")
        return False
    except Exception as e:
        print(f"Warning: Unexpected error in text file detection: {e}")
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
    except (OSError, IOError) as e:
        print(f"Error: Could not open text file {file_path}: {e}")
        return False
    except KeyboardInterrupt:
        # User interrupted - this is normal
        return True
    except Exception as e:
        print(f"Error: Unexpected error viewing text file {file_path}: {e}")
        return False