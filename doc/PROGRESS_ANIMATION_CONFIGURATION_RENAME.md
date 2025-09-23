# Progress Animation Configuration Rename

## Overview

The animation configuration options have been renamed from `ANIMATION_*` to `PROGRESS_ANIMATION_*` to better reflect their purpose and provide clearer naming throughout the TFM application.

## Changes Made

### Configuration Names

**Before:**
```python
ANIMATION_PATTERN = 'spinner'
ANIMATION_SPEED = 0.2
```

**After:**
```python
PROGRESS_ANIMATION_PATTERN = 'spinner'
PROGRESS_ANIMATION_SPEED = 0.2
```

### Files Updated

#### Configuration Files
- **`src/tfm_config.py`**: Updated DefaultConfig with renamed settings
- **`src/_config.py`**: Updated user config template with renamed settings

#### Core Implementation
- **`src/tfm_progress_animator.py`**: Updated to use `PROGRESS_ANIMATION_*` configuration options

#### Test Files
- **`test/test_search_animation.py`**: Updated all test configurations
- **`test/test_search_animation_integration.py`**: Updated integration test configurations
- **`test/test_progress_animator_generalized.py`**: Updated generalized test configurations

#### Demo Files
- **`demo/demo_search_animation.py`**: Updated demo configurations and output
- **`demo/demo_progress_animator.py`**: Updated demo configurations and examples

#### Documentation
- **`doc/SEARCH_ANIMATION_FEATURE.md`**: Updated configuration examples and API reference
- **`doc/PROGRESS_ANIMATOR_GENERALIZATION.md`**: Updated generalization documentation

## Configuration Details

### DefaultConfig and User Config

Both configuration files now use the renamed settings:

```python
class Config(DefaultConfig):
    # Progress animation settings
    PROGRESS_ANIMATION_PATTERN = 'spinner'  # 'spinner', 'dots', 'progress', 'bounce', 'pulse', 'wave', 'clock', 'arrow'
    PROGRESS_ANIMATION_SPEED = 0.2          # Animation frame update interval in seconds
```

### ProgressAnimator Integration

The `ProgressAnimator` class now looks for the renamed configuration options:

```python
self.animation_pattern = pattern_override or getattr(config, 'PROGRESS_ANIMATION_PATTERN', 'spinner')
self.animation_speed = speed_override or getattr(config, 'PROGRESS_ANIMATION_SPEED', 0.2)
```

## Benefits of the Rename

### 1. Clearer Purpose
- `PROGRESS_ANIMATION_*` clearly indicates these settings are for progress indicators
- Avoids confusion with other potential animation systems in the future

### 2. Better Namespace Organization
- Groups related settings under a common prefix
- Makes it easier to find and understand animation-related configuration

### 3. Future-Proof Naming
- Leaves room for other animation types (e.g., `UI_ANIMATION_*`, `TRANSITION_ANIMATION_*`)
- Provides a clear pattern for future animation configuration

### 4. Consistent Terminology
- Aligns with the `ProgressAnimator` class name
- Maintains consistency throughout the codebase

## Usage Examples

### Basic Configuration
```python
class Config(DefaultConfig):
    PROGRESS_ANIMATION_PATTERN = 'pulse'
    PROGRESS_ANIMATION_SPEED = 0.15
```

### Available Patterns
- `'spinner'`: Classic spinning indicator (default)
- `'dots'`: Minimalist dot-based animation
- `'progress'`: Progress bar style animation
- `'bounce'`: Simple bouncing dot animation
- `'pulse'`: Pulsing circle animation
- `'wave'`: Wave-like vertical bars
- `'clock'`: Clock face animation
- `'arrow'`: Rotating arrow animation

### Speed Configuration
- Value in seconds between frame updates
- Default: `0.2` seconds
- Recommended range: `0.1` to `0.5`
- Smaller values = faster animation
- Larger values = slower animation

## Backward Compatibility

### No Breaking Changes
- All existing functionality is preserved
- The rename is internal to the configuration system
- Users only need to update their configuration files

### Migration Path
Users with existing custom configurations need to update their `~/.tfm/config.py`:

**Old configuration:**
```python
class Config(DefaultConfig):
    ANIMATION_PATTERN = 'dots'
    ANIMATION_SPEED = 0.1
```

**New configuration:**
```python
class Config(DefaultConfig):
    PROGRESS_ANIMATION_PATTERN = 'dots'
    PROGRESS_ANIMATION_SPEED = 0.1
```

## Testing

### Comprehensive Test Coverage
All tests have been updated and continue to pass:

```
✓ test_search_animation.py - All animation tests passed
✓ test_search_animation_integration.py - All integration tests passed
✓ test_progress_animator_generalized.py - All generalized tests passed
✓ test_threaded_search_dialog.py - Existing functionality preserved
```

### Verification Tests
- Configuration rename verification
- ProgressAnimator integration testing
- SearchDialog functionality testing
- Factory method testing
- Custom configuration testing

## Documentation Updates

### Updated Files
- Configuration examples updated throughout documentation
- API reference updated with new configuration names
- Demo output updated to show new configuration names
- Comments updated to reflect new naming

### Configuration Comments
All configuration options now have clear, descriptive comments:

```python
# Progress animation settings
PROGRESS_ANIMATION_PATTERN = 'spinner'  # Animation pattern for progress indicators
PROGRESS_ANIMATION_SPEED = 0.2          # Animation frame update interval in seconds
```

## Conclusion

The rename from `ANIMATION_*` to `PROGRESS_ANIMATION_*` provides:

1. **Clearer Intent**: The purpose of these settings is immediately obvious
2. **Better Organization**: Related settings are grouped under a common prefix
3. **Future Flexibility**: Leaves room for other animation configuration categories
4. **Consistent Naming**: Aligns with the `ProgressAnimator` class and related components

The change maintains full backward compatibility while providing a cleaner, more intuitive configuration system for users.