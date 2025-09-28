#!/usr/bin/env python3
"""
Demo: AWS S3 Support in TFM

This demo shows how TFM's Path class now supports AWS S3 operations
alongside local file system operations.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path

def demo_s3_path_creation():
    """Demonstrate S3 path creation and properties"""
    print("🔗 S3 Path Creation and Properties")
    print("-" * 40)
    
    # Create various S3 paths
    bucket_path = Path('s3://my-data-bucket/')
    file_path = Path('s3://my-data-bucket/documents/report.pdf')
    nested_path = Path('s3://my-data-bucket/projects/2024/analysis/data.csv')
    
    paths = [
        ("Bucket root", bucket_path),
        ("Simple file", file_path),
        ("Nested file", nested_path)
    ]
    
    for name, path in paths:
        print(f"\n{name}: {path}")
        print(f"  Scheme: {path.get_scheme()}")
        print(f"  Is remote: {path.is_remote()}")
        print(f"  Name: {path.name}")
        print(f"  Parent: {path.parent}")
        print(f"  Parts: {path.parts}")
        if path.suffix:
            print(f"  Suffix: {path.suffix}")

def demo_path_manipulation():
    """Demonstrate S3 path manipulation"""
    print("\n\n🔧 S3 Path Manipulation")
    print("-" * 40)
    
    base_path = Path('s3://my-bucket/data/2024/')
    
    print(f"Base path: {base_path}")
    
    # Join paths
    joined = base_path / 'reports' / 'monthly.xlsx'
    print(f"Joined path: {joined}")
    
    # Change file name
    renamed = joined.with_name('quarterly.xlsx')
    print(f"With new name: {renamed}")
    
    # Change extension
    csv_version = joined.with_suffix('.csv')
    print(f"With CSV extension: {csv_version}")
    
    # Get parent directories
    print(f"Parent: {joined.parent}")
    print(f"Grandparent: {joined.parent.parent}")

def demo_mixed_operations():
    """Demonstrate mixing local and S3 paths"""
    print("\n\n🔄 Mixed Local and S3 Operations")
    print("-" * 40)
    
    local_path = Path('/tmp/local_file.txt')
    s3_path = Path('s3://backup-bucket/files/remote_file.txt')
    
    print(f"Local path: {local_path}")
    print(f"  Scheme: {local_path.get_scheme()}")
    print(f"  Is remote: {local_path.is_remote()}")
    
    print(f"\nS3 path: {s3_path}")
    print(f"  Scheme: {s3_path.get_scheme()}")
    print(f"  Is remote: {s3_path.is_remote()}")
    
    # Show how TFM can handle both types
    paths = [local_path, s3_path]
    
    print("\nPath comparison:")
    for path in paths:
        storage_type = "Remote" if path.is_remote() else "Local"
        print(f"  {storage_type}: {path} ({path.get_scheme()})")

def demo_s3_operations_mock():
    """Demonstrate S3 operations (without actual AWS calls)"""
    print("\n\n⚡ S3 Operations (Mock Demo)")
    print("-" * 40)
    
    s3_file = Path('s3://my-bucket/documents/readme.txt')
    s3_dir = Path('s3://my-bucket/images/')
    
    print(f"S3 file: {s3_file}")
    print(f"S3 directory: {s3_dir}")
    
    # These operations would work with proper AWS credentials
    print("\nOperations that would work with AWS credentials:")
    print(f"  - Check if file exists: {s3_file}.exists()")
    print(f"  - Read file content: {s3_file}.read_text()")
    print(f"  - Write file content: {s3_file}.write_text('Hello S3!')")
    print(f"  - List directory: list({s3_dir}.iterdir())")
    print(f"  - Get file info: {s3_file}.stat()")
    print(f"  - Delete file: {s3_file}.unlink()")

def demo_tfm_integration():
    """Show how S3 paths integrate with TFM"""
    print("\n\n🎯 TFM Integration")
    print("-" * 40)
    
    print("S3 paths can now be used anywhere in TFM where paths are expected:")
    print()
    print("1. Navigation:")
    print("   - Navigate to: s3://my-bucket/")
    print("   - Browse S3 buckets and objects like local directories")
    print()
    print("2. File Operations:")
    print("   - Copy files between local and S3: local_file → s3://bucket/file")
    print("   - Move files: s3://bucket/old → s3://bucket/new")
    print("   - Delete S3 objects")
    print()
    print("3. External Programs:")
    print("   - TFM environment variables work with S3 paths")
    print("   - TFM_THIS_DIR could be 's3://bucket/folder/'")
    print("   - TFM_THIS_SELECTED could include S3 objects")
    print()
    print("4. Search and Filter:")
    print("   - Search within S3 buckets")
    print("   - Filter S3 objects by name patterns")

def main():
    """Run all demos"""
    print("TFM AWS S3 Support Demo")
    print("=" * 50)
    print()
    print("This demo shows TFM's new AWS S3 support capabilities.")
    print("S3 paths use the format: s3://bucket-name/key/path")
    print()
    
    demo_s3_path_creation()
    demo_path_manipulation()
    demo_mixed_operations()
    demo_s3_operations_mock()
    demo_tfm_integration()
    
    print("\n\n🎉 Demo Complete!")
    print()
    print("To use S3 support in TFM:")
    print("1. Install boto3: pip install boto3")
    print("2. Configure AWS credentials: aws configure")
    print("3. Navigate to S3 paths in TFM: s3://your-bucket/")
    print()
    print("Note: S3 operations require valid AWS credentials and appropriate permissions.")

if __name__ == '__main__':
    main()