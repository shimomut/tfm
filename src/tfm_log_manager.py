#!/usr/bin/env python3
"""
TFM Log Manager - Handles logging and log display functionality
"""

import sys
import socket
import threading
import json
import time
import logging
from datetime import datetime
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Optional
from tfm_const import LOG_TIME_FORMAT, MAX_LOG_MESSAGES
from tfm_colors import get_log_color, get_status_color
from tfm_scrollbar import draw_scrollbar, calculate_scrollbar_width
from tfm_logging_handlers import LogPaneHandler, StreamOutputHandler, RemoteMonitoringHandler


@dataclass
class LoggingConfig:
    """Configuration for logging system."""
    
    # Log pane settings
    log_pane_enabled: bool = True
    max_log_messages: int = 1000
    
    # Stream output settings
    stream_output_enabled: Optional[bool] = None  # None = auto-detect based on mode
    stream_output_desktop_default: bool = True
    stream_output_terminal_default: bool = False
    
    # Remote monitoring settings
    remote_monitoring_enabled: bool = False
    remote_monitoring_port: Optional[int] = None
    
    # Log level settings
    default_log_level: int = logging.INFO
    logger_levels: Dict[str, int] = field(default_factory=dict)
    
    # Format settings
    timestamp_format: str = "%H:%M:%S"
    message_format: str = "%(asctime)s [%(name)s] %(message)s"


class LogCapture:
    """Capture stdout/stderr and redirect to log pane with line buffering"""
    def __init__(self, log_messages, source, remote_callback=None, update_callback=None, original_stream=None, is_desktop_mode=False, logger=None):
        self.log_messages = log_messages
        self.source = source
        self.remote_callback = remote_callback
        self.update_callback = update_callback
        self.original_stream = original_stream
        self.is_desktop_mode = is_desktop_mode  # Only write to original streams in desktop mode
        self.logger = logger  # Logger instance for routing through handler pipeline
        self.buffer = ""  # Line buffer - accumulates text until newline
        self.lock = threading.RLock()  # Thread safety for buffer access
        
    def write(self, text):
        with self.lock:
            # Add text to buffer
            self.buffer += text
            
            # Process complete lines (split on newlines)
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                
                # Only log non-empty lines to the log pane
                if line.strip():
                    self._emit_log_record(line)
    
    def _emit_log_record(self, text):
        """Emit a single log record for the given text"""
        # If logger is available, route through logging infrastructure
        if self.logger:
            # Create LogRecord with appropriate level
            # INFO for stdout, WARNING for stderr
            level = logging.INFO if self.source == "STDOUT" else logging.WARNING
            
            # Requirement 11.1: Performance optimization - check if level is enabled
            # Skip expensive LogRecord creation and formatting if level is disabled
            if not self.logger.isEnabledFor(level):
                return
            
            # Create LogRecord - preserve raw text without stripping or modifying
            record = logging.LogRecord(
                name=self.source,  # "STDOUT" or "STDERR"
                level=level,
                pathname="",
                lineno=0,
                msg=text,  # Raw text, not stripped or modified
                args=(),
                exc_info=None
            )
            
            # CRITICAL: Mark this as a stream capture (not a formatted logger message)
            # Handlers will check this flag to determine formatting behavior
            record.is_stream_capture = True
            
            # Route through the logger's handler pipeline
            self.logger.handle(record)
        else:
            # Fallback to old behavior if logger not available (backward compatibility)
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
        # flush() is called to ensure buffered data is written
        # However, we should NOT emit incomplete lines (lines without newline)
        # The buffer will be emitted when a newline is eventually received
        # This matches standard stream behavior where flush() doesn't add newlines
        pass


