#!/usr/bin/env python3
"""
Test script to demonstrate the incremental search functionality in TFM
"""

import fnmatch

def test_fnmatch_patterns():
    """Test various fnmatch patterns"""
    
    # Sample filenames
    filenames = [
        "README.md",
        "main.py", 
        "test_file.txt",
        "config.json",
        "setup.py",
        "requirements.txt",
        "LICENSE",
        "Makefile",
        "app.js",
        "style.css",
        "index.html"
    ]
    
    # Test patterns
    patterns = [
        "*.py",      # All Python files
        "*.txt",     # All text files  
        "*test*",    # Files containing 'test'
        "*.md",      # Markdown files
        "M*",        # Files starting with 'M'
        "*e*",       # Files containing 'e'
        "???.*",     # Files with 3-character names
        "*.???",     # Files with 3-character extensions
        "*config*",  # Files containing 'config'
        "*.j*"       # Files with extensions starting with 'j'
    ]
    
    print("TFM Search Pattern Testing")
    print("=" * 40)
    
    for pattern in patterns:
        print(f"\nPattern: '{pattern}'")
        matches = []
        for filename in filenames:
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                matches.append(filename)
        
        if matches:
            print(f"Matches: {', '.join(matches)}")
        else:
            print("No matches")

if __name__ == "__main__":
    test_fnmatch_patterns()