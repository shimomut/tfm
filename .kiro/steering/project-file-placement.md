---
inclusion: always
---

# TFM Project File Placement Rules

## Directory Structure

- `tfm.py` - The application entry point (FileManager + top-level UI), at the repo root
- `src/` - TFM modules imported by `tfm.py` (`tfm_*.py`)
- `test/` - TFM test files (`test_*.py`)
- `doc/` - TFM end-user documentation (`FEATURE_NAME_FEATURE.md`)
- `doc/dev/` - TFM developer documentation (`SYSTEM_NAME_SYSTEM.md`, `FEATURE_NAME_IMPLEMENTATION.md`)
- `doc/dev/_archived/` - Retired pre-PuiKit toolkit-internal docs (reference only)
- `tools/` - Development tools and scripts for Kiro/developers (`*.sh`, `*.py`)
- `src/tools/` - External programs for end users (`*.sh`, `*.py`)
- `legacy/` - Frozen pre-PuiKit code (old `ttk` toolkit + ttk-bound UI); not executed
- `temp/` - Temporary files during development

> **PuiKit** (the UI framework) is **not** in this repo — it lives in `../puikit`
> and is installed editable. There is no longer a `ttk/` directory.

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
| App entry | repo root | `tfm.py` |
| Source code | `src/` | `tfm_*.py` |
| TFM tests | `test/` | `test_*.py` |
| Development tools | `tools/` | `*.sh`, `*.py` |
| End-user external programs | `src/tools/` | `*.sh`, `*.py` |
| Retired pre-PuiKit code | `legacy/` | frozen, not executed |
| Temporary files | `temp/` | `temp_*`, `TEMP_*` |

## Key Rules

- **Temporary files** → Always use `temp/` directory during development
- **Development tools** → Use `tools/` for Kiro/developer utilities (not for end users)
- **End-user external programs** → Use `src/tools/` for user-facing external integrations
- **PuiKit is separate from TFM** → UI-framework/backend/renderer code belongs in the PuiKit repo (`../puikit`), not in this tree
- **Documentation audience** → End-user docs must not include implementation details; developer docs must not include basic usage instructions