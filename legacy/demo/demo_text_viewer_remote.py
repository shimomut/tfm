#!/usr/bin/env python3
"""
Demo: TextViewer Remote File Support

This demo shows how the TextViewer now supports remote files (like S3)
using the tfm_path abstraction mechanism.
"""

import sys
import os
import tempfile
import curses
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_text_viewer import TextViewer, is_text_file, view_text_file


def demo_local_file():
    """Demo viewing a local file"""
    print("=== Demo: Local File Support ===")
    
    # Create a temporary local file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""#!/usr/bin/env python3
# Sample Python file for TextViewer demo

def hello_world():
    \"\"\"A simple hello world function\"\"\"
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
""")
        temp_path = f.name
    
    try:
        local_path = Path(temp_path)
        print(f"Local file: {local_path}")
        print(f"Is text file: {is_text_file(local_path)}")
        print(f"Is remote: {local_path.is_remote()}")
        print(f"Scheme: {local_path.get_scheme()}")
        
        # Show file content
        content = local_path.read_text()
        lines = content.splitlines()
        print(f"File has {len(lines)} lines")
        print("First few lines:")
        for i, line in enumerate(lines[:5]):
            print(f"  {i+1}: {line}")
        
    finally:
        os.unlink(temp_path)
    
    print()


def demo_mock_s3_file():
    """Demo viewing a mock S3 file"""
    print("=== Demo: Mock S3 File Support ===")
    
    # Mock S3 file content
    s3_content = """# S3 Configuration File
# This file demonstrates remote file viewing

bucket_name: my-data-bucket
region: us-west-2
access_patterns:
  - read_heavy
  - batch_processing

endpoints:
  - name: primary
    url: https://s3.us-west-2.amazonaws.com
  - name: backup  
    url: https://s3.us-east-1.amazonaws.com

