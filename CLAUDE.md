# TFM — Claude Code Instructions

TFM is a TUI file manager. The application lives at the repo root (`tfm.py`) plus the `tfm_*` modules in `src/`, with tests in `test/` and docs in `doc/`. Its rendering/UI layer runs on **[PuiKit](https://github.com/crftwr/puikit)** — an external, capability-based framework that runs the same widget code on curses, macOS, and Windows backends. PuiKit is **not vendored** here; it is installed editable from `../puikit` (see `make install-puikit`).

The pre-PuiKit code — the old in-repo **`ttk`** toolkit and the UI modules bound to it — has been removed; consult git history if you ever need it. Don't reintroduce it or import from it.

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

Always set `PYTHONPATH=.:src` when running Python scripts or tests — the repo root holds `tfm.py`, `src/` holds the `tfm_*` modules, and PuiKit is resolved through its editable install in `.venv/`. (There is no longer a `ttk` entry on the path — the in-repo toolkit was removed in the PuiKit port.)

```bash
PYTHONPATH=.:src python script.py
PYTHONPATH=.:src pytest test/test_file.py -v
```

### Git pager

Use `--no-pager` for any git command that may page output: `diff`, `log`, `show`, `branch`, `tag`, `blame`, `grep`. `status`/`add`/`commit`/`push`/`pull` don't need it.

### Don't run TUIs

- **Never execute `tfm.py`** — it launches the interactive file manager (curses / native PuiKit backend) and blocks indefinitely. Read the source instead.
- Anything importing `curses`, PuiKit backends, or `tfm_*` UI components is blocking. PuiKit demos (`../puikit/demo/*.py`) block too.
- `test/test_*.py` are safe — run them with `pytest`, not `python` directly.
- If the user explicitly wants to see the app or a demo, tell them to run it manually rather than starting it yourself.
- Last-resort timeout wrapper: `python3 tools/timeout.py 5 python <script>`.

---

## Project file placement

| File type | Location | Naming |
|-----------|----------|--------|
| TFM app entry | repo root | `tfm.py` |
| TFM source | `src/` | `tfm_*.py` |
| TFM tests | `test/` | `test_*.py` |
| Dev tools (internal) | `tools/` | `*.sh`, `*.py` |
| End-user external programs | `src/tools/` | `*.sh`, `*.py` |
| TFM end-user docs | `doc/` | `FEATURE_NAME_FEATURE.md` |
| TFM developer docs | `doc/dev/` | `SYSTEM_NAME_SYSTEM.md`, `FEATURE_NAME_IMPLEMENTATION.md` |
| Temporary files | `temp/` | `temp_*`, `TEMP_*` |

- `tools/` is for internal/dev utilities. `src/tools/` is for end-user-facing external programs (different audience).
- PuiKit is a separate project (`../puikit`, its own repo). Don't add UI-toolkit / backend / renderer code to TFM — that belongs in PuiKit.
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

- Logging system: `doc/dev/LOGGING_SYSTEM.md`
- Logging feature: `doc/LOGGING_FEATURE.md`
- Log manager: `src/tfm_log_manager.py`
