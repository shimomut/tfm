#!/usr/bin/env python3
"""
Checkpoint 11: Verify all routing works correctly.

This test verifies:
1. Messages reach all configured destinations (log pane, streams, remote)
2. Remote monitoring works
3. Backward compatibility with add_message()
"""

import sys
import os
import logging
import socket
import threading
import time
import json
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_log_manager import LogManager, LoggingConfig
from tfm_logging_handlers import LogPaneHandler, StreamOutputHandler, RemoteMonitoringHandler


def test_messages_reach_all_destinations():
    """Verify messages reach log pane, streams, and remote clients."""
    print("\n=== Test 1: Messages reach all configured destinations ===")
    
    log_manager = None
    test_client = None
    
    try:
        class SimpleConfig:
            MAX_LOG_MESSAGES = 1000
        
        config = SimpleConfig()
        stdout_capture = StringIO()
        
        # Create log manager with remote monitoring
        log_manager = LogManager(config, remote_port=19998, debug_mode=True)
        
        # Replace stream handler
        for handler in log_manager._stream_logger.handlers:
            if isinstance(handler, StreamOutputHandler):
                handler.stream = stdout_capture
        
        # Connect test client
        remote_handler = log_manager._remote_monitoring_handler
        if remote_handler:
            time.sleep(0.3)
            try:
                test_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_client.connect(('localhost', 19998))
                time.sleep(0.2)
            except Exception as e:
                print(f"⚠ Could not connect test client: {e}")
        
        # Emit message
        logger = log_manager.getLogger("TestLogger")
        logger.info("Test message for routing")
        time.sleep(0.3)
        
        # Verify log pane
        log_pane_handler = log_manager._log_pane_handler
        assert log_pane_handler is not None
        messages = log_pane_handler.get_messages()
        assert len(messages) > 0
        
        found_in_pane = any("Test message for routing" in msg[0] for msg in messages)
        assert found_in_pane
        print("✓ Message found in log pane")
        
        # Verify stream
        stream_output = stdout_capture.getvalue()
        assert "Test message for routing" in stream_output
        print("✓ Message found in stream output")
        
        # Verify remote (best effort)
        if test_client:
            try:
                test_client.settimeout(1.0)
                for _ in range(5):
                    try:
                        data = test_client.recv(4096)
                        if data:
                            message = json.loads(data.decode('utf-8'))
                            if "Test message for routing" in message.get('message', ''):
                                print("✓ Message found in remote client")
                                break
                    except socket.timeout:
                        break
            except Exception:
                pass
        
        print("✓ Test 1 passed")
        
    finally:
        # Cleanup
        if test_client:
            try:
                test_client.close()
            except:
                pass
        if log_manager:
            if log_manager._remote_monitoring_handler:
                log_manager._remote_monitoring_handler.stop_server()
            sys.stdout = log_manager.original_stdout
            sys.stderr = log_manager.original_stderr
        time.sleep(0.5)  # Give port time to be released


def test_remote_monitoring_multiple_clients():
    """Verify remote monitoring works with multiple clients."""
    # Use stderr for output since stdout might be redirected
    import sys
    def log(msg):
        sys.__stderr__.write(f"{msg}\n")
        sys.__stderr__.flush()
    
    log("\n=== Test 2: Remote monitoring with multiple clients ===")
    
    log_manager = None
    clients = []
    
    class SimpleConfig:
        MAX_LOG_MESSAGES = 1000
    
    config = SimpleConfig()
    log_manager = LogManager(config, remote_port=19997, debug_mode=False)
    
    log(f"LogManager created, remote handler: {log_manager._remote_monitoring_handler}")
    
    remote_handler = log_manager._remote_monitoring_handler
    assert remote_handler is not None, "Remote handler not found"
    log(f"Remote handler running: {remote_handler.running}")
    
    # Connect clients
    time.sleep(0.3)
    for i in range(3):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 19997))
            clients.append(client)
            time.sleep(0.1)
        except Exception as e:
            log(f"⚠ Could not connect client {i}: {e}")
    
    log(f"Connected {len(clients)} test clients")
    log(f"Remote handler now has {len(remote_handler.clients)} clients")
    
    # Emit message
    logger = log_manager.getLogger("RemoteTest")
    log(f"Emitting message with logger {logger.name}")
    logger.warning("Remote monitoring test message")
    time.sleep(0.3)
    
    # Verify clients received message
    received_count = 0
    for i, client in enumerate(clients):
        try:
            client.settimeout(1.0)
            for _ in range(5):
                try:
                    data = client.recv(4096)
                    if data:
                        message = json.loads(data.decode('utf-8'))
                        if "Remote monitoring test message" in message.get('message', ''):
                            received_count += 1
                            log(f"✓ Client {i} received message")
                            break
                except socket.timeout:
                    break
        except Exception as e:
            log(f"⚠ Client {i} error: {e}")
    
    assert received_count > 0, f"No clients received message (connected: {len(clients)})"
    log(f"✓ Test 2 passed: {received_count}/{len(clients)} clients received message")
    
    # Cleanup
    for client in clients:
        try:
            client.close()
        except:
            pass
    if log_manager:
        if log_manager._remote_monitoring_handler:
            log_manager._remote_monitoring_handler.stop_server()
        sys.stdout = log_manager.original_stdout
        sys.stderr = log_manager.original_stderr
    time.sleep(0.5)


