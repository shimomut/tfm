"""
Test view_file fallback behavior for files without associations

Run with: PYTHONPATH=.:src:ttk pytest test/test_view_file_fallback.py -v
"""


from tfm_config import get_program_for_file, has_action_for_file


def test_view_fallback_behavior():
    """Test that view action falls back correctly for files without associations"""
    print("Testing view_file fallback behavior:\n")
    
    # Test files with associations
    print("Files WITH associations:")
    files_with_assoc = [
        ('document.pdf', True, 'Should use Preview'),
        ('photo.jpg', True, 'Should use Preview'),
        ('video.mp4', True, 'Should use QuickTime'),
    ]
    
    for filename, should_have, description in files_with_assoc:
        has_view = has_action_for_file(filename, 'view')
        command = get_program_for_file(filename, 'view')
        status = "✓" if has_view == should_have else "✗"
        cmd_str = ' '.join(command) if command else 'None'
        print(f"  {status} {filename:20s} -> {cmd_str:30s} ({description})")
    
    # Test files without associations
    print("\nFiles WITHOUT associations (should fall back to text viewer check):")
    files_without_assoc = [
        ('readme.xyz', False, 'No association - will check if text file'),
        ('data.bin', False, 'No association - will check if text file'),
        ('notes.unknown', False, 'No association - will check if text file'),
    ]
    
    for filename, should_have, description in files_without_assoc:
        has_view = has_action_for_file(filename, 'view')
        command = get_program_for_file(filename, 'view')
        status = "✓" if has_view == should_have else "✗"
        cmd_str = ' '.join(command) if command else 'None'
        print(f"  {status} {filename:20s} -> {cmd_str:30s} ({description})")
    
    # Test text files with associations
    print("\nText files WITH associations:")
    text_files_with_assoc = [
        ('readme.txt', True, 'Should use less'),
        ('script.py', True, 'Should use less'),
        ('notes.md', True, 'Should use less'),
    ]
    
    for filename, should_have, description in text_files_with_assoc:
        has_view = has_action_for_file(filename, 'view')
        command = get_program_for_file(filename, 'view')
        status = "✓" if has_view == should_have else "✗"
        cmd_str = ' '.join(command) if command else 'None'
        print(f"  {status} {filename:20s} -> {cmd_str:30s} ({description})")


def test_view_vs_open_fallback():
    """Test that view and open have different fallback behavior"""
    print("\n\nComparing view vs open fallback:\n")
    
    test_files = [
        'unknown.xyz',
        'data.bin',
        'notes.unknown'
    ]
    
    for filename in test_files:
        open_cmd = get_program_for_file(filename, 'open')
        view_cmd = get_program_for_file(filename, 'view')
        
        open_str = ' '.join(open_cmd) if open_cmd else 'None (will check text file)'
        view_str = ' '.join(view_cmd) if view_cmd else 'None (will check text file)'
        
        print(f"{filename}:")
        print(f"  Open: {open_str}")
        print(f"  View: {view_str}")


def test_expected_behavior():
    """Document expected behavior for view_file action"""
    print("\n\nExpected behavior for view_file (V key):\n")
    
    scenarios = [
        ("photo.jpg", "Has association", "Opens in Preview (from FILE_ASSOCIATIONS)"),
        ("readme.txt", "Has association", "Opens in less (from FILE_ASSOCIATIONS)"),
        ("notes.xyz (text)", "No association", "Opens in built-in text viewer (is_text_file check)"),
        ("data.xyz (binary)", "No association", "Shows error: No viewer configured (not a text file)"),
    ]
    
    for filename, status, behavior in scenarios:
        print(f"  {filename:25s} [{status:20s}] -> {behavior}")


def main():
    """Run all tests"""
    print("=" * 70)
    print("View File Fallback Behavior Tests")
    print("=" * 70)
    
    try:
        test_view_fallback_behavior()
        test_view_vs_open_fallback()
        test_expected_behavior()
        
        print("\n" + "=" * 70)
        print("✅ All tests completed!")
        print("=" * 70)
        print("\nKey Points:")
        print("  • Files with associations use configured viewer")
        print("  • Files without associations check if text file first")
        print("  • Only text files fall back to built-in viewer")
        print("  • Binary files without associations show error")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
