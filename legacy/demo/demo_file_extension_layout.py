#!/usr/bin/env python3
"""
Demo: File Extension Layout Consistency

Tests that files with and without extensions are rendered with consistent spacing.
"""

from pathlib import Path

def main():
    """Test file extension layout consistency"""
    
    # Create a test directory with files with and without extensions
    test_dir = Path(__file__).parent.parent / 'temp' / 'extension_layout_test'
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test files
    test_files = [
        'file_with_extension.jpg',
        'file_without_extension',
        'another.txt',
        'noext',
        'document.pdf',
        'README'
    ]
    
    for filename in test_files:
        (test_dir / filename).touch()
    
    print(f"✓ Created test directory: {test_dir}")
    print(f"✓ Created test files: {', '.join(test_files)}")
    print("\n" + "="*70)
    print("MANUAL TEST INSTRUCTIONS")
    print("="*70)
    print("\n1. Launch TFM:")
    print(f"   python3 tfm.py {test_dir}")
    print("\n2. Verify layout consistency:")
    print("   - Files with extensions (.jpg, .txt, .pdf) should show extension in separate column")
    print("   - Files without extensions should align with the basename column")
    print("   - Size column should be consistently aligned for ALL files")
    print("   - There should be consistent spacing between columns")
    print("\n3. Test in both wide and narrow terminal widths")
    print("\n4. Press 'q' to quit TFM when done")
    print("\n" + "="*70)
    print("\nTest files are ready. Run TFM to verify the fix.")

if __name__ == '__main__':
    main()