class LogManager:
    """Manages logging system and log display"""
    
    def __init__(self, config, remote_port=None, is_desktop_mode=False):
        # Log pane setup
        max_log_messages = getattr(config, 'MAX_LOG_MESSAGES', MAX_LOG_MESSAGES)
        self.log_messages = deque(maxlen=max_log_messages)
        self.log_scroll_offset = 0
        
        # Track log updates for redraw triggering
        self.has_new_messages = False
        self.last_message_count = 0
        
        # Logger caching - stores created loggers by name
        self._loggers = {}
        
        # Create a root logger for stream capture routing
        # This logger will be used by LogCapture to route stdout/stderr through the handler pipeline
        self._stream_logger = logging.getLogger("TFM_STREAM_CAPTURE")
        self._stream_logger.setLevel(logging.DEBUG)  # Accept all levels
        self._stream_logger.propagate = False
        
        # Store configuration for handler management
        self._config = LoggingConfig()
        self._config.max_log_messages = max_log_messages
        self._config.remote_monitoring_enabled = remote_port is not None
        self._config.remote_monitoring_port = remote_port
        # Enable stream output in desktop mode, disable in terminal mode
        self._config.stream_output_enabled = is_desktop_mode
        
        # Log level configuration
        # Global default level (defaults to INFO)
        self._default_log_level = logging.INFO
        # Per-logger level overrides (logger_name -> level)
        self._logger_levels = {}
        
        # Handler instances
        self._log_pane_handler = None
        self._stream_output_handler = None
        self._remote_monitoring_handler = None
        
        # Remote monitoring setup
        self.remote_port = remote_port
        self.remote_clients = []
        self.server_socket = None
        self.server_thread = None
        self.running = True
        
        # Store desktop mode flag
        self.is_desktop_mode = is_desktop_mode
        
        # Store original streams
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # NOTE: Old remote server code disabled - now using RemoteMonitoringHandler
        # Start remote server if port is specified
        # if self.remote_port:
        #     self._start_remote_server()
        
        # Redirect stdout and stderr
        remote_callback = self._broadcast_to_clients if self.remote_port else None
        update_callback = self._on_message_added
        sys.stdout = LogCapture(self.log_messages, "STDOUT", remote_callback, update_callback, 
                               self.original_stdout, is_desktop_mode, logger=self._stream_logger)
        sys.stderr = LogCapture(self.log_messages, "STDERR", remote_callback, update_callback,
                               self.original_stderr, is_desktop_mode, logger=self._stream_logger)
        
        # Initialize handlers based on configuration
        # This creates the LogPaneHandler by default (log_pane_enabled=True by default)
        self.configure_handlers()
    
    def configure_handlers(self, 
                          log_pane_enabled: Optional[bool] = None,
                          stream_output_enabled: Optional[bool] = None,
                          remote_enabled: Optional[bool] = None):
        """
        Configure which handlers are active.
        Supports dynamic reconfiguration without restart.
        
        Args:
            log_pane_enabled: Enable log pane display (None = keep current)
            stream_output_enabled: Enable original stream output (None = keep current)
            remote_enabled: Enable remote monitoring (None = keep current)
        """
        # Update configuration
        if log_pane_enabled is not None:
            self._config.log_pane_enabled = log_pane_enabled
        if stream_output_enabled is not None:
            self._config.stream_output_enabled = stream_output_enabled
        if remote_enabled is not None:
            self._config.remote_monitoring_enabled = remote_enabled
        
        # Configure log pane handler
        if self._config.log_pane_enabled:
            if self._log_pane_handler is None:
                # Create new handler
                self._log_pane_handler = LogPaneHandler(max_messages=self._config.max_log_messages)
                # Add to stream logger
                if self._log_pane_handler not in self._stream_logger.handlers:
                    self._stream_logger.addHandler(self._log_pane_handler)
                # Add to all existing loggers
                for logger in self._loggers.values():
                    if self._log_pane_handler not in logger.handlers:
                        logger.addHandler(self._log_pane_handler)
        else:
            if self._log_pane_handler is not None:
                # Remove from stream logger
                if self._log_pane_handler in self._stream_logger.handlers:
                    self._stream_logger.removeHandler(self._log_pane_handler)
                # Remove from all existing loggers
                for logger in self._loggers.values():
                    if self._log_pane_handler in logger.handlers:
                        logger.removeHandler(self._log_pane_handler)
                self._log_pane_handler = None
        
        # Configure stream output handler
        if self._config.stream_output_enabled:
            if self._stream_output_handler is None:
                # Create new handler
                self._stream_output_handler = StreamOutputHandler(self.original_stdout)
                # Add to stream logger
                if self._stream_output_handler not in self._stream_logger.handlers:
                    self._stream_logger.addHandler(self._stream_output_handler)
                # Add to all existing loggers
                for logger in self._loggers.values():
                    if self._stream_output_handler not in logger.handlers:
                        logger.addHandler(self._stream_output_handler)
        else:
            if self._stream_output_handler is not None:
                # Remove from stream logger
                if self._stream_output_handler in self._stream_logger.handlers:
                    self._stream_logger.removeHandler(self._stream_output_handler)
                # Remove from all existing loggers
                for logger in self._loggers.values():
                    if self._stream_output_handler in logger.handlers:
                        logger.removeHandler(self._stream_output_handler)
                self._stream_output_handler = None
        
        # Configure remote monitoring handler
        if self._config.remote_monitoring_enabled:
            if self._remote_monitoring_handler is None and self._config.remote_monitoring_port:
                # Create new handler
                self._remote_monitoring_handler = RemoteMonitoringHandler(self._config.remote_monitoring_port)
                # Start the server
                self._remote_monitoring_handler.start_server()
                # Add to stream logger
                if self._remote_monitoring_handler not in self._stream_logger.handlers:
                    self._stream_logger.addHandler(self._remote_monitoring_handler)
                # Add to all existing loggers
                for logger in self._loggers.values():
                    if self._remote_monitoring_handler not in logger.handlers:
                        logger.addHandler(self._remote_monitoring_handler)
        else:
            if self._remote_monitoring_handler is not None:
                # Stop the server
                self._remote_monitoring_handler.stop_server()
                # Remove from stream logger
                if self._remote_monitoring_handler in self._stream_logger.handlers:
                    self._stream_logger.removeHandler(self._remote_monitoring_handler)
                # Remove from all existing loggers
                for logger in self._loggers.values():
                    if self._remote_monitoring_handler in logger.handlers:
                        logger.removeHandler(self._remote_monitoring_handler)
                self._remote_monitoring_handler = None
    
    def getLogger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with TFM handlers configured.
        
        Returns existing logger if name was already used. This ensures that
        multiple calls with the same name return the same Logger instance.
        
        TFM creates multiple loggers for different purposes:
        - "Main": Main application logging
        - "FileOp": File operation logging
        - "DirDiff": Directory diff viewer logging
        - "Archive": Archive operations logging
        - etc.
        
        Args:
            name: Logger name (e.g., "Main", "FileOp", "DirDiff")
            
        Returns:
            Configured logging.Logger instance (existing or newly created)
        """
        # Return cached logger if it exists
        if name in self._loggers:
            return self._loggers[name]
        
        # Create new logger using Python's standard logging
        logger = logging.getLogger(name)
        
        # Set level based on configuration
        # Check for per-logger override first, then use default
        if name in self._logger_levels:
            logger.setLevel(self._logger_levels[name])
        else:
            logger.setLevel(self._default_log_level)
        
        # Prevent propagation to root logger to avoid duplicate messages
        logger.propagate = False
        
        # Attach configured handlers based on current configuration
        if self._log_pane_handler is not None:
            logger.addHandler(self._log_pane_handler)
        if self._stream_output_handler is not None:
            logger.addHandler(self._stream_output_handler)
        if self._remote_monitoring_handler is not None:
            logger.addHandler(self._remote_monitoring_handler)
        
        # Cache the logger
        self._loggers[name] = logger
        
        return logger
    
    def set_default_log_level(self, level: int):
        """
        Set the global default log level for all loggers.
        
        This affects all loggers that don't have a per-logger override.
        Existing loggers without overrides will be updated to the new level.
        
        Args:
            level: Log level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self._default_log_level = level
        
        # Update existing loggers that don't have per-logger overrides
        for name, logger in self._loggers.items():
            if name not in self._logger_levels:
                logger.setLevel(level)
    
    def set_logger_level(self, logger_name: str, level: int):
        """
        Set the log level for a specific logger (per-logger override).
        
        This overrides the global default level for the specified logger.
        If the logger already exists, its level is updated immediately.
        If the logger doesn't exist yet, the override is stored and will
        be applied when the logger is created.
        
        Args:
            logger_name: Name of the logger to configure
            level: Log level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self._logger_levels[logger_name] = level
        
        # Update existing logger if it exists
        if logger_name in self._loggers:
            self._loggers[logger_name].setLevel(level)
    
    def get_logger_level(self, logger_name: str) -> int:
        """
        Get the effective log level for a logger.
        
        Returns the per-logger override if set, otherwise the default level.
        
        Args:
            logger_name: Name of the logger
            
        Returns:
            Log level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        return self._logger_levels.get(logger_name, self._default_log_level)
    
    def clear_logger_level(self, logger_name: str):
        """
        Clear the per-logger level override for a specific logger.
        
        After clearing, the logger will use the global default level.
        If the logger exists, its level is updated to the default immediately.
        
        Args:
            logger_name: Name of the logger to clear override for
        """
        if logger_name in self._logger_levels:
            del self._logger_levels[logger_name]
            
            # Update existing logger to use default level
            if logger_name in self._loggers:
                self._loggers[logger_name].setLevel(self._default_log_level)
    
    def set_log_pane_visible(self, visible: bool):
        """
        Set whether the log pane is visible.
        
        When set to False, the LogPaneHandler skips expensive formatting operations
        for performance. Messages are still stored and will be formatted when the
        pane becomes visible again.
        
        Args:
            visible: True if log pane is visible, False otherwise
        """
        if self._log_pane_handler is not None:
            self._log_pane_handler.set_visible(visible)
    
    @property
    def log_pane_handler(self):
        """Get the log pane handler instance."""
        return self._log_pane_handler
    
    @property
    def stream_output_handler(self):
        """Get the stream output handler instance."""
        return self._stream_output_handler
    
    @property
    def remote_handler(self):
        """Get the remote monitoring handler instance."""
        return self._remote_monitoring_handler
        
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
        """
        Add a message directly to the log (backward compatibility method).
        
        This method maintains backward compatibility with existing code that uses
        add_message() instead of getLogger(). Messages are routed through the
        new logging infrastructure to ensure consistent handling.
        
        Args:
            source: Message source identifier (e.g., "SYSTEM", "CONFIG", "FileOp")
            message: Message text
        """
        # Route through logging infrastructure for consistent handling
        # Create a LogRecord with appropriate level based on source
        # Use INFO level for most sources, WARNING for error-related sources
        if source.upper() in ("ERROR", "STDERR"):
            level = logging.WARNING
        else:
            level = logging.INFO
        
        # Requirement 11.1: Performance optimization - check if level is enabled
        # Skip expensive LogRecord creation if level is disabled
        if not self._stream_logger.isEnabledFor(level):
            return
        
        # Create LogRecord
        record = logging.LogRecord(
            name=source,  # Use source as logger name
            level=level,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        
        # Mark this as NOT a stream capture (it's a direct log message)
        # This ensures it gets formatted like a logger message, not stdout/stderr
        record.is_stream_capture = False
        
        # Route through the stream logger's handler pipeline
        # This ensures the message goes through all configured handlers
        # (LogPaneHandler, StreamOutputHandler, RemoteMonitoringHandler)
        self._stream_logger.handle(record)
    
    def add_startup_messages(self, version, github_url, app_name):
        """
        Add startup messages directly to log pane.
        
        Routes through logging infrastructure for consistent handling.
        
        Args:
            version: Application version string
            github_url: GitHub repository URL
            app_name: Application name
        """
        # Use add_message() which now routes through logging infrastructure
        self.add_message("SYSTEM", f"TFM {version}")
        self.add_message("SYSTEM", f"GitHub: {github_url}")
        self.add_message("SYSTEM", f"{app_name} started successfully")
        self.add_message("CONFIG", "Configuration loaded")
    
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
    
    def draw_log_pane(self, renderer, y_start, height, width):
        """Draw the log pane at the specified position"""
        if height <= 0:
            return
            
        try:
            # Draw log messages (no header)
            display_height = height  # Use full height for messages
            
            # Get messages from LogPaneHandler if available, otherwise use old deque
            if self._log_pane_handler is not None:
                # New system: get messages from handler (list of (formatted_message, record) tuples)
                handler_messages = self._log_pane_handler.get_messages()
                total_messages = len(handler_messages)
            else:
                # Old system: use deque directly (list of (timestamp, source, message) tuples)
                handler_messages = None
                total_messages = len(self.log_messages)
            
            # Reserve space for scrollbar if we have messages
            scrollbar_width = calculate_scrollbar_width(total_messages, display_height)
            content_width = width - scrollbar_width
            
            if total_messages > 0 and display_height > 0:
                # Calculate which messages to show
                # Cap scroll offset to prevent scrolling beyond available content
                max_scroll = max(0, total_messages - display_height)
                self.log_scroll_offset = min(self.log_scroll_offset, max_scroll)
                
                start_idx = max(0, total_messages - display_height - self.log_scroll_offset)
                end_idx = min(total_messages, start_idx + display_height)
                
                if handler_messages is not None:
                    # New system: messages from LogPaneHandler
                    messages_to_show = handler_messages[start_idx:end_idx]
                    
                    for i, (formatted_message, record) in enumerate(messages_to_show):
                        if i >= display_height:
                            break
                            
                        y = y_start + i
                        if y >= y_start + height:
                            break
                        
                        # Truncate if too long (account for scrollbar)
                        log_line = formatted_message
                        if len(log_line) > content_width - 1:
                            log_line = log_line[:content_width - 2] + "…"
                        
                        # Get color from handler based on record
                        color_pair, attributes = self._log_pane_handler.get_color_for_record(record)
                        renderer.draw_text(y, 0, log_line.ljust(content_width)[:content_width], color_pair=color_pair, attributes=attributes)
                else:
                    # Old system: messages from deque
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
                            log_line = log_line[:content_width - 2] + "…"
                        
                        # Get color based on source (old behavior)
                        color_pair, attributes = get_log_color(source)
                        renderer.draw_text(y, 0, log_line.ljust(content_width)[:content_width], color_pair=color_pair, attributes=attributes)
                
                # Draw scrollbar if needed using unified implementation
                # Use inverted=True because scroll_offset=0 means bottom (newest messages)
                if scrollbar_width > 0:
                    draw_scrollbar(renderer, y_start, width - 1, height, 
                                 total_messages, self.log_scroll_offset, inverted=True)
            
        except Exception:
            pass  # Ignore drawing errors
        finally:
            # Always mark log updates as processed when draw_log_pane is called
            # This ensures updates are marked as processed even if drawing fails
            self.mark_log_updates_processed()
    

    
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