# Performance settings
cache_ttl: 300
max_connections: 10
retry_attempts: 3
"""
    
    # Create mock S3 path implementation
    with patch('tfm_path.Path._create_implementation') as mock_create:
        mock_impl = Mock()
        mock_impl.is_remote.return_value = True
        mock_impl.get_scheme.return_value = 's3'
        mock_impl.name = 'config.yml'
        mock_impl.suffix = '.yml'
        mock_impl.read_text.return_value = s3_content
        mock_impl.read_bytes.return_value = s3_content.encode('utf-8')
        mock_impl.exists.return_value = True
        mock_impl.is_file.return_value = True
        mock_impl.stat.return_value = Mock(st_size=len(s3_content))
        mock_create.return_value = mock_impl
        
        s3_path = Path('s3://my-bucket/config.yml')
        print(f"S3 file: {s3_path}")
        print(f"Is text file: {is_text_file(s3_path)}")
        print(f"Is remote: {s3_path.is_remote()}")
        print(f"Scheme: {s3_path.get_scheme()}")
        
        # Show file content
        content = s3_path.read_text()
        lines = content.splitlines()
        print(f"File has {len(lines)} lines")
        print("First few lines:")
        for i, line in enumerate(lines[:8]):
            print(f"  {i+1}: {line}")
    
    print()


def demo_text_viewer_initialization():
    """Demo TextViewer initialization with different file types"""
    print("=== Demo: TextViewer Initialization ===")
    
    # Mock curses screen and color functions
    mock_stdscr = Mock()
    mock_stdscr.getmaxyx.return_value = (24, 80)
    
    with patch('curses.color_pair', return_value=1):
        # Test with local file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Local file content\nLine 2\nLine 3")
            temp_path = f.name
        
        try:
            local_path = Path(temp_path)
            print("Local TextViewer:")
            viewer = TextViewer(mock_stdscr, local_path)
            print(f"  Lines loaded: {len(viewer.lines)}")
            print(f"  First line: {viewer.lines[0] if viewer.lines else 'None'}")
            print(f"  Syntax highlighting: {viewer.syntax_highlighting}")
        finally:
            os.unlink(temp_path)
        
        # Test with mock S3 file
        with patch('tfm_path.Path._create_implementation') as mock_create:
            mock_impl = Mock()
            mock_impl.is_remote.return_value = True
            mock_impl.get_scheme.return_value = 's3'
            mock_impl.name = 'data.json'
            mock_impl.suffix = '.json'
            mock_impl.read_text.return_value = '{"key": "value", "items": [1, 2, 3]}'
            mock_impl.stat.return_value = Mock(st_size=35)
            mock_create.return_value = mock_impl
            
            s3_path = Path('s3://bucket/data.json')
            print("\nS3 TextViewer:")
            viewer = TextViewer(mock_stdscr, s3_path)
            print(f"  Lines loaded: {len(viewer.lines)}")
            print(f"  First line: {viewer.lines[0] if viewer.lines else 'None'}")
            print(f"  Syntax highlighting: {viewer.syntax_highlighting}")
    
    print()


def demo_error_handling():
    """Demo error handling for remote files"""
    print("=== Demo: Error Handling ===")
    
    mock_stdscr = Mock()
    mock_stdscr.getmaxyx.return_value = (24, 80)
    
    with patch('curses.color_pair', return_value=1):
        # Test file not found
        with patch('tfm_path.Path._create_implementation') as mock_create:
            mock_impl = Mock()
            mock_impl.is_remote.return_value = True
            mock_impl.get_scheme.return_value = 's3'
            mock_impl.name = 'missing.txt'
            mock_impl.suffix = '.txt'
            mock_impl.read_text.side_effect = FileNotFoundError("S3 object not found")
            mock_create.return_value = mock_impl
            
            missing_path = Path('s3://bucket/missing.txt')
            print("File not found error:")
            viewer = TextViewer(mock_stdscr, missing_path)
            print(f"  Error message: {viewer.lines[0] if viewer.lines else 'None'}")
        
        # Test permission error
        with patch('tfm_path.Path._create_implementation') as mock_create:
            mock_impl = Mock()
            mock_impl.is_remote.return_value = True
            mock_impl.get_scheme.return_value = 's3'
            mock_impl.name = 'restricted.txt'
            mock_impl.suffix = '.txt'
            mock_impl.read_text.side_effect = PermissionError("Access denied")
            mock_create.return_value = mock_impl
            
            restricted_path = Path('s3://bucket/restricted.txt')
            print("\nPermission error:")
            viewer = TextViewer(mock_stdscr, restricted_path)
            print(f"  Error message: {viewer.lines[0] if viewer.lines else 'None'}")
    
    print()


def demo_binary_file_detection():
    """Demo binary file detection for remote files"""
    print("=== Demo: Binary File Detection ===")
    
    # Test text file
    with patch('tfm_path.Path._create_implementation') as mock_create:
        mock_impl = Mock()
        mock_impl.suffix = '.txt'
        mock_impl.name = 'text.txt'
        mock_impl.read_bytes.return_value = b"This is text content"
        mock_create.return_value = mock_impl
        
        text_path = Path('s3://bucket/text.txt')
        print(f"Text file detection: {is_text_file(text_path)}")
    
    # Test binary file
    with patch('tfm_path.Path._create_implementation') as mock_create:
        mock_impl = Mock()
        mock_impl.suffix = '.bin'
        mock_impl.name = 'binary.bin'
        mock_impl.read_bytes.return_value = b"Binary\x00content\x01\x02"
        mock_create.return_value = mock_impl
        
        binary_path = Path('s3://bucket/binary.bin')
        print(f"Binary file detection: {is_text_file(binary_path)}")
    
    # Test by extension
    with patch('tfm_path.Path._create_implementation') as mock_create:
        mock_impl = Mock()
        mock_impl.suffix = '.py'
        mock_impl.name = 'script.py'
        mock_create.return_value = mock_impl
        
        python_path = Path('s3://bucket/script.py')
        print(f"Python file detection (by extension): {is_text_file(python_path)}")
    
    print()


def main():
    """Run all demos"""
    print("TextViewer Remote File Support Demo")
    print("=" * 40)
    print()
    
    demo_local_file()
    demo_mock_s3_file()
    demo_text_viewer_initialization()
    demo_error_handling()
    demo_binary_file_detection()
    
    print("Demo completed!")
    print("\nKey improvements:")
    print("- TextViewer now uses tfm_path abstraction for file operations")
    print("- Supports both local and remote files (S3, etc.)")
    print("- Better error handling with specific exception types")
    print("- Remote file scheme shown in header (e.g., 'S3: filename')")
    print("- Binary file detection works for remote files")
    print("- File size calculation works for remote files")


if __name__ == '__main__':
    main()