#!/usr/bin/env python3
"""
TFM Log Manager - Handles logging and log display functionality
"""

import sys
from datetime import datetime
from collections import deque
from tfm_const import LOG_TIME_FORMAT, MAX_LOG_MESSAGES
from tfm_colors import get_log_color, get_status_color


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


class LogManager:
    """Manages logging system and log display"""
    
    def __init__(self, config):
        # Log pane setup
        max_log_messages = getattr(config, 'MAX_LOG_MESSAGES', MAX_LOG_MESSAGES)
        self.log_messages = deque(maxlen=max_log_messages)
        self.log_scroll_offset = 0
        
        # Store original streams
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Redirect stdout and stderr
        sys.stdout = LogCapture(self.log_messages, "STDOUT")
        sys.stderr = LogCapture(self.log_messages, "STDERR")
        
    def add_startup_messages(self, version, github_url, app_name):
        """Add startup messages directly to log pane"""
        timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
        self.log_messages.append((timestamp, "SYSTEM", f"TFM {version}"))
        self.log_messages.append((timestamp, "SYSTEM", f"GitHub: {github_url}"))
        self.log_messages.append((timestamp, "SYSTEM", f"{app_name} started successfully"))
        self.log_messages.append((timestamp, "CONFIG", "Configuration loaded"))
    
    def get_log_scroll_percentage(self, display_height=None):
        """Calculate the current log scroll position as a percentage"""
        if len(self.log_messages) <= 1:
            return 0
        
        # Calculate max scroll based on display height if available
        total_messages = len(self.log_messages)
        if display_height is not None:
            max_scroll = max(0, total_messages - display_height)
        else:
            # Fallback to conservative estimate
            max_scroll = max(0, total_messages - 1)
        
        if max_scroll == 0:
            return 0
        
        # Calculate percentage
        percentage = (self.log_scroll_offset / max_scroll) * 100
        return max(0, min(100, percentage))
    
    def scroll_log_up(self, lines=1):
        """Scroll log up by specified number of lines (toward older messages)"""
        # Use a conservative estimate for max scroll - final capping happens in draw_log_pane
        total_messages = len(self.log_messages)
        if total_messages > 0:
            # Allow scrolling up to the total number of messages
            # The draw method will cap this properly based on display height
            self.log_scroll_offset += lines
            return True
        return False
    
    def scroll_log_down(self, lines=1):
        """Scroll log down by specified number of lines (toward newer messages)"""
        if self.log_scroll_offset > 0:
            self.log_scroll_offset = max(0, self.log_scroll_offset - lines)
            return True
        return False
    
    def draw_log_pane(self, stdscr, y_start, height, width):
        """Draw the log pane at the specified position"""
        if height <= 0:
            return
            
        try:
            # Draw log messages (no header)
            display_height = height  # Use full height for messages
            
            # Reserve space for scrollbar if we have messages
            scrollbar_width = 1 if len(self.log_messages) > display_height else 0
            content_width = width - scrollbar_width
            
            if self.log_messages and display_height > 0:
                # Calculate which messages to show
                total_messages = len(self.log_messages)
                
                # Cap scroll offset to prevent scrolling beyond available content
                max_scroll = max(0, total_messages - display_height)
                self.log_scroll_offset = min(self.log_scroll_offset, max_scroll)
                
                start_idx = max(0, total_messages - display_height - self.log_scroll_offset)
                end_idx = min(total_messages, start_idx + display_height)
                
                messages_to_show = list(self.log_messages)[start_idx:end_idx]
                
                for i, (timestamp, source, message) in enumerate(messages_to_show):
                    if i >= display_height:
                        break
                        
                    y = y_start + i
                    if y >= y_start + height:
                        break
                    
                    # Format log line
                    log_line = f"{timestamp} [{source:>6}] {message}"
                    
                    # Truncate if too long (account for scrollbar)
                    if len(log_line) > content_width - 1:
                        log_line = log_line[:content_width - 4] + "..."
                    
                    # Get color based on source
                    color = get_log_color(source)
                    stdscr.addstr(y, 0, log_line.ljust(content_width)[:content_width], color)
                
                # Draw scrollbar if needed
                if scrollbar_width > 0:
                    self._draw_scrollbar(stdscr, y_start, height, width, total_messages, display_height)
                    
        except Exception:
            pass  # Ignore drawing errors
    
    def _draw_scrollbar(self, stdscr, y_start, height, width, total_messages, display_height):
        """Draw a scrollbar for the log pane"""
        try:
            from tfm_colors import get_boundary_color, get_status_color
            
            scrollbar_x = width - 1
            
            # Calculate scrollbar position and size
            if total_messages <= display_height:
                # No scrolling needed, fill entire scrollbar
                for y in range(height):
                    stdscr.addstr(y_start + y, scrollbar_x, "█", get_status_color())
            else:
                # Calculate thumb position and size
                # Thumb size represents the visible portion
                thumb_size = max(1, int((display_height / total_messages) * height))
                
                # Calculate thumb position based on scroll offset
                # When scroll_offset is 0, we're at the bottom (newest messages)
                # When scroll_offset is max, we're at the top (oldest messages)
                max_scroll = total_messages - display_height
                if max_scroll > 0:
                    # Invert the scroll position since 0 means bottom in our system
                    scroll_ratio = self.log_scroll_offset / max_scroll
                    thumb_start = int((height - thumb_size) * (1 - scroll_ratio))
                else:
                    thumb_start = height - thumb_size
                
                thumb_end = min(height, thumb_start + thumb_size)
                
                # Draw scrollbar track and thumb
                for y in range(height):
                    y_pos = y_start + y
                    if thumb_start <= y < thumb_end:
                        # Draw thumb
                        stdscr.addstr(y_pos, scrollbar_x, "█", get_status_color())
                    else:
                        # Draw track
                        stdscr.addstr(y_pos, scrollbar_x, "│", get_boundary_color())
                        
        except Exception:
            pass  # Ignore drawing errors
    
    def restore_stdio(self):
        """Restore stdout/stderr to original state"""
        if hasattr(self, 'original_stdout') and sys.stdout != self.original_stdout:
            sys.stdout = self.original_stdout
        if hasattr(self, 'original_stderr') and sys.stderr != self.original_stderr:
            sys.stderr = self.original_stderr
    
    def __del__(self):
        """Restore stdout/stderr when object is destroyed"""
        self.restore_stdio()