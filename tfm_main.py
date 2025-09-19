#!/usr/bin/env python3
"""
TUI File Manager - A terminal-based file manager using curses
"""

import curses
import os
import stat
import shutil
import sys
import io
import fnmatch
from pathlib import Path
from datetime import datetime
from collections import deque

# Import constants and colors
from tfm_const import *
from tfm_colors import *

class LogCapture:
    """Capture stdout/stderr and redirect to log pane"""
    def __init__(self, log_messages, source):
        self.log_messages = log_messages
        self.source = source
        
    def write(self, text):
        if text.strip():  # Only log non-empty messages
            timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
            self.log_messages.append((timestamp, self.source, text.strip()))
    
    def flush(self):
        pass  # Required for file-like object interface

class FileManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        
        # Dual pane setup
        self.left_pane = {
            'path': Path.cwd(),
            'selected_index': 0,
            'scroll_offset': 0,
            'files': [],
            'selected_files': set()  # Track multi-selected files
        }
        self.right_pane = {
            'path': Path.home(),  # Start right pane in home directory
            'selected_index': 0,
            'scroll_offset': 0,
            'files': [],
            'selected_files': set()  # Track multi-selected files
        }
        
        self.active_pane = 'left'  # 'left' or 'right'
        self.show_hidden = False
        
        # Pane layout - track left pane width ratio (0.1 to 0.9)
        self.left_pane_ratio = 0.5  # Start with 50/50 split
        self.log_height_ratio = DEFAULT_LOG_HEIGHT_RATIO  # Track log pane height ratio
        self.needs_full_redraw = True  # Flag to control when to redraw everything
        
        # Search mode state
        self.search_mode = False
        self.search_pattern = ""
        self.search_matches = []
        self.search_match_index = 0
        
        # Log pane setup
        self.log_messages = deque(maxlen=MAX_LOG_MESSAGES)
        self.log_scroll_offset = 0
        
        # Redirect stdout and stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = LogCapture(self.log_messages, "STDOUT")
        sys.stderr = LogCapture(self.log_messages, "STDERR")
        
        # Add startup messages to log
        self.add_startup_messages()
        
        # Initialize colors
        init_colors()
        
        # Configure curses
        curses.curs_set(0)  # Hide cursor
        self.stdscr.keypad(True)
        
    def safe_addstr(self, y, x, text, attr=curses.A_NORMAL):
        """Safely add string to screen, handling boundary conditions"""
        try:
            height, width = self.stdscr.getmaxyx()
            
            # Check bounds
            if y < 0 or y >= height or x < 0 or x >= width:
                return
                
            # Truncate text if it would exceed screen width
            max_len = width - x - 1  # Leave space to avoid last column
            if max_len <= 0:
                return
                
            truncated_text = text[:max_len] if len(text) > max_len else text
            self.stdscr.addstr(y, x, truncated_text, attr)
        except curses.error:
            pass  # Ignore curses errors
        
    def add_startup_messages(self):
        """Add startup messages directly to log pane"""
        timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
        self.log_messages.append((timestamp, "SYSTEM", f"TFM {VERSION}"))
        self.log_messages.append((timestamp, "SYSTEM", f"GitHub: {GITHUB_URL}"))
        self.log_messages.append((timestamp, "SYSTEM", f"{APP_NAME} started successfully"))
        
    def count_files_and_dirs(self, pane_data):
        """Count directories and files in a pane, excluding parent directory entry"""
        if not pane_data['files']:
            return 0, 0
            
        files = pane_data['files']
        # Skip the first entry if it's the parent directory (..)
        start_idx = 1 if (len(files) > 0 and files[0] == pane_data['path'].parent) else 0
        
        dir_count = 0
        file_count = 0
        
        for file_path in files[start_idx:]:
            if file_path.is_dir():
                dir_count += 1
            else:
                file_count += 1
                
        return dir_count, file_count
        
    def draw_file_footers(self, y, left_pane_width):
        """Draw footer bars for left and right file panes"""
        # Left pane footer
        left_dirs, left_files = self.count_files_and_dirs(self.left_pane)
        left_selected = len(self.left_pane['selected_files'])
        if left_selected > 0:
            left_footer = f" {left_dirs} dirs, {left_files} files ({left_selected} selected) "
        else:
            left_footer = f" {left_dirs} dirs, {left_files} files "
        
        try:
            # Left pane footer with active indicator
            left_color = get_footer_color(self.active_pane == 'left')
            self.stdscr.addstr(y, 2, left_footer, left_color)
        except curses.error:
            pass
            
        # Right pane footer  
        right_dirs, right_files = self.count_files_and_dirs(self.right_pane)
        right_selected = len(self.right_pane['selected_files'])
        if right_selected > 0:
            right_footer = f" {right_dirs} dirs, {right_files} files ({right_selected} selected) "
        else:
            right_footer = f" {right_dirs} dirs, {right_files} files "
        
        try:
            # Right pane footer with active indicator
            right_color = get_footer_color(self.active_pane == 'right')
            self.stdscr.addstr(y, left_pane_width + 2, right_footer, right_color)
        except curses.error:
            pass
            
    def toggle_selection(self):
        """Toggle selection of current file/directory and move to next item"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            return
            
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Don't allow selection of parent directory (..)
        if (current_pane['selected_index'] == 0 and 
            len(current_pane['files']) > 0 and 
            selected_file == current_pane['path'].parent):
            # Still move to next item even if we can't select parent directory
            if current_pane['selected_index'] < len(current_pane['files']) - 1:
                current_pane['selected_index'] += 1
            return
            
        file_path_str = str(selected_file)
        
        if file_path_str in current_pane['selected_files']:
            current_pane['selected_files'].remove(file_path_str)
            print(f"Deselected: {selected_file.name}")
        else:
            current_pane['selected_files'].add(file_path_str)
            print(f"Selected: {selected_file.name}")
        
        print(f"Total selected: {len(current_pane['selected_files'])}")
        
        # Move cursor to next item after selection
        if current_pane['selected_index'] < len(current_pane['files']) - 1:
            current_pane['selected_index'] += 1
            
    def toggle_selection_up(self):
        """Toggle selection of current file/directory and move to previous item"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            return
            
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Don't allow selection of parent directory (..)
        if (current_pane['selected_index'] == 0 and 
            len(current_pane['files']) > 0 and 
            selected_file == current_pane['path'].parent):
            # Can't move up from first item, so just return
            return
            
        file_path_str = str(selected_file)
        
        if file_path_str in current_pane['selected_files']:
            current_pane['selected_files'].remove(file_path_str)
            print(f"Deselected: {selected_file.name}")
        else:
            current_pane['selected_files'].add(file_path_str)
            print(f"Selected: {selected_file.name}")
        
        print(f"Total selected: {len(current_pane['selected_files'])}")
        
        # Move cursor to previous item after selection
        if current_pane['selected_index'] > 0:
            current_pane['selected_index'] -= 1
        
    def restore_stdio(self):
        """Restore stdout/stderr to original state"""
        if hasattr(self, 'original_stdout') and sys.stdout != self.original_stdout:
            sys.stdout = self.original_stdout
        if hasattr(self, 'original_stderr') and sys.stderr != self.original_stderr:
            sys.stderr = self.original_stderr
            
    def __del__(self):
        """Restore stdout/stderr when object is destroyed"""
        self.restore_stdio()
        
    def get_current_pane(self):
        """Get the currently active pane"""
        return self.left_pane if self.active_pane == 'left' else self.right_pane
    
    def get_inactive_pane(self):
        """Get the inactive pane"""
        return self.right_pane if self.active_pane == 'left' else self.left_pane
    
    def get_log_scroll_percentage(self):
        """Calculate the current log scroll position as a percentage"""
        if len(self.log_messages) <= 1:
            return 100  # If no messages or only one, we're at 100%
        
        # When scroll_offset is 0, we're at the bottom (newest messages) = 100%
        # When scroll_offset is max, we're at the top (oldest messages) = 0%
        max_scroll = len(self.log_messages) - 1
        if max_scroll == 0:
            return 100
        
        # Invert the percentage since offset 0 = bottom (100%) and max offset = top (0%)
        percentage = int(((max_scroll - self.log_scroll_offset) / max_scroll) * 100)
        return max(0, min(100, percentage))
    
    def refresh_files(self, pane=None):
        """Refresh the file list for specified pane or both panes"""
        panes_to_refresh = [pane] if pane else [self.left_pane, self.right_pane]
        
        for pane_data in panes_to_refresh:
            try:
                entries = list(pane_data['path'].iterdir())
                if not self.show_hidden:
                    entries = [e for e in entries if not e.name.startswith('.')]
                
                # Sort: directories first, then files, both alphabetically
                pane_data['files'] = sorted(entries, key=lambda x: (not x.is_dir(), x.name.lower()))
                
                # Add parent directory option if not at root
                if pane_data['path'] != pane_data['path'].parent:
                    pane_data['files'].insert(0, pane_data['path'].parent)
                    
            except PermissionError:
                pane_data['files'] = []
                
            # Reset selection if out of bounds
            if pane_data['selected_index'] >= len(pane_data['files']):
                pane_data['selected_index'] = max(0, len(pane_data['files']) - 1)
                
            # Don't clear selected files here - only clear when directory actually changes
            
    def get_file_info(self, path):
        """Get file information for display"""
        try:
            stat_info = path.stat()
            size = stat_info.st_size
            mtime = datetime.fromtimestamp(stat_info.st_mtime)
            
            # Format size using constants
            if size < SIZE_KB:
                size_str = f"{size}B"
            elif size < SIZE_MB:
                size_str = f"{size/SIZE_KB:.1f}K"
            elif size < SIZE_GB:
                size_str = f"{size/SIZE_MB:.1f}M"
            else:
                size_str = f"{size/SIZE_GB:.1f}G"
                
            return size_str, mtime.strftime(DATETIME_FORMAT)
        except (OSError, PermissionError):
            return "---", "---"
            
    def draw_header(self):
        """Draw the header with pane paths and controls"""
        height, width = self.stdscr.getmaxyx()
        left_pane_width = int(width * self.left_pane_ratio)
        right_pane_width = width - left_pane_width
        
        # Clear header area (avoid last column)
        try:
            self.stdscr.addstr(0, 0, " " * (width - 1), get_header_color())
        except curses.error:
            pass
        
        # Left pane path with safety checks
        if left_pane_width > 6:  # Minimum space needed
            left_path = str(self.left_pane['path'])
            max_left_path_width = max(1, left_pane_width - 4)
            if len(left_path) > max_left_path_width:
                left_path = "..." + left_path[-(max(1, max_left_path_width-3)):]
            
            left_color = get_header_color(self.active_pane == 'left')
            try:
                self.stdscr.addstr(0, 2, left_path[:max_left_path_width], left_color)
            except curses.error:
                pass  # Ignore drawing errors for narrow panes
        
        # Separator with bounds check
        if 0 <= left_pane_width < width:
            try:
                self.stdscr.addstr(0, left_pane_width, "│", get_boundary_color())
            except curses.error:
                pass
        
        # Right pane path with safety checks
        if right_pane_width > 6:  # Minimum space needed
            right_path = str(self.right_pane['path'])
            max_right_path_width = max(1, right_pane_width - 4)
            if len(right_path) > max_right_path_width:
                right_path = "..." + right_path[-(max(1, max_right_path_width-3)):]
                
            right_color = get_header_color(self.active_pane == 'right')
            try:
                right_start_x = left_pane_width + 2
                if right_start_x < width:
                    self.stdscr.addstr(0, right_start_x, right_path[:max_right_path_width], right_color)
            except curses.error:
                pass  # Ignore drawing errors for narrow panes
        
        # No controls in header anymore - moved to status bar
        
    def draw_pane(self, pane_data, start_x, pane_width, is_active):
        """Draw a single pane"""
        # Safety checks to prevent crashes
        if pane_width < 10:  # Minimum viable pane width
            return
        if start_x < 0 or start_x >= self.stdscr.getmaxyx()[1]:
            return
            
        height, width = self.stdscr.getmaxyx()
        # Allow log pane to be completely hidden (0 height) when ratio is 0
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 4  # Reserve space for header, log pane, and status
        
        # Calculate scroll offset
        if pane_data['selected_index'] < pane_data['scroll_offset']:
            pane_data['scroll_offset'] = pane_data['selected_index']
        elif pane_data['selected_index'] >= pane_data['scroll_offset'] + display_height:
            pane_data['scroll_offset'] = pane_data['selected_index'] - display_height + 1
            
        # Draw files
        for i in range(display_height):
            file_index = i + pane_data['scroll_offset']
            y = i + 1  # Start after header (no controls line anymore)
            
            if file_index >= len(pane_data['files']):
                break
                
            file_path = pane_data['files'][file_index]
            
            # Determine display name and attributes
            if file_index == 0 and len(pane_data['files']) > 0 and file_path == pane_data['path'].parent:
                display_name = ".."
                is_dir = True
            else:
                display_name = file_path.name
                is_dir = file_path.is_dir()
                
            # Get file info
            size_str, mtime_str = self.get_file_info(file_path)
            
            # Check if this file is multi-selected
            is_multi_selected = str(file_path) in pane_data['selected_files']
            
            # Check if this file is a search match
            is_search_match = (self.search_mode and is_active and 
                             file_index in self.search_matches)
            
            # Choose color based on file properties and selection
            is_executable = file_path.is_file() and os.access(file_path, os.X_OK)
            is_selected = file_index == pane_data['selected_index']
            
            color = get_file_color(is_dir, is_executable, is_selected, is_active)
            
            # Handle search match highlighting (takes precedence over multi-selection)
            if is_search_match and not is_selected:
                # Highlight search matches with underline
                base_color = get_file_color(is_dir, is_executable, False, False)
                color = base_color | curses.A_UNDERLINE
            # Handle multi-selection highlighting
            elif is_multi_selected and not is_selected:
                # Get base color and add standout for multi-selected files
                base_color = get_file_color(is_dir, is_executable, False, False)
                color = base_color | curses.A_STANDOUT
                
            # Add selection marker for multi-selected files
            selection_marker = "●" if is_multi_selected else " "
            
            # Format line to fit pane - with safety checks for narrow panes
            datetime_width = 16  # "YYYY-MM-DD HH:MM" = 16 characters
            size_width = 8
            marker_width = 2  # Space for selection marker
            
            # Safety check: ensure we have minimum space for formatting
            if pane_width < 20:  # Too narrow to display properly
                line = f"{selection_marker} {display_name[:pane_width-5]}..."
            else:
                # Calculate precise filename width for column alignment
                # Account for the fact that line will be truncated to pane_width-2
                usable_width = pane_width - 2
                
                if pane_width < 60:
                    # For narrow panes: "● filename size" (no datetime)
                    # Reserve space for: marker(2) + space(1) + size(8) = 11
                    name_width = usable_width - 11
                    
                    # Truncate filename only if necessary
                    if len(display_name) > name_width:
                        truncate_at = max(1, name_width - 3)  # Reserve 3 for "..."
                        display_name = display_name[:truncate_at] + "..."
                    
                    # Pad filename to maintain column alignment
                    padded_name = display_name.ljust(name_width)
                    line = f"{selection_marker} {padded_name}{size_str:>8}"
                else:
                    # For wider panes: "● filename size datetime"
                    # Reserve space for: marker(2) + space(1) + size(8) + space(1) + datetime(len) = 12 + datetime_width
                    name_width = usable_width - (12 + datetime_width)
                    
                    # Truncate filename only if necessary
                    if len(display_name) > name_width:
                        truncate_at = max(1, name_width - 3)  # Reserve 3 for "..."
                        display_name = display_name[:truncate_at] + "..."
                    
                    # Pad filename to maintain column alignment
                    padded_name = display_name.ljust(name_width)
                    line = f"{selection_marker} {padded_name} {size_str:>8} {mtime_str}"
            
            try:
                self.stdscr.addstr(y, start_x + 1, line[:pane_width-2], color)
            except curses.error:
                pass  # Ignore if we can't write to screen edge
                
    def draw_files(self):
        """Draw both file panes"""
        height, width = self.stdscr.getmaxyx()
        left_pane_width = int(width * self.left_pane_ratio)
        right_pane_width = width - left_pane_width
        # Allow log pane to be completely hidden (0 height) when ratio is 0
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        # Always reserve space for footer line (1) and status line (1)
        # Plus log content if visible
        file_pane_bottom = height - log_height - 2
        
        # Draw vertical separator for file panes
        for y in range(1, file_pane_bottom):
            try:
                self.stdscr.addstr(y, left_pane_width, "│", get_boundary_color())
            except curses.error:
                pass
        
        # Draw left pane
        self.draw_pane(self.left_pane, 0, left_pane_width, self.active_pane == 'left')
        
        # Draw right pane
        self.draw_pane(self.right_pane, left_pane_width, right_pane_width, self.active_pane == 'right')
        
    def draw_log_pane(self):
        """Draw the log pane at the bottom"""
        height, width = self.stdscr.getmaxyx()
        # Allow log pane to be completely hidden (0 height) when ratio is 0
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        left_pane_width = int(width * self.left_pane_ratio)
        
        # Always draw the file list footers at the correct position
        if log_height == 0:
            # When log is hidden, footers go right above status line
            footer_y = height - 2
        else:
            # When log is visible, footers go above the log area
            footer_y = height - log_height - 2
            
        # Draw horizontal separator and file list footers
        try:
            separator_line = "─" * width
            self.stdscr.addstr(footer_y, 0, separator_line, get_boundary_color())
            
            # Always draw file list footers
            self.draw_file_footers(footer_y, left_pane_width)
        except curses.error:
            pass
            
        # If log pane is hidden (0 height), don't draw log content
        if log_height == 0:
            return
            
        # Log content starts right after the footer line
        log_start_y = footer_y + 1
        
        # Calculate visible log messages (subtract 1 for the footer line)
        visible_lines = log_height - 1
        total_messages = len(self.log_messages)
        
        if total_messages == 0:
            try:
                self.stdscr.addstr(log_start_y, 2, "No log messages", curses.A_DIM)
            except curses.error:
                pass
            return
        
        # Auto-scroll to bottom if not manually scrolled
        if self.log_scroll_offset == 0:
            start_idx = max(0, total_messages - visible_lines)
        else:
            start_idx = max(0, total_messages - visible_lines - self.log_scroll_offset)
        
        # Draw log messages
        for i in range(visible_lines):
            msg_idx = start_idx + i
            y = log_start_y + i
            
            if msg_idx >= total_messages:
                break
                
            timestamp, source, message = self.log_messages[msg_idx]
            
            # Choose color based on source
            color = get_log_color(source)
            
            # Format log line
            log_line = f"{timestamp} [{source}] {message}"
            if len(log_line) > width - 2:
                log_line = log_line[:width-5] + "..."
                
            try:
                self.stdscr.addstr(y, 2, log_line, color)
            except curses.error:
                pass
                
    def draw_status(self):
        """Draw status line with file info and controls"""
        height, width = self.stdscr.getmaxyx()
        status_y = height - 1
        
        current_pane = self.get_current_pane()
        
        # If in search mode, show search interface
        if self.search_mode:
            # Fill entire status line with background color
            status_line = " " * (width - 1)
            self.safe_addstr(status_y, 0, status_line, get_status_color())
            
            # Show search prompt and pattern
            search_prompt = f"Search: {self.search_pattern}"
            if self.search_matches:
                match_info = f" ({self.search_match_index + 1}/{len(self.search_matches)} matches)"
                search_prompt += match_info
            else:
                if self.search_pattern.strip():
                    search_prompt += " (no matches)"
                else:
                    search_prompt += " (enter patterns separated by spaces)"
                
            # Add cursor indicator
            search_prompt += "_"
            
            # Draw search prompt
            self.safe_addstr(status_y, 2, search_prompt, get_status_color())
            
            # Show help text on the right if there's space
            help_text = "ESC:exit Enter:accept ↑↓:navigate Space:multi-pattern"
            if len(search_prompt) + len(help_text) + 6 < width:
                help_x = width - len(help_text) - 3
                if help_x > len(search_prompt) + 4:  # Ensure no overlap
                    self.safe_addstr(status_y, help_x, help_text, get_status_color() | curses.A_DIM)
            else:
                # Shorter help text for narrow terminals
                short_help = "ESC:exit Enter:accept ↑↓:nav"
                if len(search_prompt) + len(short_help) + 6 < width:
                    help_x = width - len(short_help) - 3
                    if help_x > len(search_prompt) + 4:
                        self.safe_addstr(status_y, help_x, short_help, get_status_color() | curses.A_DIM)
            return
        
        # Normal status display
        # Left side: status info
        status_parts = []
        if self.show_hidden:
            status_parts.append("showing hidden")
        
        # Add log scroll percentage
        log_percentage = self.get_log_scroll_percentage()
        status_parts.append(f"log: {log_percentage}%")
        
        left_status = f"({', '.join(status_parts)})" if status_parts else ""
        
        # Controls - progressively abbreviate to fit
        if width > 160:
            controls = "Space/Opt+Space:select  F:search  Opt+←→:h-resize  Ctrl+U/D:v-resize  Ctrl+K/L:log-scroll  PgUp/Dn:log-scroll  Tab:switch  ←→:nav  q:quit  h:hidden  d:debug"
        elif width > 140:
            controls = "Space/Opt+Space:select  F:search  Opt+←→:h-resize  Ctrl+U/D:v-resize  Ctrl+K/L:log-scroll  Tab:switch  ←→:nav  q:quit  h:hidden"
        elif width > 120:
            controls = "Space/Opt+Space:select  F:search  Opt+←→:h-resize  Ctrl+U/D:v-resize  Ctrl+K/L:log  Tab:switch  ←→:nav  q:quit  h:hidden"
        elif width > 100:
            controls = "Space/Opt+Space:select  F:search  Opt+←→:h-resize  Ctrl+U/D:v-resize  Tab:switch  ←→:nav  q:quit  h:hidden"
        elif width > 80:
            controls = "Space/Opt+Space:select  F:search  Opt+←→↕:resize  Tab:switch  ←→:nav  q:quit  h:hidden"
        else:
            controls = "Space:select  F:search  Opt+←→↕:resize  Tab:switch  q:quit  h:hidden"
        
        # Draw status line with background color
        # Fill entire status line with background color
        status_line = " " * (width - 1)
        self.safe_addstr(status_y, 0, status_line, get_status_color())
        
        # Always draw controls - they're the most important part
        if left_status:
            # Ensure left status fits and draw with proper color
            max_left_width = width - 20  # Reserve space for controls
            truncated_left_status = left_status[:max_left_width] if len(left_status) > max_left_width else left_status
            self.safe_addstr(status_y, 2, truncated_left_status, get_status_color())
            
            # Right-align controls
            controls_x = max(len(truncated_left_status) + 6, width - len(controls) - 3)
            if controls_x > len(truncated_left_status) + 4:  # Ensure no overlap
                self.safe_addstr(status_y, controls_x, controls, get_status_color())
            else:
                # If no room, just show controls without left status
                controls_x = max(2, (width - len(controls)) // 2)
                self.safe_addstr(status_y, controls_x, controls, get_status_color())
        else:
            # Center controls when no left status
            controls_x = max(2, (width - len(controls)) // 2)
            self.safe_addstr(status_y, controls_x, controls, get_status_color())
        
    def handle_enter(self):
        """Handle Enter key - navigate or open file"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            return
            
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Handle parent directory
        if (current_pane['selected_index'] == 0 and 
            len(current_pane['files']) > 0 and 
            selected_file == current_pane['path'].parent):
            current_pane['path'] = current_pane['path'].parent
            current_pane['selected_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()  # Clear selections when changing directory
            return
            
        if selected_file.is_dir():
            try:
                current_pane['path'] = selected_file
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
                current_pane['selected_files'].clear()  # Clear selections when changing directory
            except PermissionError:
                self.show_error("Permission denied")
        else:
            # For files, show file info
            self.show_info(f"File: {selected_file.name}")
            
    def show_error(self, message):
        """Show error message"""
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addstr(height - 1, 2, f"ERROR: {message}", get_error_color())
        self.stdscr.refresh()
        curses.napms(2000)  # Show for 2 seconds
        
    def show_info(self, message):
        """Show info message"""
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addstr(height - 1, 2, message)
        self.stdscr.refresh()
        curses.napms(1500)  # Show for 1.5 seconds
        
    def find_matches(self, pattern):
        """Find all files matching the fnmatch patterns in current pane
        
        Supports multiple space-delimited patterns where all patterns must match.
        For example: "ab*c 12?3" will match files that contain both "*ab*c*" and "*12?3*"
        """
        current_pane = self.get_current_pane()
        matches = []
        
        if not pattern or not current_pane['files']:
            return matches
            
        # Split pattern by spaces to get individual patterns
        patterns = pattern.strip().split()
        if not patterns:
            return matches
            
        # Convert all patterns to lowercase for case-insensitive matching
        # and wrap each pattern with wildcards to match "contains" behavior
        wrapped_patterns = []
        for p in patterns:
            p_lower = p.lower()
            # If pattern doesn't start with *, add it for "contains" matching
            if not p_lower.startswith('*'):
                p_lower = '*' + p_lower
            # If pattern doesn't end with *, add it for "contains" matching  
            if not p_lower.endswith('*'):
                p_lower = p_lower + '*'
            wrapped_patterns.append(p_lower)
        
        for i, file_path in enumerate(current_pane['files']):
            # Skip parent directory entry
            if (i == 0 and len(current_pane['files']) > 0 and 
                file_path == current_pane['path'].parent):
                continue
                
            filename = file_path.name.lower()
            
            # Check if filename matches ALL patterns
            all_match = True
            for wrapped_pattern in wrapped_patterns:
                if not fnmatch.fnmatch(filename, wrapped_pattern):
                    all_match = False
                    break
                    
            if all_match:
                matches.append(i)
                
        return matches
        
    def update_search_matches(self):
        """Update search matches and move cursor to nearest match"""
        self.search_matches = self.find_matches(self.search_pattern)
        
        if self.search_matches:
            current_pane = self.get_current_pane()
            current_index = current_pane['selected_index']
            
            # Find the next match at or after current position
            next_match = None
            for match_idx in self.search_matches:
                if match_idx >= current_index:
                    next_match = match_idx
                    break
                    
            # If no match found after current position, wrap to first match
            if next_match is None:
                next_match = self.search_matches[0]
                
            # Update cursor position
            current_pane['selected_index'] = next_match
            self.search_match_index = self.search_matches.index(next_match)
            
            # Ensure the selected item is visible (adjust scroll if needed)
            self.adjust_scroll_for_selection(current_pane)
        else:
            self.search_match_index = 0
            
    def adjust_scroll_for_selection(self, pane_data):
        """Ensure the selected item is visible by adjusting scroll offset"""
        height, width = self.stdscr.getmaxyx()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 4  # Reserve space for header, log pane, and status
        
        # Adjust scroll offset to keep selection visible
        if pane_data['selected_index'] < pane_data['scroll_offset']:
            pane_data['scroll_offset'] = pane_data['selected_index']
        elif pane_data['selected_index'] >= pane_data['scroll_offset'] + display_height:
            pane_data['scroll_offset'] = pane_data['selected_index'] - display_height + 1
            
    def enter_search_mode(self):
        """Enter incremental search mode"""
        self.search_mode = True
        self.search_pattern = ""
        self.search_matches = []
        self.search_match_index = 0
        self.needs_full_redraw = True
        
    def exit_search_mode(self):
        """Exit search mode"""
        self.search_mode = False
        self.search_pattern = ""
        self.search_matches = []
        self.search_match_index = 0
        self.needs_full_redraw = True
        
    def handle_search_input(self, key):
        """Handle input while in search mode"""
        if key == 27:  # ESC - exit search mode
            self.exit_search_mode()
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Enter - exit search mode and keep current position
            self.exit_search_mode()
            return True
        elif key == curses.KEY_BACKSPACE or key == KEY_BACKSPACE_1 or key == KEY_BACKSPACE_2:
            # Backspace - remove last character
            if self.search_pattern:
                self.search_pattern = self.search_pattern[:-1]
                self.update_search_matches()
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_UP or key == ord('k'):
            # Up arrow - go to previous match
            if self.search_matches:
                self.search_match_index = (self.search_match_index - 1) % len(self.search_matches)
                current_pane = self.get_current_pane()
                current_pane['selected_index'] = self.search_matches[self.search_match_index]
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_DOWN or key == ord('j'):
            # Down arrow - go to next match
            if self.search_matches:
                self.search_match_index = (self.search_match_index + 1) % len(self.search_matches)
                current_pane = self.get_current_pane()
                current_pane['selected_index'] = self.search_matches[self.search_match_index]
                self.needs_full_redraw = True
            return True
        elif 32 <= key <= 126:  # Printable characters
            # Add character to search pattern
            self.search_pattern += chr(key)
            self.update_search_matches()
            self.needs_full_redraw = True
            return True
            
        return False
        
    def adjust_pane_boundary(self, direction):
        """Adjust the boundary between left and right panes"""
        if direction == 'left':
            # Make left pane smaller, right pane larger
            self.left_pane_ratio = max(MIN_PANE_RATIO, self.left_pane_ratio - PANE_ADJUST_STEP)
        elif direction == 'right':
            # Make left pane larger, right pane smaller  
            self.left_pane_ratio = min(MAX_PANE_RATIO, self.left_pane_ratio + PANE_ADJUST_STEP)
            
        # Trigger a full redraw for the new pane layout
        self.needs_full_redraw = True
        
        # Show immediate feedback in log pane
        left_percent = int(self.left_pane_ratio * 100)
        right_percent = 100 - left_percent
        print(f"Pane split: {left_percent}% | {right_percent}%")
        
    def adjust_log_boundary(self, direction):
        """Adjust the boundary between file panes and log pane"""
        if direction == 'up':
            # Make log pane smaller, file panes larger
            self.log_height_ratio = max(MIN_LOG_HEIGHT_RATIO, self.log_height_ratio - LOG_HEIGHT_ADJUST_STEP)
        elif direction == 'down':
            # Make log pane larger, file panes smaller
            self.log_height_ratio = min(MAX_LOG_HEIGHT_RATIO, self.log_height_ratio + LOG_HEIGHT_ADJUST_STEP)
            
        # Trigger a full redraw for the new layout
        self.needs_full_redraw = True
        
        # Show immediate feedback in log pane
        log_percent = int(self.log_height_ratio * 100)
        file_percent = 100 - log_percent
        print(f"Layout: {file_percent}% files | {log_percent}% log")
        
    def show_color_palette(self):
        """Show all available colors supported by curses"""
        height, width = self.stdscr.getmaxyx()
        
        # Clear screen and show color palette
        self.stdscr.clear()
        
        # Draw header
        palette_title = "=== CURSES COLOR PALETTE ==="
        self.stdscr.addstr(1, (width - len(palette_title)) // 2, palette_title, get_header_color(True))
        
        # Get terminal capabilities
        max_colors = curses.COLORS if hasattr(curses, 'COLORS') else 8
        max_pairs = curses.COLOR_PAIRS if hasattr(curses, 'COLOR_PAIRS') else 64
        
        # Get color capabilities
        color_info = get_color_capabilities()
        
        try:
            self.stdscr.addstr(2, 4, f"Terminal: {max_colors} colors, {max_pairs} pairs, RGB: {'YES' if color_info['can_change_color'] else 'NO'}", curses.A_DIM)
        except curses.error:
            pass
        
        start_y = 4
        current_y = start_y
        
        # Show basic color constants
        try:
            self.stdscr.addstr(current_y, 4, "Basic Colors (0-7):", curses.A_BOLD)
            current_y += 1
        except curses.error:
            pass
        
        basic_colors = [
            ("BLACK", curses.COLOR_BLACK),
            ("RED", curses.COLOR_RED),
            ("GREEN", curses.COLOR_GREEN),
            ("YELLOW", curses.COLOR_YELLOW),
            ("BLUE", curses.COLOR_BLUE),
            ("MAGENTA", curses.COLOR_MAGENTA),
            ("CYAN", curses.COLOR_CYAN),
            ("WHITE", curses.COLOR_WHITE),
        ]
        
        for name, color_num in basic_colors:
            if current_y >= height - 8:  # Leave space for instructions
                break
            try:
                # Create a temporary color pair for demonstration
                temp_pair = 50 + color_num  # Use high numbers to avoid conflicts
                if temp_pair < max_pairs:
                    curses.init_pair(temp_pair, color_num, curses.COLOR_BLACK)
                    color_attr = curses.color_pair(temp_pair)
                    
                    self.stdscr.addstr(current_y, 6, f"{name:<10} ({color_num})", curses.A_NORMAL)
                    self.stdscr.addstr(current_y, 20, "  SAMPLE  ", color_attr)
                    
                    # Also show with white background
                    temp_pair_bg = 58 + color_num
                    if temp_pair_bg < max_pairs:
                        curses.init_pair(temp_pair_bg, color_num, curses.COLOR_WHITE)
                        color_attr_bg = curses.color_pair(temp_pair_bg)
                        self.stdscr.addstr(current_y, 32, "  ON WHITE  ", color_attr_bg)
                current_y += 1
            except curses.error:
                current_y += 1
                continue
        
        current_y += 1
        
        # Show extended colors if available
        if max_colors > 8:
            try:
                self.stdscr.addstr(current_y, 4, f"Extended Colors (8-{min(max_colors-1, 15)}):", curses.A_BOLD)
                current_y += 1
            except curses.error:
                pass
            
            # Show colors 8-15 if available
            for color_num in range(8, min(max_colors, 16)):
                if current_y >= height - 6:
                    break
                try:
                    temp_pair = 70 + color_num
                    if temp_pair < max_pairs:
                        curses.init_pair(temp_pair, color_num, curses.COLOR_BLACK)
                        color_attr = curses.color_pair(temp_pair)
                        
                        self.stdscr.addstr(current_y, 6, f"Color {color_num:<3}", curses.A_NORMAL)
                        self.stdscr.addstr(current_y, 16, "  SAMPLE  ", color_attr)
                    current_y += 1
                except curses.error:
                    current_y += 1
                    continue
        
        current_y += 1
        
        # Show text attributes
        try:
            self.stdscr.addstr(current_y, 4, "Text Attributes:", curses.A_BOLD)
            current_y += 1
        except curses.error:
            pass
        
        attributes = [
            ("A_NORMAL", curses.A_NORMAL),
            ("A_STANDOUT", curses.A_STANDOUT),
            ("A_UNDERLINE", curses.A_UNDERLINE),
            ("A_REVERSE", curses.A_REVERSE),
            ("A_BLINK", curses.A_BLINK),
            ("A_DIM", curses.A_DIM),
            ("A_BOLD", curses.A_BOLD),
        ]
        
        for name, attr in attributes:
            if current_y >= height - 3:
                break
            try:
                self.stdscr.addstr(current_y, 6, f"{name:<12}", curses.A_NORMAL)
                self.stdscr.addstr(current_y, 20, "SAMPLE TEXT", attr)
                current_y += 1
            except curses.error:
                current_y += 1
                continue
        
        # Show 256-color info if available
        if max_colors >= 256:
            try:
                self.stdscr.addstr(current_y, 4, f"Terminal supports 256 colors! (showing first 16)", curses.A_DIM)
                current_y += 1
            except curses.error:
                pass
        
        # Instructions at bottom
        try:
            self.stdscr.addstr(height - 2, 4, "Press 'n' for next page, 'p' for previous, any other key to return", curses.A_BOLD)
        except curses.error:
            pass
            
        self.stdscr.refresh()
        
        # Wait for key press
        key = self.stdscr.getch()
        
        # Handle pagination for 256-color terminals
        if key == ord('n') or key == ord('N'):
            self.show_extended_colors()
        elif key == ord('p') or key == ord('P'):
            # Already on first page, just return
            pass
    
    def show_extended_colors(self):
        """Show extended color palette for 256-color terminals"""
        height, width = self.stdscr.getmaxyx()
        max_colors = curses.COLORS if hasattr(curses, 'COLORS') else 8
        max_pairs = curses.COLOR_PAIRS if hasattr(curses, 'COLOR_PAIRS') else 64
        
        if max_colors < 256:
            return  # Not supported
        
        self.stdscr.clear()
        
        # Draw header
        palette_title = "=== EXTENDED COLORS (16-255) ==="
        self.stdscr.addstr(1, (width - len(palette_title)) // 2, palette_title, get_header_color(True))
        
        try:
            self.stdscr.addstr(2, 4, "256-color palette (colors 16-255)", curses.A_DIM)
        except curses.error:
            pass
        
        start_y = 4
        current_y = start_y
        colors_per_row = min(16, (width - 8) // 5)  # Adjust based on screen width
        
        # Show colors 16-255 in a grid
        for color_start in range(16, min(256, max_colors), colors_per_row * 8):  # Show in chunks
            if current_y >= height - 4:
                break
                
            # Show 8 rows of colors at a time
            for row in range(8):
                if current_y >= height - 4:
                    break
                    
                try:
                    row_text = f"{color_start + row * colors_per_row:3d}: "
                    self.stdscr.addstr(current_y, 4, row_text, curses.A_DIM)
                    
                    x_offset = 9
                    for col in range(colors_per_row):
                        color_num = color_start + row * colors_per_row + col
                        if color_num >= min(256, max_colors):
                            break
                            
                        try:
                            # Use a high color pair number to avoid conflicts
                            temp_pair = 100 + (color_num % (max_pairs - 100))
                            curses.init_pair(temp_pair, curses.COLOR_WHITE, color_num)
                            color_attr = curses.color_pair(temp_pair)
                            
                            self.stdscr.addstr(current_y, x_offset, f"{color_num:3d}", color_attr)
                            x_offset += 4
                        except curses.error:
                            x_offset += 4
                            continue
                    
                    current_y += 1
                except curses.error:
                    current_y += 1
                    continue
            
            current_y += 1  # Extra space between chunks
        
        # Instructions at bottom
        try:
            self.stdscr.addstr(height - 2, 4, "Press 'p' for previous page, any other key to return to debug mode", curses.A_BOLD)
        except curses.error:
            pass
            
        self.stdscr.refresh()
        
        # Wait for key press
        key = self.stdscr.getch()
        
        if key == ord('p') or key == ord('P'):
            self.show_color_palette()  # Go back to main palette

    def debug_mode(self):
        """Interactive debug mode to detect modifier key combinations"""
        height, width = self.stdscr.getmaxyx()
        
        # Clear screen and show debug interface
        self.stdscr.clear()
        
        # Draw debug header
        debug_title = "=== MODIFIER KEY DETECTION MODE ==="
        self.stdscr.addstr(2, (width - len(debug_title)) // 2, debug_title, get_header_color(True))
        
        # Instructions
        instructions = [
            "",
            "Try pressing these key combinations:",
            "",
            "• Option+Space (works on macOS)",
            "• Option+Left/Right (horizontal pane resizing)",
            "• Ctrl+U/Ctrl+D (vertical pane resizing)",
            "• Shift+Up/Down (log pane scrolling - may not work)",
            "• Ctrl+K/Ctrl+L (alternative log scrolling)",
            "• Page Up/Down (also scrolls log)",
            "• Ctrl+Space   (alternative)",
            "• Ctrl+S       (alternative)",
            "• Command+Space (probably won't work)",
            "• F (F key - enter search mode)",
            "",
            "Key codes will appear below as you press them.",
            "If a combination works for upward selection, it will be noted.",
            "",
            "Press 'c' to show color palette",
            "Press 'q' to exit debug mode and return to file manager"
        ]
        
        for i, line in enumerate(instructions):
            try:
                self.stdscr.addstr(4 + i, 4, line)
            except curses.error:
                pass
        
        # Results area
        results_y = 4 + len(instructions) + 2
        self.stdscr.addstr(results_y, 4, "Key detection results:", curses.A_BOLD)
        results_start_y = results_y + 2
        
        self.stdscr.refresh()
        
        # Debug loop
        result_line = 0
        while True:
            debug_key = self.stdscr.getch()
            
            if debug_key == ord('q') or debug_key == ord('Q'):
                break
            elif debug_key == ord('c') or debug_key == ord('C'):
                self.show_color_palette()
                # Redraw debug mode after returning from color palette
                self.stdscr.clear()
                self.stdscr.addstr(2, (width - len(debug_title)) // 2, debug_title, get_header_color(True))
                for i, line in enumerate(instructions):
                    try:
                        self.stdscr.addstr(4 + i, 4, line)
                    except curses.error:
                        pass
                self.stdscr.addstr(results_y, 4, "Key detection results:", curses.A_BOLD)
                # Redraw previous results
                for i in range(min(result_line, 7)):
                    # We can't easily restore previous results, so just show a message
                    pass
                self.stdscr.refresh()
                continue
            
            # Display the key code
            y_pos = results_start_y + result_line
            if y_pos < height - 2:  # Don't write past screen bottom
                key_info = ""
                
                if debug_key == 0:
                    key_info = f"Ctrl+Space detected! (key code: {debug_key}) ✓ WORKS FOR UPWARD SELECTION"
                    color = get_file_color(False, False, True, True) | curses.A_BOLD
                elif debug_key == 19:
                    key_info = f"Ctrl+S detected! (key code: {debug_key}) ✓ WORKS FOR UPWARD SELECTION"  
                    color = get_file_color(False, False, True, True) | curses.A_BOLD
                elif debug_key == 27:
                    # Check for ESC sequences (Option+Left/Right)
                    next_key = self.stdscr.getch()
                    if next_key == 98:  # 'b'
                        key_info = f"Option+Left detected! (key codes: 27, 98) ✓ WORKS FOR PANE RESIZE"
                        color = get_file_color(False, False, True, True) | curses.A_BOLD
                    elif next_key == 102:  # 'f'
                        key_info = f"Option+Right detected! (key codes: 27, 102) ✓ WORKS FOR PANE RESIZE"
                        color = get_file_color(False, False, True, True) | curses.A_BOLD
                    else:
                        key_info = f"ESC sequence: 27 followed by {next_key} (char: {chr(next_key) if 32 <= next_key <= 126 else 'non-printable'})"
                        color = curses.A_NORMAL
                elif debug_key == 194:
                    # Check for Option+Space sequence
                    next_key = self.stdscr.getch()
                    if next_key == 160:
                        key_info = f"Option+Space detected! (key codes: 194, 160) ✓ WORKS FOR UPWARD SELECTION"
                        color = get_file_color(False, False, True, True) | curses.A_BOLD
                    else:
                        key_info = f"Option key sequence: 194 followed by {next_key} (unknown)"
                        color = curses.A_NORMAL
                elif debug_key == 337:
                    key_info = f"Shift+Up detected! (key code: {debug_key}) ✓ WORKS FOR LOG SCROLL UP"
                    color = get_file_color(False, False, True, True) | curses.A_BOLD
                elif debug_key == 336:
                    key_info = f"Shift+Down detected! (key code: {debug_key}) ✓ WORKS FOR LOG SCROLL DOWN"
                    color = get_file_color(False, False, True, True) | curses.A_BOLD
                elif debug_key == 393:
                    key_info = f"Alt Shift+Up detected! (key code: {debug_key}) ✓ WORKS FOR LOG SCROLL UP"
                    color = get_file_color(False, False, True, True) | curses.A_BOLD
                elif debug_key == 402:
                    key_info = f"Alt Shift+Down detected! (key code: {debug_key}) ✓ WORKS FOR LOG SCROLL DOWN"
                    color = get_file_color(False, False, True, True) | curses.A_BOLD
                elif debug_key == 11:
                    key_info = f"Ctrl+K detected! (key code: {debug_key}) ✓ WORKS FOR LOG SCROLL UP"
                    color = get_file_color(False, False, True, True) | curses.A_BOLD
                elif debug_key == 12:
                    key_info = f"Ctrl+L detected! (key code: {debug_key}) ✓ WORKS FOR LOG SCROLL DOWN"
                    color = get_file_color(False, False, True, True) | curses.A_BOLD
                elif debug_key == 1:
                    key_info = f"Ctrl+A detected (key code: {debug_key})"
                    color = curses.A_NORMAL
                elif 32 <= debug_key <= 126:
                    key_info = f"Key '{chr(debug_key)}' pressed (key code: {debug_key})"
                    color = curses.A_NORMAL
                else:
                    key_info = f"Special key pressed (key code: {debug_key})"
                    color = curses.A_NORMAL
                
                try:
                    # Clear the line first (avoid last column)
                    clear_width = min(width - 9, width - 4)  # Safe width for clearing
                    if clear_width > 0:
                        self.stdscr.addstr(y_pos, 4, " " * clear_width)
                        self.stdscr.addstr(y_pos, 4, key_info[:clear_width], color)
                    self.stdscr.refresh()
                    result_line += 1
                except curses.error:
                    pass
            
            # If we've filled the results area, scroll up
            if result_line >= 8:  # Keep last 8 results visible
                result_line = 7
        
    def run(self):
        """Main application loop"""
        while True:
            # Only do full redraw when needed
            if self.needs_full_redraw:
                self.refresh_files()
                
                # Clear screen
                self.stdscr.clear()
                
                # Draw interface
                self.draw_header()
                self.draw_files()
                self.draw_log_pane()
                self.draw_status()
                
                # Refresh screen
                self.stdscr.refresh()
                self.needs_full_redraw = False
            
            # Get user input
            key = self.stdscr.getch()
            current_pane = self.get_current_pane()
            
            # Handle search mode input first
            if self.search_mode:
                if self.handle_search_input(key):
                    continue  # Search mode handled the key
            
            if key == ord('q') or key == ord('Q'):
                break
            elif key == KEY_CTRL_U:  # Ctrl+U - make log pane smaller
                self.adjust_log_boundary('up')
            elif key == KEY_CTRL_D:  # Ctrl+D - make log pane larger
                self.adjust_log_boundary('down')
            elif key == 11:  # Ctrl+K - scroll log up
                if self.log_scroll_offset < len(self.log_messages) - 1:
                    self.log_scroll_offset += 1
                    self.needs_full_redraw = True
            elif key == 12:  # Ctrl+L - scroll log down
                if self.log_scroll_offset > 0:
                    self.log_scroll_offset -= 1
                    self.needs_full_redraw = True
            elif key == curses.KEY_RESIZE:  # Terminal window resized
                # Clear screen and trigger full redraw to handle new dimensions
                self.stdscr.clear()
                self.needs_full_redraw = True
            elif key == KEY_TAB:  # Tab key - switch panes
                self.active_pane = 'right' if self.active_pane == 'left' else 'left'
                self.needs_full_redraw = True
            elif key == curses.KEY_UP or key == ord('k'):
                if current_pane['selected_index'] > 0:
                    current_pane['selected_index'] -= 1
                    self.needs_full_redraw = True
            elif key == curses.KEY_DOWN or key == ord('j'):
                if current_pane['selected_index'] < len(current_pane['files']) - 1:
                    current_pane['selected_index'] += 1
                    self.needs_full_redraw = True
            elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
                self.handle_enter()
                self.needs_full_redraw = True
            elif key == ord('h') or key == ord('H'):
                self.show_hidden = not self.show_hidden
                # Reset both panes
                self.left_pane['selected_index'] = 0
                self.left_pane['scroll_offset'] = 0
                self.right_pane['selected_index'] = 0
                self.right_pane['scroll_offset'] = 0
                self.needs_full_redraw = True
            elif key == curses.KEY_HOME:
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
                self.needs_full_redraw = True
            elif key == curses.KEY_END:
                current_pane['selected_index'] = max(0, len(current_pane['files']) - 1)
                self.needs_full_redraw = True
            elif key == curses.KEY_PPAGE:  # Page Up - scroll log up when Ctrl is held, otherwise file navigation
                # Check if this is Ctrl+Page Up for log scrolling
                if self.log_scroll_offset < len(self.log_messages) - 1:
                    # Try log scrolling first, fall back to file navigation
                    self.log_scroll_offset += 5  # Scroll multiple lines
                    self.log_scroll_offset = min(self.log_scroll_offset, len(self.log_messages) - 1)
                    self.needs_full_redraw = True
                else:
                    # Regular file navigation
                    current_pane['selected_index'] = max(0, current_pane['selected_index'] - 10)
                    self.needs_full_redraw = True
            elif key == curses.KEY_NPAGE:  # Page Down - scroll log down when Ctrl is held, otherwise file navigation  
                # Check if this is Ctrl+Page Down for log scrolling
                if self.log_scroll_offset > 0:
                    # Try log scrolling first, fall back to file navigation
                    self.log_scroll_offset -= 5  # Scroll multiple lines
                    self.log_scroll_offset = max(0, self.log_scroll_offset)
                    self.needs_full_redraw = True
                else:
                    # Regular file navigation
                    current_pane['selected_index'] = min(len(current_pane['files']) - 1, current_pane['selected_index'] + 10)
                    self.needs_full_redraw = True
            elif key == curses.KEY_BACKSPACE or key == KEY_BACKSPACE_2 or key == KEY_BACKSPACE_1:  # Backspace - go to parent directory
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                        current_pane['selected_files'].clear()  # Clear selections when changing directory
                        self.needs_full_redraw = True
                    except PermissionError:
                        self.show_error("Permission denied")
                        self.needs_full_redraw = True
            elif key == curses.KEY_LEFT and self.active_pane == 'left':  # Left arrow in left pane - go to parent
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                        current_pane['selected_files'].clear()  # Clear selections when changing directory
                    except PermissionError:
                        self.show_error("Permission denied")
            elif key == curses.KEY_RIGHT and self.active_pane == 'right':  # Right arrow in right pane - go to parent
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                        current_pane['selected_files'].clear()  # Clear selections when changing directory
                    except PermissionError:
                        self.show_error("Permission denied")
            elif key == curses.KEY_RIGHT and self.active_pane == 'left':  # Right arrow in left pane - switch to right pane
                self.active_pane = 'right'
            elif key == curses.KEY_LEFT and self.active_pane == 'right':  # Left arrow in right pane - switch to left pane
                self.active_pane = 'left'
            elif key == ord('l'):  # 'l' key - scroll log up
                if self.log_scroll_offset < len(self.log_messages) - 1:
                    self.log_scroll_offset += 1
                    self.needs_full_redraw = True
            elif key == ord('L'):  # 'L' key - scroll log down  
                if self.log_scroll_offset > 0:
                    self.log_scroll_offset -= 1
                    self.needs_full_redraw = True
            elif key == 337:  # Shift+Up in many terminals
                if self.log_scroll_offset < len(self.log_messages) - 1:
                    self.log_scroll_offset += 1
                    self.needs_full_redraw = True
            elif key == 336:  # Shift+Down in many terminals  
                if self.log_scroll_offset > 0:
                    self.log_scroll_offset -= 1
                    self.needs_full_redraw = True
            elif key == 393:  # Alternative Shift+Up code
                if self.log_scroll_offset < len(self.log_messages) - 1:
                    self.log_scroll_offset += 1
                    self.needs_full_redraw = True
            elif key == 402:  # Alternative Shift+Down code
                if self.log_scroll_offset > 0:
                    self.log_scroll_offset -= 1
                    self.needs_full_redraw = True
            elif key == ord(' '):  # Space key - toggle selection and move down
                self.toggle_selection()
                self.needs_full_redraw = True

            elif key == 0:  # Ctrl+Space - toggle selection and move up
                self.toggle_selection_up()
                self.needs_full_redraw = True
            elif key == 19:  # Ctrl+S - toggle selection and move up  
                self.toggle_selection_up()
                self.needs_full_redraw = True
            elif key == 27:  # ESC key - check for Option key sequences
                # Option+Left sends 27 followed by 'b' (98)
                # Option+Right sends 27 followed by 'f' (102)
                # Option+Space sends 194 followed by 160
                next_key = self.stdscr.getch()
                if next_key == 98:  # Option+Left (ESC + 'b')
                    self.adjust_pane_boundary('left')
                elif next_key == 102:  # Option+Right (ESC + 'f')
                    self.adjust_pane_boundary('right')

                else:
                    # Log unknown ESC sequence for debugging
                    print(f"Unknown ESC sequence: 27, {next_key}")
            elif key == 194:  # Option+Space sequence (first byte)
                # Option+Space sends 194 followed by 160 on macOS
                next_key = self.stdscr.getch()
                if next_key == 160:  # Option+Space
                    self.toggle_selection_up()
                    self.needs_full_redraw = True
                else:
                    # Log unknown Option key sequence for debugging
                    print(f"Unknown Option key sequence: 194, {next_key}")
            elif key == ord('t') or key == ord('T'):  # 't' key - test log output
                print(f"{APP_NAME} v{VERSION} - Test stdout message")
                print("Another stdout message with timestamp")
                sys.stderr.write("Test stderr error message\n")
                import time
                time.sleep(0.1)  # Small delay to see messages appear
                print(f"Current time: {datetime.now()}")
            elif key == ord('d'):  # 'd' key - debug mode to detect modifier keys
                self.debug_mode()
            elif key == ord('f') or key == ord('F'):  # 'F' key - enter search mode
                self.enter_search_mode()
            elif key == ord('-'):  # '-' key - reset pane ratio to 50/50
                self.left_pane_ratio = 0.5
                self.needs_full_redraw = True
                print("Pane split reset to 50% | 50%")
        
        # Restore stdout/stderr before exiting
        self.restore_stdio()

def main(stdscr):
    """Main function to run the file manager"""
    fm = None
    try:
        fm = FileManager(stdscr)
        fm.run()
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        pass
    except Exception as e:
        # Restore stdout/stderr before handling exception
        if fm is not None:
            fm.restore_stdio()
        
        # Print error information to help with debugging
        import traceback
        print(f"\nTFM encountered an unexpected error:", file=sys.stderr)
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
        print("\nFull traceback:", file=sys.stderr)
        traceback.print_exc()
        
        # Re-raise the exception so it can be seen after TFM exits
        raise
    finally:
        # Always restore stdout/stderr in case of any exit path
        if fm is not None:
            fm.restore_stdio()

if __name__ == "__main__":
    curses.wrapper(main)