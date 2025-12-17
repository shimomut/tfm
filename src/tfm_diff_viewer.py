#!/usr/bin/env python3
"""
TFM Text Diff Viewer

A side-by-side text diff viewer component for TFM that shows differences
between two text files with syntax highlighting support.
"""

import difflib
from tfm_path import Path
from typing import List, Tuple, Optional
from ttk import KeyEvent, KeyCode
from tfm_colors import *
from tfm_wide_char_utils import get_display_width, truncate_to_width
from tfm_scrollbar import draw_scrollbar, calculate_scrollbar_width

# Try to import pygments for syntax highlighting
try:
    from pygments import lex
    from pygments.lexers import get_lexer_for_filename, get_lexer_by_name, TextLexer
    from pygments.token import Token
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class DiffViewer:
    """Side-by-side text diff viewer"""
    
    def __init__(self, renderer, file1_path: Path, file2_path: Path):
        self.renderer = renderer
        self.file1_path = file1_path
        self.file2_path = file2_path
        self.file1_lines = []
        self.file2_lines = []
        self.file1_original_lines = []  # Original lines with tabs preserved
        self.file2_original_lines = []  # Original lines with tabs preserved
        self.file1_highlighted = []  # List of lists of (text, color) tuples for syntax highlighting
        self.file2_highlighted = []  # List of lists of (text, color) tuples for syntax highlighting
        self.diff_lines = []  # List of (line1, line2, status, line_num1, line_num2) tuples
        self.scroll_offset = 0
        self.horizontal_offset = 0
        self.line_number_width = 5  # Width for line numbers (e.g., "  123 ")
        self.show_line_numbers = True
        self.syntax_highlighting = PYGMENTS_AVAILABLE
        self.tab_width = 4  # Number of spaces per tab
        self.diff_indices = []  # List of line indices where differences occur
        self.current_diff_index = -1  # Index into diff_indices (-1 means no focus)
        self.ignore_whitespace = False  # Whether to ignore whitespace when comparing
        
        # Load files and compute diff
        self.load_files()
        self.compute_diff()
    
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
        self.file1_lines = [self.expand_tabs(line) for line in self.file1_original_lines]
        self.file2_lines = [self.expand_tabs(line) for line in self.file2_original_lines]
        
        # Apply syntax highlighting if enabled
        if self.syntax_highlighting:
            self.file1_highlighted = self._apply_syntax_highlighting(self.file1_path, self.file1_lines)
            self.file2_highlighted = self._apply_syntax_highlighting(self.file2_path, self.file2_lines)
        else:
            # Create plain highlighted lines (no colors)
            self.file1_highlighted = [[(line, COLOR_REGULAR_FILE)] for line in self.file1_lines]
            self.file2_highlighted = [[(line, COLOR_REGULAR_FILE)] for line in self.file2_lines]
        
        # Recompute diff with new tab expansion
        self.compute_diff()
    
    def load_files(self):
        """Load both text files"""
        self.file1_original_lines = self._load_file(self.file1_path)
        self.file2_original_lines = self._load_file(self.file2_path)
        
        # Expand tabs for display
        self.refresh_tab_expansion()
    
    def _load_file(self, file_path: Path) -> List[str]:
        """Load a single text file"""
        try:
            # First check if file contains null bytes (binary indicator)
            try:
                chunk = file_path.read_bytes()
                # Check first 1024 bytes for null bytes
                check_size = min(1024, len(chunk))
                if b'\x00' in chunk[:check_size]:
                    return ["[Binary file - cannot display as text]"]
            except (FileNotFoundError, PermissionError, OSError):
                raise
            
            # Try to decode as text with different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
                except (FileNotFoundError, OSError):
                    raise
            
            if content is None:
                # Last resort - decode as latin-1 with error replacement
                content = chunk.decode('latin-1', errors='replace')
            
            return content.splitlines()
                
        except FileNotFoundError:
            return [f"File not found: {file_path}"]
        except PermissionError:
            return [f"Permission denied: {file_path}"]
        except OSError as e:
            return [f"Error reading file: {e}"]
        except Exception as e:
            return [f"Unexpected error: {e}"]
    
    def _apply_syntax_highlighting(self, file_path: Path, lines: List[str]) -> List[List[Tuple[str, int]]]:
        """Apply syntax highlighting to file lines using pygments"""
        if not PYGMENTS_AVAILABLE or not lines:
            return [[(line, COLOR_REGULAR_FILE)] for line in lines]
        
        try:
            # Get appropriate lexer for the file
            lexer = None
            
            # Try to get lexer by filename
            try:
                lexer = get_lexer_for_filename(file_path.name)
            except ClassNotFound:
                # Try by file extension
                ext = file_path.suffix.lower()
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
            content = '\n'.join(lines)
            tokens = list(lexer.get_tokens(content))
            
            # Convert tokens to highlighted lines
            return self._tokens_to_highlighted_lines(tokens)
            
        except Exception as e:
            # If highlighting fails, create plain highlighted lines
            print(f"Warning: Syntax highlighting failed: {e}")
            return [[(line, COLOR_REGULAR_FILE)] for line in lines]
    
    def _tokens_to_highlighted_lines(self, tokens) -> List[List[Tuple[str, int]]]:
        """Convert pygments tokens to lines of (text, color) tuples"""
        highlighted_lines = []
        current_line = []
        
        for token_type, text in tokens:
            # Get the appropriate color for this token type
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
    
    def _strip_whitespace(self, line: str) -> str:
        """
        Remove all whitespace characters (spaces and tabs) from a line.
        
        Args:
            line: Line of text
            
        Returns:
            Line with all spaces and tabs removed
        """
        return line.replace(' ', '').replace('\t', '')
    
    def _compute_char_diff(self, line1: str, line2: str) -> Tuple[List[Tuple[str, bool]], List[Tuple[str, bool]]]:
        """
        Compute character-level differences between two lines.
        
        Returns:
            Two lists of (text, is_different) tuples for line1 and line2
        """
        if not line1 or not line2:
            return [(line1, False)], [(line2, False)]
        
        # Prepare lines for comparison
        compare_line1 = self._strip_whitespace(line1) if self.ignore_whitespace else line1
        compare_line2 = self._strip_whitespace(line2) if self.ignore_whitespace else line2
        
        # Use SequenceMatcher for character-level comparison
        matcher = difflib.SequenceMatcher(None, compare_line1, compare_line2)
        
        result1 = []
        result2 = []
        
        if self.ignore_whitespace:
            # When ignoring whitespace, we need to map back to original positions
            # Build mappings from stripped position to original position
            map1 = []  # List of original indices for non-whitespace chars in line1
            map2 = []  # List of original indices for non-whitespace chars in line2
            
            for i, char in enumerate(line1):
                if char not in (' ', '\t'):
                    map1.append(i)
            
            for i, char in enumerate(line2):
                if char not in (' ', '\t'):
                    map2.append(i)
            
            # Track position in original lines
            pos1 = 0
            pos2 = 0
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                # Get original positions
                orig_start1 = map1[i1] if i1 < len(map1) else len(line1)
                orig_end1 = map1[i2 - 1] + 1 if i2 > 0 and i2 - 1 < len(map1) else len(line1)
                orig_start2 = map2[j1] if j1 < len(map2) else len(line2)
                orig_end2 = map2[j2 - 1] + 1 if j2 > 0 and j2 - 1 < len(map2) else len(line2)
                
                # Add any whitespace before this segment
                if pos1 < orig_start1:
                    result1.append((line1[pos1:orig_start1], False))
                if pos2 < orig_start2:
                    result2.append((line2[pos2:orig_start2], False))
                
                if tag == 'equal':
                    # Characters are the same
                    result1.append((line1[orig_start1:orig_end1], False))
                    result2.append((line2[orig_start2:orig_end2], False))
                elif tag == 'replace':
                    # Characters are different
                    result1.append((line1[orig_start1:orig_end1], True))
                    result2.append((line2[orig_start2:orig_end2], True))
                elif tag == 'delete':
                    # Characters only in line1
                    result1.append((line1[orig_start1:orig_end1], True))
                elif tag == 'insert':
                    # Characters only in line2
                    result2.append((line2[orig_start2:orig_end2], True))
                
                pos1 = orig_end1
                pos2 = orig_end2
            
            # Add any trailing whitespace
            if pos1 < len(line1):
                result1.append((line1[pos1:], False))
            if pos2 < len(line2):
                result2.append((line2[pos2:], False))
        else:
            # Normal comparison without whitespace stripping
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    # Characters are the same
                    result1.append((line1[i1:i2], False))
                    result2.append((line2[j1:j2], False))
                elif tag == 'replace':
                    # Characters are different
                    result1.append((line1[i1:i2], True))
                    result2.append((line2[j1:j2], True))
                elif tag == 'delete':
                    # Characters only in line1
                    result1.append((line1[i1:i2], True))
                elif tag == 'insert':
                    # Characters only in line2
                    result2.append((line2[j1:j2], True))
        
        return result1, result2
    
    def compute_diff(self):
        """Compute side-by-side diff using difflib"""
        # Prepare lines for comparison (strip whitespace if mode is enabled)
        compare_lines1 = [self._strip_whitespace(line) for line in self.file1_lines] if self.ignore_whitespace else self.file1_lines
        compare_lines2 = [self._strip_whitespace(line) for line in self.file2_lines] if self.ignore_whitespace else self.file2_lines
        
        # Use difflib's SequenceMatcher for line-by-line comparison
        matcher = difflib.SequenceMatcher(None, compare_lines1, compare_lines2)
        
        self.diff_lines = []
        self.diff_indices = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Lines are the same
                for i in range(i2 - i1):
                    line1 = self.file1_lines[i1 + i] if i1 + i < len(self.file1_lines) else ""
                    line2 = self.file2_lines[j1 + i] if j1 + i < len(self.file2_lines) else ""
                    line_num1 = i1 + i + 1
                    line_num2 = j1 + i + 1
                    self.diff_lines.append((line1, line2, 'equal', line_num1, line_num2, None, None))
            
            elif tag == 'replace':
                # Lines are different - compute character-level diff
                max_lines = max(i2 - i1, j2 - j1)
                start_index = len(self.diff_lines)
                for i in range(max_lines):
                    line1 = self.file1_lines[i1 + i] if i1 + i < i2 else ""
                    line2 = self.file2_lines[j1 + i] if j1 + i < j2 else ""
                    line_num1 = (i1 + i + 1) if i1 + i < i2 else None
                    line_num2 = (j1 + i + 1) if j1 + i < j2 else None
                    
                    # Compute character-level differences for replace operations
                    char_diff1, char_diff2 = None, None
                    if line1 and line2:
                        char_diff1, char_diff2 = self._compute_char_diff(line1, line2)
                    
                    self.diff_lines.append((line1, line2, 'replace', line_num1, line_num2, char_diff1, char_diff2))
                # Record the first line of this difference block
                self.diff_indices.append(start_index)
            
            elif tag == 'delete':
                # Lines only in file1
                start_index = len(self.diff_lines)
                for i in range(i1, i2):
                    line_num1 = i + 1
                    self.diff_lines.append((self.file1_lines[i], "", 'delete', line_num1, None, None, None))
                # Record the first line of this difference block
                self.diff_indices.append(start_index)
            
            elif tag == 'insert':
                # Lines only in file2
                start_index = len(self.diff_lines)
                for i in range(j1, j2):
                    line_num2 = i + 1
                    self.diff_lines.append(("", self.file2_lines[i], 'insert', None, line_num2, None, None))
                # Record the first line of this difference block
                self.diff_indices.append(start_index)
        
        # Initialize current diff index if we have differences
        if self.diff_indices and self.current_diff_index == -1:
            self.current_diff_index = 0
            self.scroll_offset = self.diff_indices[0]
    
    def get_display_dimensions(self) -> Tuple[int, int, int, int]:
        """Get the dimensions for the diff display area"""
        try:
            height, width = self.renderer.get_dimensions()
            
            if not isinstance(height, int) or not isinstance(width, int):
                height, width = 24, 80
            
            # Reserve space for header (2 lines) and status bar (1 line)
            start_y = 2
            display_height = max(1, height - 3)
            start_x = 0
            display_width = max(1, width)
            
            return start_y, start_x, display_height, display_width
            
        except Exception as e:
            print(f"Error in get_display_dimensions: {e}")
            return 2, 0, 21, 80
    
    def draw_header(self):
        """Draw the viewer header"""
        height, width = self.renderer.get_dimensions()
        
        header_color_pair, header_attrs = get_header_color()
        
        # Clear header area
        self.renderer.draw_text(0, 0, " " * width, header_color_pair, header_attrs)
        self.renderer.draw_text(1, 0, " " * width, header_color_pair, header_attrs)
        
        # File names
        file1_display = self.file1_path.get_display_title()
        file2_display = self.file2_path.get_display_title()
        
        # Calculate column width for each file
        pane_width = width // 2
        
        # Truncate file names if needed
        if len(file1_display) > pane_width - 4:
            file1_display = "..." + file1_display[-(pane_width - 7):]
        if len(file2_display) > pane_width - 4:
            file2_display = "..." + file2_display[-(pane_width - 7):]
        
        # Draw file names
        self.renderer.draw_text(0, 2, file1_display, header_color_pair, header_attrs)
        self.renderer.draw_text(0, pane_width + 2, file2_display, header_color_pair, header_attrs)
        
        # Draw separator
        separator_x = pane_width
        for y in range(height - 1):
            self.renderer.draw_text(y, separator_x, "│", header_color_pair, header_attrs)
        
        # Controls
        controls = "q/Enter:quit ↑↓:scroll ←→:h-scroll n/p:next/prev diff PgUp/PgDn:page #:line# s:syntax t:tab w:whitespace"
        status_color_pair, status_attrs = get_status_color()
        
        if len(controls) + 4 < width:
            controls_x = (width - len(controls)) // 2
        else:
            controls_x = 2
        
        self.renderer.draw_text(1, controls_x, controls[:width - 4], status_color_pair, status_attrs)
    
    def draw_status_bar(self):
        """Draw the status bar"""
        height, width = self.renderer.get_dimensions()
        status_y = height - 1
        
        status_color_pair, status_attrs = get_status_color()
        
        # Clear status bar
        self.renderer.draw_text(status_y, 0, " " * width, status_color_pair, status_attrs)
        
        # Calculate statistics
        total_lines = len(self.diff_lines)
        equal_lines = sum(1 for item in self.diff_lines if item[2] == 'equal')
        changed_lines = sum(1 for item in self.diff_lines if item[2] in ('replace', 'delete', 'insert'))
        
        current_line = self.scroll_offset + 1
        scroll_percent = min(100, int((current_line / max(1, total_lines)) * 100)) if total_lines > 0 else 100
        
        # Status text with diff navigation info
        diff_nav_info = ""
        if self.diff_indices and self.current_diff_index >= 0:
            diff_nav_info = f" Diff {self.current_diff_index + 1}/{len(self.diff_indices)} "
        
        left_status = f" Line {current_line}/{total_lines} ({scroll_percent}%){diff_nav_info}"
        
        # Build right status with options
        right_parts = []
        right_parts.append(f"Equal: {equal_lines}")
        right_parts.append(f"Changed: {changed_lines}")
        
        # Show active options
        options = []
        if self.show_line_numbers:
            options.append("NUM")
        if PYGMENTS_AVAILABLE and self.syntax_highlighting:
            options.append("SYNTAX")
        options.append(f"TAB:{self.tab_width}")
        if self.ignore_whitespace:
            options.append("IGNORE-WS")
        
        if options:
            right_parts.extend(options)
        
        right_status = f" {' | '.join(right_parts)} "
        
        self.renderer.draw_text(status_y, 0, left_status, status_color_pair, status_attrs)
        
        right_x = max(len(left_status) + 2, width - len(right_status))
        if right_x < width:
            self.renderer.draw_text(status_y, right_x, right_status, status_color_pair, status_attrs)
    
    def draw_content(self):
        """Draw the side-by-side diff content"""
        start_y, start_x, display_height, display_width = self.get_display_dimensions()
        
        # Calculate pane width (split screen in half with separator)
        pane_width = (display_width - 1) // 2
        separator_x = pane_width
        
        # Calculate line number width if showing line numbers
        line_num_width = self.line_number_width if self.show_line_numbers else 0
        
        # Reserve space for scroll bar and line numbers
        scroll_bar_width = calculate_scrollbar_width(len(self.diff_lines), display_height)
        content_width = pane_width - scroll_bar_width - line_num_width
        
        # Get background color
        bg_color_pair, bg_attrs = get_background_color_pair()
        
        # Get line number color
        line_num_color_pair, line_num_attrs = get_line_number_color()
        
        # Draw visible lines
        for i in range(display_height):
            line_index = self.scroll_offset + i
            y_pos = start_y + i
            
            # Fill entire line with background
            self.renderer.draw_text(y_pos, start_x, ' ' * display_width, bg_color_pair, bg_attrs)
            
            if line_index >= len(self.diff_lines):
                continue
            
            diff_item = self.diff_lines[line_index]
            line1, line2, status, line_num1, line_num2 = diff_item[0], diff_item[1], diff_item[2], diff_item[3], diff_item[4]
            char_diff1, char_diff2 = diff_item[5] if len(diff_item) > 5 else None, diff_item[6] if len(diff_item) > 6 else None
            
            # Check if this line is part of the focused difference
            # Only focus lines with actual content (not dummy alignment lines)
            is_focused = False
            has_real_content = line1 or line2  # At least one side has content
            if has_real_content and self.current_diff_index >= 0 and self.current_diff_index < len(self.diff_indices):
                focused_start = self.diff_indices[self.current_diff_index]
                # Find the end of this difference block
                focused_end = focused_start
                while focused_end < len(self.diff_lines) and self.diff_lines[focused_end][2] != 'equal':
                    focused_end += 1
                is_focused = focused_start <= line_index < focused_end
            
            # Determine colors based on status (with background colors)
            # Dummy lines (blank alignment lines) always get gray background, even when focused
            if is_focused:
                # Use focused color for lines with real content
                color_pair, attrs = get_color_with_attrs(COLOR_DIFF_FOCUSED)
                # Blank lines (dummy lines) always get gray background, even when focused
                blank_color_pair, blank_attrs = get_color_with_attrs(COLOR_DIFF_BLANK)
            elif status == 'equal':
                color_pair, attrs = get_color_with_attrs(COLOR_REGULAR_FILE)
                blank_color_pair, blank_attrs = color_pair, attrs
            elif status == 'delete' or status == 'insert':
                # Lines only in one side (delete/insert) - brown background
                color_pair, attrs = get_color_with_attrs(COLOR_DIFF_ONLY_ONE_SIDE)
                # Blank lines (dummy lines) get gray background
                blank_color_pair, blank_attrs = get_color_with_attrs(COLOR_DIFF_BLANK)
            else:  # replace
                # Different lines (both sides have content but different) - yellow/brown background
                color_pair, attrs = get_color_with_attrs(COLOR_DIFF_CHANGE)
                # Blank lines (dummy lines) get gray background
                blank_color_pair, blank_attrs = get_color_with_attrs(COLOR_DIFF_BLANK)
            
            # Get character-level change color
            char_change_color_pair, char_change_attrs = get_color_with_attrs(COLOR_DIFF_CHAR_CHANGE)
            
            # Draw left pane line number if enabled
            content_start_x = start_x
            if self.show_line_numbers:
                line_num_str1 = f"{line_num1:4d} " if line_num1 is not None else "     "
                self.renderer.draw_text(y_pos, start_x, line_num_str1, line_num_color_pair, line_num_attrs)
                content_start_x = start_x + line_num_width
            
            # Apply horizontal scrolling and draw left pane content
            if line1:
                # Get syntax-highlighted version if available
                highlighted_line1 = None
                if line_num1 is not None and line_num1 - 1 < len(self.file1_highlighted):
                    highlighted_line1 = self.file1_highlighted[line_num1 - 1]
                
                if char_diff1 and status == 'replace':
                    # Draw with character-level highlighting
                    self._draw_line_with_char_diff(y_pos, content_start_x, char_diff1, content_width, 
                                                   color_pair, attrs, char_change_color_pair, char_change_attrs,
                                                   highlighted_line1)
                elif self.syntax_highlighting and highlighted_line1:
                    # Draw with syntax highlighting (only when enabled)
                    # Use syntax colors only for equal lines, diff background for others
                    self._draw_highlighted_line(y_pos, content_start_x, highlighted_line1, content_width,
                                               color_pair, attrs, use_syntax_colors=(status == 'equal'))
                else:
                    # No syntax highlighting or no highlighted line available
                    # Apply horizontal scrolling manually
                    visible_line1 = self._apply_horizontal_scroll(line1)
                    visible_line1 = truncate_to_width(visible_line1, content_width, "")
                    self.renderer.draw_text(y_pos, content_start_x, visible_line1, color_pair, attrs)
            else:
                # Draw blank line with gray background for alignment (dummy line)
                self.renderer.draw_text(y_pos, content_start_x, ' ' * content_width, blank_color_pair, blank_attrs)
            
            # Draw separator
            header_color_pair, header_attrs = get_header_color()
            self.renderer.draw_text(y_pos, separator_x, "│", header_color_pair, header_attrs)
            
            # Draw right pane line number if enabled
            content_start_x2 = separator_x + 1
            if self.show_line_numbers:
                line_num_str2 = f"{line_num2:4d} " if line_num2 is not None else "     "
                self.renderer.draw_text(y_pos, separator_x + 1, line_num_str2, line_num_color_pair, line_num_attrs)
                content_start_x2 = separator_x + 1 + line_num_width
            
            # Apply horizontal scrolling and draw right pane content
            if line2:
                # Get syntax-highlighted version if available
                highlighted_line2 = None
                if line_num2 is not None and line_num2 - 1 < len(self.file2_highlighted):
                    highlighted_line2 = self.file2_highlighted[line_num2 - 1]
                
                if char_diff2 and status == 'replace':
                    # Draw with character-level highlighting
                    self._draw_line_with_char_diff(y_pos, content_start_x2, char_diff2, content_width,
                                                   color_pair, attrs, char_change_color_pair, char_change_attrs,
                                                   highlighted_line2)
                elif self.syntax_highlighting and highlighted_line2:
                    # Draw with syntax highlighting (only when enabled)
                    # Use syntax colors only for equal lines, diff background for others
                    self._draw_highlighted_line(y_pos, content_start_x2, highlighted_line2, content_width,
                                               color_pair, attrs, use_syntax_colors=(status == 'equal'))
                else:
                    # No syntax highlighting or no highlighted line available
                    # Apply horizontal scrolling manually
                    visible_line2 = self._apply_horizontal_scroll(line2)
                    visible_line2 = truncate_to_width(visible_line2, content_width, "")
                    self.renderer.draw_text(y_pos, content_start_x2, visible_line2, color_pair, attrs)
            else:
                # Draw blank line with gray background for alignment (dummy line)
                self.renderer.draw_text(y_pos, content_start_x2, ' ' * content_width, blank_color_pair, blank_attrs)
        
        # Draw scroll bar
        draw_scrollbar(self.renderer, start_y, display_width - 1, display_height,
                      len(self.diff_lines), self.scroll_offset)
    
    def _draw_highlighted_line(self, y_pos: int, start_x: int, highlighted_line: List[Tuple[str, int]],
                              max_width: int, bg_color: int, bg_attrs: int, use_syntax_colors: bool = False):
        """
        Draw a syntax-highlighted line with diff background color.
        
        Args:
            y_pos: Y position to draw at
            start_x: Starting X position
            highlighted_line: List of (text, syntax_color) tuples
            max_width: Maximum width to draw
            bg_color: Background color pair for the diff status
            bg_attrs: Background attributes for the diff status
            use_syntax_colors: If True, use syntax colors (for equal lines); if False, use bg_color (for diff lines)
        """
        current_x = start_x
        remaining_width = max_width
        
        # Track cumulative width for horizontal scrolling
        cumulative_width = 0
        offset_applied = False
        
        for text, syntax_color in highlighted_line:
            if remaining_width <= 0:
                break
            
            # Calculate width of this segment
            segment_width = sum(get_display_width(char) for char in text)
            
            # Apply horizontal scrolling only once at the beginning
            if not offset_applied and self.horizontal_offset > 0:
                # Check if we need to skip this entire segment
                if cumulative_width + segment_width <= self.horizontal_offset:
                    cumulative_width += segment_width
                    continue
                
                # Partially skip this segment
                if cumulative_width < self.horizontal_offset:
                    skip_amount = self.horizontal_offset - cumulative_width
                    skip_chars = 0
                    skip_width = 0
                    
                    for char in text:
                        char_width = get_display_width(char)
                        if skip_width + char_width > skip_amount:
                            break
                        skip_width += char_width
                        skip_chars += 1
                    
                    text = text[skip_chars:]
                    cumulative_width = self.horizontal_offset
                    offset_applied = True
                else:
                    offset_applied = True
            
            cumulative_width += sum(get_display_width(char) for char in text)
            
            if not text:
                continue
            
            # Truncate to fit remaining width
            visible_text = truncate_to_width(text, remaining_width, "")
            if not visible_text:
                break
            
            # Choose color based on whether this is an equal line or a diff line
            if use_syntax_colors:
                # For equal lines, use syntax highlighting colors
                draw_color = syntax_color
            else:
                # For diff lines (delete/insert/change/focused), use diff background color
                # to preserve diff highlighting (syntax color would override the background)
                draw_color = bg_color
            
            self.renderer.draw_text(y_pos, current_x, visible_text, draw_color, bg_attrs)
            
            # Update position
            text_width = get_display_width(visible_text)
            current_x += text_width
            remaining_width -= text_width
    
    def _draw_line_with_char_diff(self, y_pos: int, start_x: int, char_diff: List[Tuple[str, bool]], 
                                   max_width: int, normal_color: int, normal_attrs: int,
                                   highlight_color: int, highlight_attrs: int,
                                   highlighted_line: Optional[List[Tuple[str, int]]] = None):
        """
        Draw a line with character-level diff highlighting.
        
        Args:
            y_pos: Y position to draw at
            start_x: Starting X position
            char_diff: List of (text, is_different) tuples
            max_width: Maximum width to draw
            normal_color: Color pair for normal text
            normal_attrs: Attributes for normal text
            highlight_color: Color pair for highlighted (different) text
            highlight_attrs: Attributes for highlighted text
            highlighted_line: Optional syntax-highlighted line (list of (text, color) tuples)
        """
        # If we have syntax highlighting, we need to merge it with char diff
        # For now, character-level diff takes precedence over syntax highlighting
        # This is a simplified approach
        
        current_x = start_x
        remaining_width = max_width
        
        # Track cumulative width for horizontal scrolling
        cumulative_width = 0
        offset_applied = False
        
        for text, is_different in char_diff:
            if remaining_width <= 0:
                break
            
            # Calculate width of this segment
            segment_width = sum(get_display_width(char) for char in text)
            
            # Apply horizontal scrolling only once at the beginning
            if not offset_applied and self.horizontal_offset > 0:
                # Check if we need to skip this entire segment
                if cumulative_width + segment_width <= self.horizontal_offset:
                    cumulative_width += segment_width
                    continue
                
                # Partially skip this segment
                if cumulative_width < self.horizontal_offset:
                    skip_amount = self.horizontal_offset - cumulative_width
                    skip_chars = 0
                    skip_width = 0
                    
                    for char in text:
                        char_width = get_display_width(char)
                        if skip_width + char_width > skip_amount:
                            break
                        skip_width += char_width
                        skip_chars += 1
                    
                    text = text[skip_chars:]
                    cumulative_width = self.horizontal_offset
                    offset_applied = True
                else:
                    offset_applied = True
            
            cumulative_width += sum(get_display_width(char) for char in text)
            
            if not text:
                continue
            
            # Truncate to fit remaining width
            visible_text = truncate_to_width(text, remaining_width, "")
            if not visible_text:
                break
            
            # Choose color based on whether this segment is different
            color_pair = highlight_color if is_different else normal_color
            attrs = highlight_attrs if is_different else normal_attrs
            
            # Draw the text segment
            self.renderer.draw_text(y_pos, current_x, visible_text, color_pair, attrs)
            
            # Update position
            text_width = get_display_width(visible_text)
            current_x += text_width
            remaining_width -= text_width
    
    def _apply_horizontal_scroll(self, line: str) -> str:
        """Apply horizontal scrolling to a line"""
        if self.horizontal_offset == 0:
            return line
        
        # Skip characters based on horizontal offset
        current_width = 0
        start_index = len(line)  # Default to end of line if we scroll past everything
        
        for i, char in enumerate(line):
            char_width = get_display_width(char)
            if current_width + char_width > self.horizontal_offset:
                start_index = i
                break
            current_width += char_width
        
        return line[start_index:]
    
    def handle_key(self, event: KeyEvent) -> bool:
        """Handle key input. Returns True if viewer should continue, False to exit"""
        if event is None:
            return True
        
        start_y, start_x, display_height, display_width = self.get_display_dimensions()
        
        # Check for character-based commands
        if event.char:
            char_lower = event.char.lower()
            if char_lower == 'q':
                return False
            elif char_lower == 'n':
                # Jump to next difference
                if self.diff_indices:
                    if self.current_diff_index < len(self.diff_indices) - 1:
                        self.current_diff_index += 1
                        self.scroll_offset = self.diff_indices[self.current_diff_index]
            elif char_lower == 'p':
                # Jump to previous difference
                if self.diff_indices:
                    if self.current_diff_index > 0:
                        self.current_diff_index -= 1
                        self.scroll_offset = self.diff_indices[self.current_diff_index]
            elif char_lower == '#':
                # Toggle line numbers
                self.show_line_numbers = not self.show_line_numbers
            elif char_lower == 's':
                # Toggle syntax highlighting
                if PYGMENTS_AVAILABLE:
                    self.syntax_highlighting = not self.syntax_highlighting
                    # Re-apply highlighting
                    if self.syntax_highlighting:
                        self.file1_highlighted = self._apply_syntax_highlighting(self.file1_path, self.file1_lines)
                        self.file2_highlighted = self._apply_syntax_highlighting(self.file2_path, self.file2_lines)
                    else:
                        # Create plain highlighted lines (no colors)
                        self.file1_highlighted = [[(line, COLOR_REGULAR_FILE)] for line in self.file1_lines]
                        self.file2_highlighted = [[(line, COLOR_REGULAR_FILE)] for line in self.file2_lines]
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
            elif char_lower == 'w':
                # Toggle whitespace ignore mode
                self.ignore_whitespace = not self.ignore_whitespace
                # Recompute diff with new whitespace mode
                self.compute_diff()
        
        # Check for special keys
        if event.key_code == KeyCode.ESCAPE:
            return False
        elif event.key_code == KeyCode.ENTER:
            return False
        elif event.key_code == KeyCode.UP:
            if self.scroll_offset > 0:
                self.scroll_offset -= 1
        elif event.key_code == KeyCode.DOWN:
            max_scroll = max(0, len(self.diff_lines) - display_height)
            if self.scroll_offset < max_scroll:
                self.scroll_offset += 1
        elif event.key_code == KeyCode.LEFT:
            if self.horizontal_offset > 0:
                self.horizontal_offset = max(0, self.horizontal_offset - 1)
        elif event.key_code == KeyCode.RIGHT:
            self.horizontal_offset += 1
        elif event.key_code == KeyCode.PAGE_UP:
            self.scroll_offset = max(0, self.scroll_offset - display_height)
        elif event.key_code == KeyCode.PAGE_DOWN:
            max_scroll = max(0, len(self.diff_lines) - display_height)
            self.scroll_offset = min(max_scroll, self.scroll_offset + display_height)
        elif event.key_code == KeyCode.HOME:
            self.scroll_offset = 0
            self.horizontal_offset = 0
        elif event.key_code == KeyCode.END:
            max_scroll = max(0, len(self.diff_lines) - display_height)
            self.scroll_offset = max_scroll
        
        return True
    
    def run(self):
        """Main viewer loop"""
        self.renderer.set_cursor_visibility(False)
        
        # Initial draw
        self.renderer.clear()
        self.draw_header()
        self.draw_content()
        self.draw_status_bar()
        self.renderer.refresh()
        
        while True:
            try:
                event = self.renderer.get_input()
                if not self.handle_key(event):
                    break
                
                self.draw_header()
                self.draw_content()
                self.draw_status_bar()
                self.renderer.refresh()
                
            except KeyboardInterrupt:
                break


def view_diff(renderer, file1_path: Path, file2_path: Path) -> bool:
    """
    View differences between two text files
    
    Args:
        renderer: TTK renderer object
        file1_path: Path to the first file
        file2_path: Path to the second file
        
    Returns:
        True if diff was viewed successfully, False otherwise
    """
    if not file1_path.exists() or not file1_path.is_file():
        print(f"Error: First file does not exist or is not a file: {file1_path}")
        return False
    
    if not file2_path.exists() or not file2_path.is_file():
        print(f"Error: Second file does not exist or is not a file: {file2_path}")
        return False
    
    try:
        viewer = DiffViewer(renderer, file1_path, file2_path)
        viewer.run()
        return True
    except (OSError, IOError) as e:
        print(f"Error: Could not open files for diff: {e}")
        return False
    except KeyboardInterrupt:
        return True
    except Exception as e:
        print(f"Error: Unexpected error viewing diff: {e}")
        return False
