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
    
    def get_log_scroll_percentage(self):
        """Calculate the current log scroll position as a percentage"""
        if len(self.log_messages) <= 1:
            return 0
        
        # Calculate how many messages we can display
        # This will be updated when we know the actual display height
        max_scroll = max(0, len(self.log_messages) - 1)
        
        if max_scroll == 0:
            return 0
        
        # Calculate percentage
        percentage = (self.log_scroll_offset / max_scroll) * 100
        return max(0, min(100, percentage))
    
    def scroll_log_up(self, lines=1):
        """Scroll log up by specified number of lines"""
        if self.log_scroll_offset > 0:
            self.log_scroll_offset = max(0, self.log_scroll_offset - lines)
            return True
        return False
    
    def scroll_log_down(self, lines=1):
        """Scroll log down by specified number of lines"""
        max_scroll = max(0, len(self.log_messages) - 1)
        if self.log_scroll_offset < max_scroll:
            self.log_scroll_offset = min(max_scroll, self.log_scroll_offset + lines)
            return True
        return False
    
    def draw_log_pane(self, stdscr, y_start, height, width):
        """Draw the log pane at the specified position"""
        if height <= 0:
            return
            
        try:
            # Draw log header
            log_header = f" Log ({len(self.log_messages)} messages)"
            if self.log_messages:
                scroll_pct = self.get_log_scroll_percentage()
                log_header += f" - {scroll_pct:.0f}%"
            
            stdscr.addstr(y_start, 0, log_header.ljust(width)[:width], get_status_color())
            
            # Draw log messages
            display_height = height - 1  # Reserve one line for header
            
            if self.log_messages and display_height > 0:
                # Calculate which messages to show
                total_messages = len(self.log_messages)
                start_idx = max(0, total_messages - display_height - self.log_scroll_offset)
                end_idx = min(total_messages, start_idx + display_height)
                
                messages_to_show = list(self.log_messages)[start_idx:end_idx]
                
                for i, (timestamp, source, message) in enumerate(messages_to_show):
                    if i >= display_height:
                        break
                        
                    y = y_start + 1 + i
                    if y >= y_start + height:
                        break
                    
                    # Format log line
                    log_line = f"{timestamp} [{source:>6}] {message}"
                    
                    # Truncate if too long
                    if len(log_line) > width - 1:
                        log_line = log_line[:width - 4] + "..."
                    
                    # Get color based on source
                    color = get_log_color(source)
                    stdscr.addstr(y, 0, log_line.ljust(width)[:width], color)
                    
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