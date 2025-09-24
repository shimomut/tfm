#!/usr/bin/env python3
"""
TFM Remote Log Client - Monitor TFM logs remotely

This client connects to a TFM instance running with remote log monitoring
enabled and displays the log messages in real-time.

Usage:
    python tfm_log_client.py [host] [port]
    
Examples:
    python tfm_log_client.py localhost 8888
    python tfm_log_client.py 192.168.1.100 8888
"""

import sys
import socket
import json
import argparse
import signal
from datetime import datetime

class TFMLogClient:
    """Client for monitoring TFM logs remotely"""
    
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.running = True
        
        # Color codes for different log sources
        self.colors = {
            'SYSTEM': '\033[92m',    # Green
            'CONFIG': '\033[94m',    # Blue
            'STDOUT': '\033[97m',    # White
            'STDERR': '\033[91m',    # Red
            'ERROR': '\033[91m',     # Red
            'REMOTE': '\033[95m',    # Magenta
            'PING': '\033[90m',      # Dark gray
        }
        self.reset_color = '\033[0m'
    
    def connect(self):
        """Connect to the TFM log server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to TFM log server at {self.host}:{self.port}")
            print("Press Ctrl+C to disconnect\n")
            return True
        except ConnectionRefusedError:
            print(f"Error: Could not connect to {self.host}:{self.port}")
            print("Make sure TFM is running with --remote-log-port option")
            return False
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
    
    def format_log_message(self, timestamp, source, message):
        """Format a log message with colors"""
        if not message.strip():  # Skip empty messages (like pings)
            return None
            
        color = self.colors.get(source, '')
        formatted_time = timestamp
        formatted_source = f"[{source:>6}]"
        
        return f"{color}{formatted_time} {formatted_source} {message}{self.reset_color}"
    
    def listen(self):
        """Listen for log messages from the server"""
        if not self.socket:
            return
            
        buffer = ""
        
        try:
            while self.running:
                try:
                    data = self.socket.recv(4096).decode('utf-8')
                    if not data:
                        print("Server disconnected")
                        break
                    
                    buffer += data
                    
                    # Process complete JSON messages
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                message = json.loads(line)
                                formatted = self.format_log_message(
                                    message['timestamp'],
                                    message['source'],
                                    message['message']
                                )
                                if formatted:
                                    print(formatted)
                                    sys.stdout.flush()
                            except json.JSONDecodeError:
                                # Skip malformed messages
                                pass
                                
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Error receiving data: {e}")
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.disconnect()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nDisconnecting...")
    sys.exit(0)

def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="TFM Remote Log Client - Monitor TFM logs remotely",
        epilog="Connect to a TFM instance running with --remote-log-port option"
    )
    
    parser.add_argument(
        'host',
        nargs='?',
        default='localhost',
        help='TFM server hostname or IP address (default: localhost)'
    )
    
    parser.add_argument(
        'port',
        nargs='?',
        type=int,
        default=8888,
        help='TFM server port number (default: 8888)'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    return parser

def main():
    """Main function"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and configure client
    client = TFMLogClient(args.host, args.port)
    
    # Disable colors if requested
    if args.no_color:
        client.colors = {key: '' for key in client.colors}
        client.reset_color = ''
    
    # Connect and listen
    if client.connect():
        try:
            client.listen()
        except KeyboardInterrupt:
            print("\nDisconnecting...")
        finally:
            client.disconnect()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()