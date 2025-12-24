#!/usr/bin/env python3
"""
TFM Logging Handlers - Custom handlers for Python's logging module

This module provides custom logging handlers that integrate Python's standard
logging framework with TFM's unique requirements:
- LogPaneHandler: Routes messages to TFM's visual log display
- StreamOutputHandler: Routes messages to original stdout/stderr streams
- RemoteMonitoringHandler: Broadcasts messages to TCP clients
"""

import sys
import socket
import threading
import json
import logging
from datetime import datetime
from collections import deque
from typing import List, Tuple, Optional, Dict
from tfm_const import LOG_TIME_FORMAT


class LogPaneHandler(logging.Handler):
    """
    Custom handler that stores log messages in a deque for display in TFM's log pane.
    
    This handler distinguishes between:
    - Logger messages: Formatted with timestamp, logger name, level, and message
    - Stdout/stderr: Displayed as-is with only timestamp and source prefix
    
    The distinction is made using the `is_stream_capture` attribute on LogRecord.
    """
    
    def __init__(self, max_messages: int = 1000):
        """
        Initialize log pane handler.
        
        Args:
            max_messages: Maximum messages to retain (oldest discarded when limit reached)
        """
        super().__init__()
        self.messages = deque(maxlen=max_messages)
        self.lock = threading.RLock()  # Use RLock to allow recursive acquisition
        self.is_visible = True  # Track whether log pane is visible (Requirement 11.3)
        
    def emit(self, record: logging.LogRecord):
        """
        Process a log record and add to display queue.
        
        Checks record.is_stream_capture to determine formatting:
        - If True: Display as-is (stdout/stderr)
        - If False: Format with timestamp, name, level, message (logger)
        
        Error handling: All exceptions are caught and logged to sys.__stderr__
        to prevent logging failures from crashing the application. The handler
        continues operating with remaining handlers even if this one fails.
        
        Args:
            record: Log record to process
        """
        try:
            # Requirement 11.3: Performance optimization - skip rendering when not visible
            # Messages are still stored (for when pane becomes visible), but we skip
            # expensive formatting operations when the log pane is not visible
            if not self.is_visible:
                # Still store the record for later display, but skip formatting
                with self.lock:
                    # Store unformatted - will be formatted when pane becomes visible
                    self.messages.append((None, record))
                return
            
            with self.lock:
                if getattr(record, 'is_stream_capture', False):
                    # Stdout/stderr: display as-is with minimal formatting
                    formatted_lines = self.format_stream_message(record)
                    for line in formatted_lines:
                        # Store tuple of (formatted_message, record) for color determination
                        self.messages.append((line, record))
                else:
                    # Logger message: apply full formatting
                    formatted = self.format_logger_message(record)
                    # Store tuple of (formatted_message, record) for color determination
                    self.messages.append((formatted, record))
        except Exception as e:
            # Requirement 12.1: Handler failure isolation
            # Requirement 12.5: Log errors using fallback mechanism
            # Error isolation: Log to fallback (sys.__stderr__) and continue
            # This prevents handler failures from crashing the application
            try:
                sys.__stderr__.write(f"[LogPaneHandler] Error processing log record: {e}\n")
                sys.__stderr__.flush()
            except Exception:
                # Even fallback failed, but continue silently
                pass
    
    def format_logger_message(self, record: logging.LogRecord) -> str:
        """
        Format a logger message with full formatting.
        
        Args:
            record: Log record from a logger
            
        Returns:
            Formatted string: "HH:MM:SS [LoggerName] LEVEL: message"
        """
        timestamp = datetime.fromtimestamp(record.created).strftime(LOG_TIME_FORMAT)
        return f"{timestamp} [{record.name}] {record.levelname}: {record.getMessage()}"
    
    def format_stream_message(self, record: logging.LogRecord) -> List[str]:
        """
        Format a stdout/stderr message as-is, preserving multi-line output.
        Only adds timestamp and source prefix, no other formatting.
        
        Args:
            record: Log record from stdout/stderr capture
            
        Returns:
            List of formatted strings, one per line
        """
        timestamp = datetime.fromtimestamp(record.created).strftime(LOG_TIME_FORMAT)
        source = record.name  # "STDOUT" or "STDERR"
        raw_message = record.getMessage()
        
        # Preserve multi-line output - each line gets its own entry
        lines = raw_message.split('\n')
        return [f"{timestamp} [{source}] {line}" for line in lines if line]
    
    def get_messages(self) -> List[Tuple[str, logging.LogRecord]]:
        """
        Get messages for display.
        
        Formats any unformatted messages (those added while pane was not visible).
        
        Returns:
            List of (formatted_message, record) tuples
        """
        with self.lock:
            # Format any unformatted messages (None in first element of tuple)
            formatted_messages = []
            for formatted_msg, record in self.messages:
                if formatted_msg is None:
                    # Format the message now
                    if getattr(record, 'is_stream_capture', False):
                        formatted_lines = self.format_stream_message(record)
                        for line in formatted_lines:
                            formatted_messages.append((line, record))
                    else:
                        formatted = self.format_logger_message(record)
                        formatted_messages.append((formatted, record))
                else:
                    formatted_messages.append((formatted_msg, record))
            return formatted_messages
    
    def set_visible(self, visible: bool):
        """
        Set whether the log pane is visible.
        
        When set to False, formatting operations are skipped for performance.
        Messages are still stored and will be formatted when pane becomes visible.
        
        Args:
            visible: True if log pane is visible, False otherwise
        """
        self.is_visible = visible
    
    def get_color_for_record(self, record: logging.LogRecord) -> Tuple[int, int]:
        """
        Determine color pair and attributes for a log record.
        
        For logger messages: Uses record.levelno to determine color
        For stdout/stderr: Uses record.name ("STDOUT"/"STDERR") to determine color
        
        Args:
            record: Log record
            
        Returns:
            (color_pair, attributes) tuple
        """
        # Import here to avoid circular dependency
        from tfm_colors import get_log_color, COLOR_ERROR, COLOR_LOG_SYSTEM
        from ttk import TextAttribute
        
        # Check if this is a stream capture (stdout/stderr) or logger message
        if getattr(record, 'is_stream_capture', False):
            # For stdout/stderr: use record.name ("STDOUT"/"STDERR") to determine color
            return get_log_color(record.name)
        else:
            # For logger messages: use record.levelno to determine color
            # Map log levels to colors:
            # DEBUG (10) -> STDOUT color (gray)
            # INFO (20) -> STDOUT color (gray)
            # WARNING (30) -> SYSTEM color (light blue)
            # ERROR (40) -> ERROR color (red)
            # CRITICAL (50) -> ERROR color (red)
            
            if record.levelno >= logging.ERROR:  # ERROR (40) or CRITICAL (50)
                return COLOR_ERROR, TextAttribute.NORMAL
            elif record.levelno >= logging.WARNING:  # WARNING (30)
                return COLOR_LOG_SYSTEM, TextAttribute.NORMAL
            else:  # DEBUG (10) or INFO (20)
                return get_log_color("STDOUT")


