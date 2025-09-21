#!/usr/bin/env python3
"""
Test script for new confirmation options in TFM configuration system
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_confirmation_config_options():
    """Test that new confirmation options are available in configuration"""
    print("Testing confirmation configuration options...")
    
    try:
        from tfm_config import DefaultConfig, get_config
        
        # Test that new confirmation options exist in DefaultConfig
        assert hasattr(DefaultConfig, 'CONFIRM_COPY'), "CONFIRM_COPY not found in DefaultConfig"
        assert hasattr(DefaultConfig, 'CONFIRM_MOVE'), "CONFIRM_MOVE not found in DefaultConfig"
        assert hasattr(DefaultConfig, 'CONFIRM_EXTRACT_ARCHIVE'), "CONFIRM_EXTRACT_ARCHIVE not found in DefaultConfig"
        
        # Test default values
        assert DefaultConfig.CONFIRM_COPY == True, "CONFIRM_COPY should default to True"
        assert DefaultConfig.CONFIRM_MOVE == True, "CONFIRM_MOVE should default to True"
        assert DefaultConfig.CONFIRM_EXTRACT_ARCHIVE == True, "CONFIRM_EXTRACT_ARCHIVE should default to True"
        
        print("✓ All new confirmation options found in DefaultConfig with correct defaults")
        
        # Test that config can be loaded
        config = get_config()
        
        # Test that new options are accessible (may fall back to defaults for existing user configs)
        confirm_copy = getattr(config, 'CONFIRM_COPY', True)
        confirm_move = getattr(config, 'CONFIRM_MOVE', True)
        confirm_extract = getattr(config, 'CONFIRM_EXTRACT_ARCHIVE', True)
        
        # These should be boolean values (either from config or default fallback)
        assert isinstance(confirm_copy, bool), "CONFIRM_COPY should be boolean"
        assert isinstance(confirm_move, bool), "CONFIRM_MOVE should be boolean"
        assert isinstance(confirm_extract, bool), "CONFIRM_EXTRACT_ARCHIVE should be boolean"
        
        print("✓ All new confirmation options accessible from loaded config (with fallback defaults)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing confirmation options: {e}")
        return False

def test_template_config_file():
    """Test that template config file contains new confirmation options"""
    print("Testing template configuration file...")
    
    try:
        template_file = Path(__file__).parent.parent / 'src' / '_config.py'
        
        if not template_file.exists():
            print(f"✗ Template config file not found: {template_file}")
            return False
        
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Check that new confirmation options are in the template
        assert 'CONFIRM_COPY' in content, "CONFIRM_COPY not found in template config"
        assert 'CONFIRM_MOVE' in content, "CONFIRM_MOVE not found in template config"
        assert 'CONFIRM_EXTRACT_ARCHIVE' in content, "CONFIRM_EXTRACT_ARCHIVE not found in template config"
        
        print("✓ All new confirmation options found in template config file")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing template config file: {e}")
        return False

def test_confirmation_usage():
    """Test that confirmation options can be used with getattr"""
    print("Testing confirmation option usage pattern...")
    
    try:
        from tfm_config import get_config
        
        config = get_config()
        
        # Test the getattr pattern used in the main code
        confirm_copy = getattr(config, 'CONFIRM_COPY', True)
        confirm_move = getattr(config, 'CONFIRM_MOVE', True)
        confirm_extract = getattr(config, 'CONFIRM_EXTRACT_ARCHIVE', True)
        
        # These should all be boolean values
        assert isinstance(confirm_copy, bool), "CONFIRM_COPY should be boolean"
        assert isinstance(confirm_move, bool), "CONFIRM_MOVE should be boolean"
        assert isinstance(confirm_extract, bool), "CONFIRM_EXTRACT_ARCHIVE should be boolean"
        
        print("✓ All confirmation options work with getattr pattern")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing confirmation usage: {e}")
        return False

def main():
    """Run all confirmation option tests"""
    print("=" * 60)
    print("TFM Confirmation Options Test")
    print("=" * 60)
    
    tests = [
        test_confirmation_config_options,
        test_template_config_file,
        test_confirmation_usage,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        if test():
            passed += 1
        else:
            print("Test failed!")
    
    print()
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All confirmation option tests passed!")
        return True
    else:
        print("✗ Some tests failed!")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)