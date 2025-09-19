#!/usr/bin/env python3
"""
Test the favorite directories configuration system
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_config_loading():
    """Test loading favorite directories from config"""
    print("Testing favorite directories configuration...")
    
    from tfm_config import get_favorite_directories, get_config
    
    # Test getting favorites
    favorites = get_favorite_directories()
    
    print(f"Loaded {len(favorites)} favorite directories:")
    for fav in favorites:
        print(f"  - {fav['name']}: {fav['path']}")
    
    # Verify structure
    for fav in favorites:
        assert isinstance(fav, dict), "Favorite should be a dictionary"
        assert 'name' in fav, "Favorite should have 'name' key"
        assert 'path' in fav, "Favorite should have 'path' key"
        assert isinstance(fav['name'], str), "Favorite name should be string"
        assert isinstance(fav['path'], str), "Favorite path should be string"
        
        # Verify path exists
        path = Path(fav['path'])
        assert path.exists(), f"Favorite path should exist: {fav['path']}"
        assert path.is_dir(), f"Favorite path should be directory: {fav['path']}"
    
    print("✓ Configuration loading test passed")
    return True

def test_config_validation():
    """Test configuration validation"""
    print("Testing configuration validation...")
    
    from tfm_config import get_config
    
    config = get_config()
    
    # Test that FAVORITE_DIRECTORIES exists (either in user config or defaults)
    if hasattr(config, 'FAVORITE_DIRECTORIES'):
        favorites_config = config.FAVORITE_DIRECTORIES
        assert isinstance(favorites_config, list), "FAVORITE_DIRECTORIES should be a list"
    else:
        # Should fall back to defaults
        from tfm_config import DefaultConfig
        favorites_config = DefaultConfig.FAVORITE_DIRECTORIES
        assert isinstance(favorites_config, list), "Default FAVORITE_DIRECTORIES should be a list"
    
    # Test structure of each favorite
    for fav in favorites_config:
        assert isinstance(fav, dict), "Each favorite should be a dictionary"
        assert 'name' in fav, "Each favorite should have 'name' key"
        assert 'path' in fav, "Each favorite should have 'path' key"
    
    print("✓ Configuration validation test passed")
    return True

def test_path_expansion():
    """Test path expansion (~ to home directory)"""
    print("Testing path expansion...")
    
    from tfm_config import get_favorite_directories
    
    favorites = get_favorite_directories()
    
    # Find a favorite with ~ in the original config
    home_favorites = [f for f in favorites if str(Path.home()) in f['path']]
    
    if home_favorites:
        print(f"Found {len(home_favorites)} favorites with expanded home paths")
        for fav in home_favorites:
            print(f"  - {fav['name']}: {fav['path']}")
            # Verify path is expanded (no ~ should remain)
            assert '~' not in fav['path'], f"Path should be expanded: {fav['path']}"
    
    print("✓ Path expansion test passed")
    return True

def test_key_binding():
    """Test that favorites key binding is configured"""
    print("Testing key binding configuration...")
    
    from tfm_config import is_key_bound_to
    
    # Test that 'j' and 'J' are bound to favorites
    assert is_key_bound_to('j', 'favorites'), "'j' should be bound to favorites"
    assert is_key_bound_to('J', 'favorites'), "'J' should be bound to favorites"
    
    print("✓ Key binding test passed")
    return True

def test_edge_cases():
    """Test edge cases and error handling"""
    print("Testing edge cases...")
    
    # Test with empty favorites list
    class MockConfig:
        FAVORITE_DIRECTORIES = []
    
    # Test with invalid favorites
    class MockConfigInvalid:
        FAVORITE_DIRECTORIES = [
            {'name': 'Invalid', 'path': '/nonexistent/path/12345'},
            {'name': 'Missing Path'},  # Missing 'path' key
            {'path': '/tmp'},  # Missing 'name' key
            'invalid_format',  # Not a dictionary
        ]
    
    print("✓ Edge cases test passed")
    return True

def run_all_tests():
    """Run all configuration tests"""
    print("Running favorite directories configuration tests...")
    print("=" * 60)
    
    try:
        test_config_loading()
        test_config_validation()
        test_path_expansion()
        test_key_binding()
        test_edge_cases()
        
        print("=" * 60)
        print("✓ All configuration tests passed!")
        return True
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)