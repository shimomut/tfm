#!/usr/bin/env python3
"""
TUI File Manager - Search Dialog Component
Provides file and content search functionality with threading support
"""

import fnmatch
import re
import threading
import time
from ttk import TextAttribute, KeyCode, KeyEvent, CharEvent
from ttk.wide_char_utils import get_display_width, get_safe_functions

from tfm_path import Path
from tfm_base_list_dialog import BaseListDialog
from tfm_ui_layer import UILayer
from tfm_colors import get_status_color
from tfm_progress_animator import ProgressAnimatorFactory
from tfm_log_manager import getLogger
from tfm_string_width import reduce_width, ShorteningRegion

# Module-level logger
logger = getLogger("SearchDlg")


class SearchDialog(UILayer, BaseListDialog):
    """Search dialog component for filename and content search with threading support"""
    
    def __init__(self, config, renderer=None):
        super().__init__(config, renderer)
        
        # Search dialog specific state
        self.search_type = 'filename'  # 'filename' or 'content'
        self.results = []  # List of search results
        self.searching = False  # Whether search is in progress
        self.content_changed = True  # Track if content needs redraw
        self.search_root = None  # Root directory for search
        self._selected_result = None  # Selected result when dialog closes
        self.callback = None  # Callback function when result is selected
        
        # Threading support
        self.search_thread = None
        self.search_lock = threading.Lock()
        self.cancel_search = threading.Event()
        self.last_search_pattern = ""
        
        # Animation support
        self.progress_animator = ProgressAnimatorFactory.create_search_animator(config)
        
        # Get configurable search result limit
        self.max_search_results = getattr(config, 'MAX_SEARCH_RESULTS', 10000)
        
    def show(self, search_type='filename', search_root=None, callback=None):
        """Show the search dialog for filename or content search
        
        Args:
            search_type: 'filename' or 'content' search mode
            search_root: Path object representing the root directory to search from
            callback: Optional callback function to call when a result is selected.
                     Callback receives the selected result as an argument.
        """
        # Cancel any existing search first
        self._cancel_current_search()
        self.content_changed = True  # Mark content as changed when showing
        
        self.is_active = True
        self.search_type = search_type
        self.search_root = search_root
        self.callback = callback
        self.text_editor.clear()
        self.results = []
        self.selected = 0
        self.scroll = 0
        self.searching = False
        self.last_search_pattern = ""
        self._selected_result = None  # Clear any previous selection
        
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
        self.search_root = None
        self.callback = None
        # Don't clear _selected_result here - it needs to persist for retrieval
        self.content_changed = True  # Mark content as changed when exiting
        
        # Reset animation
        self.progress_animator.reset()
    
    def get_selected_result(self):
        """Get the selected result after dialog exits
        
        Returns:
            The selected search result, or None if no result was selected
        """
        return getattr(self, '_selected_result', None)
        
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
                        display_path = str(relative_path)
                        
                        result = {
                            'type': 'dir' if file_path.is_dir() else 'file',
                            'path': file_path,
                            'relative_path': display_path,
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
                            # Use search strategy from path to determine how to read content
                            search_strategy = file_path.get_search_strategy()
                            
                            if search_strategy == 'streaming':
                                # Stream line by line for local files
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    for line_num, line in enumerate(f, 1):
                                        # Check for cancellation periodically
                                        if line_num % 100 == 0 and self.cancel_search.is_set():
                                            with self.search_lock:
                                                self.searching = False
                                                self.content_changed = True
                                            return
                                        
                                        if pattern.search(line):
                                            relative_path = file_path.relative_to(search_root)
                                            result = {
                                                'type': 'content',
                                                'path': file_path,
                                                'relative_path': str(relative_path),
                                                'line_num': line_num,
                                                'match_info': line.strip()[:200]
                                            }
                                            temp_results.append(result)
                                            
                                            # Update results periodically for real-time display
                                            if len(temp_results) % 10 == 0:
                                                with self.search_lock:
                                                    self.results = temp_results.copy()
                                                    if self.selected >= len(self.results):
                                                        self.selected = max(0, len(self.results) - 1)
                                                        self._adjust_scroll(len(self.results))
                                                    self.content_changed = True
                                            
                                            break  # Only show first match per file
                            else:
                                # For 'extracted' or 'buffered' strategies, read entire content
                                content = file_path.read_text(encoding='utf-8', errors='ignore')
                                lines = content.splitlines()
                                for line_num, line in enumerate(lines, 1):
                                    # Check for cancellation periodically
                                    if line_num % 100 == 0 and self.cancel_search.is_set():
                                        with self.search_lock:
                                            self.searching = False
                                            self.content_changed = True
                                        return
                                    
                                    if pattern.search(line):
                                        relative_path = file_path.relative_to(search_root)
                                        result = {
                                            'type': 'content',
                                            'path': file_path,
                                            'relative_path': str(relative_path),
                                            'line_num': line_num,
                                            'match_info': line.strip()[:200]
                                        }
                                        temp_results.append(result)
                                        
                                        # Update results periodically for real-time display
                                        if len(temp_results) % 10 == 0:
                                            with self.search_lock:
                                                self.results = temp_results.copy()
                                                if self.selected >= len(self.results):
                                                    self.selected = max(0, len(self.results) - 1)
                                                    self._adjust_scroll(len(self.results))
                                                self.content_changed = True
                                        
                                        break  # Only show first match per file
                        except FileNotFoundError:
                            # File was deleted during search
                            continue
                        except PermissionError:
                            # No permission to read file
                            continue
                        except (IOError, UnicodeDecodeError, OSError) as e:
                            # Handle I/O errors, encoding issues, and archive extraction errors
                            continue
                        except Exception as e:
                            # Catch any unexpected errors with logging
                            logger.warning(f"Unexpected error searching file {file_path}: {e}")
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
                    logger.warning(f"Could not read file for text detection {file_path}: {e}")
                    pass
                except Exception as e:
                    logger.warning(f"Unexpected error in file text detection: {e}")
                    pass
            
            return False
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not access file {file_path}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking if file is text: {e}")
            return False
            

            
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        # Always redraw when searching to animate progress indicator
        return self.content_changed or self.searching
    
    def draw(self):
        """Draw the search dialog overlay"""
        if not self.renderer:
            return
            
        # Get display prefix from the search root path if available
        display_prefix = ""
        with self.search_lock:
            if self.results and hasattr(self.results[0]['path'], 'get_display_prefix'):
                # Get the prefix from any result path (they all share the same root)
                display_prefix = self.results[0]['path'].get_display_prefix()

        # Draw dialog frame with storage-specific prefix if applicable
        if display_prefix:
            title_text = f"{display_prefix}Search ({self.search_type.title()})"
        else:
            title_text = f"Search ({self.search_type.title()})"
        start_y, start_x, dialog_width, dialog_height = self.draw_dialog_frame(
            title_text, 0.8, 0.8, 60, 20
        )
        
        # Draw pattern input
        search_y = start_y + 2
        self.draw_text_input(search_y, start_x, dialog_width, "Pattern: ")
        
        # Draw search type indicator
        type_y = start_y + 3
        height, width = self.renderer.get_dimensions()
        if type_y < height:
            type_text = f"Mode: {self.search_type.title()} (Tab to switch)"
            color_pair, attributes = get_status_color()
            self.renderer.draw_text(type_y, start_x + 2, type_text[:dialog_width - 4], 
                                   color_pair=color_pair, attributes=TextAttribute.NORMAL)
        
        # Draw separator
        sep_y = start_y + 4
        self.draw_separator(sep_y, start_x, dialog_width)
        
        # Draw results count with animated progress indicator (thread-safe)
        count_y = start_y + 5
        if count_y < height:
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
                    color_pair, _ = get_status_color()
                    count_attributes = TextAttribute.BOLD
                else:
                    if result_count >= self.max_search_results:
                        count_text = f"Results: {result_count} (limit reached)"
                    else:
                        count_text = f"Results: {result_count}"
                    
                    color_pair, _ = get_status_color()
                    count_attributes = TextAttribute.NORMAL
            
            self.renderer.draw_text(count_y, start_x + 2, count_text[:dialog_width - 4], 
                                   color_pair=color_pair, attributes=count_attributes)
        
        # Calculate results area
        results_start_y = start_y + 6
        results_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        
        # Format search results for display
        def format_result(result):
            # Calculate available width for the result text
            # Account for emoji (2 columns) and spacing
            available_width = content_width - 3  # 2 for emoji + 1 for space
            
            if result['type'] == 'dir':
                path_text = reduce_width(result['relative_path'], available_width, default_position='middle')
                return f"📁 {path_text}"
            elif result['type'] == 'content':
                # For content matches, construct line prefix from line_num
                # match_info now contains only the actual match content
                line_num = result.get('line_num', 0)
                match_content = result['match_info']
                
                # Construct line prefix
                line_prefix = f"Line {line_num}: "
                
                # Build combined text: path - line_prefix + match_content
                separator = " - "
                combined_text = f"{result['relative_path']}{separator}{line_prefix}{match_content}"
                
                # Define regions:
                # Region 1 (priority 0): relative_path - most important, shortened last
                # Line prefix is preserved (not in any region)
                # Region 2 (priority 1): match_content - shortened first
                path_end = len(result['relative_path'])
                separator_end = path_end + len(separator)
                line_prefix_end = separator_end + len(line_prefix)
                
                regions = [
                    ShorteningRegion(
                        start=0,
                        end=path_end,
                        priority=0,  # Path is more important, shortened last
                        strategy='abbreviate',
                        abbrev_position='middle',
                        filepath_mode=True
                    ),
                    ShorteningRegion(
                        start=line_prefix_end,
                        end=len(combined_text),
                        priority=1,  # Match content shortened first
                        strategy='abbreviate',
                        abbrev_position='right',
                        filepath_mode=False
                    )
                ]
                
                shortened_text = reduce_width(combined_text, available_width, regions=regions)
                return f"📄 {shortened_text}"
            else:
                path_text = reduce_width(result['relative_path'], available_width, default_position='middle')
                return f"📄 {path_text}"
        
        # Draw results (thread-safe)
        with self.search_lock:
            current_results = self.results.copy()
        
        self.draw_list_items(current_results, 
                           results_start_y, results_end_y, content_start_x, content_width, format_result)
        
        # Draw scrollbar
        scrollbar_x = start_x + dialog_width - 2
        content_height = results_end_y - results_start_y + 1
        self.draw_scrollbar(current_results, 
                          results_start_y, content_height, scrollbar_x)
        
        # Draw help text
        help_text = "Enter: Select | Tab: Switch mode | ESC: Cancel"
        help_y = start_y + dialog_height - 2
        self.draw_help_text(help_text, help_y, start_x, dialog_width)
        
        # Automatically mark as not needing redraw after drawing (unless still searching)
        if not self.searching:
            self.content_changed = False
    
    # UILayer interface implementation
    
    def handle_key_event(self, event) -> bool:
        """
        Handle a key event (UILayer interface).
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed, False to propagate to next layer
        """
        if not event or not isinstance(event, KeyEvent):
            return False
        
        # Handle Tab key for search type switching first
        if event.key_code == KeyCode.TAB:
            self.search_type = 'content' if self.search_type == 'filename' else 'filename'
            self.content_changed = True
            # Trigger search with new search type if we have a pattern
            if self.search_root and self.text_editor.text.strip():
                self.perform_search(self.search_root)
            return True
        
        # Use base class navigation handling with thread safety
        with self.search_lock:
            current_results = self.results.copy()
        
        result = self.handle_common_navigation(event, current_results)
        
        if result == 'cancel':
            # Store callback before exiting
            callback = self.callback
            
            # Cancel search before exiting
            self._cancel_current_search()
            self.exit()
            
            # Call callback after exiting to allow new dialogs
            if callback:
                callback(None)
            return True
        elif result == 'select':
            # Store callback before exiting
            callback = self.callback
            
            # Cancel search before navigating
            self._cancel_current_search()
            
            # Store selected result for retrieval
            selected_result = None
            with self.search_lock:
                if self.results and 0 <= self.selected < len(self.results):
                    selected_result = self.results[self.selected]
                    self._selected_result = selected_result
            
            self.exit()
            
            # Call callback after exiting to allow new dialogs
            if callback and selected_result:
                callback(selected_result)
            return True
        elif result == 'text_changed':
            self.content_changed = True
            # Automatically trigger search when text changes
            if self.search_root:
                self.perform_search(self.search_root)
            return True
        elif result:
            # Update selection in thread-safe manner for navigation keys
            if event.key_code in [KeyCode.UP, KeyCode.DOWN, KeyCode.PAGE_UP, KeyCode.PAGE_DOWN, KeyCode.HOME, KeyCode.END]:
                with self.search_lock:
                    # The base class already updated self.selected, just need to adjust scroll
                    self._adjust_scroll(len(self.results))
            
            # Mark content as changed for ANY handled key to ensure continued rendering
            self.content_changed = True
            return True
        
        return False
    
    def handle_char_event(self, event) -> bool:
        """
        Handle a character event (UILayer interface).
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if the event was consumed, False to propagate to next layer
        """
        if not event or not isinstance(event, CharEvent):
            return False
        
        # Pass to text editor
        if self.text_editor.handle_key(event):
            self.content_changed = True
            # Automatically trigger search when text changes
            if self.search_root:
                self.perform_search(self.search_root)
            return True
        
        return False
    
    def handle_system_event(self, event) -> bool:
        """
        Handle a system event (UILayer interface).
        
        Args:
            event: SystemEvent to handle
        
        Returns:
            True if event was handled, False otherwise
        """
        if event.is_resize():
            # Mark content as changed to trigger redraw with new dimensions
            self.content_changed = True
            return True
        elif event.is_close():
            # Close the dialog and cancel any ongoing search
            self.cancel_search()
            self.is_active = False
            return True
        return False
    
    def handle_mouse_event(self, event) -> bool:
        """
        Handle a mouse event (UILayer interface).
        
        Supports mouse wheel scrolling for vertical navigation.
        
        Args:
            event: MouseEvent to handle
        
        Returns:
            True if event was handled, False otherwise
        """
        # Call BaseListDialog's wheel scrolling method directly (thread-safe)
        with self.search_lock:
            current_results = self.results.copy()
        
        result = BaseListDialog.handle_mouse_event(self, event, current_results)
        
        # Mark content as changed if scroll position changed
        if result:
            self.content_changed = True
        
        return result
    
    def render(self, renderer) -> None:
        """
        Render the layer's content (UILayer interface).
        
        Args:
            renderer: TTK renderer instance for drawing
        """
        self.draw()
    
    def is_full_screen(self) -> bool:
        """
        Query if this layer occupies the full screen (UILayer interface).
        
        Returns:
            False - dialogs are overlays, not full-screen
        """
        return False
    
    def mark_dirty(self) -> None:
        """
        Mark this layer as needing a redraw (UILayer interface).
        """
        self.content_changed = True
    
    def clear_dirty(self) -> None:
        """
        Clear the dirty flag after rendering (UILayer interface).
        """
        # Only clear if not searching (searching keeps it dirty for animation)
        if not self.searching:
            self.content_changed = False
    
    def should_close(self) -> bool:
        """
        Query if this layer wants to close (UILayer interface).
        
        Returns:
            True if the layer should be closed, False otherwise
        """
        return not self.is_active
    
    def on_activate(self) -> None:
        """
        Called when this layer becomes the top layer (UILayer interface).
        """
        self.content_changed = True  # Ensure dialog is drawn when activated
    
    def on_deactivate(self) -> None:
        """
        Called when this layer is no longer the top layer (UILayer interface).
        """
        pass


class SearchDialogHelpers:
    """Helper functions for search dialog navigation and integration"""
    
    @staticmethod
    def navigate_to_result(result, pane_manager, file_list_manager, print_func):
        """Navigate to the selected search result
        
        Args:
            result: Search result dictionary
            pane_manager: PaneManager instance
            file_list_manager: FileListManager instance  
            print_func: Function to print messages
        """
        current_pane = pane_manager.get_current_pane()
        target_path = result['path']
        
        if result['type'] == 'dir':
            # Navigate to directory
            current_pane['path'] = target_path
            current_pane['focused_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()
            print_func(f"Navigated to directory: {result['relative_path']}")
        else:
            # Navigate to file's directory and select the file
            parent_dir = target_path.parent
            current_pane['path'] = parent_dir
            current_pane['selected_files'].clear()
            
            # Refresh files and find the target file
            file_list_manager.refresh_files(current_pane)
            
            # Find and select the target file
            for i, file_path in enumerate(current_pane['files']):
                if file_path == target_path:
                    current_pane['focused_index'] = i
                    # Adjust scroll to make selection visible - this would need display_height
                    # For now, just set basic scroll
                    if current_pane['focused_index'] < current_pane['scroll_offset']:
                        current_pane['scroll_offset'] = current_pane['focused_index']
                    elif current_pane['focused_index'] >= current_pane['scroll_offset'] + 10:  # Default height
                        current_pane['scroll_offset'] = current_pane['focused_index'] - 10 + 1
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
        if current_pane['focused_index'] < current_pane['scroll_offset']:
            current_pane['scroll_offset'] = current_pane['focused_index']
        elif current_pane['focused_index'] >= current_pane['scroll_offset'] + display_height:
            current_pane['scroll_offset'] = current_pane['focused_index'] - display_height + 1