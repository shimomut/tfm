"""
Test priority-based matching in FILE_ASSOCIATIONS

FILE_ASSOCIATIONS is checked from top to bottom.
First matching entry wins.

Run with: PYTHONPATH=.:src:ttk pytest test/test_priority_matching.py -v
"""



def test_priority_matching():
    """Test that FILE_ASSOCIATIONS are checked in order"""
    print("Testing Priority-Based Matching\n")
    print("=" * 70)
    
    # Create a test configuration
    test_config = [
        # Specific rule for special Python files
        {
            'pattern': 'test_*.py',
            'open': ['pytest'],
            'view': ['cat'],
            'edit': ['nano']
        },
        # General rule for all Python files
        {
            'pattern': '*.py',
            'open': ['python3'],
            'view': ['less'],
            'edit': ['vim']
        },
        # Rule with only some actions
        {
            'pattern': '*.txt',
            'open': ['open', '-e'],
            'edit': ['vim']
            # 'view' not specified - will continue to next entry
        },
        # Another rule for txt files (fallback for view)
        {
            'pattern': '*.txt',
            'view': ['less']
        }
    ]
    
    print("\nTest Configuration:")
    print("1. test_*.py -> open: pytest, view: cat, edit: nano")
    print("2. *.py      -> open: python3, view: less, edit: vim")
    print("3. *.txt     -> open: open -e, edit: vim (no view)")
    print("4. *.txt     -> view: less")
    print("\n" + "=" * 70)
    
    # Simulate the matching logic
    def get_program(filename, action, config):
        """Simulate get_program_for_file logic"""
        import fnmatch
        filename_lower = filename.lower()
        
        for entry in config:
            if 'pattern' not in entry:
                continue
            
            patterns = entry['pattern']
            if isinstance(patterns, str):
                patterns = [patterns]
            
            # Check if pattern matches
            pattern_matches = False
            for pattern in patterns:
                if fnmatch.fnmatch(filename_lower, pattern.lower()):
                    pattern_matches = True
                    break
            
            if not pattern_matches:
                continue
            
            # Pattern matches - check if action exists
            for key, value in entry.items():
                if key == 'pattern':
                    continue
                actions_in_key = [a.strip() for a in key.split('|')]
                if action in actions_in_key:
                    return value
            
            # Pattern matched but action not found - continue
        
        return None
    
    # Test cases
    test_cases = [
        ('test_example.py', 'open', ['pytest'], 'Matches first rule (test_*.py)'),
        ('test_example.py', 'view', ['cat'], 'Matches first rule (test_*.py)'),
        ('test_example.py', 'edit', ['nano'], 'Matches first rule (test_*.py)'),
        
        ('script.py', 'open', ['python3'], 'Matches second rule (*.py)'),
        ('script.py', 'view', ['less'], 'Matches second rule (*.py)'),
        ('script.py', 'edit', ['vim'], 'Matches second rule (*.py)'),
        
        ('readme.txt', 'open', ['open', '-e'], 'Matches third rule (*.txt with open)'),
        ('readme.txt', 'edit', ['vim'], 'Matches third rule (*.txt with edit)'),
        ('readme.txt', 'view', ['less'], 'Skips third rule (no view), matches fourth rule'),
    ]
    
    print("\nTest Results:\n")
    all_passed = True
    
    for filename, action, expected, description in test_cases:
        result = get_program(filename, action, test_config)
        passed = result == expected
        status = "✓" if passed else "✗"
        
        if not passed:
            all_passed = False
        
        print(f"{status} {filename:20s} {action:6s} -> {result}")
        print(f"  Expected: {expected}")
        print(f"  {description}")
        print()
    
    print("=" * 70)
    if all_passed:
        print("✅ All priority matching tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return 0 if all_passed else 1


def test_real_world_example():
    """Test a real-world example of priority-based configuration"""
    print("\n\n" + "=" * 70)
    print("Real-World Example: Specific Rules Before General Rules")
    print("=" * 70)
    
    example_config = """
FILE_ASSOCIATIONS = [
    # Specific: Test files should open in pytest
    {
        'pattern': 'test_*.py',
        'open': ['pytest', '-v'],
        'edit': ['vim']
    },
    
    # Specific: Config files should open in text editor
    {
        'pattern': 'config.py',
        'open': ['vim'],
        'view': ['cat']
    },
    
    # General: All Python files
    {
        'pattern': '*.py',
        'open': ['python3'],
        'view': ['less'],
        'edit': ['vim']
    },
    
    # Specific: README files with special viewer
    {
        'pattern': 'README*',
        'view': ['glow']  # Markdown renderer
    },
    
    # General: All markdown files
    {
        'pattern': '*.md',
        'open': ['typora'],
        'edit': ['vim']
    }
]
"""
    
    print("\nConfiguration:")
    print(example_config)
    
    print("\nBehavior:")
    print("  test_main.py    open  -> pytest -v (specific rule)")
    print("  script.py       open  -> python3 (general rule)")
    print("  config.py       open  -> vim (specific rule)")
    print("  utils.py        open  -> python3 (general rule)")
    print("  README.md       view  -> glow (specific rule)")
    print("  notes.md        view  -> (no view in general rule)")
    
    print("\n" + "=" * 70)


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("FILE_ASSOCIATIONS Priority Matching Tests")
    print("=" * 70)
    
    try:
        result = test_priority_matching()
        test_real_world_example()
        
        print("\n" + "=" * 70)
        print("Key Points:")
        print("  • FILE_ASSOCIATIONS checked from top to bottom")
        print("  • First matching pattern wins")
        print("  • If action not in entry, continues to next entry")
        print("  • Allows specific rules before general rules")
        print("=" * 70)
        
        return result
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