class StreamOutputHandler(logging.Handler):
    """
    Custom handler that writes log messages to original stdout/stderr streams.
    
    This handler respects the is_stream_capture flag:
    - Logger messages: Written with full formatting
    - Stdout/stderr: Written as-is (raw text) to preserve original output
    """
    
    def __init__(self, stream):
        """
        Initialize stream output handler.
        
        Args:
            stream: Output stream (sys.__stdout__ or sys.__stderr__)
        """
        super().__init__()
        self.stream = stream
        self.lock = threading.RLock()  # Use RLock to allow recursive acquisition
        
    def emit(self, record: logging.LogRecord):
        """
        Write log record to stream.
        
        Respects is_stream_capture flag for formatting:
        - If True: Write raw message without additional formatting
        - If False: Write with full formatting
        
        Error handling: Stream write failures (OSError, IOError) are suppressed
        to prevent logging from crashing the application. Other exceptions are
        logged to fallback. The handler continues operating with remaining
        handlers even if this one fails.
        
        Args:
            record: Log record to write
        """
        try:
            with self.lock:
                if getattr(record, 'is_stream_capture', False):
                    # Stdout/stderr: write raw message without additional formatting
                    msg = record.getMessage()
                    self.stream.write(msg)
                    if not msg.endswith('\n'):
                        self.stream.write('\n')
                else:
                    # Logger message: write with full formatting
                    formatted = self.format(record)
                    self.stream.write(formatted + '\n')
                self.stream.flush()
        except (OSError, IOError):
            # Requirement 12.3: Stream write failure suppression
            # Suppress stream write errors to prevent logging from crashing application
            pass
        except Exception as e:
            # Requirement 12.1: Handler failure isolation
            # Requirement 12.5: Log errors using fallback mechanism
            # Log unexpected errors to fallback stream
            try:
                sys.__stderr__.write(f"[StreamOutputHandler] Error writing to stream: {e}\n")
                sys.__stderr__.flush()
            except:
                # Even fallback failed, silently continue
                pass


