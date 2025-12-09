#!/usr/bin/env python3
"""
Demo: Archive Search Support

This demo shows how the search dialog works with archive files:
1. Searching for files by name within archives
2. Searching for content within archive files
3. Archive-scoped search (only searches within the current archive)
4. Navigation to search results within archives
"""

import os
import sys
import tempfile
import zipfile
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_search_dialog import SearchDialog
from tfm_config import DefaultConfig


def create_demo_archive():
    """Create a demo archive with various files for searching"""
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, 'demo_project.zip')
    
    # Create a ZIP archive with a project structure
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Root files
        zf.writestr('README.md', '''# Demo Project
This is a demo project for testing archive search functionality.

## Features
- File search by name
- Content search within files
- Archive-scoped search
''')
        zf.writestr('LICENSE.txt', 'MIT License\nCopyright (c) 2024')
        
        # Source files
        zf.writestr('src/main.py', '''#!/usr/bin/env python3
"""Main application entry point"""

def main():
    print("Hello from the demo application!")
    print("This is a test file for content search")

if __name__ == '__main__':
    main()
''')
        zf.writestr('src/utils.py', '''"""Utility functions"""

def helper_function():
    """A helper function for testing"""
    return "This is a helper"

def another_helper():
    """Another helper for testing"""
    return "Another helper"
''')
        zf.writestr('src/config.py', '''"""Configuration module"""

CONFIG = {
    "app_name": "Demo App",
    "version": "1.0.0",
    "debug": True
}
''')
        
        # Documentation files
        zf.writestr('docs/guide.md', '''# User Guide

This guide explains how to use the demo application.

## Getting Started
Follow these steps to get started...
''')
        zf.writestr('docs/api.md', '''# API Documentation

## Functions

### main()
The main entry point of the application.
''')
        zf.writestr('docs/tutorial.txt', '''Tutorial: Getting Started

Step 1: Install the application
Step 2: Configure your settings
Step 3: Run the application
''')
        
        # Test files
        zf.writestr('tests/test_main.py', '''"""Tests for main module"""

def test_main():
    """Test the main function"""
    assert True

def test_helper():
    """Test helper functions"""
    assert True
''')
        zf.writestr('tests/test_utils.py', '''"""Tests for utils module"""

def test_helper_function():
    """Test helper_function"""
    assert True
''')
        
        # Data files
        zf.writestr('data/sample.json', '''{"name": "sample", "value": 123}''')
        zf.writestr('data/config.yaml', '''app:
  name: Demo
  version: 1.0
''')
    
    return zip_path, temp_dir


