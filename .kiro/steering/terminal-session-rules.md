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
