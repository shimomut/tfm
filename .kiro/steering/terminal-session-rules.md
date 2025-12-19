---
inclusion: always
---

# TFM Terminal Session Rules

## Overview

This document establishes standards for terminal command execution in the TFM (TUI File Manager) project to ensure efficient workflows and consistent behavior.

---

## Python Virtual Environment Management

### Core Principle

**Check if the virtual environment is already active before activating it.** Avoid redundant activation in ongoing terminal sessions.

### How to Check if Virtual Environment is Active

The virtual environment is active if:
- The terminal prompt shows `(.venv)` prefix
- `VIRTUAL_ENV` environment variable is set
- `which python` points to `.venv/bin/python`

### For Kiro/AI Assistants

- **DO NOT activate venv if the terminal is already using it**
- Check the environment context or assume venv is active in ongoing sessions
- Only include activation in commands when starting a fresh terminal session or when explicitly needed
- **Run activation as a separate command**, not chained with `&&`
  - First command: `source .venv/bin/activate`
  - Second command: `python script.py`
  - This ensures the activation persists for subsequent commands in the session

### Activation Command

```bash
source .venv/bin/activate
```

### When to Activate

Activate the virtual environment:
- **Before running any Python scripts** in the project
- **Before running tests** (`pytest`, test scripts)
- **Before running demo scripts** in the `demo/` directory
- **Before running tools** that depend on project dependencies
- **At the start of any terminal session** where you'll be working with TFM code

### Verification

After activation, you should see:
- `(.venv)` prefix in your terminal prompt
- `which python` should point to `.venv/bin/python`

### Deactivation

To deactivate the virtual environment when done:
```bash
deactivate
```

### Common Mistakes to Avoid

#### ❌ Running Scripts Without Activation
```bash
# Bad - virtual environment not activated
python demo/demo_remote_log.py
# May fail with import errors
```

#### ✅ Correct Approach
```bash
# Good - activate first
source .venv/bin/activate
python demo/demo_remote_log.py
```

### Integration with Development Workflow

#### Starting a Development Session
```bash
cd /path/to/tfm
source .venv/bin/activate
# Now ready to run scripts, tests, etc.
```

#### Running Tests
```bash
source .venv/bin/activate
pytest test/
```

#### Running Demo Scripts
```bash
source .venv/bin/activate
python demo/demo_remote_log.py
```

### Troubleshooting

#### Virtual Environment Not Found
If `.venv` doesn't exist, create it:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Wrong Python Version
Ensure you're using the correct Python version when creating the virtual environment:
```bash
python3.9 -m venv .venv  # Use specific version if needed
```

---

## Git Command Standards

### Core Principle

**Always disable git pager when running git commands.** This prevents interactive pager sessions that require manual scrolling and quitting.

### Rules

#### 1. Disable Pager for All Git Commands

Git uses a pager (like `less`) by default for commands with long output. This creates an interactive session that must be manually quit, which is inefficient for automated workflows.

##### ❌ Avoid - Default Git Commands (Uses Pager)
```bash
git diff                    # Opens pager, requires manual quit
git log                     # Opens pager, requires manual quit
git show                    # Opens pager, requires manual quit
git branch -a               # Opens pager if output is long
```

##### ✅ Preferred - Disable Pager
```bash
git --no-pager diff         # Shows all output immediately
git --no-pager log          # Shows all output immediately
git --no-pager show         # Shows all output immediately
git --no-pager branch -a    # Shows all output immediately
```

#### 2. Commands That Should Always Use --no-pager

The following git commands commonly trigger the pager and should always use `--no-pager`:

- `git diff` - Show changes
- `git log` - Show commit history
- `git show` - Show commit details
- `git branch` - List branches (when output is long)
- `git tag` - List tags (when output is long)
- `git blame` - Show file annotations
- `git grep` - Search repository

#### 3. Commands That Don't Need --no-pager

Short-output commands that don't typically trigger the pager:

- `git status` - Usually short output
- `git status --short` - Always short output
- `git add` - No output
- `git commit` - No output (unless viewing message)
- `git push` - Progress output
- `git pull` - Progress output

### Rationale

#### Why Disable Pager?

1. **Efficiency** - Get all output immediately without manual interaction
2. **Automation-friendly** - Works better in scripts and automated workflows
3. **Context preservation** - All output visible in terminal history
4. **No manual intervention** - No need to scroll and quit pager
5. **Consistent behavior** - Same behavior regardless of output length

### Standard Git Commands

```bash
# ✅ Viewing changes
git --no-pager diff
git --no-pager diff --stat
git --no-pager diff HEAD~1

# ✅ Viewing history
git --no-pager log
git --no-pager log --oneline
git --no-pager log --graph --oneline

# ✅ Viewing commits
git --no-pager show
git --no-pager show HEAD
git --no-pager show <commit-hash>

# ✅ Listing branches
git --no-pager branch
git --no-pager branch -a
git --no-pager branch -r

# ✅ Searching
git --no-pager grep "pattern"
git --no-pager blame file.py
```

### Limiting Output When Needed

If output is too long, use command-specific options instead of pager:

```bash
# Limit diff output
git --no-pager diff | head -100
git --no-pager diff --stat

# Limit log output
git --no-pager log -10
git --no-pager log --oneline -20

# Limit branch output
git --no-pager branch | head -20
```

### Examples

#### Checking Changes
```bash
# ❌ Bad - uses pager
git diff

# ✅ Good - no pager
git --no-pager diff

# ✅ Good - limit output if needed
git --no-pager diff | head -50
```

#### Viewing History
```bash
# ❌ Bad - uses pager
git log

# ✅ Good - no pager
git --no-pager log

# ✅ Good - limit to recent commits
git --no-pager log -10
git --no-pager log --oneline -20
```

---

## Review Checklist

When providing terminal commands:

### Virtual Environment
- [ ] Is the virtual environment already active in the current session?
- [ ] If not active, is the activation command included?
- [ ] Are redundant activations avoided?
- [ ] Is the activation command appropriate for the platform (macOS/Linux)?

### Git Commands
- [ ] Are git commands using `--no-pager` flag?
- [ ] Are long outputs being limited with `head` or command options?
- [ ] Are commands that don't need `--no-pager` left without it?
- [ ] Is the output manageable and readable?

## Benefits

- **Dependency Isolation**: Virtual environment ensures project dependencies don't conflict with system packages
- **Consistent Environment**: All developers use the same package versions
- **Prevents Import Errors**: All required packages are available in the virtual environment
- **Faster Workflow**: No waiting for git pager to load and quit
- **Better for AI Assistants**: Can see all output at once
- **Easier Debugging**: Full output visible in terminal
- **No Interruptions**: Commands complete immediately
