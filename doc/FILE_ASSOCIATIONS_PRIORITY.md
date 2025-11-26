# File Associations Priority Matching

## Overview

FILE_ASSOCIATIONS entries are checked in order from top to bottom. This allows you to define specific rules before general rules, giving you fine-grained control over file handling.

## How It Works

When TFM needs to find a program for a file and action:

1. **Check each entry** in FILE_ASSOCIATIONS from top to bottom
2. **For each entry**:
   - Check if the filename matches the pattern
   - If pattern matches, check if the action exists in that entry
   - If action exists, use that command (even if None)
   - If action doesn't exist, continue to next entry
3. **Stop at first match** where both pattern and action are found

## Key Principle

**First matching entry wins** - but only if the action is present in that entry.

## Examples

### Example 1: Specific Before General

```python
FILE_ASSOCIATIONS = [
    # Specific: Test files
    {
        'pattern': 'test_*.py',
        'open': ['pytest', '-v'],
        'edit': ['vim']
    },
    # General: All Python files
    {
        'pattern': '*.py',
        'open': ['python3'],
        'view': ['less'],
        'edit': ['vim']
    }
]
```

**Behavior**:
- `test_main.py` + open → `pytest -v` (matches first entry)
- `test_main.py` + view → `less` (first entry has no 'view', uses second entry)
- `script.py` + open → `python3` (doesn't match first pattern, uses second entry)

### Example 2: Split Actions Across Entries

```python
FILE_ASSOCIATIONS = [
    # Entry 1: Only open and edit
    {
        'pattern': '*.txt',
        'open': ['open', '-e'],
        'edit': ['vim']
        # 'view' not specified
    },
    # Entry 2: Only view (fallback)
    {
        'pattern': '*.txt',
        'view': ['less']
    }
]
```

**Behavior**:
- `readme.txt` + open → `open -e` (matches first entry)
- `readme.txt` + edit → `vim` (matches first entry)
- `readme.txt` + view → `less` (first entry has no 'view', uses second entry)

### Example 3: README Files

```python
FILE_ASSOCIATIONS = [
    # Specific: README files with special viewer
    {
        'pattern': 'README*',
        'view': ['glow']  # Markdown renderer
    },
    # General: All markdown files
    {
        'pattern': '*.md',
        'open': ['typora'],
        'view': ['less'],
        'edit': ['vim']
    }
]
```

**Behavior**:
- `README.md` + view → `glow` (matches first entry)
- `README.md` + open → `typora` (first entry has no 'open', uses second entry)
- `notes.md` + view → `less` (doesn't match first pattern, uses second entry)

### Example 4: Configuration Files

```python
FILE_ASSOCIATIONS = [
    # Specific: Main config file
    {
        'pattern': 'config.py',
        'open': ['vim'],
        'view': ['cat']
    },
    # Specific: Test config files
    {
        'pattern': 'test_config.py',
        'open': ['vim'],
        'edit': ['vim']
    },
    # General: All Python files
    {
        'pattern': '*.py',
        'open': ['python3'],
        'view': ['less'],
        'edit': ['vim']
    }
]
```

**Behavior**:
- `config.py` + open → `vim` (matches first entry)
- `test_config.py` + open → `vim` (matches second entry)
- `utils.py` + open → `python3` (doesn't match first two, uses third entry)

## Use Cases

### 1. Special Handling for Specific Files

Put specific file patterns before general patterns:

```python
[
    {'pattern': 'Makefile', 'edit': ['vim']},
    {'pattern': '*', 'edit': ['nano']}  # Default for everything else
]
```

### 2. Different Programs for Different File Types

```python
[
    {'pattern': 'test_*.py', 'open': ['pytest']},
    {'pattern': '*.py', 'open': ['python3']}
]
```

### 3. Partial Action Definitions

Define some actions in one entry, others in another:

```python
[
    {'pattern': '*.log', 'view': ['tail', '-f']},  # Live view
    {'pattern': '*.log', 'edit': ['vim']}          # Edit separately
]
```

### 4. Override for Specific Directories

Use more specific patterns first:

```python
[
    {'pattern': 'docs/*.md', 'view': ['glow']},
    {'pattern': '*.md', 'view': ['less']}
]
```

## Best Practices

### 1. Specific Patterns First

Always put more specific patterns before general ones:

```python
# ✓ Good
[
    {'pattern': 'test_*.py', ...},
    {'pattern': '*.py', ...}
]

# ✗ Bad - general pattern will match first
[
    {'pattern': '*.py', ...},
    {'pattern': 'test_*.py', ...}  # Never reached!
]
```

### 2. Complete Entries vs Split Entries

**Complete entries** (all actions in one place):
```python
{
    'pattern': '*.py',
    'open': ['python3'],
    'view': ['less'],
    'edit': ['vim']
}
```

**Split entries** (actions in different places):
```python
{
    'pattern': '*.txt',
    'open': ['open', '-e'],
    'edit': ['vim']
},
{
    'pattern': '*.txt',
    'view': ['less']
}
```

Both are valid - use split entries when you want different fallback behavior.

### 3. Document Your Intent

Add comments to explain why entries are ordered:

```python
FILE_ASSOCIATIONS = [
    # Specific: Test files need pytest
    {'pattern': 'test_*.py', 'open': ['pytest']},
    
    # General: Regular Python files
    {'pattern': '*.py', 'open': ['python3']},
]
```

## Common Patterns

### Pattern 1: Specific File, General Extension

```python
[
    {'pattern': 'README.md', 'view': ['glow']},
    {'pattern': '*.md', 'view': ['less']}
]
```

### Pattern 2: Test Files

```python
[
    {'pattern': 'test_*.py', 'open': ['pytest']},
    {'pattern': '*_test.py', 'open': ['pytest']},
    {'pattern': '*.py', 'open': ['python3']}
]
```

### Pattern 3: Configuration Hierarchy

```python
[
    {'pattern': '.env', 'edit': ['vim']},
    {'pattern': '*.env', 'edit': ['vim']},
    {'pattern': 'config.*', 'edit': ['vim']},
    {'pattern': '*', 'edit': ['nano']}
]
```

## Debugging Tips

### Check Which Entry Matches

If you're unsure which entry is being used:

1. Add a unique command to each entry
2. See which command is returned
3. Adjust order as needed

### Test Your Configuration

Use the test script to verify behavior:

```bash
python3 test/test_priority_matching.py
```

### Common Issues

**Issue**: General pattern matches before specific one
**Solution**: Move specific pattern above general pattern

**Issue**: Action not found in first matching entry
**Solution**: Either add the action to that entry, or ensure it's in a later entry

## Related Documentation

- File Associations: `doc/FILE_ASSOCIATIONS_FEATURE.md`
- Compact Format: `doc/FILE_ASSOCIATIONS_COMPACT_FORMAT.md`
- Usage Guide: `doc/FILE_ASSOCIATIONS_USAGE.md`
