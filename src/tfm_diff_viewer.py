#!/usr/bin/env python3
"""
TFM Text Diff Viewer

A side-by-side text diff viewer component for TFM that shows differences
between two text files.
"""

import difflib
from tfm_path import Path
from typing import List, Tuple, Optional
from ttk import KeyEvent, KeyCode
from tfm_colors import *
from tfm_wide_char_utils import get_display_width, truncate_to_width
from tfm_scrollbar import draw_scrollbar, calculate_scrollbar_width


class DiffViewer:
    """Side-by-side text diff viewer"""
    
    def __init__(self, renderer, file1_path: Path, file2_path: Path):
        self.renderer = renderer
        self.file1_path = file1_path
        self.file2_path = file2_path
        self.file1_lines = []
        self.file2_lines = []
        self.diff_lines = []  # List of (line1, line2, status) tuples
        self.scroll_offset = 0
        self.horizontal_offset = 0
        
        # Load files and compute diff
        self.load_files()
        self.compute_diff()
    
    def load_files(self):
        """Load both text files"""
        self.file1_lines = self._load_file(self.file1_path)
        self.file2_lines = self._load_file(self.file2_path)
    
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
    
    def compute_diff(self):
        """Compute side-by-side diff using difflib"""
        # Use difflib's SequenceMatcher for line-by-line comparison
        matcher = difflib.SequenceMatcher(None, self.file1_lines, self.file2_lines)
        
        self.diff_lines = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Lines are the same
                for i in range(i2 - i1):
                    line1 = self.file1_lines[i1 + i] if i1 + i < len(self.file1_lines) else ""
                    line2 = self.file2_lines[j1 + i] if j1 + i < len(self.file2_lines) else ""
                    self.diff_lines.append((line1, line2, 'equal'))
            
            elif tag == 'replace':
                # Lines are different
                max_lines = max(i2 - i1, j2 - j1)
                for i in range(max_lines):
                    line1 = self.file1_lines[i1 + i] if i1 + i < i2 else ""
                    line2 = self.file2_lines[j1 + i] if j1 + i < j2 else ""
                    self.diff_lines.append((line1, line2, 'replace'))
            
            elif tag == 'delete':
                # Lines only in file1
                for i in range(i1, i2):
                    self.diff_lines.append((self.file1_lines[i], "", 'delete'))
            
            elif tag == 'insert':
                # Lines only in file2
                for i in range(j1, j2):
                    self.diff_lines.append(("", self.file2_lines[i], 'insert'))
    
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
        controls = "q/Enter:quit ↑↓:scroll ←→:h-scroll PgUp/PgDn:page"
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
        equal_lines = sum(1 for _, _, status in self.diff_lines if status == 'equal')
        changed_lines = sum(1 for _, _, status in self.diff_lines if status in ('replace', 'delete', 'insert'))
        
        current_line = self.scroll_offset + 1
        scroll_percent = min(100, int((current_line / max(1, total_lines)) * 100)) if total_lines > 0 else 100
        
        # Status text
        left_status = f" Line {current_line}/{total_lines} ({scroll_percent}%) "
        right_status = f" Equal: {equal_lines} | Changed: {changed_lines} "
        
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
        
        # Reserve space for scroll bar
        scroll_bar_width = calculate_scrollbar_width(len(self.diff_lines), display_height)
        content_width = pane_width - scroll_bar_width
        
        # Get background color
        bg_color_pair, bg_attrs = get_background_color_pair()
        
        # Draw visible lines
        for i in range(display_height):
            line_index = self.scroll_offset + i
            y_pos = start_y + i
            
            # Fill entire line with background
            self.renderer.draw_text(y_pos, start_x, ' ' * display_width, bg_color_pair, bg_attrs)
            
            if line_index >= len(self.diff_lines):
                continue
            
            line1, line2, status = self.diff_lines[line_index]
            
            # Determine colors based on status
            if status == 'equal':
                color_pair, attrs = get_color_with_attrs(COLOR_REGULAR_FILE)
            elif status == 'delete':
                color_pair, attrs = get_color_with_attrs(COLOR_ERROR)
            elif status == 'insert':
                color_pair, attrs = get_color_with_attrs(COLOR_DIRECTORIES)
            else:  # replace
                color_pair, attrs = get_color_with_attrs(COLOR_EXECUTABLES)
            
            # Apply horizontal scrolling and draw left pane
            if line1:
                visible_line1 = self._apply_horizontal_scroll(line1)
                visible_line1 = truncate_to_width(visible_line1, content_width, "")
                self.renderer.draw_text(y_pos, start_x, visible_line1, color_pair, attrs)
            
            # Draw separator
            header_color_pair, header_attrs = get_header_color()
            self.renderer.draw_text(y_pos, separator_x, "│", header_color_pair, header_attrs)
            
            # Apply horizontal scrolling and draw right pane
            if line2:
                visible_line2 = self._apply_horizontal_scroll(line2)
                visible_line2 = truncate_to_width(visible_line2, content_width, "")
                self.renderer.draw_text(y_pos, separator_x + 1, visible_line2, color_pair, attrs)
        
        # Draw scroll bar
        draw_scrollbar(self.renderer, start_y, display_width - 1, display_height,
                      len(self.diff_lines), self.scroll_offset)
    
    def _apply_horizontal_scroll(self, line: str) -> str:
        """Apply horizontal scrolling to a line"""
        if self.horizontal_offset == 0:
            return line
        
        # Skip characters based on horizontal offset
        current_width = 0
        start_index = 0
        
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
