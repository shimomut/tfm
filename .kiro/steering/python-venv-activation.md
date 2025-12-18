# Python Virtual Environment Activation Policy

## Overview

This document establishes the standard practice for activating the Python virtual environment when working with TFM (TUI File Manager) in terminal sessions.

## Core Principle

### Check Before Activating Virtual Environment

When working with TFM in a terminal session:
- **Check if the virtual environment is already active** before activating it
- Only activate if not already active (avoid redundant activation)
- This ensures all dependencies are available and the correct Python interpreter is used
- Prevents import errors and version conflicts

### How to Check if Virtual Environment is Active

The virtual environment is active if:
- The terminal prompt shows `(.venv)` prefix
- `VIRTUAL_ENV` environment variable is set
- `which python` points to `.venv/bin/python`

**For Kiro/AI assistants:**
- **DO NOT activate venv if the terminal is already using it**
- Check the environment context or assume venv is active in ongoing sessions
- Only include activation in commands when starting a fresh terminal session or when explicitly needed
- **Run activation as a separate command**, not chained with `&&`
  - First command: `source .venv/bin/activate`
  - Second command: `python script.py`
  - This ensures the activation persists for subsequent commands in the session

## Activation Command

```bash
source .venv/bin/activate
```

## When to Activate

Activate the virtual environment:
- **Before running any Python scripts** in the project
- **Before running tests** (`pytest`, test scripts)
- **Before running demo scripts** in the `demo/` directory
- **Before running tools** that depend on project dependencies
- **At the start of any terminal session** where you'll be working with TFM code

## Verification

After activation, you should see:
- `(.venv)` prefix in your terminal prompt
- `which python` should point to `.venv/bin/python`

## Deactivation

To deactivate the virtual environment when done:
```bash
deactivate
```

## Benefits

- **Dependency Isolation**: Ensures project dependencies don't conflict with system packages
- **Consistent Environment**: All developers use the same package versions
- **Prevents Import Errors**: All required packages are available in the virtual environment
- **Reproducible Builds**: Virtual environment ensures consistent behavior across machines

## Common Mistakes to Avoid

### ❌ Running Scripts Without Activation
```bash
# Bad - virtual environment not activated
python demo/demo_remote_log.py
# May fail with import errors
```

### ✅ Correct Approach
```bash
# Good - activate first
source .venv/bin/activate
python demo/demo_remote_log.py
```

## Integration with Development Workflow

### Starting a Development Session
```bash
cd /path/to/tfm
source .venv/bin/activate
# Now ready to run scripts, tests, etc.
```

### Running Tests
```bash
source .venv/bin/activate
pytest test/
```

### Running Demo Scripts
```bash
source .venv/bin/activate
python demo/demo_remote_log.py
```

## Automation

Consider adding activation to your shell profile or using tools like `direnv` to automatically activate the virtual environment when entering the project directory.

### Example with direnv
Create `.envrc` in project root:
```bash
source .venv/bin/activate
```

Then run `direnv allow` to enable automatic activation.

## Troubleshooting

### Virtual Environment Not Found
If `.venv` doesn't exist, create it:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Wrong Python Version
Ensure you're using the correct Python version when creating the virtual environment:
```bash
python3.9 -m venv .venv  # Use specific version if needed
```

## Review Checklist

When providing terminal commands:
- [ ] Is the virtual environment already active in the current session?
- [ ] If not active, is the activation command included?
- [ ] Are redundant activations avoided?
- [ ] Is the activation command appropriate for the platform (macOS/Linux)?

## Important Notes for AI Assistants

- **Avoid redundant activation**: If you've already activated the venv in the current conversation/session, don't activate it again
- **Assume active in ongoing sessions**: In most development workflows, the venv remains active throughout the session
- **Only activate when necessary**: Fresh terminal sessions, explicit user requests, or when there's clear evidence venv is not active
