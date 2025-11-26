#!/usr/bin/env python3
"""
Demo: File Extension Associations

This demo shows how to use the file extension associations system
to get appropriate programs for different file types and actions.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_config import get_file_associations, get_program_for_file, has_action_for_file


def demo_basic_usage():
    """Demonstrate basic usage of file associations"""
    print("=" * 60)
    print("Basic Usage Demo")
    print("=" * 60)
    
    files = [
        'document.pdf',
        'photo.jpg',
        'video.mp4',
        'song.mp3',
        'script.py',
        'readme.txt'
    ]
    
    for filename in files:
        print(f"\n{filename}:")
        for action in ['open', 'view', 'edit']:
            command = get_program_for_file(filename, action)
            if command:
                print(f"  {action:6s}: {' '.join(command)}")
            else:
                print(f"  {action:6s}: (not configured)")


def demo_action_availability():
    """Demonstrate checking action availability"""
    print("\n" + "=" * 60)
    print("Action Availability Demo")
    print("=" * 60)
    
    filename = 'video.avi'
    print(f"\nChecking actions for {filename}:")
    
    for action in ['open', 'view', 'edit']:
        available = has_action_for_file(filename, action)
        status = "✓ Available" if available else "✗ Not available"
        print(f"  {action:6s}: {status}")


def demo_same_program_multiple_actions():
    """Demonstrate using same program for multiple actions"""
    print("\n" + "=" * 60)
    print("Same Program for Multiple Actions Demo")
    print("=" * 60)
    
    filename = 'image.png'
    print(f"\n{filename}:")
    
    open_cmd = get_program_for_file(filename, 'open')
    view_cmd = get_program_for_file(filename, 'view')
    edit_cmd = get_program_for_file(filename, 'edit')
    
    print(f"  Open:  {' '.join(open_cmd) if open_cmd else 'N/A'}")
    print(f"  View:  {' '.join(view_cmd) if view_cmd else 'N/A'}")
    print(f"  Edit:  {' '.join(edit_cmd) if edit_cmd else 'N/A'}")
    
    if open_cmd == view_cmd:
        print("\n  ℹ️  Open and View use the same program (Preview)")
    if edit_cmd and edit_cmd != open_cmd:
        print("  ℹ️  Edit uses a different program (image editor)")


def demo_case_insensitive():
    """Demonstrate case-insensitive matching"""
    print("\n" + "=" * 60)
    print("Case-Insensitive Matching Demo")
    print("=" * 60)
    
    filenames = ['document.pdf', 'DOCUMENT.PDF', 'Document.Pdf']
    
    print("\nAll these filenames match the same pattern:")
    for filename in filenames:
        command = get_program_for_file(filename, 'open')
        print(f"  {filename:20s} -> {' '.join(command) if command else 'N/A'}")


def demo_all_associations():
    """Show all configured file associations"""
    print("\n" + "=" * 60)
    print("All Configured Associations (Compact Format)")
    print("=" * 60)
    
    associations = get_file_associations()
    
    for i, entry in enumerate(associations, 1):
        if not isinstance(entry, dict) or 'extensions' not in entry:
            continue
        
        extensions = entry['extensions']
        if isinstance(extensions, str):
            ext_str = extensions
        else:
            ext_str = ', '.join(extensions)
        
        print(f"\n{i}. {ext_str}:")
        
        for key, command in entry.items():
            if key == 'extensions':
                continue
            
            if command:
                if isinstance(command, list):
                    cmd_str = ' '.join(command)
                else:
                    cmd_str = command
                print(f"  {key:12s}: {cmd_str}")
            else:
                print(f"  {key:12s}: (not configured)")


def demo_practical_example():
    """Show a practical example of using file associations"""
    print("\n" + "=" * 60)
    print("Practical Example: File Operation Handler")
    print("=" * 60)
    
    def handle_file_action(filename, action):
        """Simulate handling a file action"""
        command = get_program_for_file(filename, action)
        
        if command:
            print(f"\n{action.capitalize()} {filename}:")
            print(f"  Would execute: {' '.join(command)} {filename}")
            # In real code: subprocess.run(command + [filename])
        else:
            print(f"\n{action.capitalize()} {filename}:")
            print(f"  ✗ No program configured for this action")
    
    # Simulate user actions
    handle_file_action('vacation.jpg', 'view')
    handle_file_action('vacation.jpg', 'edit')
    handle_file_action('report.pdf', 'open')
    handle_file_action('unknown.xyz', 'open')


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("FILE EXTENSION ASSOCIATIONS DEMO")
    print("=" * 60)
    
    demo_basic_usage()
    demo_action_availability()
    demo_same_program_multiple_actions()
    demo_case_insensitive()
    demo_practical_example()
    demo_all_associations()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nTo customize file associations, edit ~/.tfm/config.py")
    print("and modify the FILE_ASSOCIATIONS dictionary.")


if __name__ == '__main__':
    main()
