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
from tfm_path import Path
from tfm_base_list_dialog import BaseListDialog
from tfm_const import KEY_ENTER_1, KEY_ENTER_2
from tfm_colors import get_status_color
from tfm_progress_animator import ProgressAnimatorFactory


class SearchDialog(BaseListDialog):
    """Search dialog component for filename and content search with threading support"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Search dialog specific state
        self.search_type = 'filename'  # 'filename' or 'content'
        self.results = []  # List of search results
        self.searching = False  # Whether search is in progress
        self.content_changed = True  # Track if content needs redraw
        
        # Threading support
        self.search_thread = None
        self.search_lock = threading.Lock()
        self.cancel_search = threading.Event()
        self.last_search_pattern = ""
        
        # Animation support
        self.progress_animator = ProgressAnimatorFactory.create_search_animator(config)
        
        # Get configurable search result limit
        self.max_search_results = getattr(config, 'MAX_SEARCH_RESULTS', 10000)
        
    def show(self, search_type='filename'):
        """Show the search dialog for filename or content search
        
        Args:
            search_type: 'filename' or 'content' search mode
        """
        # Cancel any existing search first
        self._cancel_current_search()
        self.content_changed = True  # Mark content as changed when showing
        
        self.mode = True
        self.search_type = search_type
        self.text_editor.clear()
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
        
        super().exit()
        self.search_type = 'filename'
        self.results = []
        self.searching = False
        self.last_search_pattern = ""
        self.content_changed = True  # Mark content as changed when exiting
        
        # Reset animation
        self.progress_animator.reset()
        
    def handle_input(self, key):
        """Handle input while in search dialog mode"""
        # Handle Tab key for search type switching first
        if key == ord('\t'):  # Tab - switch between filename and content search
            self.search_type = 'content' if self.search_type == 'filename' else 'filename'
            self.content_changed = True  # Mark content as changed when switching search type
            return ('search', None)
            
        # Use base class navigation handling with thread safety
        with self.search_lock:
            current_results = self.results.copy()
        
        result = self.handle_common_navigation(key, current_results)
        
        if result == 'cancel':
            # Cancel search before exiting
            self._cancel_current_search()
            self.exit()
            return True
        elif result == 'select':
            # Cancel search before navigating
            self._cancel_current_search()
            
            # Return the selected result for navigation (thread-safe)
            with self.search_lock:
                if self.results and 0 <= self.selected < len(self.results):
                    selected_result = self.results[self.selected]
                    return ('navigate', selected_result)
            return ('navigate', None)
        elif result == 'text_changed':
            self.content_changed = True  # Mark content as changed when text changes
            return ('search', None)
        elif result:
            # Update selection in thread-safe manner for navigation keys
            if key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_PPAGE, curses.KEY_NPAGE, curses.KEY_HOME, curses.KEY_END]:
                with self.search_lock:
                    # The base class already updated self.selected, just need to adjust scroll
                    self._adjust_scroll(len(self.results))
            
            # Mark content as changed for ANY handled key to ensure continued rendering
            self.content_changed = True
            return True
            
        return False
        
    def perform_search(self, search_root):
        """Start asynchronous search based on current pattern and type
        
        Args:
            search_root: Path object representing the root directory to search from
        """
        pattern_text = self.text_editor.text.strip()
        
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
        
        # Clear previous results immediately when starting new search
        with self.search_lock:
            self.results = []
            self.selected = 0
            self.scroll = 0
        
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
        self.content_changed = True  # Mark content as changed when search is canceled
    
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
                        with self.search_lock:
                            self.searching = False
                            self.content_changed = True  # Mark content as changed when search is canceled
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
                                    self._adjust_scroll(len(self.results))
                                self.content_changed = True  # Mark content as changed when results update
            
            elif search_type == 'content':
                # Recursive grep-based content search
                pattern = re.compile(pattern_text, re.IGNORECASE)
                
                for file_path in search_root.rglob('*'):
                    # Check for cancellation
                    if self.cancel_search.is_set():
                        with self.search_lock:
                            self.searching = False
                            self.content_changed = True  # Mark content as changed when search is canceled
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
                                        with self.search_lock:
                                            self.searching = False
                                            self.content_changed = True  # Mark content as changed when search is canceled
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
                                                    self._adjust_scroll(len(self.results))
                                                self.content_changed = True  # Mark content as changed when results update
                                        
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
                    self._adjust_scroll(len(self.results))
                self.searching = False
                self.content_changed = True  # Mark content as changed when search completes
        
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
                except (OSError, IOError) as e:
                    print(f"Warning: Could not read file for text detection {file_path}: {e}")
                    pass
                except Exception as e:
                    print(f"Warning: Unexpected error in file text detection: {e}")
                    pass
            
            return False
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not access file {file_path}: {e}")
            return False
        except Exception as e:
            print(f"Warning: Unexpected error checking if file is text: {e}")
            return False
            

            
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        # Always redraw when searching to animate progress indicator
        return self.content_changed or self.searching
    
    def draw(self, stdscr, safe_addstr_func):
        """Draw the search dialog overlay"""

        # Draw dialog frame
        title_text = f"Search ({self.search_type.title()})"
        start_y, start_x, dialog_width, dialog_height = self.draw_dialog_frame(
            stdscr, safe_addstr_func, title_text, 0.8, 0.8, 60, 20
        )
        
        # Draw pattern input
        search_y = start_y + 2
        self.draw_text_input(stdscr, safe_addstr_func, search_y, start_x, dialog_width, "Pattern: ")
        
        # Draw search type indicator
        type_y = start_y + 3
        if type_y < stdscr.getmaxyx()[0]:
            type_text = f"Mode: {self.search_type.title()} (Tab to switch)"
            safe_addstr_func(type_y, start_x + 2, type_text[:dialog_width - 4], get_status_color() | curses.A_DIM)
        
        # Draw separator
        sep_y = start_y + 4
        self.draw_separator(stdscr, safe_addstr_func, sep_y, start_x, dialog_width)
        
        # Draw results count with animated progress indicator (thread-safe)
        count_y = start_y + 5
        if count_y < stdscr.getmaxyx()[0]:
            with self.search_lock:
                result_count = len(self.results)
                is_searching = self.searching
                
                if is_searching:
                    # Get animated status text
                    if result_count >= self.max_search_results:
                        context_info = f"limit reached: {result_count}"
                    else:
                        context_info = f"{result_count} found"
                    
                    count_text = self.progress_animator.get_status_text("Searching", context_info, is_searching)
                    
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
        
        # Format search results for display
        def format_result(result):
            if result['type'] == 'dir':
                return f"📁 {result['relative_path']}"
            elif result['type'] == 'content':
                return f"📄 {result['relative_path']} - {result['match_info']}"
            else:
                return f"📄 {result['relative_path']}"
        
        # Draw results (thread-safe)
        with self.search_lock:
            current_results = self.results.copy()
        
        self.draw_list_items(stdscr, safe_addstr_func, current_results, 
                           results_start_y, results_end_y, content_start_x, content_width, format_result)
        
        # Draw scrollbar
        scrollbar_x = start_x + dialog_width - 2
        content_height = results_end_y - results_start_y + 1
        self.draw_scrollbar(stdscr, safe_addstr_func, current_results, 
                          results_start_y, content_height, scrollbar_x)
        
        # Draw help text
        help_text = "Enter: Select | Tab: Switch mode | ESC: Cancel"
        help_y = start_y + dialog_height - 2
        self.draw_help_text(stdscr, safe_addstr_func, help_text, help_y, start_x, dialog_width)
        
        # Automatically mark as not needing redraw after drawing (unless still searching)
        if not self.searching:
            self.content_changed = False


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