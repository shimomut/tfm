# S3 TTL Configuration Feature

## Overview

The S3 cache TTL (Time To Live) is now configurable through the TFM configuration system. This allows users to customize how long S3 API responses are cached, providing flexibility to balance between performance and data freshness.

## Configuration

### Default Value

The default S3 cache TTL is **60 seconds**, which provides a good balance between performance and data freshness for most use cases.

### Customizing TTL

To customize the S3 cache TTL, add the `S3_CACHE_TTL` setting to your `~/.tfm/config.py` file:

```python
class Config:
    # ... other settings ...
    
    # S3 cache TTL in seconds (default: 60)
    S3_CACHE_TTL = 120  # Cache for 2 minutes
    
    # ... rest of your config ...
```

### Recommended TTL Values

| TTL (seconds) | Duration | Use Case |
|---------------|----------|----------|
| 30 | 30 seconds | Very fresh data, more API calls |
| 60 | 1 minute | Default, good balance |
| 120 | 2 minutes | Less API calls, slightly stale data |
| 300 | 5 minutes | Good for stable directories |
| 600 | 10 minutes | Minimal API calls, longer staleness |

## Implementation Details

### Configuration Classes

The `S3_CACHE_TTL` setting is available in both:

- `DefaultConfig` class in `src/tfm_config.py` - provides the default value
- `Config` class in `src/_config.py` - template for user configuration

### S3 Cache Integration

The S3 cache system (`S3Cache` class) now:

1. **Reads TTL from configuration** - The `get_s3_cache()` function reads the TTL value from the user's configuration
2. **Falls back gracefully** - If configuration is unavailable or missing the setting, defaults to 60 seconds
3. **Uses configurable default TTL** - All cache entries use the configured TTL unless explicitly overridden

### Removed Hard-coded Values

Previously hard-coded TTL values of 300 seconds (5 minutes) in the following locations have been removed:

- Directory listing cache in `iterdir()` method
- File metadata cache in `_yield_paths_from_cached_listing()` method

These now use the configurable default TTL from the cache instance.

## Benefits

### Performance Tuning

- **Lower TTL values** (30-60 seconds): More API calls, fresher data, better for frequently changing directories
- **Higher TTL values** (300-600 seconds): Fewer API calls, better performance, suitable for stable directories

### Cost Optimization

- Longer TTL values reduce S3 API calls, which can help reduce AWS costs for high-traffic applications
- Users can tune based on their specific usage patterns and cost requirements

### Flexibility

- Different environments (development, staging, production) can use different TTL values
- Users can experiment with different values to find the optimal balance for their workflow

## Usage Examples

### Development Environment
```python
# Shorter TTL for development where files change frequently
S3_CACHE_TTL = 30
```

### Production Environment
```python
# Longer TTL for production where directories are more stable
S3_CACHE_TTL = 300
```

### High-Performance Setup
```python
# Very long TTL for maximum performance
S3_CACHE_TTL = 600
```

## Testing

The feature includes comprehensive tests in `test/test_s3_ttl_configuration.py` that verify:

- Default TTL configuration is properly set
- S3 cache uses the configured TTL value
- Fallback behavior when configuration is unavailable
- Custom TTL values are respected
- Singleton behavior of the global cache

## Demo

Run the demo script to see the configuration in action:

```bash
python demo/demo_s3_ttl_configuration.py
```

The demo shows:
- Current default and configured TTL values
- S3 cache creation with the configured TTL
- Examples of different TTL values and their use cases
- Instructions for configuring custom TTL values

## Migration

### Existing Users

Existing TFM installations will automatically use the new default TTL of 60 seconds, which is more conservative than the previous hard-coded 300 seconds. This provides fresher data by default.

### Upgrading Configuration

Users who want to maintain the previous behavior can set:

```python
S3_CACHE_TTL = 300  # Previous hard-coded value
```

### No Breaking Changes

The change is fully backward compatible - existing configurations without `S3_CACHE_TTL` will use the default value.