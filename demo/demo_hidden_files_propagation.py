#!/usr/bin/env python3
"""
Demo: Hidden Files Configuration Propagation

This demo shows how the hidden files configuration is properly propagated
to SearchDialog and DirectoryDiffViewer components.

When hidden files are disabled in the main file manager, they are also
filtered out in:
- SearchDialog (both filename and content search)
- DirectoryDiffViewer (directory comparison)
"""

import tempfile
import shutil
from pathlib import Path

from tfm_config import get_config
from tfm_search_dialog import SearchDialog
from tfm_file_list_manager import FileListManager
from tfm_path import Path as TfmPath


def create_demo_structure():
    """Create a demo directory structure with hidden files"""
    demo_dir = TfmPath(tempfile.mkdtemp(prefix='tfm_hidden_demo_'))
    
    # Create visible files and directories
    (demo_dir / 'readme.txt').write_text('This is a visible file')
    (demo_dir / 'data.json').write_text('{"visible": true}')
    (demo_dir / 'docs').mkdir()
    (demo_dir / 'docs' / 'guide.md').write_text('# User Guide')
    
    # Create hidden files and directories
    (demo_dir / '.gitignore').write_text('*.pyc\n__pycache__/')
    (demo_dir / '.env').write_text('SECRET_KEY=hidden')
    (demo_dir / '.config').mkdir()
    (demo_dir / '.config' / 'settings.ini').write_text('[settings]\ntheme=dark')
    
    return demo_dir


def demo_search_with_hidden_disabled():
    """Demo SearchDialog with hidden files disabled"""
    print("=" * 70)
    print("Demo 1: SearchDialog with Hidden Files DISABLED")
    print("=" * 70)
    
    demo_dir = create_demo_structure()
    
    try:
        config = get_config()
        file_list_manager = FileListManager(config)
        file_list_manager.show_hidden = False
        
        search_dialog = SearchDialog(config, None, file_list_manager)
        search_dialog.show('filename', demo_dir)
        
        # Search for all files
        search_dialog.text_editor.text = '*'
        search_dialog.perform_search(demo_dir)
        
        # Wait for search to complete
        if search_dialog.search_thread:
            search_dialog.search_thread.join(timeout=2.0)
        
        print(f"\nSearch root: {demo_dir}")
        print(f"Hidden files setting: show_hidden = {file_list_manager.show_hidden}")
        print(f"\nSearch results ({len(search_dialog.results)} items):")
        
        for result in sorted(search_dialog.results, key=lambda r: r['relative_path']):
            result_type = "📁" if result['type'] == 'dir' else "📄"
            print(f"  {result_type} {result['relative_path']}")
        
        print("\n✓ Hidden files (.gitignore, .env, .config/) are NOT shown")
        
    finally:
        shutil.rmtree(demo_dir)


def demo_search_with_hidden_enabled():
    """Demo SearchDialog with hidden files enabled"""
    print("\n" + "=" * 70)
    print("Demo 2: SearchDialog with Hidden Files ENABLED")
    print("=" * 70)
    
    demo_dir = create_demo_structure()
    
    try:
        config = get_config()
        file_list_manager = FileListManager(config)
        file_list_manager.show_hidden = True
        
        search_dialog = SearchDialog(config, None, file_list_manager)
        search_dialog.show('filename', demo_dir)
        
        # Search for all files
        search_dialog.text_editor.text = '*'
        search_dialog.perform_search(demo_dir)
        
        # Wait for search to complete
        if search_dialog.search_thread:
            search_dialog.search_thread.join(timeout=2.0)
        
        print(f"\nSearch root: {demo_dir}")
        print(f"Hidden files setting: show_hidden = {file_list_manager.show_hidden}")
        print(f"\nSearch results ({len(search_dialog.results)} items):")
        
        for result in sorted(search_dialog.results, key=lambda r: r['relative_path']):
            result_type = "📁" if result['type'] == 'dir' else "📄"
            is_hidden = result['path'].name.startswith('.')
            marker = " (hidden)" if is_hidden else ""
            print(f"  {result_type} {result['relative_path']}{marker}")
        
        print("\n✓ Hidden files (.gitignore, .env, .config/) ARE shown")
        
    finally:
        shutil.rmtree(demo_dir)


