# TFM — Claude Code Instructions

TFM is a TUI file manager. The codebase is split between the TFM application (`src/`, `test/`, `demo/`, `doc/`) and the TTK library it ships with (`ttk/`).

Historical Kiro design docs live in `.kiro/specs/<feature>/` — useful as reference for existing features, but not authoritative for current state. Source of truth is the code.

---

## Terminal session rules

### Virtual environment

- A venv lives at `.venv/`. Assume it is active in ongoing sessions; only activate when starting fresh.
- If you do activate, run it as a separate command (not chained with `&&`):
  ```bash
  source .venv/bin/activate
  python script.py
  ```

### PYTHONPATH

Always set `PYTHONPATH=.:src:ttk` when running Python scripts or tests — TFM imports from `src/` and TTK from `ttk/`.

```bash
PYTHONPATH=.:src:ttk python script.py
PYTHONPATH=.:src:ttk pytest test/test_file.py -v
```

### Git pager

Use `--no-pager` for any git command that may page output: `diff`, `log`, `show`, `branch`, `tag`, `blame`, `grep`. `status`/`add`/`commit`/`push`/`pull` don't need it.

### Don't run TUIs

- **Never execute `demo/*.py`** — they launch interactive curses/TTK apps and block indefinitely. Read the source instead.
- Anything importing `curses`, `ttk.TtkApplication`, or `tfm_*` UI components is blocking.
- `test/test_*.py` and `ttk/test/test_*.py` are safe — run them with `pytest`, not `python` directly.
- If the user explicitly wants to see a demo, tell them to run it manually rather than starting it yourself.
- Last-resort timeout wrapper: `python3 tools/timeout.py 5 python demo/script.py`.

---

## Project file placement

| File type | Location | Naming |
|-----------|----------|--------|
| TFM source | `src/` | `tfm_*.py` |
| TFM tests | `test/` | `test_*.py` |
| TFM demos | `demo/` | `demo_*.py` |
| TTK source | `ttk/` | |
| TTK tests | `ttk/test/` | `test_*.py` |
| TTK demos | `ttk/demo/` | `demo_*.py` |
| Dev tools (internal) | `tools/` | `*.sh`, `*.py` |
| End-user external programs | `src/tools/` | `*.sh`, `*.py` |
| TFM end-user docs | `doc/` | `FEATURE_NAME_FEATURE.md` |
| TFM developer docs | `doc/dev/` | `SYSTEM_NAME_SYSTEM.md`, `FEATURE_NAME_IMPLEMENTATION.md` |
| TTK end-user docs | `ttk/doc/` | |
| TTK developer docs | `ttk/doc/dev/` | |
| Temporary files | `temp/` | `temp_*`, `TEMP_*` |

- `tools/` is for internal/dev utilities. `src/tools/` is for end-user-facing external programs (different audience).
- Keep TTK files under `ttk/` — don't mix them with TFM.
- Use `temp/` for any throwaway file produced during development.

### Documentation policy

- User-facing features → write **both** `doc/<NAME>_FEATURE.md` and `doc/dev/<NAME>_IMPLEMENTATION.md`.
- Internal-only changes → `doc/dev/` only.
- Don't put implementation details in end-user docs; don't put basic usage in developer docs.
- Only create docs when the user asks or the change clearly warrants it — don't generate docs for every edit.

---

## Coding standards

### Logging

**All TFM source files MUST use the unified logger.** `print()` is prohibited in production code under `src/`.

```python
from tfm_log_manager import getLogger

# Class-based:
class MyComponent:
    def __init__(self):
        self.logger = getLogger("ComponentName")
    def foo(self):
        self.logger.info("...")

# Module-level:
logger = getLogger("ModuleName")
```

Logger names: PascalCase, descriptive, ≤15 chars (e.g. `Main`, `FileOp`, `Archive`, `Cache`, `UILayer`, `ExtProg`).

Levels:
- `error` — failures, exceptions, data loss
- `warning` — degraded behavior the user should know about
- `info` — normal operation, user actions (most common)
- `debug` — rarely used

Don't gate calls on `if self.logger:` — the logger is always present.

When migrating `print()` → logger, **preserve the exact message string**.

### Exceptions

- Prefer specific exception types over bare `except:`.
- When catching `Exception`, always log with context via `self.logger.error(...)`.

```python
try:
    risky()
except FileNotFoundError as e:
    self.logger.error(f"File not found: {e}")
except Exception as e:
    self.logger.error(f"Unexpected error: {e}")
```

### Imports

Before adding an import, check whether the module is already imported at the top of the file.

### File permissions

Python files should NOT be executable. Run them via `python3 script.py`, not `./script.py`. Shell scripts in `src/tools/` (end-user external programs) may be executable.

---

## References

- Logging migration guide: `doc/dev/LOGGING_MIGRATION_GUIDE.md`
- Logging feature: `doc/LOGGING_FEATURE.md`
- Log manager: `src/tfm_log_manager.py`
