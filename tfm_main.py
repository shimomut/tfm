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
from pathlib import Path
from datetime import datetime
from collections import deque

# Import constants
from tfm_const import *

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
            'files': []
        }
        self.right_pane = {
            'path': Path.home(),  # Start right pane in home directory
            'selected_index': 0,
            'scroll_offset': 0,
            'files': []
        }
        
        self.active_pane = 'left'  # 'left' or 'right'
        self.show_hidden = False
        
        # Log pane setup
        self.log_messages = deque(maxlen=MAX_LOG_MESSAGES)
        self.log_scroll_offset = 0
        
        # Redirect stdout and stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = LogCapture(self.log_messages, "STDOUT")
        sys.stderr = LogCapture(self.log_messages, "STDERR")
        
        # Initialize colors
        curses.start_color()
        curses.init_pair(COLOR_DIRECTORIES, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_EXECUTABLES, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_SELECTED, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_ERROR, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(COLOR_HEADER, curses.COLOR_WHITE, curses.COLOR_BLUE)
        
        # Configure curses
        curses.curs_set(0)  # Hide cursor
        self.stdscr.keypad(True)
        
    def __del__(self):
        """Restore stdout/stderr when object is destroyed"""
        if hasattr(self, 'original_stdout'):
            sys.stdout = self.original_stdout
        if hasattr(self, 'original_stderr'):
            sys.stderr = self.original_stderr
        
    def get_current_pane(self):
        """Get the currently active pane"""
        return self.left_pane if self.active_pane == 'left' else self.right_pane
    
    def get_inactive_pane(self):
        """Get the inactive pane"""
        return self.right_pane if self.active_pane == 'left' else self.left_pane
    
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
        pane_width = width // 2
        
        # Clear header area
        self.stdscr.addstr(0, 0, " " * width, curses.color_pair(COLOR_HEADER))
        
        # Left pane path
        left_path = str(self.left_pane['path'])
        max_path_width = pane_width - 4
        if len(left_path) > max_path_width:
            left_path = "..." + left_path[-(max_path_width-3):]
        
        left_color = curses.color_pair(COLOR_HEADER) | curses.A_BOLD if self.active_pane == 'left' else curses.color_pair(COLOR_HEADER)
        self.stdscr.addstr(0, 2, left_path, left_color)
        
        # Separator
        self.stdscr.addstr(0, pane_width, "│", curses.color_pair(COLOR_HEADER))
        
        # Right pane path
        right_path = str(self.right_pane['path'])
        if len(right_path) > max_path_width:
            right_path = "..." + right_path[-(max_path_width-3):]
            
        right_color = curses.color_pair(COLOR_HEADER) | curses.A_BOLD if self.active_pane == 'right' else curses.color_pair(COLOR_HEADER)
        self.stdscr.addstr(0, pane_width + 2, right_path, right_color)
        
        # Controls at bottom of header
        controls = "Tab/←→:switch ←/→/Backspace:up l/L:log-scroll t:test q:quit h:hidden"
        self.stdscr.addstr(1, 2, controls, curses.color_pair(COLOR_HEADER))
        
    def draw_pane(self, pane_data, start_x, pane_width, is_active):
        """Draw a single pane"""
        height, width = self.stdscr.getmaxyx()
        log_height = max(MIN_LOG_HEIGHT, int(height * DEFAULT_LOG_HEIGHT_RATIO))
        display_height = height - log_height - 5  # Reserve space for header, log pane, and status
        
        # Calculate scroll offset
        if pane_data['selected_index'] < pane_data['scroll_offset']:
            pane_data['scroll_offset'] = pane_data['selected_index']
        elif pane_data['selected_index'] >= pane_data['scroll_offset'] + display_height:
            pane_data['scroll_offset'] = pane_data['selected_index'] - display_height + 1
            
        # Draw files
        for i in range(display_height):
            file_index = i + pane_data['scroll_offset']
            y = i + 2  # Start after header
            
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
            
            # Choose color based on selection and activity
            base_color = curses.A_NORMAL
            if is_dir:
                base_color = curses.color_pair(COLOR_DIRECTORIES) | curses.A_BOLD
            elif file_path.is_file() and os.access(file_path, os.X_OK):
                base_color = curses.color_pair(COLOR_EXECUTABLES)
                
            if file_index == pane_data['selected_index'] and is_active:
                color = curses.color_pair(COLOR_SELECTED) | curses.A_REVERSE
            elif file_index == pane_data['selected_index']:
                color = base_color | curses.A_UNDERLINE
            else:
                color = base_color
                
            # Format line to fit pane - allocate proper space for full datetime
            datetime_width = 16  # "YYYY-MM-DD HH:MM" = 16 characters
            size_width = 8
            name_width = pane_width - datetime_width - size_width - 4  # 4 for spacing
            
            if len(display_name) > name_width:
                display_name = display_name[:name_width-3] + "..."
                
            # Show full datetime format or abbreviated based on pane width
            if pane_width < 60:
                # For narrow panes, show just filename and size
                line = f"{display_name:<{name_width + datetime_width}} {size_str:>8}"
            else:
                # For wider panes, show full format
                line = f"{display_name:<{name_width}} {size_str:>8} {mtime_str}"
            
            try:
                self.stdscr.addstr(y, start_x + 1, line[:pane_width-2], color)
            except curses.error:
                pass  # Ignore if we can't write to screen edge
                
    def draw_files(self):
        """Draw both file panes"""
        height, width = self.stdscr.getmaxyx()
        pane_width = width // 2
        log_height = max(MIN_LOG_HEIGHT, int(height * DEFAULT_LOG_HEIGHT_RATIO))
        file_pane_bottom = height - log_height - 2
        
        # Draw vertical separator for file panes
        for y in range(2, file_pane_bottom):
            try:
                self.stdscr.addstr(y, pane_width, "│", curses.color_pair(COLOR_HEADER))
            except curses.error:
                pass
        
        # Draw left pane
        self.draw_pane(self.left_pane, 0, pane_width, self.active_pane == 'left')
        
        # Draw right pane
        self.draw_pane(self.right_pane, pane_width, pane_width, self.active_pane == 'right')
        
    def draw_log_pane(self):
        """Draw the log pane at the bottom"""
        height, width = self.stdscr.getmaxyx()
        log_height = max(MIN_LOG_HEIGHT, int(height * DEFAULT_LOG_HEIGHT_RATIO))
        log_start_y = height - log_height - 1
        
        # Draw horizontal separator
        try:
            separator_line = "─" * width
            self.stdscr.addstr(log_start_y - 1, 0, separator_line, curses.color_pair(COLOR_HEADER))
            
            # Log pane header with version
            log_header = f" Log ({len(self.log_messages)} messages) - {APP_NAME} v{VERSION} "
            self.stdscr.addstr(log_start_y - 1, 2, log_header, curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        except curses.error:
            pass
        
        # Calculate visible log messages
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
            if source == "STDERR":
                color = curses.color_pair(COLOR_ERROR)  # Red for stderr
            else:
                color = curses.A_NORMAL
            
            # Format log line
            log_line = f"{timestamp} [{source}] {message}"
            if len(log_line) > width - 2:
                log_line = log_line[:width-5] + "..."
                
            try:
                self.stdscr.addstr(y, 2, log_line, color)
            except curses.error:
                pass
                
    def draw_status(self):
        """Draw status line"""
        height, width = self.stdscr.getmaxyx()
        status_y = height - 1
        
        current_pane = self.get_current_pane()
        
        if current_pane['files']:
            status = f"[{self.active_pane.upper()}] File {current_pane['selected_index'] + 1} of {len(current_pane['files'])}"
            if self.show_hidden:
                status += " (showing hidden)"
        else:
            status = f"[{self.active_pane.upper()}] No files"
            
        self.stdscr.addstr(status_y, 2, status)
        
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
            return
            
        if selected_file.is_dir():
            try:
                current_pane['path'] = selected_file
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
            except PermissionError:
                self.show_error("Permission denied")
        else:
            # For files, show file info
            self.show_info(f"File: {selected_file.name}")
            
    def show_error(self, message):
        """Show error message"""
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addstr(height - 1, 2, f"ERROR: {message}", curses.color_pair(COLOR_ERROR))
        self.stdscr.refresh()
        curses.napms(2000)  # Show for 2 seconds
        
    def show_info(self, message):
        """Show info message"""
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addstr(height - 1, 2, message)
        self.stdscr.refresh()
        curses.napms(1500)  # Show for 1.5 seconds
        
    def run(self):
        """Main application loop"""
        while True:
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
            
            # Get user input
            key = self.stdscr.getch()
            current_pane = self.get_current_pane()
            
            if key == ord('q') or key == ord('Q'):
                break
            elif key == KEY_TAB:  # Tab key - switch panes
                self.active_pane = 'right' if self.active_pane == 'left' else 'left'
            elif key == curses.KEY_UP or key == ord('k'):
                if current_pane['selected_index'] > 0:
                    current_pane['selected_index'] -= 1
            elif key == curses.KEY_DOWN or key == ord('j'):
                if current_pane['selected_index'] < len(current_pane['files']) - 1:
                    current_pane['selected_index'] += 1
            elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
                self.handle_enter()
            elif key == ord('h') or key == ord('H'):
                self.show_hidden = not self.show_hidden
                # Reset both panes
                self.left_pane['selected_index'] = 0
                self.left_pane['scroll_offset'] = 0
                self.right_pane['selected_index'] = 0
                self.right_pane['scroll_offset'] = 0
            elif key == curses.KEY_HOME:
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
            elif key == curses.KEY_END:
                current_pane['selected_index'] = max(0, len(current_pane['files']) - 1)
            elif key == curses.KEY_PPAGE:  # Page Up
                current_pane['selected_index'] = max(0, current_pane['selected_index'] - 10)
            elif key == curses.KEY_NPAGE:  # Page Down
                current_pane['selected_index'] = min(len(current_pane['files']) - 1, current_pane['selected_index'] + 10)
            elif key == curses.KEY_BACKSPACE or key == KEY_BACKSPACE_2 or key == KEY_BACKSPACE_1:  # Backspace - go to parent directory
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                    except PermissionError:
                        self.show_error("Permission denied")
            elif key == curses.KEY_LEFT and self.active_pane == 'left':  # Left arrow in left pane - go to parent
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                    except PermissionError:
                        self.show_error("Permission denied")
            elif key == curses.KEY_RIGHT and self.active_pane == 'right':  # Right arrow in right pane - go to parent
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                    except PermissionError:
                        self.show_error("Permission denied")
            elif key == curses.KEY_RIGHT and self.active_pane == 'left':  # Right arrow in left pane - switch to right pane
                self.active_pane = 'right'
            elif key == curses.KEY_LEFT and self.active_pane == 'right':  # Left arrow in right pane - switch to left pane
                self.active_pane = 'left'
            elif key == ord('l'):  # 'l' key - scroll log up
                if self.log_scroll_offset < len(self.log_messages) - 1:
                    self.log_scroll_offset += 1
            elif key == ord('L'):  # 'L' key - scroll log down  
                if self.log_scroll_offset > 0:
                    self.log_scroll_offset -= 1
            elif key == ord('t') or key == ord('T'):  # 't' key - test log output
                print(f"{APP_NAME} v{VERSION} - Test stdout message")
                print("Another stdout message with timestamp")
                sys.stderr.write("Test stderr error message\n")
                import time
                time.sleep(0.1)  # Small delay to see messages appear
                print(f"Current time: {datetime.now()}")
        
        # Restore stdout/stderr before exiting
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

def main(stdscr):
    """Main function to run the file manager"""
    try:
        fm = FileManager(stdscr)
        fm.run()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    curses.wrapper(main)