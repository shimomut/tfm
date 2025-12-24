#!/usr/bin/env python3
"""
Thread Safety Verification Test

This test verifies that the thread safety implementation in LogPaneHandler
and RemoteMonitoringHandler works correctly under concurrent access.
"""

import sys
import os
import logging
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tfm_logging_handlers import LogPaneHandler, RemoteMonitoringHandler


def test_logpane_handler_concurrent_emit():
    """
    Verify LogPaneHandler handles concurrent emit() calls without corruption.
    
    This test creates multiple threads that simultaneously emit log messages
    and verifies that all messages are captured without data corruption.
    """
    handler = LogPaneHandler(max_messages=1000)
    
    # Number of threads and messages per thread
    num_threads = 10
    messages_per_thread = 100
    
    def emit_messages(thread_id):
        """Emit messages from a specific thread."""
        for i in range(messages_per_thread):
            record = logging.LogRecord(
                name=f"Thread{thread_id}",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Message {i} from thread {thread_id}",
                args=(),
                exc_info=None
            )
            handler.emit(record)
    
    # Create and start threads
    threads = []
    for thread_id in range(num_threads):
        thread = threading.Thread(target=emit_messages, args=(thread_id,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify all messages were captured
    messages = handler.get_messages()
    expected_count = num_threads * messages_per_thread
    
    print(f"Expected {expected_count} messages, got {len(messages)}")
    assert len(messages) == expected_count, f"Expected {expected_count} messages, got {len(messages)}"
    
    print("✓ LogPaneHandler concurrent emit test passed")


def test_logpane_handler_concurrent_get_messages():
    """
    Verify LogPaneHandler handles concurrent get_messages() calls safely.
    
    This test creates threads that simultaneously read messages while other
    threads are writing, verifying no crashes or data corruption occur.
    """
    handler = LogPaneHandler(max_messages=1000)
    
    # Add some initial messages
    for i in range(50):
        record = logging.LogRecord(
            name="Initial",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Initial message {i}",
            args=(),
            exc_info=None
        )
        handler.emit(record)
    
    num_reader_threads = 5
    num_writer_threads = 5
    iterations = 100
    
    def read_messages():
        """Read messages repeatedly."""
        for _ in range(iterations):
            messages = handler.get_messages()
            # Just verify we can read without crashing
            assert isinstance(messages, list)
    
    def write_messages(thread_id):
        """Write messages repeatedly."""
        for i in range(iterations):
            record = logging.LogRecord(
                name=f"Writer{thread_id}",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Message {i}",
                args=(),
                exc_info=None
            )
            handler.emit(record)
    
    # Create reader and writer threads
    threads = []
    
    for i in range(num_reader_threads):
        thread = threading.Thread(target=read_messages)
        threads.append(thread)
    
    for i in range(num_writer_threads):
        thread = threading.Thread(target=write_messages, args=(i,))
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("✓ LogPaneHandler concurrent read/write test passed")


def test_remote_handler_concurrent_client_management():
    """
    Verify RemoteMonitoringHandler handles concurrent client operations safely.
    
    This test simulates concurrent client additions and message broadcasts
    to verify thread-safe client list management.
    """
    handler = RemoteMonitoringHandler(port=9999)
    
    # Mock client sockets (we won't actually connect)
    class MockSocket:
        def __init__(self, client_id):
            self.client_id = client_id
            self.closed = False
        
        def send(self, data):
            if self.closed:
                raise ConnectionError("Socket closed")
        
        def close(self):
            self.closed = True
    
    num_threads = 10
    operations_per_thread = 50
    
    def add_and_remove_clients(thread_id):
        """Add and remove mock clients."""
        for i in range(operations_per_thread):
            # Add a mock client
            mock_socket = MockSocket(f"{thread_id}-{i}")
            with handler.lock:
                handler.clients.append(mock_socket)
            
            # Simulate some work
            time.sleep(0.001)
            
            # Remove the client
            with handler.lock:
                if mock_socket in handler.clients:
                    handler.clients.remove(mock_socket)
    
    def broadcast_messages(thread_id):
        """Broadcast messages while clients are being added/removed."""
        for i in range(operations_per_thread):
            message = {
                'timestamp': '12:00:00',
                'source': f'Thread{thread_id}',
                'level': 'INFO',
                'message': f'Message {i}'
            }
            handler._broadcast_to_clients(message)
            time.sleep(0.001)
    
    # Create threads
    threads = []
    
    for i in range(num_threads // 2):
        thread = threading.Thread(target=add_and_remove_clients, args=(i,))
        threads.append(thread)
    
    for i in range(num_threads // 2):
        thread = threading.Thread(target=broadcast_messages, args=(i,))
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("✓ RemoteMonitoringHandler concurrent client management test passed")


if __name__ == '__main__':
    print("Running thread safety verification tests...")
    print()
    
    test_logpane_handler_concurrent_emit()
    test_logpane_handler_concurrent_get_messages()
    test_remote_handler_concurrent_client_management()
    
    print()
    print("All thread safety verification tests passed!")
