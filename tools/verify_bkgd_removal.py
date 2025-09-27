#!/usr/bin/env python3
"""
Verification script to ensure bkgd() method has been completely removed
and replaced with addstr() approach for background colors.
"""

import os
import sys
import re

def check_file_for_bkgd(filepath):
    """Check a single file for bkgd() usage"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for bkgd usage
        bkgd_matches = re.findall(r'\.bkgd\s*\(', content, re.IGNORECASE)
        
        if bkgd_matches:
            return True, len(bkgd_matches)
        
        return False, 0
        
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False, 0

def scan_directory(directory, extensions=None):
    """Scan directory for bkgd() usage"""
    if extensions is None:
        extensions = ['.py']
    
    found_bkgd = False
    total_files = 0
    
    print(f"Scanning {directory} for bkgd() usage...")
    print("=" * 50)
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                
                # Skip the verification script itself
                if file == 'verify_bkgd_removal.py':
                    continue
                
                total_files += 1
                
                has_bkgd, count = check_file_for_bkgd(filepath)
                
                if has_bkgd:
                    found_bkgd = True
                    print(f"❌ FOUND bkgd() in {filepath} ({count} occurrences)")
                else:
                    print(f"✅ Clean: {filepath}")
    
    print("=" * 50)
    print(f"Scanned {total_files} files")
    
    if found_bkgd:
        print("❌ VERIFICATION FAILED: bkgd() usage still found!")
        return False
    else:
        print("✅ VERIFICATION PASSED: No bkgd() usage found!")
        return True

def check_addstr_background_usage():
    """Check that the new addstr() background approach is being used"""
    print("\nChecking for new addstr() background implementation...")
    print("=" * 50)
    
    # Check tfm_colors.py for the new implementation
    colors_file = os.path.join('src', 'tfm_colors.py')
    
    if not os.path.exists(colors_file):
        print(f"❌ {colors_file} not found!")
        return False
    
    try:
        with open(colors_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for COLOR_BACKGROUND constant
        if 'COLOR_BACKGROUND' in content:
            print("✅ COLOR_BACKGROUND constant found")
        else:
            print("❌ COLOR_BACKGROUND constant not found")
            return False
        
        # Check for addstr() in apply_background_to_window
        if 'window.addstr(y, 0,' in content and 'apply_background_to_window' in content:
            print("✅ New addstr() background implementation found")
        else:
            print("❌ New addstr() background implementation not found")
            return False
        
        # Check that bkgd is not used
        if '.bkgd(' in content:
            print("❌ bkgd() still found in colors file!")
            return False
        else:
            print("✅ No bkgd() usage in colors file")
        
        return True
        
    except Exception as e:
        print(f"Error checking {colors_file}: {e}")
        return False

def main():
    """Main verification function"""
    print("TFM Background Color Fix Verification")
    print("=" * 40)
    
    # Change to project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    success = True
    
    # Scan source files
    if not scan_directory('src'):
        success = False
    
    # Scan demo files
    if not scan_directory('demo'):
        success = False
    
    # Scan test files
    if not scan_directory('test'):
        success = False
    
    # Scan tools
    if not scan_directory('tools'):
        success = False
    
    # Check main file
    if os.path.exists('tfm.py'):
        has_bkgd, count = check_file_for_bkgd('tfm.py')
        if has_bkgd:
            print(f"❌ FOUND bkgd() in tfm.py ({count} occurrences)")
            success = False
        else:
            print("✅ Clean: tfm.py")
    
    # Check for new implementation
    if not check_addstr_background_usage():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 OVERALL VERIFICATION PASSED!")
        print("✅ No bkgd() usage found")
        print("✅ New addstr() background implementation confirmed")
        print("✅ Background color fix is complete and consistent")
        return 0
    else:
        print("❌ OVERALL VERIFICATION FAILED!")
        print("Some issues were found that need to be addressed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())