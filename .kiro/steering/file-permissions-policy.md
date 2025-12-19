---
inclusion: always
---

# TFM File Permissions Policy

## Overview

This document establishes the file permissions standards for the TFM (TUI File Manager) project to maintain consistency and proper execution practices.

## Core Principle

**Python files should NOT have executable permissions.** Always run Python scripts by explicitly invoking the Python interpreter.

## Rules

### 1. Python Files Should Not Be Executable

Python files (`.py`) should be run using the Python interpreter explicitly, not as executable scripts.

#### ❌ Avoid - Making Python Files Executable
```bash
chmod +x script.py
./script.py  # Bad - relies on shebang and executable permission
```

#### ✅ Preferred - Explicit Python Interpreter
```bash
python3 script.py  # Good - explicit interpreter
```

### 2. Shell Scripts Can Be Executable

Shell scripts (`.sh`) in the `tools/` directory can have executable permissions since they are designed to be run directly.

#### ✅ Acceptable - Executable Shell Scripts
```bash
chmod +x tools/script.sh
./tools/script.sh  # OK for shell scripts
```

### 3. Main Entry Point

The main entry point `tfm.py` should NOT have executable permissions. Users should run it with:

```bash
python3 tfm.py
```

## Rationale

### Why Not Make Python Files Executable?

1. **Explicit is better than implicit** - Clearly shows which Python version is being used
2. **Virtual environment compatibility** - Works correctly with activated virtual environments
3. **Cross-platform consistency** - Works the same on all platforms
4. **No shebang dependency** - Doesn't rely on shebang line being correct
5. **Standard Python practice** - Follows Python community conventions

### Benefits

- **Consistency**: All Python files are run the same way
- **Clarity**: Clear which interpreter is being used
- **Portability**: Works across different systems and environments
- **Maintainability**: No need to manage executable permissions

## Implementation

### When Creating New Python Files

1. Create the file without executable permissions (default)
2. Add appropriate shebang if needed for documentation: `#!/usr/bin/env python3`
3. Run using: `python3 filename.py`

### When You Find Executable Python Files

1. Remove executable permissions: `chmod -x filename.py`
2. Update any documentation to use explicit interpreter
3. Test that the file still works with explicit interpreter

### Checking for Executable Python Files

```bash
# Find all executable Python files
find . -name "*.py" -perm +111 -type f

# Remove executable permissions from all Python files
find . -name "*.py" -perm +111 -type f -exec chmod -x {} \;
```

## Exceptions

There are NO exceptions to this rule for Python files in the TFM project. All Python files should be run with an explicit interpreter.

## Examples

### Demo Scripts
```bash
# ❌ Bad
chmod +x demo/demo_script.py
./demo/demo_script.py

# ✅ Good
python3 demo/demo_script.py
```

### Test Scripts
```bash
# ❌ Bad
chmod +x test/test_feature.py
./test/test_feature.py

# ✅ Good
python3 test/test_feature.py
```

### Main Application
```bash
# ❌ Bad
chmod +x tfm.py
./tfm.py

# ✅ Good
python3 tfm.py
```

### Tools (Shell Scripts)
```bash
# ✅ OK for shell scripts
chmod +x tools/setup.sh
./tools/setup.sh
```

## Review Checklist

When reviewing code changes:
- [ ] Are any Python files being made executable with `chmod +x`?
- [ ] Are Python files being run with explicit interpreter (`python3`)?
- [ ] Are shell scripts in `tools/` directory (if executable)?
- [ ] Is documentation showing correct execution method?

## Migration

If you find executable Python files in the project:

1. **Remove permissions**: `chmod -x *.py`
2. **Update documentation**: Change `./script.py` to `python3 script.py`
3. **Update CI/CD**: Ensure build scripts use explicit interpreter
4. **Test**: Verify all scripts still work correctly

## Summary

- **Python files**: NO executable permissions, run with `python3 script.py`
- **Shell scripts**: CAN have executable permissions, run with `./script.sh`
- **Consistency**: Always use explicit interpreter for Python files
- **Standard practice**: Follows Python community conventions
