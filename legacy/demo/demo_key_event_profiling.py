#!/usr/bin/env python3
"""
Demo: Key Event Profiling

This demo shows how key event profiling works in TFM.
It demonstrates:
1. Profiling key event handling
2. Profile file generation with timestamps
3. Profile file location output
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_profiling import ProfilingManager


def simulate_key_handler(event):
    """Simulate a key handler that does some work"""
    # Simulate file list processing
    files = []
    for i in range(100):
        files.append(f"file_{i}.txt")
    
    # Simulate sorting
    files.sort()
    
    # Simulate filtering
    filtered = [f for f in files if 'file' in f]
    
    # Simulate cursor movement
    cursor_pos = 0
    for _ in range(10):
        cursor_pos = (cursor_pos + 1) % len(filtered)
    
    return len(filtered)


class MockEvent:
    """Mock input event for testing"""
    def __init__(self, key_code):
        self.key_code = key_code


def main():
    print("=" * 70)
    print("TFM Key Event Profiling Demo")
    print("=" * 70)
    print()
    
    # Create temporary directory for profiling output
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary output directory: {temp_dir}")
    print()
    
    try:
        # Create profiling manager
        print("Creating ProfilingManager with profiling enabled...")
        profiling_manager = ProfilingManager(enabled=True, output_dir=temp_dir)
        print("✓ ProfilingManager created")
        print()
        
        # Simulate several key events
        print("Simulating key events with profiling:")
        print("-" * 70)
        
        key_events = [
            ('DOWN', 'Down arrow key'),
            ('UP', 'Up arrow key'),
            ('ENTER', 'Enter key'),
            ('TAB', 'Tab key'),
            ('ESC', 'Escape key'),
        ]
        
        for key_code, description in key_events:
            print(f"\nProcessing: {description} ({key_code})")
            event = MockEvent(key_code)
            
            # Profile the key handling
            result = profiling_manager.profile_key_handling(simulate_key_handler, event)
            print(f"  Handler returned: {result}")
            
            # Small delay to ensure unique timestamps
            time.sleep(0.01)
        
        print()
        print("-" * 70)
        print()
        
        # Show generated profile files
        print("Generated Profile Files:")
        print("-" * 70)
        profile_files = sorted(Path(temp_dir).glob("key_profile_*.prof"))
        
        for i, profile_file in enumerate(profile_files, 1):
            size = profile_file.stat().st_size
            print(f"{i}. {profile_file.name}")
            print(f"   Size: {size:,} bytes")
            print(f"   Path: {profile_file}")
            print()
        
        print(f"Total profile files created: {len(profile_files)}")
        print()
        
        # Show README
        readme_path = Path(temp_dir) / "README.txt"
        if readme_path.exists():
            print("README.txt created in output directory:")
            print("-" * 70)
            readme_content = readme_path.read_text()
            # Show first 20 lines
            lines = readme_content.split('\n')[:20]
            for line in lines:
                print(line)
            if len(readme_content.split('\n')) > 20:
                print("... (truncated)")
            print()
        
        # Show how to analyze profiles
        print("=" * 70)
        print("How to Analyze Profile Files:")
        print("=" * 70)
        print()
        print("1. Using pstats (built-in):")
        print(f"   python3 -m pstats {profile_files[0]}")
        print("   Then use commands like:")
        print("     sort cumulative")
        print("     stats 20")
        print("     callers function_name")
        print()
        print("2. Using snakeviz (visual):")
        print("   pip install snakeviz")
        print(f"   snakeviz {profile_files[0]}")
        print()
        
        # Demonstrate disabled profiling
        print("=" * 70)
        print("Testing Disabled Profiling (Zero Overhead):")
        print("=" * 70)
        print()
        
        disabled_manager = ProfilingManager(enabled=False, output_dir=temp_dir)
        print("Created ProfilingManager with profiling disabled")
        
        event = MockEvent('TEST')
        result = disabled_manager.profile_key_handling(simulate_key_handler, event)
        print(f"Handler executed and returned: {result}")
        
        # Verify no new files were created
        new_profile_files = sorted(Path(temp_dir).glob("key_profile_*.prof"))
        if len(new_profile_files) == len(profile_files):
            print("✓ No profile files created (as expected)")
        else:
            print("✗ Unexpected profile files created")
        print()
        
    finally:
        # Clean up
        print("=" * 70)
        print("Cleaning up temporary directory...")
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
        print("✓ Cleanup complete")
        print()
    
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
