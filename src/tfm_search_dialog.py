#!/usr/bin/env python3
"""
TUI File Manager - Search Dialog Component
Provides file and content search functionality with threading support
"""

import curses
import fnmatch
import re
import threading
import time
from pathlib import Path
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_const import KEY_ENTER_1, KEY_ENTER_2
from tfm_colors import get_status_color


class SearchProgressAnimator:
    """Handles animated progress indicators for search operations"""
    
    def __init__(self, config):
        self.config = config
        self.animation_pattern = getattr(config, 'SEARCH_ANIMATION_PATTERN', 'spinner')
        self.animation_speed = getattr(config, 'SEARCH_ANIMATION_SPEED', 0.2)
        
        # Animation patterns
        self.patterns = {
            'spinner': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
            'dots': ['⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈'],
            'progress': ['▏', '▎', '▍', '▌', '▋', '▊', '▉', '█']
        }
        
        # Animation state
        self.frame_index = 0
        self.last_update_time = 0
        
    def get_current_frame(self):
        """Get the current animation frame"""
        current_time = time.time()
        
        # Update frame if enough time has passed
        if current_time - self.last_update_time >= self.animation_speed:
            pattern = self.patterns.get(self.animation_pattern, self.patterns['spinner'])
            self.frame_index = (self.frame_index + 1) % len(pattern)
            self.last_update_time = current_time
        
        pattern = self.patterns.get(self.animation_pattern, self.patterns['spinner'])
        return pattern[self.frame_index]
    
    def reset(self):
        """Reset animation to first frame"""
        self.frame_index = 0
        self.last_update_time = 0
    
    def get_progress_indicator(self, result_count, is_searching):
        """Get formatted progress indicator text"""
        if not is_searching:
            return ""
        
        frame = self.get_current_frame()
        
        if self.animation_pattern == 'progress':
            # For progress pattern, show a progress bar effect
            progress_length = 8
            filled = (self.frame_index * progress_length) // len(self.patterns['progress'])
            bar = '█' * filled + '░' * (progress_length - filled)
            return f" [{bar}] "
        else:
            # For spinner and dots, show rotating indicator
            return f" {frame} "


