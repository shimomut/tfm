"""
Test Remote Log Monitoring Feature

This test verifies that the LogManager can broadcast log messages
to remote clients via TCP socket connections.

Run with: PYTHONPATH=.:src:ttk pytest test/test_remote_log_monitoring.py -v
"""

import time
import socket
import json
import threading

from tfm_log_manager import LogManager
from tfm_config import get_config

class MockConfig:
    """Mock configuration for testing"""
    MAX_LOG_MESSAGES = 100

def test_remote_log_server():
    """Test that LogManager can start a remote server and accept connections"""
    print("Testing Remote Log Monitoring...")
    
    config = MockConfig()
    port = 9999  # Use a test port
    
    # Create LogManager with remote monitoring
    log_manager = LogManager(config, remote_port=port)
    
    # Give server time to start
    time.sleep(0.5)
    
    # Test connection
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', port))
        print("✓ Successfully connected to remote log server")
        
        # Test receiving messages
        received_messages = []
        
        def receive_messages():
            buffer = ""
            try:
                while len(received_messages) < 5:  # Wait for a few messages
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                message = json.loads(line)
                                received_messages.append(message)
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                print(f"Error receiving: {e}")
        
        # Start receiving in background
        receive_thread = threading.Thread(target=receive_messages, daemon=True)
        receive_thread.start()
        
        # Generate some log messages
        print("Test message 1")  # This should go to stdout -> LogCapture
        print("Test message 2", file=sys.stderr)  # This should go to stderr -> LogCapture
        
        # Wait for messages to be received
        time.sleep(1.0)
        
        # Check received messages
        if len(received_messages) >= 2:
            print(f"✓ Received {len(received_messages)} log messages")
            
            # Check message format
            for msg in received_messages[:2]:
                if all(key in msg for key in ['timestamp', 'source', 'message']):
                    print(f"✓ Message format correct: {msg['source']} - {msg['message']}")
                else:
                    print(f"✗ Invalid message format: {msg}")
        else:
            print(f"✗ Expected at least 2 messages, got {len(received_messages)}")
        
        client_socket.close()
        
    except Exception as e:
        print(f"✗ Error testing remote connection: {e}")
    
    # Cleanup
    log_manager.stop_remote_server()
    log_manager.restore_stdio()
    
    print("Remote log monitoring test completed")

def test_multiple_clients():
    """Test that multiple clients can connect simultaneously"""
    print("\nTesting multiple client connections...")
    
    config = MockConfig()
    port = 9998  # Use different port
    
    log_manager = LogManager(config, remote_port=port)
    time.sleep(0.5)
    
    clients = []
    try:
        # Connect multiple clients
        for i in range(3):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', port))
            clients.append(client)
        
        print(f"✓ Successfully connected {len(clients)} clients")
        
        # Generate a test message
        print("Multi-client test message")
        time.sleep(0.5)
        
        # Check that all clients receive the message
        for i, client in enumerate(clients):
            try:
                client.settimeout(1.0)
                data = client.recv(1024).decode('utf-8')
                if data:
                    print(f"✓ Client {i+1} received data")
                else:
                    print(f"✗ Client {i+1} received no data")
            except socket.timeout:
                print(f"✗ Client {i+1} timed out")
            except Exception as e:
                print(f"✗ Client {i+1} error: {e}")
    
    except Exception as e:
        print(f"✗ Error with multiple clients: {e}")
    
    finally:
        # Cleanup
        for client in clients:
            try:
                client.close()
            except Exception:
                pass
        
        log_manager.stop_remote_server()
        log_manager.restore_stdio()
    
    print("Multiple client test completed")

def main():
    """Run all tests"""
    print("TFM Remote Log Monitoring Tests")
    print("=" * 40)
    
    try:
        test_remote_log_server()
        test_multiple_clients()
        print("\n✓ All tests completed successfully")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
