#!/usr/bin/env python3
"""
Demo: Profiling Output Directory Management

This demo demonstrates the profiling output directory management features:
1. Automatic directory creation
2. README.txt generation with analysis instructions
3. Configurable output directory path
4. Graceful error handling for file I/O issues
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_profiling import ProfilingManager, ProfileWriter


def demo_automatic_directory_creation():
    """Demonstrate automatic directory creation on first profile write"""
    print("=" * 70)
    print("Demo 1: Automatic Directory Creation")
    print("=" * 70)
    print()
    
    # Create a temporary directory for this demo
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "my_profiling_output")
        
        print(f"Output directory: {output_dir}")
        print(f"Directory exists before profiling: {Path(output_dir).exists()}")
        print()
        
        # Create profiling manager
        manager = ProfilingManager(enabled=True, output_dir=output_dir)
        
        # Profile a simple function
        def sample_function():
            return sum(range(1000))
        
        print("Profiling a sample function...")
        result = manager.profile_key_handling(sample_function)
        print(f"Function result: {result}")
        print()
        
        print(f"Directory exists after profiling: {Path(output_dir).exists()}")
        print(f"Directory is a directory: {Path(output_dir).is_dir()}")
        print()
        
        # List contents
        print("Directory contents:")
        for item in sorted(Path(output_dir).iterdir()):
            print(f"  - {item.name}")
        print()


def demo_readme_generation():
    """Demonstrate README.txt generation with analysis instructions"""
    print("=" * 70)
    print("Demo 2: README.txt Generation")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "profiling_with_readme")
        
        # Create profile writer
        writer = ProfileWriter(output_dir)
        writer.ensure_output_dir()
        
        readme_path = Path(output_dir) / "README.txt"
        print(f"README.txt created: {readme_path.exists()}")
        print()
        
        # Display README content
        print("README.txt content:")
        print("-" * 70)
        with open(readme_path, 'r') as f:
            print(f.read())
        print("-" * 70)
        print()


def demo_configurable_output_path():
    """Demonstrate configurable output directory path"""
    print("=" * 70)
    print("Demo 3: Configurable Output Directory Path")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Try different output directory paths
        paths = [
            os.path.join(tmpdir, "custom_profiling"),
            os.path.join(tmpdir, "nested", "profiling", "output"),
            os.path.join(tmpdir, "another_location"),
        ]
        
        for path in paths:
            print(f"Creating profiling manager with output_dir: {path}")
            manager = ProfilingManager(enabled=True, output_dir=path)
            
            # Profile a simple function to trigger directory creation
            def sample_function():
                return 42
            
            manager.profile_key_handling(sample_function)
            
            print(f"  Directory created: {Path(path).exists()}")
            print(f"  README.txt exists: {(Path(path) / 'README.txt').exists()}")
            print()


def demo_error_handling():
    """Demonstrate graceful error handling for file I/O issues"""
    print("=" * 70)
    print("Demo 4: Graceful Error Handling")
    print("=" * 70)
    print()
    
    # Test 1: Try to create directory in a read-only location (simulated)
    print("Test 1: Handling directory creation errors")
    print("-" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a directory and make it read-only
        readonly_dir = os.path.join(tmpdir, "readonly")
        os.makedirs(readonly_dir)
        os.chmod(readonly_dir, 0o444)  # Read-only
        
        # Try to create profiling output in a subdirectory of read-only dir
        output_dir = os.path.join(readonly_dir, "profiling_output")
        
        print(f"Attempting to create output directory in read-only location:")
        print(f"  {output_dir}")
        print()
        
        writer = ProfileWriter(output_dir)
        writer.ensure_output_dir()
        
        print("Note: Error message should be printed above (if any)")
        
        # Try to check if directory exists, but handle permission errors
        try:
            exists = Path(output_dir).exists()
            print(f"Directory created: {exists}")
        except PermissionError:
            print("Directory created: Cannot check (permission denied)")
        
        print()
        
        # Restore permissions for cleanup
        os.chmod(readonly_dir, 0o755)
    
    # Test 2: Verify profiling continues even if directory creation fails
    print("Test 2: Profiling continues despite directory errors")
    print("-" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        readonly_dir = os.path.join(tmpdir, "readonly2")
        os.makedirs(readonly_dir)
        os.chmod(readonly_dir, 0o444)
        
        output_dir = os.path.join(readonly_dir, "profiling_output")
        
        # Create profiling manager
        manager = ProfilingManager(enabled=True, output_dir=output_dir)
        
        # Profile a function - should not crash even if directory creation fails
        def sample_function():
            return "success"
        
        try:
            result = manager.profile_key_handling(sample_function)
            print(f"Function executed successfully: {result}")
            print("Profiling manager handled errors gracefully")
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        print()
        
        # Restore permissions for cleanup
        os.chmod(readonly_dir, 0o755)


def demo_multiple_profile_files():
    """Demonstrate multiple profile files in the same directory"""
    print("=" * 70)
    print("Demo 5: Multiple Profile Files")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "multi_profile")
        
        manager = ProfilingManager(enabled=True, output_dir=output_dir)
        
        # Create multiple profiles
        def key_handler():
            return "key"
        
        def render_function():
            return "render"
        
        print("Creating multiple profile files...")
        for i in range(3):
            manager.profile_key_handling(key_handler)
            manager.profile_rendering(render_function)
        
        print()
        print(f"Total key profiles: {manager.key_profile_count}")
        print(f"Total render profiles: {manager.render_profile_count}")
        print()
        
        # List all profile files
        print("Profile files in directory:")
        key_profiles = sorted(Path(output_dir).glob("key_profile_*.prof"))
        render_profiles = sorted(Path(output_dir).glob("render_profile_*.prof"))
        
        print(f"\nKey profiles ({len(key_profiles)}):")
        for profile in key_profiles:
            print(f"  - {profile.name}")
        
        print(f"\nRender profiles ({len(render_profiles)}):")
        for profile in render_profiles:
            print(f"  - {profile.name}")
        
        print()


def main():
    """Run all demos"""
    print()
    print("=" * 70)
    print("TFM Profiling Output Directory Management Demo")
    print("=" * 70)
    print()
    
    try:
        demo_automatic_directory_creation()
        demo_readme_generation()
        demo_configurable_output_path()
        demo_error_handling()
        demo_multiple_profile_files()
        
        print("=" * 70)
        print("All Demos Completed Successfully!")
        print("=" * 70)
        print()
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"Demo Error: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