class SearchDialog:
    """Search dialog component for filename and content search with threading support"""
    
    def __init__(self, config):
        self.config = config
        
        # Search dialog state
        self.mode = False
        self.search_type = 'filename'  # 'filename' or 'content'
        self.pattern_editor = SingleLineTextEdit()  # Pattern editor for search dialog
        self.results = []  # List of search results
        self.selected = 0  # Index of currently selected result
        self.scroll = 0  # Scroll offset for results
        self.searching = False  # Whether search is in progress
        
        # Threading support
        self.search_thread = None
        self.search_lock = threading.Lock()
        self.cancel_search = threading.Event()
        self.last_search_pattern = ""
        
        # Animation support
        self.progress_animator = SearchProgressAnimator(config)
        
        # Get configurable search result limit
        self.max_search_results = getattr(config, 'MAX_SEARCH_RESULTS', 10000)
        
    def show(self, search_type='filename'):
        """Show the search dialog for filename or content search
        
        Args:
            search_type: 'filename' or 'content' search mode
        """
        # Cancel any existing search first
        self._cancel_current_search()
        
        self.mode = True
        self.search_type = search_type
        self.pattern_editor.clear()
        self.results = []
        self.selected = 0
        self.scroll = 0
        self.searching = False
        self.last_search_pattern = ""
        
        # Reset animation
        self.progress_animator.reset()
        
    def exit(self):
        """Exit search dialog mode"""
        # Cancel any running search
        self._cancel_current_search()
        
        self.mode = False
        self.search_type = 'filename'
        self.pattern_editor.clear()
        self.results = []
        self.selected = 0
        self.scroll = 0
        self.searching = False
        self.last_search_pattern = ""
        
        # Reset animation
        self.progress_animator.reset()
        
    def handle_input(self, key):
        """Handle input while in search dialog mode"""
        if key == 27:  # ESC - cancel
            # Cancel search before exiting
            self._cancel_current_search()
            self.exit()
            return True
        elif key == curses.KEY_UP:
            # Move selection up (thread-safe)
            with self.search_lock:
                if self.results and self.selected > 0:
                    self.selected -= 1
                    self._adjust_scroll()
            return True
        elif key == curses.KEY_DOWN:
            # Move selection down (thread-safe)
            with self.search_lock:
                if self.results and self.selected < len(self.results) - 1:
                    self.selected += 1
                    self._adjust_scroll()
            return True
        elif key == curses.KEY_PPAGE:  # Page Up
            with self.search_lock:
                if self.results:
                    self.selected = max(0, self.selected - 10)
                    self._adjust_scroll()
            return True
        elif key == curses.KEY_NPAGE:  # Page Down
            with self.search_lock:
                if self.results:
                    self.selected = min(len(self.results) - 1, self.selected + 10)
                    self._adjust_scroll()
            return True
        elif key == curses.KEY_HOME:  # Home - text cursor or list navigation
            # If there's text in pattern, let editor handle it for cursor movement
            if self.pattern_editor.text:
                if self.pattern_editor.handle_key(key):
                    return True
            else:
                # If no pattern text, use for list navigation (thread-safe)
                with self.search_lock:
                    if self.results:
                        self.selected = 0
                        self.scroll = 0
            return True
        elif key == curses.KEY_END:  # End - text cursor or list navigation
            # If there's text in pattern, let editor handle it for cursor movement
            if self.pattern_editor.text:
                if self.pattern_editor.handle_key(key):
                    return True
            else:
                # If no pattern text, use for list navigation (thread-safe)
                with self.search_lock:
                    if self.results:
                        self.selected = len(self.results) - 1
                        self._adjust_scroll()
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Cancel search before navigating
            self._cancel_current_search()
            
            # Return the selected result for navigation (thread-safe)
            with self.search_lock:
                if self.results and 0 <= self.selected < len(self.results):
                    selected_result = self.results[self.selected]
                    return ('navigate', selected_result)
            return ('navigate', None)
        elif key == curses.KEY_LEFT or key == curses.KEY_RIGHT:
            # Let the editor handle cursor movement keys
            if self.pattern_editor.handle_key(key):
                return ('search', None)
            return True
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            # Let the editor handle backspace
            if self.pattern_editor.handle_key(key):
                return ('search', None)
            return True
        elif key == ord('\t'):  # Tab - switch between filename and content search
            self.search_type = 'content' if self.search_type == 'filename' else 'filename'
            return ('search', None)
        elif 32 <= key <= 126:  # Printable characters
            # Let the editor handle printable characters
            if self.pattern_editor.handle_key(key):
                return ('search', None)
            return True
        return False
        
    def perform_search(self, search_root):
        """Start asynchronous search based on current pattern and type
        
        Args:
            search_root: Path object representing the root directory to search from
        """
        pattern_text = self.pattern_editor.text.strip()
        
        if not pattern_text:
            # Cancel any running search when pattern becomes empty
            self._cancel_current_search()
            with self.search_lock:
                self.results = []
                self.selected = 0
                self.scroll = 0
            return
        
        # Cancel any existing search
        self._cancel_current_search()
        
        # Start new search thread
        self.cancel_search.clear()
        self.searching = True
        self.last_search_pattern = pattern_text
        
        # Reset animation for new search
        self.progress_animator.reset()
        
        self.search_thread = threading.Thread(
            target=self._search_worker,
            args=(search_root, pattern_text, self.search_type),
            daemon=True
        )
        self.search_thread.start()
    
    def _cancel_current_search(self):
        """Cancel the current search operation"""
        if self.search_thread and self.search_thread.is_alive():
            self.cancel_search.set()
            # Give the thread a moment to finish
            self.search_thread.join(timeout=0.1)
        
        self.searching = False
        self.search_thread = None
    
    def _search_worker(self, search_root, pattern_text, search_type):
        """Worker thread for performing the actual search
        
        Args:
            search_root: Path object representing the root directory to search from
            pattern_text: The search pattern text
            search_type: 'filename' or 'content'
        """
        temp_results = []
        
        try:
            if search_type == 'filename':
                # Recursive filename search using fnmatch
                for file_path in search_root.rglob('*'):
                    # Check for cancellation
                    if self.cancel_search.is_set():
                        return
                    
                    # Check result limit
                    if len(temp_results) >= self.max_search_results:
                        break
                    
                    if fnmatch.fnmatch(file_path.name.lower(), pattern_text.lower()):
                        relative_path = file_path.relative_to(search_root)
                        result = {
                            'type': 'dir' if file_path.is_dir() else 'file',
                            'path': file_path,
                            'relative_path': str(relative_path),
                            'match_info': file_path.name
                        }
                        temp_results.append(result)
                        
                        # Update results periodically for real-time display
                        if len(temp_results) % 50 == 0:
                            with self.search_lock:
                                self.results = temp_results.copy()
                                if self.selected >= len(self.results):
                                    self.selected = max(0, len(self.results) - 1)
                                    self._adjust_scroll()
            
            elif search_type == 'content':
                # Recursive grep-based content search
                pattern = re.compile(pattern_text, re.IGNORECASE)
                
                for file_path in search_root.rglob('*'):
                    # Check for cancellation
                    if self.cancel_search.is_set():
                        return
                    
                    # Check result limit
                    if len(temp_results) >= self.max_search_results:
                        break
                    
                    if file_path.is_file() and self._is_text_file(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                for line_num, line in enumerate(f, 1):
                                    # Check for cancellation periodically
                                    if line_num % 100 == 0 and self.cancel_search.is_set():
                                        return
                                    
                                    if pattern.search(line):
                                        relative_path = file_path.relative_to(search_root)
                                        result = {
                                            'type': 'content',
                                            'path': file_path,
                                            'relative_path': str(relative_path),
                                            'line_num': line_num,
                                            'match_info': f"Line {line_num}: {line.strip()[:50]}"
                                        }
                                        temp_results.append(result)
                                        
                                        # Update results periodically for real-time display
                                        if len(temp_results) % 10 == 0:
                                            with self.search_lock:
                                                self.results = temp_results.copy()
                                                if self.selected >= len(self.results):
                                                    self.selected = max(0, len(self.results) - 1)
                                                    self._adjust_scroll()
                                        
                                        break  # Only show first match per file
                        except (IOError, UnicodeDecodeError):
                            continue
                            
        except Exception as e:
            # Handle search errors gracefully
            pass
        
        # Final update of results if not cancelled
        if not self.cancel_search.is_set():
            with self.search_lock:
                self.results = temp_results
                if self.selected >= len(self.results):
                    self.selected = max(0, len(self.results) - 1)
                    self._adjust_scroll()
                self.searching = False
        
    def _is_text_file(self, file_path):
        """Check if a file is likely to be a text file"""
        try:
            # Check file extension
            text_extensions = {
                '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
                '.md', '.rst', '.c', '.cpp', '.h', '.hpp', '.java', '.php', '.rb',
                '.go', '.rs', '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
                '.ini', '.cfg', '.conf', '.config', '.log', '.csv', '.tsv', '.sql'
            }
            
            if file_path.suffix.lower() in text_extensions:
                return True
            
            # Check if file has no extension (might be text)
            if not file_path.suffix:
                # Try to read first few bytes to check if it's text
                try:
                    with open(file_path, 'rb') as f:
                        sample = f.read(512)
                        # Check if sample contains mostly printable characters
                        if sample:
                            text_chars = sum(1 for byte in sample if 32 <= byte <= 126 or byte in [9, 10, 13])
                            return text_chars / len(sample) > 0.7
                except:
                    pass
            
            return False
        except:
            return False
            
    def _adjust_scroll(self):
        """Adjust scroll offset to keep selected item visible"""
        # Use default dialog dimensions for scroll calculation
        dialog_height = 20  # Default height
        content_height = dialog_height - 8  # Account for title, search box, borders, help
        
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + content_height:
            self.scroll = self.selected - content_height + 1
            
    def draw(self, stdscr, safe_addstr_func):
        """Draw the search dialog overlay"""
        height, width = stdscr.getmaxyx()
        
        # Calculate dialog dimensions
        dialog_width = max(60, int(width * 0.8))
        dialog_height = max(20, int(height * 0.8))
        
        # Update scroll calculation with actual dimensions
        content_height = dialog_height - 8
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + content_height:
            self.scroll = self.selected - content_height + 1
        
        # Center the dialog
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        # Draw dialog background
        for y in range(start_y, start_y + dialog_height):
            if y < height:
                bg_line = " " * min(dialog_width, width - start_x)
                safe_addstr_func(y, start_x, bg_line, get_status_color())
        
        # Draw border
        border_color = get_status_color() | curses.A_BOLD
        
        # Top border
        if start_y >= 0:
            top_line = "┌" + "─" * (dialog_width - 2) + "┐"
            safe_addstr_func(start_y, start_x, top_line[:dialog_width], border_color)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height:
                safe_addstr_func(y, start_x, "│", border_color)
                if start_x + dialog_width - 1 < width:
                    safe_addstr_func(y, start_x + dialog_width - 1, "│", border_color)
        
        # Bottom border
        if start_y + dialog_height - 1 < height:
            bottom_line = "└" + "─" * (dialog_width - 2) + "┘"
            safe_addstr_func(start_y + dialog_height - 1, start_x, bottom_line[:dialog_width], border_color)
        
        # Draw title
        title_text = f" Search ({self.search_type.title()}) "
        title_x = start_x + (dialog_width - len(title_text)) // 2
        if title_x >= start_x and title_x + len(title_text) <= start_x + dialog_width:
            safe_addstr_func(start_y, title_x, title_text, border_color)
        
        # Draw search box
        search_y = start_y + 2
        # Draw pattern input using SingleLineTextEdit
        if search_y < height:
            max_pattern_width = dialog_width - 4  # Leave some margin
            self.pattern_editor.draw(
                stdscr, search_y, start_x + 2, max_pattern_width,
                "Pattern: ",
                is_active=True
            )
        
        # Draw search type indicator
        type_y = start_y + 3
        if type_y < height:
            type_text = f"Mode: {self.search_type.title()} (Tab to switch)"
            safe_addstr_func(type_y, start_x + 2, type_text[:dialog_width - 4], get_status_color() | curses.A_DIM)
        
        # Draw separator line
        sep_y = start_y + 4
        if sep_y < height:
            sep_line = "├" + "─" * (dialog_width - 2) + "┤"
            safe_addstr_func(sep_y, start_x, sep_line[:dialog_width], border_color)
        
        # Draw results count with animated progress indicator (thread-safe)
        count_y = start_y + 5
        if count_y < height:
            with self.search_lock:
                result_count = len(self.results)
                is_searching = self.searching
                
                if is_searching:
                    # Get animated progress indicator
                    progress_indicator = self.progress_animator.get_progress_indicator(result_count, is_searching)
                    
                    if result_count >= self.max_search_results:
                        count_text = f"Searching{progress_indicator}(limit reached: {result_count})"
                    else:
                        count_text = f"Searching{progress_indicator}({result_count} found)"
                    
                    # Use brighter color for active search
                    count_color = get_status_color() | curses.A_BOLD
                else:
                    if result_count >= self.max_search_results:
                        count_text = f"Results: {result_count} (limit reached)"
                    else:
                        count_text = f"Results: {result_count}"
                    
                    count_color = get_status_color() | curses.A_DIM
            
            safe_addstr_func(count_y, start_x + 2, count_text[:dialog_width - 4], count_color)
        
        # Calculate results area
        results_start_y = start_y + 6
        results_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        content_height = results_end_y - results_start_y + 1
        
        # Draw results (thread-safe)
        with self.search_lock:
            visible_results = self.results[self.scroll:self.scroll + content_height]
            current_selected = self.selected
        
        for i, result in enumerate(visible_results):
            y = results_start_y + i
            if y <= results_end_y and y < height:
                result_index = self.scroll + i
                is_selected = result_index == current_selected
                
                # Format result text
                if result['type'] == 'dir':
                    result_text = f"� {result['relative_path']}"
                elif result['type'] == 'content':
                    result_text = f"📄 {result['relative_path']} - {result['match_info']}"
                else:
                    result_text = f"📄 {result['relative_path']}"
                
                if len(result_text) > content_width - 2:
                    result_text = result_text[:content_width - 5] + "..."
                
                # Add selection indicator
                if is_selected:
                    display_text = f"► {result_text}"
                    item_color = get_status_color() | curses.A_BOLD | curses.A_STANDOUT
                else:
                    display_text = f"  {result_text}"
                    item_color = get_status_color()
                
                # Ensure text fits
                display_text = display_text[:content_width]
                safe_addstr_func(y, content_start_x, display_text, item_color)
        
        # Draw help text
        help_y = start_y + dialog_height - 2
        if help_y < height:
            help_text = "Enter: Select | Tab: Switch mode | ESC: Cancel"
            help_x = start_x + (dialog_width - len(help_text)) // 2
            if help_x >= start_x:
                safe_addstr_func(help_y, help_x, help_text, get_status_color() | curses.A_DIM)


class SearchDialogHelpers:
    """Helper functions for search dialog navigation and integration"""
    
    @staticmethod
    def navigate_to_result(result, pane_manager, file_operations, print_func):
        """Navigate to the selected search result
        
        Args:
            result: Search result dictionary
            pane_manager: PaneManager instance
            file_operations: FileOperations instance  
            print_func: Function to print messages
        """
        current_pane = pane_manager.get_current_pane()
        target_path = result['path']
        
        if result['type'] == 'dir':
            # Navigate to directory
            current_pane['path'] = target_path
            current_pane['selected_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()
            print_func(f"Navigated to directory: {result['relative_path']}")
        else:
            # Navigate to file's directory and select the file
            parent_dir = target_path.parent
            current_pane['path'] = parent_dir
            current_pane['selected_files'].clear()
            
            # Refresh files and find the target file
            file_operations.refresh_files(current_pane)
            
            # Find and select the target file
            for i, file_path in enumerate(current_pane['files']):
                if file_path == target_path:
                    current_pane['selected_index'] = i
                    # Adjust scroll to make selection visible - this would need display_height
                    # For now, just set basic scroll
                    if current_pane['selected_index'] < current_pane['scroll_offset']:
                        current_pane['scroll_offset'] = current_pane['selected_index']
                    elif current_pane['selected_index'] >= current_pane['scroll_offset'] + 10:  # Default height
                        current_pane['scroll_offset'] = current_pane['selected_index'] - 10 + 1
                    break
            
            if result['type'] == 'content':
                print_func(f"Found content match in: {result['relative_path']} at line {result['line_num']}")
            else:
                print_func(f"Navigated to file: {result['relative_path']}")
    
    @staticmethod
    def adjust_scroll_for_display_height(current_pane, display_height):
        """Adjust scroll offset based on actual display height
        
        Args:
            current_pane: Current pane data
            display_height: Actual display height available
        """
        if current_pane['selected_index'] < current_pane['scroll_offset']:
            current_pane['scroll_offset'] = current_pane['selected_index']
        elif current_pane['selected_index'] >= current_pane['scroll_offset'] + display_height:
            current_pane['scroll_offset'] = current_pane['selected_index'] - display_height + 1