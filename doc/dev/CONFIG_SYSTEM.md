# TFM Configuration System

## Overview

TFM uses a single-source configuration system where all default values are defined in `src/_config.py`, and user customizations are stored in `~/.tfm/config.py`.

## Architecture

### Single Source of Truth

All configuration defaults are defined in the `Config` class in `src/_config.py`. This file serves dual purposes:

1. **Template** - Copied to `~/.tfm/config.py` when user first runs TFM
2. **Default Provider** - Source for filling missing fields in user configs

### Automatic Field Copying

When TFM loads configuration, it automatically:
1. Loads the user's `~/.tfm/config.py` (if it exists)
2. Loads the template `Config` class from `src/_config.py`
3. Copies any missing fields from template to user config
4. Returns a complete config with all fields present

This ensures:
- New config options appear automatically in existing user configs
- Corrupted configs get filled in with defaults
- Users never need to manually update their config files

## Configuration Loading Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ConfigManager.load_config() called                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Load template Config class from src/_config.py           │
│    (_load_template_config)                                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Check if ~/.tfm/config.py exists                         │
└─────────────────────────────────────────────────────────────┘
         ↓ No                              ↓ Yes
┌──────────────────────┐      ┌──────────────────────────────┐
│ 4a. Copy _config.py  │      │ 4b. Load user's config.py    │
│     to ~/.tfm/       │      │     (may fail if corrupted)  │
└──────────────────────┘      └──────────────────────────────┘
         ↓                                  ↓
         └──────────────┬───────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Copy missing fields from template to user config         │
│    (_copy_missing_fields)                                   │
│    - Compares user config attributes with template          │
│    - Adds any missing public attributes                     │
│    - Logs each field that gets added                        │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Return complete config with all fields present           │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### ConfigManager (src/tfm_config.py)

Main class that manages configuration loading and access.

**Key Methods:**
- `load_config()` - Loads user config and fills missing fields
- `get_config()` - Returns current config (loads if needed)
- `reload_config()` - Forces reload from disk
- `get_key_bindings()` - Returns KeyBindings instance

### Helper Functions (src/tfm_config.py)

**`_load_template_config()`**
- Dynamically loads `Config` class from `src/_config.py`
- Returns the class (not instance) for field inspection
- Handles import errors gracefully

**`_copy_missing_fields(user_config, template_config_class)`**
- Copies missing attributes from template to user config
- Only copies public attributes (excludes `_` prefixed)
- Logs each field added and total count

### KeyBindings Class (src/tfm_config.py)

Manages key binding lookups and parsing.

**Key Methods:**
- `find_action_for_event(event, has_selection)` - Find action for key press
- `get_keys_for_action(action)` - Get keys bound to action
- `format_key_for_display(key_expr)` - Format key for UI display

## Adding New Configuration Options

### Step 1: Add to _config.py

Add your new option to the `Config` class in `src/_config.py`:

```python
class Config:
    # ... existing options ...
    
    # Your new option
    MY_NEW_OPTION = 'default_value'
```

### Step 2: That's It!

The system automatically:
- Copies the new field to existing user configs on next launch
- Provides the default value from template
- Logs when the field is added

### Example

```python
# In src/_config.py
class Config:
    # New option for controlling cache size
    CACHE_MAX_SIZE = 1000  # Maximum cache entries
```

When users launch TFM:
```
INFO: Added missing config field: CACHE_MAX_SIZE
INFO: Copied 1 missing fields from template config
```

## Configuration Access

### Getting Config Values

```python
from tfm_config import get_config

config = get_config()
value = config.MY_OPTION
```

### Getting Specific Config Data

```python
from tfm_config import (
    get_favorite_directories,  # List of favorite dirs
    get_programs,              # External programs list
    get_file_associations,     # File type associations
    get_keys_for_action,       # Key bindings for action
    find_action_for_event      # Action for key event
)

# Get favorite directories
favorites = get_favorite_directories()

# Get key bindings for an action
keys, selection_req = get_keys_for_action('copy_files')
```

## User Configuration

### Location

User configuration is stored at: `~/.tfm/config.py`

### First Run

On first run, TFM automatically:
1. Creates `~/.tfm/` directory
2. Copies `src/_config.py` to `~/.tfm/config.py`
3. User can then edit `~/.tfm/config.py` to customize

### Customization

Users edit `~/.tfm/config.py` to customize:
- Key bindings
- Favorite directories
- External programs
- File associations
- Display settings
- Behavior settings

### Automatic Updates

When TFM adds new config options:
- Users don't need to update their config files
- New fields appear automatically with default values
- Old customizations are preserved

## Error Handling

### Missing Config File

If `~/.tfm/config.py` doesn't exist:
1. Copy `src/_config.py` as template
2. If copy fails, create empty config
3. Fill from template

### Corrupted Config File

If `~/.tfm/config.py` fails to load:
1. Log error message
2. Create empty config class
3. Fill all fields from template
4. User gets working config with defaults

### Missing Fields

If user config is missing fields:
1. Detect missing attributes
2. Copy from template
3. Log each field added
4. Return complete config

## Testing

### Manual Testing

```python
from tfm_config import config_manager

# Test normal loading
config = config_manager.get_config()
assert hasattr(config, 'PREFERRED_BACKEND')

# Test missing field handling
# (create minimal config, verify fields get added)
```

### Unit Tests

See `test/test_config_completeness.py` for comprehensive tests.

## Migration from Old System

### Before (Dual Class System)

Previously, TFM maintained two identical classes:
- `Config` in `src/_config.py` (user template)
- `DefaultConfig` in `src/tfm_config.py` (built-in defaults)

This required updating both classes for every new option.

### After (Single Source System)

Now, only `Config` in `src/_config.py` exists:
- Single source of truth for all defaults
- Automatic field copying eliminates duplication
- No maintenance overhead

### Breaking Changes

None. The new system is fully backward compatible:
- Existing user configs continue to work
- Missing fields get added automatically
- No user action required

## Implementation Details

### Why Not Inheritance?

We considered making user config inherit from template, but:
- Import dependencies in `_config.py` would cause circular imports
- Dynamic field copying is more flexible
- Allows template to use runtime detection (`is_desktop_mode()`)

### Why Not Build Script?

We considered generating defaults at build time, but:
- Adds complexity to development workflow
- Requires remembering to run generator
- Runtime copying is simpler and automatic

### Why This Approach?

Dynamic field copying provides:
- Single source of truth
- No circular dependencies
- Automatic updates for users
- Simple implementation
- Easy to understand and maintain

## References

- User configuration template: `src/_config.py`
- Configuration manager: `src/tfm_config.py`
- Configuration tests: `test/test_config_completeness.py`
- Implementation summary: `temp/CONFIG_CONSOLIDATION_COMPLETE.md`
