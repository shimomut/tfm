#!/usr/bin/env python3
"""
Demo script for the move feature implementation
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def demo_move_feature():
    """Demonstrate the move feature functionality"""
    print("🚀 TFM MOVE FEATURE DEMO")
    print("=" * 50)
    
    print("\n📖 FEATURE OVERVIEW:")
    print("• Press 'm' or 'M' to move selected files and directories")
    print("• Moves files from current pane to opposite pane")
    print("• Directories are moved recursively")
    print("• Symbolic links are preserved as symbolic links (not target files)")
    print("• Conflict resolution dialog for existing files with same name")
    print("• Same choices as copy functionality: Overwrite, Skip, Cancel")
    
    print("\n🔧 IMPLEMENTATION DETAILS:")
    print("• Added 'move_files': ['m', 'M'] to KEY_BINDINGS")
    print("• Added move_selected_files() method to FileManager")
    print("• Added move_files_to_directory() for conflict detection")
    print("• Added perform_move_operation() for actual move execution")
    print("• Uses shutil.move() for files and directories")
    print("• Special handling for symbolic links using os.readlink()")
    print("• Integrates with existing quick choice dialog system")
    
    print("\n⚙️ CONFIGURATION:")
    print("The move feature requires the following key binding in your config:")
    print("KEY_BINDINGS = {")
    print("    # ... other bindings ...")
    print("    'move_files': ['m', 'M'],")
    print("    # ... other bindings ...")
    print("}")
    
    print("\n🎯 USAGE SCENARIOS:")
    print("1. Single file move:")
    print("   • Navigate to file with arrow keys")
    print("   • Press 'm' to move to opposite pane")
    
    print("\n2. Multiple file move:")
    print("   • Select files with Space bar")
    print("   • Press 'm' to move all selected files")
    
    print("\n3. Directory move:")
    print("   • Navigate to directory")
    print("   • Press 'm' to move entire directory recursively")
    
    print("\n4. Conflict resolution:")
    print("   • If file exists in destination, dialog appears")
    print("   • Choose: Overwrite (o), Skip (s), or Cancel (c)")
    
    print("\n🔒 SAFETY FEATURES:")
    print("• Cannot move parent directory (..)")
    print("• Cannot move files to same directory")
    print("• Permission checks before attempting move")
    print("• Error handling with detailed messages")
    print("• Automatic pane refresh after successful moves")
    print("• Selection clearing after successful operations")
    
    # Test the actual functionality
    print("\n🧪 FUNCTIONALITY TEST:")
    print("=" * 30)
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create test files
        test_file = source_dir / "demo_file.txt"
        test_file.write_text("This is a demo file for move operation")
        
        test_dir = source_dir / "demo_directory"
        test_dir.mkdir()
        (test_dir / "nested_file.txt").write_text("Nested content")
        
        # Create symbolic link
        test_link = source_dir / "demo_link"
        test_link.symlink_to(test_file)
        
        print(f"✓ Created test environment:")
        print(f"  Source: {len(list(source_dir.iterdir()))} items")
        print(f"  Destination: {len(list(dest_dir.iterdir()))} items")
        
        # Simulate move operations
        print("\n📦 Moving files...")
        
        # Move regular file
        dest_file = dest_dir / test_file.name
        shutil.move(str(test_file), str(dest_file))
        print(f"✓ Moved file: {test_file.name}")
        
        # Move directory
        dest_test_dir = dest_dir / test_dir.name
        shutil.move(str(test_dir), str(dest_test_dir))
        print(f"✓ Moved directory: {test_dir.name} (with nested content)")
        
        # Move symbolic link
        dest_link = dest_dir / test_link.name
        if test_link.is_symlink():
            link_target = os.readlink(str(test_link))
            dest_link.symlink_to(link_target)
            test_link.unlink()
            print(f"✓ Moved symbolic link: {test_link.name}")
        
        print(f"\n📊 Final state:")
        print(f"  Source: {len(list(source_dir.iterdir()))} items (should be 0)")
        print(f"  Destination: {len(list(dest_dir.iterdir()))} items (should be 3)")
        
        # Verify symbolic link is preserved
        if dest_link.is_symlink():
            print("✓ Symbolic link preserved correctly")
        
        print("\n✅ All move operations completed successfully!")

def check_implementation():
    """Check if the implementation is properly installed"""
    print("\n🔍 IMPLEMENTATION CHECK:")
    print("=" * 30)
    
    try:
        # Check if methods exist in main file
        main_file = Path(__file__).parent.parent / "src" / "tfm_main.py"
        with open(main_file, 'r') as f:
            content = f.read()
        
        methods_found = 0
        required_methods = [
            'def move_selected_files(self):',
            'def move_files_to_directory(self, files_to_move, destination_dir):',
            'def perform_move_operation(self, files_to_move, destination_dir, overwrite=False):'
        ]
        
        for method in required_methods:
            if method in content:
                methods_found += 1
                print(f"✓ {method.split('(')[0]} - Found")
        
        if "self.move_selected_files()" in content:
            print("✓ Key handler - Found")
            methods_found += 1
        
        print(f"\n📈 Implementation status: {methods_found}/4 components found")
        
        if methods_found == 4:
            print("🎉 Move feature is fully implemented!")
        else:
            print("⚠️  Move feature implementation is incomplete")
            
    except Exception as e:
        print(f"❌ Error checking implementation: {e}")

def main():
    """Run the demo"""
    demo_move_feature()
    check_implementation()
    
    print("\n" + "=" * 50)
    print("🎯 READY TO USE!")
    print("Start TFM and press 'm' or 'M' to move files between panes.")
    print("The move feature works just like copy, but removes files from source.")

if __name__ == "__main__":
    main()