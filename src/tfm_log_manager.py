#!/usr/bin/env python3
"""
TFM Log Manager - Handles logging and log display functionality
"""

import sys
import socket
import threading
import json
import time
from datetime import datetime
from collections import deque
from tfm_const import LOG_TIME_FORMAT, MAX_LOG_MESSAGES
from tfm_colors import get_log_color, get_status_color


class LogCapture:
    """Capture stdout/stderr and redirect to log pane"""
    def __init__(self, log_messages, source, remote_callback=None, update_callback=None):
        self.log_messages = log_messages
        self.source = source
        self.remote_callback = remote_callback
        self.update_callback = update_callback
        
    def write(self, text):
        if text.strip():  # Only log non-empty messages
            timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
            log_entry = (timestamp, self.source, text.strip())
            self.log_messages.append(log_entry)
            
            # Notify about new message for redraw triggering
            if self.update_callback:
                self.update_callback()
            
            # Send to remote clients if callback is available
            if self.remote_callback:
                self.remote_callback(log_entry)
    
    def flush(self):
        pass  # Required for file-like object interface


class LogManager:
    """Manages logging system and log display"""
    
    def __init__(self, config, remote_port=None):
        # Log pane setup
        max_log_messages = getattr(config, 'MAX_LOG_MESSAGES', MAX_LOG_MESSAGES)
        self.log_messages = deque(maxlen=max_log_messages)
        self.log_scroll_offset = 0
        
        # Track log updates for redraw triggering
        self.has_new_messages = False
        self.last_message_count = 0
        
        # Remote monitoring setup
        self.remote_port = remote_port
        self.remote_clients = []
        self.server_socket = None
        self.server_thread = None
        self.running = True
        
        # Store original streams
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Start remote server if port is specified
        if self.remote_port:
            self._start_remote_server()
        
        # Redirect stdout and stderr
        remote_callback = self._broadcast_to_clients if self.remote_port else None
        update_callback = self._on_message_added
        sys.stdout = LogCapture(self.log_messages, "STDOUT", remote_callback, update_callback)
        sys.stderr = LogCapture(self.log_messages, "STDERR", remote_callback, update_callback)
        
    def _start_remote_server(self):
        """Start TCP server for remote log monitoring"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.remote_port))
            self.server_socket.listen(5)
            
            self.server_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.server_thread.start()
            
            # Log server start
            timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
            log_entry = (timestamp, "REMOTE", f"Log server started on port {self.remote_port}")
            self.log_messages.append(log_entry)
            
        except Exception as e:
            timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
            log_entry = (timestamp, "ERROR", f"Failed to start remote server: {e}")
            self.log_messages.append(log_entry)
    
    def _accept_connections(self):
        """Accept incoming client connections"""
        while self.running and self.server_socket:
            try:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, address), 
                    daemon=True
                )
                client_thread.start()
                
                # Log new connection using original stdout to avoid recursion
                try:
                    self.original_stdout.write(f"Client connected from {address[0]}:{address[1]}\n")
                    self.original_stdout.flush()
                except (OSError, IOError) as e:
                    # Can't write to stdout, but continue serving the client
                    pass
                
            except (ConnectionError, OSError) as e:
                if self.running:  # Only log if we're still supposed to be running
                    try:
                        self.original_stdout.write(f"Error accepting client connection: {e}\n")
                        self.original_stdout.flush()
                    except (OSError, IOError):
                        pass  # Can't log the error, but continue
                break
            except Exception as e:
                if self.running:
                    try:
                        self.original_stdout.write(f"Unexpected error in server loop: {e}\n")
                        self.original_stdout.flush()
                    except (OSError, IOError):
                        pass
                break
    
    def _handle_client(self, client_socket, address):
        """Handle individual client connection"""
        try:
            # Add client to list
            self.remote_clients.append(client_socket)
            
            # Send existing log messages to new client
            for log_entry in self.log_messages:
                try:
                    self._send_log_entry(client_socket, log_entry)
                except (ConnectionError, BrokenPipeError, OSError) as e:
                    # Client disconnected during initial message send
                    return
                except Exception as e:
                    # Unexpected error sending initial messages
                    try:
                        self.original_stdout.write(f"Warning: Could not send initial log to client: {e}\n")
                        self.original_stdout.flush()
                    except (OSError, IOError):
                        pass
                    return
            
            # Keep the thread alive - disconnection will be detected in _broadcast_to_clients
            # when we try to send data and it fails
            while self.running and client_socket in self.remote_clients:
                time.sleep(1.0)  # Just keep the thread alive
                    
        except Exception as e:
            try:
                self.original_stdout.write(f"Warning: Client handler error: {e}\n")
                self.original_stdout.flush()
            except (OSError, IOError):
                pass
        finally:
            # Remove client and close socket
            if client_socket in self.remote_clients:
                self.remote_clients.remove(client_socket)
            try:
                client_socket.close()
            except (OSError, ConnectionError) as e:
                # Socket already closed or connection error
                pass
            except Exception as e:
                try:
                    self.original_stdout.write(f"Warning: Error closing client socket: {e}\n")
                    self.original_stdout.flush()
                except (OSError, IOError):
                    pass
            
            # Don't add disconnection message to avoid potential recursion issues
            # Just use the original stdout to log
            try:
                self.original_stdout.write(f"Client disconnected from {address[0]}:{address[1]}\n")
                self.original_stdout.flush()
            except (OSError, IOError) as e:
                # Can't write to stdout, but that's not critical
                pass
            except Exception as e:
                # Unexpected error, but don't let it crash the handler
                pass
    
    def _broadcast_to_clients(self, log_entry):
        """Broadcast log entry to all connected clients"""
        if not self.remote_clients:
            return
            
        # Create a copy of the client list to avoid modification during iteration
        clients_copy = self.remote_clients.copy()
        
        for client_socket in clients_copy:
            try:
                self._send_log_entry(client_socket, log_entry)
            except (ConnectionError, BrokenPipeError, OSError):
                # Remove failed client - connection lost
                if client_socket in self.remote_clients:
                    self.remote_clients.remove(client_socket)
                try:
                    client_socket.close()
                except (OSError, ConnectionError):
                    pass  # Socket already closed
                except Exception as e:
                    try:
                        self.original_stdout.write(f"Warning: Error closing failed client socket: {e}\n")
                        self.original_stdout.flush()
                    except (OSError, IOError):
                        pass
            except Exception as e:
                # Unexpected error - log it and remove client
                try:
                    self.original_stdout.write(f"Warning: Unexpected error broadcasting to client: {e}\n")
                    self.original_stdout.flush()
                except (OSError, IOError):
                    pass
                if client_socket in self.remote_clients:
                    self.remote_clients.remove(client_socket)
                try:
                    client_socket.close()
                except Exception:
                    pass
    
    def _send_log_entry(self, client_socket, log_entry):
        """Send a single log entry to a client"""
        try:
            # Format as JSON for easy parsing by clients
            message = {
                'timestamp': log_entry[0],
                'source': log_entry[1],
                'message': log_entry[2]
            }
            json_data = json.dumps(message) + '\n'
            client_socket.send(json_data.encode('utf-8'))
        except (ConnectionError, BrokenPipeError, OSError):
            raise  # Re-raise connection errors to handle in calling method
        except (UnicodeEncodeError, TypeError) as e:
            # Data encoding error - log and re-raise
            try:
                self.original_stdout.write(f"Warning: Could not encode log message: {e}\n")
                self.original_stdout.flush()
            except (OSError, IOError):
                pass
            raise
        except Exception as e:
            # Unexpected error - log and re-raise
            try:
                self.original_stdout.write(f"Warning: Unexpected error sending log entry: {e}\n")
                self.original_stdout.flush()
            except (OSError, IOError):
                pass
            raise

    def _on_message_added(self):
        """Called when a new message is added to the log"""
        self.has_new_messages = True
    
    def has_log_updates(self):
        """Check if there are new log messages since last check"""
        current_count = len(self.log_messages)
        if current_count != self.last_message_count or self.has_new_messages:
            return True
        return False
    
    def mark_log_updates_processed(self):
        """Mark that log updates have been processed (redraw completed)"""
        self.has_new_messages = False
        self.last_message_count = len(self.log_messages)
    
    def add_message(self, source, message):
        """Add a message directly to the log (bypasses stdout/stderr capture)"""
        timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
        log_entry = (timestamp, source, message)
        self.log_messages.append(log_entry)
        
        # Trigger update notification
        self._on_message_added()
        
        # Broadcast to remote clients if available
        if self.remote_port:
            self._broadcast_to_clients(log_entry)
    
    def add_startup_messages(self, version, github_url, app_name):
        """Add startup messages directly to log pane"""
        timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
        
        startup_messages = [
            (timestamp, "SYSTEM", f"TFM {version}"),
            (timestamp, "SYSTEM", f"GitHub: {github_url}"),
            (timestamp, "SYSTEM", f"{app_name} started successfully"),
            (timestamp, "CONFIG", "Configuration loaded")
        ]
        
        for log_entry in startup_messages:
            self.log_messages.append(log_entry)
            # Broadcast to remote clients if available
            if self.remote_port:
                self._broadcast_to_clients(log_entry)
        
        # Trigger update notification for startup messages
        self._on_message_added()
    
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
        finally:
            # Always mark log updates as processed when draw_log_pane is called
            # This ensures updates are marked as processed even if drawing fails
            self.mark_log_updates_processed()
    
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
    
    def stop_remote_server(self):
        """Stop the remote server and close all connections"""
        self.running = False
        
        # Close all client connections
        for client_socket in self.remote_clients.copy():
            try:
                client_socket.close()
            except Exception:
                pass
        self.remote_clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
        
        # Wait for server thread to finish
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)
    
    def restore_stdio(self):
        """Restore stdout/stderr to original state"""
        if hasattr(self, 'original_stdout') and sys.stdout != self.original_stdout:
            sys.stdout = self.original_stdout
        if hasattr(self, 'original_stderr') and sys.stderr != self.original_stderr:
            sys.stderr = self.original_stderr
    
    def __del__(self):
        """Restore stdout/stderr when object is destroyed"""
        self.stop_remote_server()
        self.restore_stdio()