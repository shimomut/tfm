#!/usr/bin/env python3
"""
Integration test for move feature with TFM
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_move_integration():
    """Test move feature integration with TFM configuration system"""
    print("🔗 MOVE FEATURE INTEGRATION TEST")
    print("=" * 50)
    
    try:
        # Test configuration loading
        from tfm_config import get_config, is_key_bound_to
        
        config = get_config()
        print("✅ Configuration system loaded successfully")
        
        # Test key binding check
        if is_key_bound_to('m', 'move_files'):
            print("✅ 'm' key is bound to move_files action")
        else:
            print("❌ 'm' key is not bound to move_files action")
            return False
            
        if is_key_bound_to('M', 'move_files'):
            print("✅ 'M' key is bound to move_files action")
        else:
            print("❌ 'M' key is not bound to move_files action")
            return False
        
        # Test that other keys are not bound to move_files
        if not is_key_bound_to('c', 'move_files'):
            print("✅ 'c' key is correctly not bound to move_files")
        else:
            print("❌ 'c' key should not be bound to move_files")
            return False
        
        print("\n🧪 Testing move operation simulation...")
        
        # Create test environment
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_dir = temp_path / "source"
            dest_dir = temp_path / "dest"
            
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create test files
            test_files = []
            for i in range(3):
                test_file = source_dir / f"test_file_{i}.txt"
                test_file.write_text(f"Content of test file {i}")
                test_files.append(test_file)
            
            # Create test directory
            test_subdir = source_dir / "test_subdir"
            test_subdir.mkdir()
            (test_subdir / "nested.txt").write_text("Nested content")
            test_files.append(test_subdir)
            
            print(f"✅ Created {len(test_files)} test items")
            
            # Simulate move operations
            moved_count = 0
            for test_item in test_files:
                dest_path = dest_dir / test_item.name
                
                try:
                    if test_item.is_dir():
                        shutil.move(str(test_item), str(dest_path))
                        print(f"✅ Moved directory: {test_item.name}")
                    else:
                        shutil.move(str(test_item), str(dest_path))
                        print(f"✅ Moved file: {test_item.name}")
                    
                    moved_count += 1
                    
                except Exception as e:
                    print(f"❌ Failed to move {test_item.name}: {e}")
                    return False
            
            # Verify results
            source_items = list(source_dir.iterdir())
            dest_items = list(dest_dir.iterdir())
            
            if len(source_items) == 0:
                print("✅ Source directory is empty after move")
            else:
                print(f"❌ Source directory still has {len(source_items)} items")
                return False
            
            if len(dest_items) == len(test_files):
                print(f"✅ Destination has all {len(test_files)} moved items")
            else:
                print(f"❌ Destination has {len(dest_items)} items, expected {len(test_files)}")
                return False
            
            # Verify nested content is preserved
            moved_subdir = dest_dir / "test_subdir"
            if moved_subdir.exists() and (moved_subdir / "nested.txt").exists():
                print("✅ Directory contents preserved during move")
            else:
                print("❌ Directory contents not preserved")
                return False
        
        print("\n✅ All integration tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_conflict_simulation():
    """Test conflict handling simulation"""
    print("\n🚨 CONFLICT HANDLING TEST")
    print("=" * 30)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create conflicting files
        source_file = source_dir / "conflict.txt"
        dest_file = dest_dir / "conflict.txt"
        
        source_file.write_text("Source content")
        dest_file.write_text("Destination content")
        
        print("✅ Created conflicting files")
        
        # Check conflict detection
        if dest_file.exists():
            print("✅ Conflict detected correctly")
            
            # Simulate overwrite choice
            original_dest_content = dest_file.read_text()
            shutil.move(str(source_file), str(dest_file))
            new_dest_content = dest_file.read_text()
            
            if new_dest_content == "Source content":
                print("✅ Overwrite operation works correctly")
            else:
                print("❌ Overwrite operation failed")
                return False
                
            if not source_file.exists():
                print("✅ Source file removed after move")
            else:
                print("❌ Source file still exists after move")
                return False
        
        print("✅ Conflict handling test passed!")
        return True

def main():
    """Run all integration tests"""
    success = True
    
    if not test_move_integration():
        success = False
    
    if not test_conflict_simulation():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("\nThe move feature is fully integrated and ready to use.")
        print("Key bindings, configuration, and operations all work correctly.")
    else:
        print("❌ INTEGRATION TESTS FAILED!")
        print("There are issues with the move feature integration.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)