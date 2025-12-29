"""
Test script for batch rename functionality

Run with: PYTHONPATH=.:src:ttk pytest test/test_batch_rename.py -v
"""

import re
from tfm_path import Path

def test_batch_rename_logic():
    """Test the batch rename logic without the UI"""
    
    # Mock file list
    files = [
        Path("file001.txt"),
        Path("file002.txt"), 
        Path("file003.txt"),
        Path("document_old.md"),
        Path("document_new.md")
    ]
    
    # Test case 1: Add prefix
    print("=== Test 1: Add prefix ===")
    regex = "(.*)"
    destination = "backup_\\1"
    test_rename(files, regex, destination)
    
    # Test case 2: Change extension
    print("\n=== Test 2: Change extension ===")
    regex = "(.*)\.txt"
    destination = "\\1.bak"
    test_rename(files, regex, destination)
    
    # Test case 3: Add sequential numbers
    print("\n=== Test 3: Add sequential numbers ===")
    regex = "(.*)"
    destination = "\\1_\\d"
    test_rename(files, regex, destination)
    
    # Test case 4: Extract parts
    print("\n=== Test 4: Extract and reorder ===")
    regex = "(.*)_(.*)"
    destination = "\\2_\\1"
    test_rename(files, regex, destination)

def test_rename(files, regex_pattern, destination_pattern):
    """Test rename logic for given patterns"""
    print(f"Regex: {regex_pattern}")
    print(f"Destination: {destination_pattern}")
    print("Results:")
    
    try:
        pattern = re.compile(regex_pattern)
    except re.error as e:
        print(f"Invalid regex: {e}")
        return
    
    for i, file_path in enumerate(files):
        original_name = file_path.name
        match = pattern.search(original_name)
        
        if match:
            # Apply destination pattern with substitutions
            new_name = destination_pattern
            
            # Replace \0 with entire original filename
            new_name = new_name.replace('\\0', original_name)
            
            # Replace \1-\9 with regex groups
            for j in range(1, 10):
                group_placeholder = f'\\{j}'
                if group_placeholder in new_name:
                    try:
                        group_value = match.group(j) if j <= len(match.groups()) else ''
                        new_name = new_name.replace(group_placeholder, group_value)
                    except IndexError:
                        new_name = new_name.replace(group_placeholder, '')
            
            # Replace \d with index number
            new_name = new_name.replace('\\d', str(i + 1))
            
            print(f"  {original_name} → {new_name}")
        else:
            print(f"  {original_name} → (no match)")
