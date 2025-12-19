#!/usr/bin/env python3
"""
Demo: Remote Log Monitoring

This demo shows how to use the remote log monitoring feature.

1. Run this script: python demo_remote_log.py
2. In another terminal, run: python tools/tfm_log_client.py localhost 8888
3. Watch the log messages appear in the client terminal
"""

import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_log_manager import LogManager

class MockConfig:
    """Mock configuration for demo"""
    MAX_LOG_MESSAGES = 100

def main():
    """Demo the remote log monitoring feature"""
    print("TFM Remote Log Monitoring Demo")
    print("=" * 40)
    print("Starting log server on port 8888...")
    print("Connect with: python tools/tfm_log_client.py localhost 8888")
    print("Press Ctrl+C to stop")
    print()
    
    config = MockConfig()
    log_manager = LogManager(config, remote_port=8888)
    
    # Add some startup messages
    log_manager.add_startup_messages("0.95", "https://github.com/shimomut/tfm", "TFM Demo")
    
    try:
        counter = 1
        while True:
            # Generate various types of log messages
            if counter % 5 == 0:
                print(f"STDOUT message #{counter}", file=sys.stderr)
            else:
                print(f"Demo log message #{counter}")
            
            if counter % 10 == 0:
                # Simulate an error message
                import logging
                logging.error(f"Simulated error #{counter//10}")
            
            counter += 1
            time.sleep(2)  # Wait 2 seconds between messages
            
    except KeyboardInterrupt:
        print("\nStopping demo...")
    finally:
        log_manager.stop_remote_server()
        log_manager.restore_stdio()
        print("Demo stopped")

if __name__ == "__main__":
    main()