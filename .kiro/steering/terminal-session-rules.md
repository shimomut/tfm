---
inclusion: always
---

# TFM Terminal Session Rules

## Python Virtual Environment Management

**For Kiro/AI Assistants:**
- **DO NOT activate venv if the terminal is already using it** - check environment context or assume venv is active in ongoing sessions
- Only include activation when starting a fresh terminal session or when explicitly needed
- **Run activation as a separate command**, not chained with `&&`:
  ```bash
  source .venv/bin/activate
  python script.py
  ```

Activate the virtual environment before running any Python scripts, tests, or demo scripts in the project.

## Python Path Configuration

**When running Python scripts or tests**, always set PYTHONPATH to include the necessary directories:

```bash
# ✅ CORRECT - Include current directory, src, and ttk
PYTHONPATH=.:src:ttk python script.py
PYTHONPATH=.:src:ttk pytest test/test_file.py -v

# ❌ AVOID - Missing PYTHONPATH can cause import errors
python script.py
pytest test/test_file.py -v
```

**Why this is needed:**
- TFM source code is in `src/` directory
- TTK library is in `ttk/` directory
- Tests and scripts need to import from both locations
- Setting PYTHONPATH ensures imports work correctly

## Git Command Standards

**Always disable git pager when running git commands** to prevent interactive pager sessions:

```bash
# ✅ Correct
git --no-pager diff
git --no-pager log
git --no-pager show
git --no-pager branch -a

# ❌ Avoid (opens pager)
git diff
git log
```

Commands that should always use `--no-pager`: `diff`, `log`, `show`, `branch`, `tag`, `blame`, `grep`

Commands that don't need it: `status`, `add`, `commit`, `push`, `pull`

## Interactive Program Execution Rules

**NEVER run GUI/TUI applications directly in automated sessions** - they block execution and wait for user input indefinitely.

### Demo and Test Script Guidelines

**Demo scripts (`demo/*.py`):**
- ❌ **DO NOT execute** - These launch interactive TUI applications that require user input
- ✅ **Only inspect code** to verify implementation
- If user explicitly requests running a demo, warn them it will block and suggest they run it manually

**Test scripts (`test/test_*.py`, `ttk/test/test_*.py`):**
- ✅ **Safe to run** - Use pytest which exits automatically
- Always run with pytest: `pytest test/test_file.py -v`
- Never run test files directly with `python test_file.py`

### Identifying Blocking Programs

Programs that will block execution:
- Any file in `demo/` directory (TUI applications)
- Scripts that import `curses`, `ttk.TtkApplication`, or `tfm_*` UI components
- Scripts with event loops or `while True` without timeout
- Scripts that call `.run()`, `.mainloop()`, or similar blocking methods

### Safe Alternatives

Instead of running interactive programs:
1. **Read the source code** to understand implementation
2. **Run unit tests** to verify functionality: `pytest test/test_*.py -v`
3. **Use timeout utility** as last resort: `python3 tools/timeout.py 5 python demo/script.py`
4. **Suggest manual execution** if user wants to see the program in action

### Example Patterns

```bash
# ❌ WRONG - Will block indefinitely
python demo/demo_file_manager.py

# ✅ CORRECT - Inspect code instead
cat demo/demo_file_manager.py

# ✅ CORRECT - Run tests
pytest test/test_file_manager.py -v

# ⚠️ USE WITH CAUTION - Timeout as last resort (kills after 5 seconds)
python3 tools/timeout.py 5 python demo/demo_file_manager.py
```

### Recovery from Stuck Processes

**If Kiro gets stuck on a blocking process:**

1. **User must intervene** - Kiro cannot forcibly cancel stuck foreground processes
2. **Cancel the agent execution** in the Kiro UI
3. **Kill the process manually** if needed: `ps aux | grep python` then `kill <PID>`
4. **Prevention is key** - Follow the rules above to avoid blocking in the first place

**For Kiro/AI Assistants:**
- If you realize you've started a blocking process, immediately acknowledge the error
- Explain to the user that they need to cancel the execution
- Learn from the mistake and avoid similar patterns in future interactions