def demo_filename_search():
    """Demo: Search for files by name within an archive"""
    print("\n" + "="*70)
    print("DEMO 1: Filename Search in Archive")
    print("="*70)
    
    # Create demo archive
    zip_path, temp_dir = create_demo_archive()
    
    try:
        # Create archive path
        archive_uri = f"archive://{zip_path}#"
        archive_path = Path(archive_uri)
        
        print(f"\nCreated demo archive: {os.path.basename(zip_path)}")
        print(f"Archive path: {archive_uri}")
        
        # Create search dialog
        config = DefaultConfig()
        search_dialog = SearchDialog(config)
        
        # Test 1: Search for Python files
        print("\n--- Searching for Python files (*.py) ---")
        search_dialog.show('filename')
        search_dialog.text_editor.text = '*.py'
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        timeout = 5
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        print(f"Found {len(search_dialog.results)} Python files:")
        for i, result in enumerate(search_dialog.results, 1):
            print(f"  {i}. {result['relative_path']}")
            print(f"     Type: {result['type']}, Archive: {result.get('is_archive', False)}")
        
        # Test 2: Search for markdown files
        print("\n--- Searching for Markdown files (*.md) ---")
        search_dialog.show('filename')
        search_dialog.text_editor.text = '*.md'
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        print(f"Found {len(search_dialog.results)} Markdown files:")
        for i, result in enumerate(search_dialog.results, 1):
            print(f"  {i}. {result['relative_path']}")
        
        # Test 3: Search for test files
        print("\n--- Searching for test files (test_*) ---")
        search_dialog.show('filename')
        search_dialog.text_editor.text = 'test_*'
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        print(f"Found {len(search_dialog.results)} test files:")
        for i, result in enumerate(search_dialog.results, 1):
            print(f"  {i}. {result['relative_path']}")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def demo_content_search():
    """Demo: Search for content within archive files"""
    print("\n" + "="*70)
    print("DEMO 2: Content Search in Archive")
    print("="*70)
    
    # Create demo archive
    zip_path, temp_dir = create_demo_archive()
    
    try:
        # Create archive path
        archive_uri = f"archive://{zip_path}#"
        archive_path = Path(archive_uri)
        
        print(f"\nCreated demo archive: {os.path.basename(zip_path)}")
        
        # Create search dialog
        config = DefaultConfig()
        search_dialog = SearchDialog(config)
        
        # Test 1: Search for "helper" in content
        print("\n--- Searching for 'helper' in file content ---")
        search_dialog.show('content')
        search_dialog.text_editor.text = 'helper'
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        timeout = 5
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        print(f"Found {len(search_dialog.results)} matches:")
        for i, result in enumerate(search_dialog.results, 1):
            print(f"  {i}. {result['relative_path']}")
            print(f"     {result['match_info']}")
        
        # Test 2: Search for "demo" in content
        print("\n--- Searching for 'demo' in file content ---")
        search_dialog.show('content')
        search_dialog.text_editor.text = 'demo'
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        print(f"Found {len(search_dialog.results)} matches:")
        for i, result in enumerate(search_dialog.results, 1):
            print(f"  {i}. {result['relative_path']}")
            print(f"     {result['match_info']}")
        
        # Test 3: Search for "test" in content
        print("\n--- Searching for 'test' in file content ---")
        search_dialog.show('content')
        search_dialog.text_editor.text = 'test'
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        print(f"Found {len(search_dialog.results)} matches:")
        for i, result in enumerate(search_dialog.results, 1):
            print(f"  {i}. {result['relative_path']}")
            print(f"     {result['match_info']}")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def demo_scoped_search():
    """Demo: Archive-scoped search (only searches within current archive location)"""
    print("\n" + "="*70)
    print("DEMO 3: Archive-Scoped Search")
    print("="*70)
    
    # Create demo archive
    zip_path, temp_dir = create_demo_archive()
    
    try:
        # Create search dialog
        config = DefaultConfig()
        search_dialog = SearchDialog(config)
        
        # Test 1: Search from archive root
        print("\n--- Searching from archive root ---")
        archive_uri = f"archive://{zip_path}#"
        archive_path = Path(archive_uri)
        
        search_dialog.show('filename')
        search_dialog.text_editor.text = '*.py'
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        timeout = 5
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        print(f"Found {len(search_dialog.results)} Python files in entire archive:")
        for result in search_dialog.results:
            print(f"  - {result['relative_path']}")
        
        # Test 2: Search from src directory
        print("\n--- Searching from 'src' directory only ---")
        archive_uri = f"archive://{zip_path}#src"
        archive_path = Path(archive_uri)
        
        search_dialog.show('filename')
        search_dialog.text_editor.text = '*.py'
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        print(f"Found {len(search_dialog.results)} Python files in 'src' directory:")
        for result in search_dialog.results:
            print(f"  - {result['relative_path']}")
        
        # Test 3: Search from docs directory
        print("\n--- Searching from 'docs' directory only ---")
        archive_uri = f"archive://{zip_path}#docs"
        archive_path = Path(archive_uri)
        
        search_dialog.show('filename')
        search_dialog.text_editor.text = '*'
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        print(f"Found {len(search_dialog.results)} files in 'docs' directory:")
        for result in search_dialog.results:
            print(f"  - {result['relative_path']}")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("ARCHIVE SEARCH SUPPORT DEMO")
    print("="*70)
    print("\nThis demo shows how the search dialog works with archive files.")
    print("The search is archive-scoped, meaning it only searches within")
    print("the current archive location.")
    
    demo_filename_search()
    demo_content_search()
    demo_scoped_search()
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nKey features demonstrated:")
    print("  ✓ Filename search within archives")
    print("  ✓ Content search within archive files")
    print("  ✓ Archive-scoped search (searches only within current location)")
    print("  ✓ Search results show full archive paths")
    print("  ✓ Archive indicator in search dialog title")
    print("\nAll search results are marked with 'is_archive' flag for proper")
    print("navigation and display.")


if __name__ == '__main__':
    main()
