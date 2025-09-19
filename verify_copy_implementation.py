#!/usr/bin/env python3
"""
Verification script for the copy feature implementation
"""

def verify_implementation():
    """Verify that all copy feature components are properly implemented"""
    print("🔍 Verifying Copy Feature Implementation")
    print("=" * 45)
    
    errors = []
    warnings = []
    
    # Check 1: Configuration files
    print("\n1. Checking configuration files...")
    
    try:
        from _config import Config
        if hasattr(Config, 'KEY_BINDINGS') and 'copy_files' in Config.KEY_BINDINGS:
            copy_keys = Config.KEY_BINDINGS['copy_files']
            if 'c' in copy_keys and 'C' in copy_keys:
                print("   ✓ _config.py has copy_files binding")
            else:
                errors.append("_config.py missing 'c' and 'C' in copy_files binding")
        else:
            errors.append("_config.py missing copy_files key binding")
    except Exception as e:
        errors.append(f"Error loading _config.py: {e}")
    
    try:
        from tfm_config import DefaultConfig
        if hasattr(DefaultConfig, 'KEY_BINDINGS') and 'copy_files' in DefaultConfig.KEY_BINDINGS:
            copy_keys = DefaultConfig.KEY_BINDINGS['copy_files']
            if 'c' in copy_keys and 'C' in copy_keys:
                print("   ✓ tfm_config.py has copy_files binding")
            else:
                errors.append("tfm_config.py missing 'c' and 'C' in copy_files binding")
        else:
            errors.append("tfm_config.py missing copy_files key binding")
    except Exception as e:
        errors.append(f"Error loading tfm_config.py: {e}")
    
    # Check 2: Main implementation
    print("\n2. Checking main implementation...")
    
    try:
        with open('tfm_main.py', 'r') as f:
            content = f.read()
        
        required_methods = [
            'def copy_selected_files(self):',
            'def copy_files_to_directory(self, files_to_copy, destination_dir):',
            'def perform_copy_operation(self, files_to_copy, destination_dir, overwrite=False):'
        ]
        
        for method in required_methods:
            if method in content:
                print(f"   ✓ Found {method.split('(')[0].replace('def ', '')}")
            else:
                errors.append(f"Missing method: {method}")
        
        # Check key handler
        if "elif self.is_key_for_action(key, 'copy_files'):" in content:
            print("   ✓ Copy key handler found")
        else:
            errors.append("Copy key handler not found in main loop")
        
        # Check method call
        if "self.copy_selected_files()" in content:
            print("   ✓ Copy method call found")
        else:
            errors.append("Copy method call not found")
            
    except Exception as e:
        errors.append(f"Error reading tfm_main.py: {e}")
    
    # Check 3: Required imports
    print("\n3. Checking required imports...")
    
    try:
        with open('tfm_main.py', 'r') as f:
            content = f.read()
        
        required_imports = ['import os', 'import shutil', 'from pathlib import Path']
        
        for imp in required_imports:
            if imp in content:
                print(f"   ✓ {imp}")
            else:
                warnings.append(f"Import may be missing: {imp}")
                
    except Exception as e:
        errors.append(f"Error checking imports: {e}")
    
    # Check 4: Configuration integration
    print("\n4. Checking configuration integration...")
    
    try:
        from tfm_config import is_key_bound_to
        
        if is_key_bound_to('c', 'copy_files'):
            print("   ✓ 'c' key binding works")
        else:
            errors.append("'c' key binding not working")
            
        if is_key_bound_to('C', 'copy_files'):
            print("   ✓ 'C' key binding works")
        else:
            errors.append("'C' key binding not working")
            
    except Exception as e:
        errors.append(f"Error testing key bindings: {e}")
    
    # Check 5: Dialog integration
    print("\n5. Checking dialog integration...")
    
    try:
        with open('tfm_main.py', 'r') as f:
            content = f.read()
        
        dialog_features = [
            'self.show_dialog(',
            'choices = [',
            '"text": "Overwrite"',
            '"text": "Skip"',
            '"text": "Cancel"'
        ]
        
        for feature in dialog_features:
            if feature in content:
                print(f"   ✓ Dialog feature: {feature}")
            else:
                warnings.append(f"Dialog feature may be missing: {feature}")
                
    except Exception as e:
        errors.append(f"Error checking dialog integration: {e}")
    
    # Summary
    print("\n" + "=" * 45)
    print("VERIFICATION SUMMARY")
    print("=" * 45)
    
    if not errors and not warnings:
        print("🎉 ALL CHECKS PASSED!")
        print("The copy feature is fully implemented and ready to use.")
    else:
        if errors:
            print(f"❌ {len(errors)} ERRORS found:")
            for error in errors:
                print(f"   • {error}")
        
        if warnings:
            print(f"⚠️  {len(warnings)} WARNINGS:")
            for warning in warnings:
                print(f"   • {warning}")
        
        if not errors:
            print("\n✅ No critical errors found. Implementation should work.")
    
    print("\n📖 USAGE REMINDER:")
    print("• Press 'c' or 'C' to copy selected files")
    print("• Files are copied to the opposite pane's directory")
    print("• Directories are copied recursively")
    print("• Conflicts show Overwrite/Skip/Cancel dialog")

if __name__ == "__main__":
    verify_implementation()