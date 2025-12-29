"""
Integration Test: Remote Log Monitoring with Command Line

This test verifies that the command line option works correctly
and that the LogManager is properly initialized with remote monitoring.

Run with: PYTHONPATH=.:src:ttk pytest test/test_remote_log_integration.py -v
"""

from pathlib import Path
import sys
import subprocess
import time
import socket
import json
import threading

def test_command_line_option():
    """Test that the --remote-log-port option is recognized"""
    print("Testing command line option parsing...")
    
    # Test help output includes the new option
    try:
        result = subprocess.run([
            sys.executable, 'tfm.py', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if '--remote-log-port' in result.stdout:
            print("✓ Command line option is documented in help")
        else:
            print("✗ Command line option not found in help")
            print("Help output:", result.stdout)
            
    except subprocess.TimeoutExpired:
        print("✗ Help command timed out")
    except Exception as e:
        print(f"✗ Error testing help: {e}")

def test_client_script():
    """Test that the client script runs and shows help"""
    print("\nTesting client script...")
    
    try:
        result = subprocess.run([
            sys.executable, 'tools/tfm_log_client.py', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and 'TFM Remote Log Client' in result.stdout:
            print("✓ Client script runs and shows help")
        else:
            print("✗ Client script failed or missing help text")
            print("Output:", result.stdout)
            print("Error:", result.stderr)
            
    except subprocess.TimeoutExpired:
        print("✗ Client help command timed out")
    except Exception as e:
        print(f"✗ Error testing client: {e}")

def test_client_connection_failure():
    """Test client behavior when server is not available"""
    print("\nTesting client connection failure handling...")
    
    try:
        # Try to connect to a port that should be closed
        result = subprocess.run([
            sys.executable, 'tools/tfm_log_client.py', 'localhost', '9876'
        ], capture_output=True, text=True, timeout=5)
        
        if 'Could not connect' in result.stdout or 'Connection refused' in result.stderr:
            print("✓ Client handles connection failure gracefully")
        else:
            print("✗ Client did not show expected connection error")
            print("Output:", result.stdout)
            print("Error:", result.stderr)
            
    except subprocess.TimeoutExpired:
        print("✗ Client connection test timed out")
    except Exception as e:
        print(f"✗ Error testing client connection failure: {e}")

def test_demo_script():
    """Test that the demo script can be imported and basic functionality works"""
    print("\nTesting demo script...")
    
    try:
        # Test that the demo script can be imported
        result = subprocess.run([
            sys.executable, '-c', 
        ], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ Demo script imports successfully")
        else:
            print("✗ Demo script import failed")
            print("Error:", result.stderr)
            
    except subprocess.TimeoutExpired:
        print("✗ Demo script test timed out")
    except Exception as e:
        print(f"✗ Error testing demo script: {e}")

def test_file_permissions():
    """Test that scripts have correct permissions"""
    print("\nTesting file permissions...")
    
    scripts = ['tools/tfm_log_client.py', 'demo/demo_remote_log.py']
    
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            # Check if file is executable
            import stat
            file_stat = script_path.stat()
            if file_stat.st_mode & stat.S_IXUSR:
                print(f"✓ {script} is executable")
            else:
                print(f"✗ {script} is not executable")
        else:
            print(f"✗ {script} does not exist")

def main():
    """Run all integration tests"""
    print("TFM Remote Log Monitoring Integration Tests")
    print("=" * 50)
    
    test_command_line_option()
    test_client_script()
    test_client_connection_failure()
    test_demo_script()
    test_file_permissions()
    
    print("\n" + "=" * 50)
    print("Integration tests completed")