class RemoteMonitoringHandler(logging.Handler):
    """
    Custom handler that broadcasts log messages to TCP clients.
    
    This handler:
    - Maintains a list of connected clients
    - Formats messages as JSON
    - Handles client disconnections gracefully
    - Only active when remote monitoring is enabled
    """
    
    def __init__(self, port: int):
        """
        Initialize remote monitoring handler.
        
        Args:
            port: TCP port to listen on
        """
        super().__init__()
        self.port = port
        self.clients = []
        self.server_socket = None
        self.server_thread = None
        self.running = False
        self.lock = threading.RLock()  # Use RLock to allow recursive acquisition
        
    def emit(self, record: logging.LogRecord):
        """
        Broadcast log record to all connected clients.
        
        Error handling: All exceptions are caught and logged to sys.__stderr__
        to prevent logging failures from crashing the application. Client
        connection failures are handled in _broadcast_to_clients(). The handler
        continues operating with remaining handlers even if this one fails.
        
        Args:
            record: Log record to broadcast
        """
        try:
            # Format as JSON message
            timestamp = datetime.fromtimestamp(record.created).strftime(LOG_TIME_FORMAT)
            
            if getattr(record, 'is_stream_capture', False):
                # Stdout/stderr message
                message_dict = {
                    'timestamp': timestamp,
                    'source': record.name,
                    'message': record.getMessage()
                }
            else:
                # Logger message
                message_dict = {
                    'timestamp': timestamp,
                    'source': record.name,
                    'level': record.levelname,
                    'message': record.getMessage()
                }
            
            self._broadcast_to_clients(message_dict)
        except Exception as e:
            # Requirement 12.1: Handler failure isolation
            # Requirement 12.5: Log errors using fallback mechanism
            # Log error to fallback stream
            try:
                sys.__stderr__.write(f"[RemoteMonitoringHandler] Error broadcasting message: {e}\n")
                sys.__stderr__.flush()
            except:
                # Even fallback failed, silently continue
                pass
    
    def start_server(self):
        """Start TCP server for accepting client connections."""
        if self.running:
            return
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.port))
            self.server_socket.listen(5)
            
            self.running = True
            self.server_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.server_thread.start()
            
        except Exception as e:
            # Log error to fallback (sys.__stderr__)
            try:
                sys.__stderr__.write(f"Failed to start remote monitoring server: {e}\n")
                sys.__stderr__.flush()
            except:
                pass
    
    def stop_server(self):
        """Stop TCP server and close all client connections."""
        self.running = False
        
        # Close all client connections
        with self.lock:
            for client_socket in self.clients.copy():
                try:
                    client_socket.close()
                except Exception:
                    pass
            self.clients.clear()
        
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
    
    def _accept_connections(self):
        """Background thread for accepting new clients."""
        while self.running and self.server_socket:
            try:
                client_socket, address = self.server_socket.accept()
                
                with self.lock:
                    self.clients.append(client_socket)
                
                # Log connection to fallback stream
                try:
                    sys.__stdout__.write(f"Remote client connected from {address[0]}:{address[1]}\n")
                    sys.__stdout__.flush()
                except:
                    pass
                    
            except (ConnectionError, OSError):
                if self.running:
                    break
            except Exception:
                if self.running:
                    break
    
    def _broadcast_to_clients(self, message: dict):
        """
        Send message to all connected clients.
        
        Args:
            message: JSON-serializable message dict
        """
        if not self.clients:
            return
        
        try:
            json_data = json.dumps(message) + '\n'
            data = json_data.encode('utf-8')
        except (UnicodeEncodeError, TypeError):
            # Can't encode message, skip broadcast
            return
        
        # Create a copy of the client list to avoid modification during iteration
        with self.lock:
            clients_copy = self.clients.copy()
        
        failed_clients = []
        
        for client_socket in clients_copy:
            try:
                client_socket.send(data)
            except (ConnectionError, BrokenPipeError, OSError):
                # Client connection failed, mark for removal
                failed_clients.append(client_socket)
            except Exception:
                # Unexpected error, mark for removal
                failed_clients.append(client_socket)
        
        # Remove failed clients
        if failed_clients:
            with self.lock:
                for client_socket in failed_clients:
                    if client_socket in self.clients:
                        self.clients.remove(client_socket)
                    try:
                        client_socket.close()
                    except Exception:
                        pass
