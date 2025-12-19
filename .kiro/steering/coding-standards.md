---
inclusion: always
---

# TFM Python Coding Standards

## Import Best Practices

**Before adding any import statement**, check if the module is already imported at the module level to avoid redundant imports.

## Exception Handling Standards

- **Catch specific exception types** when possible rather than bare `except:` clauses
- When catching all exceptions is necessary, use `except Exception as e:` and **always log or print a warning/error message** with context
- TFM-specific: When `LogManager` is available, prefer logging over print statements

## File Permissions Standards

**Python files should NOT have executable permissions.** Always run Python scripts by explicitly invoking the Python interpreter:

```bash
# ✅ Correct
python3 script.py

# ❌ Avoid
chmod +x script.py
./script.py
```

Shell scripts in `tools/` directory can have executable permissions.
