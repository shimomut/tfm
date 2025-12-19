---
inclusion: always
---

# TFM Git Command Policy

## Overview

This document establishes standards for using git commands in the TFM project to ensure efficient and user-friendly command execution.

## Core Principle

**Always disable git pager when running git commands.** This prevents interactive pager sessions that require manual scrolling and quitting.

## Rules

### 1. Disable Pager for All Git Commands

Git uses a pager (like `less`) by default for commands with long output. This creates an interactive session that must be manually quit, which is inefficient for automated workflows.

#### ❌ Avoid - Default Git Commands (Uses Pager)
```bash
git diff                    # Opens pager, requires manual quit
git log                     # Opens pager, requires manual quit
git show                    # Opens pager, requires manual quit
git branch -a               # Opens pager if output is long
```

#### ✅ Preferred - Disable Pager
```bash
git --no-pager diff         # Shows all output immediately
git --no-pager log          # Shows all output immediately
git --no-pager show         # Shows all output immediately
git --no-pager branch -a    # Shows all output immediately
```

### 2. Alternative: Use GIT_PAGER Environment Variable

For multiple git commands, you can set the environment variable:

```bash
GIT_PAGER=cat git diff
GIT_PAGER=cat git log
```

### 3. Commands That Should Always Use --no-pager

The following git commands commonly trigger the pager and should always use `--no-pager`:

- `git diff` - Show changes
- `git log` - Show commit history
- `git show` - Show commit details
- `git branch` - List branches (when output is long)
- `git tag` - List tags (when output is long)
- `git blame` - Show file annotations
- `git grep` - Search repository

### 4. Commands That Don't Need --no-pager

Short-output commands that don't typically trigger the pager:

- `git status` - Usually short output
- `git status --short` - Always short output
- `git add` - No output
- `git commit` - No output (unless viewing message)
- `git push` - Progress output
- `git pull` - Progress output

## Rationale

### Why Disable Pager?

1. **Efficiency** - Get all output immediately without manual interaction
2. **Automation-friendly** - Works better in scripts and automated workflows
3. **Context preservation** - All output visible in terminal history
4. **No manual intervention** - No need to scroll and quit pager
5. **Consistent behavior** - Same behavior regardless of output length

### Benefits

- **Faster workflow** - No waiting for pager to load and quit
- **Better for AI assistants** - Can see all output at once
- **Easier debugging** - Full output visible in terminal
- **No interruptions** - Commands complete immediately

## Implementation

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

## Examples

### Checking Changes
```bash
# ❌ Bad - uses pager
git diff

# ✅ Good - no pager
git --no-pager diff

# ✅ Good - limit output if needed
git --no-pager diff | head -50
```

### Viewing History
```bash
# ❌ Bad - uses pager
git log

# ✅ Good - no pager
git --no-pager log

# ✅ Good - limit to recent commits
git --no-pager log -10
git --no-pager log --oneline -20
```

### Checking Status
```bash
# ✅ OK - status rarely triggers pager
git status

# ✅ Better - short format
git status --short
```

## Configuration (Optional)

To disable pager globally for your git configuration:

```bash
# Disable pager for all git commands
git config --global core.pager cat

# Or disable pager entirely
git config --global --replace-all core.pager ""
```

**Note**: This is a user preference and should not be enforced project-wide. Use `--no-pager` flag instead for consistency.

## Review Checklist

When reviewing code or commands:
- [ ] Are git commands using `--no-pager` flag?
- [ ] Are long outputs being limited with `head` or command options?
- [ ] Are commands that don't need `--no-pager` left without it?
- [ ] Is the output manageable and readable?

## Summary

- **Always use `--no-pager`** for git commands with potentially long output
- **Commands to always use it with**: `diff`, `log`, `show`, `branch`, `grep`, `blame`
- **Limit output** using `head` or command-specific options when needed
- **Don't use pager** - it requires manual interaction and slows down workflow
- **Standard practice**: `git --no-pager <command>` for all viewing commands
