#!/usr/bin/env python3
"""
Demo: SSH/SFTP Filename Spaces Fix

This demo shows that SFTP operations now correctly handle filenames with:
- Spaces
- Special characters
- Quotes

The fix adds proper quoting to all SFTP commands to handle these cases.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tfm_ssh_connection import SSHConnection


def demo_quote_path():
    """Demonstrate path quoting functionality."""
    print("=" * 70)
    print("SSH/SFTP Filename Spaces Fix Demo")
    print("=" * 70)
    print()
    
    # Create a connection instance (not actually connecting)
    config = {
        'HostName': 'example.com',
        'User': 'testuser',
        'Port': '22',
    }
    conn = SSHConnection('test-host', config)
    
    print("Testing path quoting for various filenames:")
    print()
    
    test_cases = [
        # (description, path, expected_result)
        ("Simple path", "/path/to/file.txt", '"/path/to/file.txt"'),
        ("Path with spaces", "/path/to/my file.txt", '"/path/to/my file.txt"'),
        ("Multiple spaces", "/path/with  multiple   spaces", '"/path/with  multiple   spaces"'),
        ("Path with quotes", '/path/to/"quoted".txt', '"/path/to/\\"quoted\\".txt"'),
        ("Path with parentheses", "/path/to/file (1).txt", '"/path/to/file (1).txt"'),
        ("Path with brackets", "/path/to/file[1].txt", '"/path/to/file[1].txt"'),
        ("Complex filename", '/remote/My Document (draft) "final".txt', 
         '"/remote/My Document (draft) \\"final\\".txt"'),
    ]
    
    for description, path, expected in test_cases:
        result = conn._quote_path(path)
        status = "✓" if result == expected else "✗"
        print(f"{status} {description}:")
        print(f"  Input:    {path}")
        print(f"  Output:   {result}")
        if result != expected:
            print(f"  Expected: {expected}")
        print()
    
    print("=" * 70)
    print("Key Points:")
    print("=" * 70)
    print()
    print("1. All paths are now wrapped in double quotes")
    print("2. Internal double quotes are escaped with backslash")
    print("3. This fixes SFTP operations with filenames containing:")
    print("   - Spaces")
    print("   - Special characters (parentheses, brackets, etc.)")
    print("   - Quotes")
    print()
    print("4. Affected operations:")
    print("   - list_directory() - listing directories")
    print("   - stat() - getting file metadata")
    print("   - read_file() - downloading files")
    print("   - write_file() - uploading files")
    print("   - delete_file() - deleting files")
    print("   - delete_directory() - deleting directories")
    print("   - create_directory() - creating directories")
    print("   - rename() - renaming/moving files")
    print()
    print("=" * 70)
    print("Implementation Details:")
    print("=" * 70)
    print()
    print("The fix adds a _quote_path() helper method that:")
    print("1. Escapes any double quotes in the path: \" → \\\"")
    print("2. Wraps the entire path in double quotes")
    print()
    print("All SFTP commands now use this method:")
    print("  Before: commands = [f'get {remote_path} {tmp_path}']")
    print("  After:  commands = [f'get {self._quote_path(remote_path)} {self._quote_path(tmp_path)}']")
    print()
    print("This ensures SFTP batch mode correctly interprets paths with spaces.")
    print()


if __name__ == '__main__':
    demo_quote_path()