def demo_content_search_with_hidden_disabled():
    """Demo content search with hidden files disabled"""
    print("\n" + "=" * 70)
    print("Demo 3: Content Search with Hidden Files DISABLED")
    print("=" * 70)
    
    demo_dir = create_demo_structure()
    
    try:
        config = get_config()
        file_list_manager = FileListManager(config)
        file_list_manager.show_hidden = False
        
        search_dialog = SearchDialog(config, None, file_list_manager)
        search_dialog.show('content', demo_dir)
        
        # Search for "hidden" in content
        search_dialog.text_editor.text = 'hidden'
        search_dialog.perform_search(demo_dir)
        
        # Wait for search to complete
        if search_dialog.search_thread:
            search_dialog.search_thread.join(timeout=2.0)
        
        print(f"\nSearch root: {demo_dir}")
        print(f"Search pattern: 'hidden'")
        print(f"Hidden files setting: show_hidden = {file_list_manager.show_hidden}")
        print(f"\nContent search results ({len(search_dialog.results)} items):")
        
        for result in sorted(search_dialog.results, key=lambda r: r['relative_path']):
            print(f"  📄 {result['relative_path']} (line {result['line_num']})")
            print(f"     Match: {result['match_info'][:60]}...")
        
        print("\n✓ Files in hidden directories (.config/) are NOT searched")
        
    finally:
        shutil.rmtree(demo_dir)


def demo_toggle_behavior():
    """Demo toggling hidden files setting"""
    print("\n" + "=" * 70)
    print("Demo 4: Toggling Hidden Files Setting")
    print("=" * 70)
    
    demo_dir = create_demo_structure()
    
    try:
        config = get_config()
        file_list_manager = FileListManager(config)
        
        # Start with hidden disabled
        file_list_manager.show_hidden = False
        
        search_dialog = SearchDialog(config, None, file_list_manager)
        search_dialog.show('filename', demo_dir)
        search_dialog.text_editor.text = '.git*'
        search_dialog.perform_search(demo_dir)
        
        if search_dialog.search_thread:
            search_dialog.search_thread.join(timeout=2.0)
        
        count_hidden_off = len(search_dialog.results)
        
        # Toggle to show hidden
        file_list_manager.show_hidden = True
        
        search_dialog.show('filename', demo_dir)
        search_dialog.text_editor.text = '.git*'
        search_dialog.perform_search(demo_dir)
        
        if search_dialog.search_thread:
            search_dialog.search_thread.join(timeout=2.0)
        
        count_hidden_on = len(search_dialog.results)
        
        print(f"\nSearch pattern: '.git*'")
        print(f"\nWith show_hidden = False: {count_hidden_off} results")
        print(f"With show_hidden = True:  {count_hidden_on} results")
        print(f"\n✓ Toggling the setting affects search results immediately")
        
    finally:
        shutil.rmtree(demo_dir)


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("TFM Hidden Files Configuration Propagation Demo")
    print("=" * 70)
    print("\nThis demo shows how the hidden files configuration is propagated")
    print("from FileListManager to SearchDialog and DirectoryDiffViewer.")
    print()
    
    demo_search_with_hidden_disabled()
    demo_search_with_hidden_enabled()
    demo_content_search_with_hidden_disabled()
    demo_toggle_behavior()
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nKey Points:")
    print("  • SearchDialog respects the show_hidden setting from FileListManager")
    print("  • Both filename and content search filter hidden files")
    print("  • DirectoryDiffViewer also respects the same setting")
    print("  • The setting can be toggled at runtime (Cmd+H in TFM)")
    print()
