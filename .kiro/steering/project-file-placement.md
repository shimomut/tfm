---
inclusion: always
---

# TFM Project File Placement Rules

## Directory Structure

- `test/` - TFM test files (`test_*.py`)
- `ttk/test/` - TTK library test files (`test_*.py`)
- `ttk/demo/` - TTK library demo files (`demo_*.py`)
- `ttk/doc/` - TTK end-user documentation
- `ttk/doc/dev/` - TTK developer documentation
- `doc/` - TFM end-user documentation (`FEATURE_NAME_FEATURE.md`)
- `doc/dev/` - TFM developer documentation (`SYSTEM_NAME_SYSTEM.md`, `FEATURE_NAME_IMPLEMENTATION.md`)
- `demo/` - TFM demo scripts (`demo_*.py`)
- `tools/` - External programs and scripts (`*.sh`, `*.py`)
- `src/` - Core application code (`tfm_*.py`)
- `temp/` - Temporary files during development

## Documentation Policy

**Create separate documentation for end-users and developers** when features affect both audiences:
- User-facing features → Both `doc/` and `doc/dev/`
- Internal changes only → `doc/dev/` only

**Naming conventions:**
- End-user: `doc/FEATURE_NAME_FEATURE.md`
- Developer: `doc/dev/SYSTEM_NAME_SYSTEM.md`, `doc/dev/FEATURE_NAME_IMPLEMENTATION.md`

## Quick Reference

| File Type | Location | Naming |
|-----------|----------|--------|
| TFM tests | `test/` | `test_*.py` |
| TTK tests | `ttk/test/` | `test_*.py` |
| TFM demos | `demo/` | `demo_*.py` |
| TTK demos | `ttk/demo/` | `demo_*.py` |
| External tools | `tools/` | `*.sh`, `*.py` |
| Source code | `src/` | `tfm_*.py` |
| Temporary files | `temp/` | `temp_*`, `TEMP_*` |

## Key Rules

- **Temporary files** → Always use `temp/` directory during development
- **External programs** → Always use `tools/` directory
- **Separate TTK from TFM** → TTK library files go in `ttk/` subdirectories
- **Documentation audience** → End-user docs must not include implementation details; developer docs must not include basic usage instructions