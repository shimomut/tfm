#!/usr/bin/env python3
"""
Demo: Remote Monitoring Handler - Task 9

This demo demonstrates the RemoteMonitoringHandler functionality:
- Starting a TCP server for remote log monitoring
- Broadcasting logger messages to connected clients
- Broadcasting stdout/stderr to connected clients
- Handling client connections and disconnections gracefully

To test this demo:
1. Run this script in one terminal
2. In another terminal, connect with: nc localhost 9999
3. You'll see JSON-formatted log messages appear in the nc terminal
"""

import sys
import os
import logging
import time
import threading

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_logging_handlers import RemoteMonitoringHandler


def demo_basic_remote_monitoring():
    """Demonstrate basic remote monitoring with logger messages"""
    print("=" * 60)
    print("Demo: Basic Remote Monitoring")
    print("=" * 60)
    print()
    print("Starting remote monitoring server on port 9999...")
    print("Connect with: nc localhost 9999")
    print()
    
    # Create and start handler
    handler = RemoteMonitoringHandler(port=9999)
    handler.start_server()
    
    # Create a logger and attach the handler
    logger = logging.getLogger("DemoLogger")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    print("Waiting 3 seconds for clients to connect...")
    time.sleep(3)
    
    print(f"Connected clients: {len(handler.clients)}")
    print()
    
    # Send various log messages
    print("Sending log messages...")
    logger.debug("This is a DEBUG message")
    time.sleep(0.5)
    
    logger.info("This is an INFO message")
    time.sleep(0.5)
    
    logger.warning("This is a WARNING message")
    time.sleep(0.5)
    
    logger.error("This is an ERROR message")
    time.sleep(0.5)
    
    logger.critical("This is a CRITICAL message")
    time.sleep(0.5)
    
    print()
    print("Demo complete. Stopping server...")
    handler.stop_server()
    print("✓ Server stopped")
    print()


def demo_stream_capture_monitoring():
    """Demonstrate remote monitoring with stdout/stderr capture"""
    print("=" * 60)
    print("Demo: Stream Capture Remote Monitoring")
    print("=" * 60)
    print()
    print("Starting remote monitoring server on port 9999...")
    print("Connect with: nc localhost 9999")
    print()
    
    # Create and start handler
    handler = RemoteMonitoringHandler(port=9999)
    handler.start_server()
    
    print("Waiting 3 seconds for clients to connect...")
    time.sleep(3)
    
    print(f"Connected clients: {len(handler.clients)}")
    print()
    
    # Send stream capture messages
    print("Sending stdout/stderr messages...")
    
    # Simulate stdout capture
    stdout_record = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="This is stdout output",
        args=(),
        exc_info=None
    )
    stdout_record.is_stream_capture = True
    handler.emit(stdout_record)
    time.sleep(0.5)
    
    # Simulate stderr capture
    stderr_record = logging.LogRecord(
        name="STDERR",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="This is stderr output",
        args=(),
        exc_info=None
    )
    stderr_record.is_stream_capture = True
    handler.emit(stderr_record)
    time.sleep(0.5)
    
    print()
    print("Demo complete. Stopping server...")
    handler.stop_server()
    print("✓ Server stopped")
    print()


def demo_multiple_clients():
    """Demonstrate broadcasting to multiple clients"""
    print("=" * 60)
    print("Demo: Multiple Client Broadcasting")
    print("=" * 60)
    print()
    print("Starting remote monitoring server on port 9999...")
    print("Connect multiple clients with: nc localhost 9999")
    print()
    
    # Create and start handler
    handler = RemoteMonitoringHandler(port=9999)
    handler.start_server()
    
    # Create a logger
    logger = logging.getLogger("MultiClientDemo")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    print("Waiting 5 seconds for clients to connect...")
    time.sleep(5)
    
    print(f"Connected clients: {len(handler.clients)}")
    print()
    
    if len(handler.clients) == 0:
        print("No clients connected. Skipping broadcast demo.")
    else:
        print(f"Broadcasting to {len(handler.clients)} client(s)...")
        
        for i in range(5):
            logger.info(f"Broadcast message {i+1} to all clients")
            time.sleep(1)
    
    print()
    print("Demo complete. Stopping server...")
    handler.stop_server()
    print("✓ Server stopped")
    print()


def demo_json_format():
    """Demonstrate JSON message format"""
    print("=" * 60)
    print("Demo: JSON Message Format")
    print("=" * 60)
    print()
    print("This demo shows the JSON format of messages sent to clients.")
    print()
    
    # Create handler (don't start server)
    handler = RemoteMonitoringHandler(port=9999)
    
    print("Logger message format:")
    print("-" * 40)
    print("{")
    print('  "timestamp": "HH:MM:SS",')
    print('  "source": "LoggerName",')
    print('  "level": "INFO",')
    print('  "message": "Log message text"')
    print("}")
    print()
    
    print("Stream capture format (stdout/stderr):")
    print("-" * 40)
    print("{")
    print('  "timestamp": "HH:MM:SS",')
    print('  "source": "STDOUT" or "STDERR",')
    print('  "message": "Raw output text"')
    print("}")
    print()
    print("Note: Stream captures don't include 'level' field")
    print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Remote Monitoring Handler Demo - Task 9")
    print("=" * 60)
    print()
    
    # Show JSON format first
    demo_json_format()
    
    # Run interactive demos
    print("Choose a demo to run:")
    print("1. Basic remote monitoring (logger messages)")
    print("2. Stream capture monitoring (stdout/stderr)")
    print("3. Multiple client broadcasting")
    print("4. Run all demos")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    print()
    
    if choice == '1':
        demo_basic_remote_monitoring()
    elif choice == '2':
        demo_stream_capture_monitoring()
    elif choice == '3':
        demo_multiple_clients()
    elif choice == '4':
        demo_basic_remote_monitoring()
        demo_stream_capture_monitoring()
        demo_multiple_clients()
    else:
        print("Invalid choice. Exiting.")
    
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)
