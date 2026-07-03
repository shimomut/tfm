#!/usr/bin/env python3
"""
Demo: S3 TTL Configuration

This demo shows how to configure S3 cache TTL through the Config class.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from _config import Config, get_config
    from tfm_s3 import get_s3_cache
except ImportError as e:
    print(f"Import error: {e}")
    print("This demo requires the TFM modules to be available")
    sys.exit(1)


def demo_default_ttl():
    """Demonstrate the default S3 cache TTL configuration"""
    print("=== S3 Cache TTL Configuration Demo ===\n")
    
    print("1. Default Configuration:")
    print(f"   Config.S3_CACHE_TTL = {Config.S3_CACHE_TTL} seconds")
    
    # Get current config
    config = get_config()
    if hasattr(config, 'S3_CACHE_TTL'):
        print(f"   Current Config.S3_CACHE_TTL = {config.S3_CACHE_TTL} seconds")
    else:
        print("   Current config does not have S3_CACHE_TTL set (will use default)")
    
    print()


def demo_cache_creation():
    """Demonstrate S3 cache creation with configured TTL"""
    print("2. S3 Cache Creation:")
    
    # Clear any existing cache to demonstrate fresh creation
    import tfm_s3
    tfm_s3._s3_cache = None
    
    # Get the cache (this will create it with configured TTL)
    cache = get_s3_cache()
    
    print(f"   Created S3 cache with TTL: {cache.default_ttl} seconds")
    print(f"   Cache max entries: {cache.max_entries}")
    
    # Get cache stats
    stats = cache.get_stats()
    print(f"   Cache stats: {stats}")
    
    print()


def demo_custom_ttl_simulation():
    """Simulate different TTL configurations"""
    print("3. Custom TTL Simulation:")
    
    # Simulate different TTL values that could be set in config
    custom_ttls = [30, 60, 120, 300, 600]
    
    print("   Different TTL values you can set in your config:")
    for ttl in custom_ttls:
        print(f"   - S3_CACHE_TTL = {ttl} seconds ({ttl//60} minutes)" if ttl >= 60 else f"   - S3_CACHE_TTL = {ttl} seconds")
    
    print()


def demo_configuration_instructions():
    """Show how to configure S3 TTL"""
    print("4. How to Configure S3 Cache TTL:")
    print("""
   To customize the S3 cache TTL, add this to your ~/.tfm/config.py:
   
   class Config:
       # ... other settings ...
       
       # S3 cache TTL in seconds (default: 60)
       S3_CACHE_TTL = 120  # Cache for 2 minutes
       
       # ... rest of your config ...
   
   Common TTL values:
   - 30 seconds  - Very fresh data, more API calls
   - 60 seconds  - Default, good balance
   - 120 seconds - Less API calls, slightly stale data
   - 300 seconds - 5 minutes, good for stable directories
   - 600 seconds - 10 minutes, minimal API calls
   """)


def main():
    """Run the S3 TTL configuration demo"""
    try:
        demo_default_ttl()
        demo_cache_creation()
        demo_custom_ttl_simulation()
        demo_configuration_instructions()
        
        print("=== Demo Complete ===")
        print("The S3 cache TTL is now configurable through the Config class!")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()