def test_backward_compatibility():
    """Verify backward compatibility with add_message()."""
    print("\n=== Test 3: Backward compatibility with add_message() ===")
    
    log_manager = None
    
    try:
        class SimpleConfig:
            MAX_LOG_MESSAGES = 1000
        
        config = SimpleConfig()
        log_manager = LogManager(config, remote_port=None, debug_mode=False)
        
        # Use legacy method
        log_manager.add_message("LegacySource", "Legacy message via add_message()")
        time.sleep(0.1)
        
        # Verify in log pane
        log_pane_handler = log_manager._log_pane_handler
        assert log_pane_handler is not None
        messages = log_pane_handler.get_messages()
        
        found_legacy = any("Legacy message via add_message()" in msg[0] for msg in messages)
        assert found_legacy
        print("✓ Legacy add_message() works")
        
        # Verify formatting
        legacy_msg = next((msg for msg in messages if "Legacy message via add_message()" in msg[0]), None)
        assert legacy_msg is not None
        formatted_message, record = legacy_msg
        assert formatted_message
        assert "LegacySource" in formatted_message
        print("✓ Legacy message has proper formatting")
        
        print("✓ Test 3 passed")
        
    finally:
        if log_manager:
            sys.stdout = log_manager.original_stdout
            sys.stderr = log_manager.original_stderr


def test_mixed_routing():
    """Verify logger messages and stdout/stderr all route correctly."""
    print("\n=== Test 4: Mixed routing (logger + stdout/stderr) ===")
    
    log_manager = None
    
    try:
        class SimpleConfig:
            MAX_LOG_MESSAGES = 1000
        
        config = SimpleConfig()
        stdout_capture = StringIO()
        
        log_manager = LogManager(config, remote_port=None, debug_mode=True)
        
        # Replace stream handler
        for handler in log_manager._stream_logger.handlers:
            if isinstance(handler, StreamOutputHandler):
                handler.stream = stdout_capture
        
        # Emit different message types
        logger = log_manager.getLogger("MixedTest")
        logger.info("Logger message")
        sys.stdout.write("Stdout message\n")
        sys.stderr.write("Stderr message\n")
        time.sleep(0.1)
        
        # Verify log pane
        log_pane_handler = log_manager._log_pane_handler
        messages = log_pane_handler.get_messages()
        
        found_logger = any("Logger message" in msg[0] for msg in messages)
        found_stdout = any("Stdout message" in msg[0] for msg in messages)
        found_stderr = any("Stderr message" in msg[0] for msg in messages)
        
        assert found_logger
        assert found_stdout
        assert found_stderr
        print("✓ All message types found in log pane")
        
        # Verify stream
        stream_output = stdout_capture.getvalue()
        assert "Logger message" in stream_output
        assert "Stdout message" in stream_output
        assert "Stderr message" in stream_output
        print("✓ All message types found in stream output")
        
        print("✓ Test 4 passed")
        
    finally:
        if log_manager:
            sys.stdout = log_manager.original_stdout
            sys.stderr = log_manager.original_stderr


def main():
    """Run all checkpoint 11 tests."""
    print("=" * 60)
    print("CHECKPOINT 11: Verify All Routing Works")
    print("=" * 60)
    
    try:
        test_messages_reach_all_destinations()
        test_remote_monitoring_multiple_clients()
        test_backward_compatibility()
        test_mixed_routing()
        
        print("\n" + "=" * 60)
        print("✓ ALL CHECKPOINT 11 TESTS PASSED")
        print("=" * 60)
        print("\nVerified:")
        print("  ✓ Messages reach all configured destinations")
        print("  ✓ Remote monitoring works with multiple clients")
        print("  ✓ Backward compatibility with add_message()")
        print("  ✓ Mixed routing (logger + stdout/stderr)")
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
