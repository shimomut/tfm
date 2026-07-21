# External Programs System

## Overview

The External Programs system lets users run configured external programs from
within TFM with access to the current file-manager state through environment
variables. It also provides the interactive sub-shell feature. Both are
implemented in `src/tfm_external_programs.py` by the `ExternalProgramManager`
class.

This document covers the implementation. For the interactive shell in
particular, see [SUBSHELL_SYSTEM.md](SUBSHELL_SYSTEM.md); for the user-facing
description see [External Programs Feature](../EXTERNAL_PROGRAMS_FEATURE.md).

## Architecture

### `ExternalProgramManager`

```python
ExternalProgramManager(config, log_manager, renderer=None)
```

The class holds the config, the log manager, and the active renderer, and
exposes two entry points:

| Method | Purpose |
|---|---|
| `execute_external_program(pane_manager, program)` | Run one configured program with TFM environment variables set. |
| `enter_subshell_mode(pane_manager)` | Start an interactive shell (`$SHELL`) with the same environment. |

Both follow the same shape: set up the TFM environment, suspend the renderer,
run the child process, then restore the renderer and stdio in a `finally` block.

### Module-level helpers

- `tfm_tool(tool_name)` — resolve a tool script to an absolute path, searching
  `~/.tfm/tools/` (user tools, highest priority) then the `tools/` directory
  next to the module (bundled tools; `src/tools/` in a source checkout). Returns
  the original name if not found, so execution fails later with a clear error.
- `tfm_python` — path to the correct Python interpreter, accounting for the
  macOS app bundle where a bundled `python3` lives inside the `.app`.
- `quote_filenames_with_double_quotes(filenames)` — quote filenames with double
  quotes (escaping `"` and `\`) for safe use in the `TFM_*_SELECTED` variables.
- `get_selected_or_cursor_files(pane_data)` — the selected files, or the file
  under the cursor when nothing is selected.
- `ensure_common_paths_in_env(env)` — on macOS, prepend common binary paths
  (`/usr/local/bin`, `/opt/homebrew/bin`, …) to `PATH`, since an app launched
  from Finder/Dock does not inherit the user's shell `PATH`.

## Configuration

External programs are configured as a `PROGRAMS` list in the config
(`src/_config.py`, overridable in `~/.tfm/config.py`). Each entry:

- `name` — display name.
- `command` — command as a list of arguments (executed without a shell, so no
  shell injection).
- `options` (optional) — currently just `auto_return` (bool, default `False`):
  return to TFM immediately after the program exits instead of waiting for the
  user to press Enter.

```python
PROGRAMS = [
    {'name': 'Git Status', 'command': ['git', 'status']},
    {'name': 'Git Log', 'command': ['git', 'log', '--oneline', '-10']},
    {'name': 'Python REPL', 'command': ['python3']},
    {'name': 'My Tool', 'command': [tfm_python, tfm_tool('my_script.py')]},
    {'name': 'Quick Git Status', 'command': ['git', 'status', '--short'],
     'options': {'auto_return': True}},
]
```

## Environment variables

Before running a program (or the sub-shell), `ExternalProgramManager` copies the
current environment and adds:

- `TFM_ACTIVE` — set to `'1'` to indicate TFM launched the program.
- `TFM_LEFT_DIR` / `TFM_RIGHT_DIR` — left / right pane directory paths.
- `TFM_THIS_DIR` / `TFM_OTHER_DIR` — active / inactive pane directory paths.
- `TFM_LEFT_SELECTED` / `TFM_RIGHT_SELECTED` — space-separated, double-quoted
  selected filenames in the left / right panes.
- `TFM_THIS_SELECTED` / `TFM_OTHER_SELECTED` — same for the active / inactive
  panes.

If no files are selected in a pane, the file under the cursor is used instead.

The working directory is set to the active pane's directory, except when that
pane is browsing a remote path (e.g. S3), in which case it falls back to TFM's
own working directory.

## Execution flow

`execute_external_program` branches on `is_desktop_mode()`:

- **Terminal mode** — restore stdout/stderr so the child can use the terminal
  directly, suspend the renderer, and run with `subprocess.run(command, env=env)`
  so the program shares the terminal. On completion it prints the exit status
  and, unless `auto_return` is set, waits for the user to press Enter.
- **Desktop mode** — keep `LogCapture` active and run with
  `capture_output=True`; the program's stdout is echoed to the log pane at
  `info` level and stderr at `error` level. Desktop mode always returns
  immediately (no Enter prompt), even on error, since the user can read the log
  pane.

Errors (`FileNotFoundError`, other exceptions) are logged with a hint to use
`tfm_tool()` for TFM tools. In every case the `finally` block resumes the
renderer, re-initializes colors, and restores stdio capture.

## Comparison with sub-shell mode

| | External program | Sub-shell mode |
|---|---|---|
| Purpose | Run one specific program | Interactive shell session |
| Configuration | Pre-configured `PROGRAMS` list | Uses `$SHELL` |
| Environment | TFM variables set | TFM variables + `[TFM]` prompt hint |
| Interaction | Program runs and exits | Full shell session |
| Use case | Quick operations, scripts | Extended command-line work |

`enter_subshell_mode` additionally sets a `[TFM]` prefix on `PS1`/`PROMPT` and
logs snippets the user can add to their shell config to show the marker
themselves. See [SUBSHELL_SYSTEM.md](SUBSHELL_SYSTEM.md).

## Authoring external programs

Standards for scripts that integrate with TFM, folded in from the former
External Programs Policy.

### Use environment variables, not arguments

External programs **must** read TFM's environment variables rather than expect
command-line arguments. This keeps every program integrated with TFM's
selection and navigation state in the same way, and lets a program adapt to the
user's current context automatically.

Directory variables: `TFM_THIS_DIR`, `TFM_OTHER_DIR`, `TFM_LEFT_DIR`,
`TFM_RIGHT_DIR`. Selection variables (space-separated, double-quoted filenames):
`TFM_THIS_SELECTED`, `TFM_OTHER_SELECTED`, `TFM_LEFT_SELECTED`,
`TFM_RIGHT_SELECTED`. Status: `TFM_ACTIVE` (set to `"1"` under TFM).

### Script placement

Bundled end-user programs live in **`src/tools/`** and may be executable shell
scripts; user-specific tools go in `~/.tfm/tools/`. Reference them from a
`PROGRAMS` entry via `tfm_tool('script_name.sh')`, which resolves either
location to an absolute path. Follow a descriptive naming convention
(`descriptive_name.sh`).

### Script structure

```bash
#!/bin/bash
# script_name.sh - Brief description
# Uses TFM environment variables for integration.

# Validate the TFM environment.
if [ -z "$TFM_THIS_DIR" ]; then
    echo "Error: TFM environment variables not set"
    echo "This script should be run from within TFM"
    exit 1
fi

CURRENT_DIR="$TFM_THIS_DIR"

if [ -n "$TFM_THIS_SELECTED" ]; then
    # Parse selected files (properly handles quoted filenames).
    eval "SELECTED_FILES=($TFM_THIS_SELECTED)"
    for file in "${SELECTED_FILES[@]}"; do
        [ -n "$file" ] && process_file "$CURRENT_DIR/$file"
    done
else
    # No selection — operate on the current directory.
    process_directory "$CURRENT_DIR"
fi
```

Guidelines:

- Always validate that TFM variables are set; provide clear error messages and
  meaningful exit codes.
- Support both the "files selected" and "no selection" cases, and validate file
  existence before operating.
- Use `eval` to parse the quoted selection variables, and build absolute paths
  by joining `TFM_THIS_DIR` with each filename, so spaces and special
  characters are handled correctly.
- When launching a GUI application, `unset` the `TFM_*` variables first and set
  `options.auto_return = True` for a seamless return.

### Registering the program

Add it to the `PROGRAMS` list in `src/_config.py` (or the user's
`~/.tfm/config.py`). Platform-specific programs can be appended conditionally:

```python
import platform

if platform.system() == 'Darwin':
    PROGRAMS.append({'name': 'macOS Program',
                     'command': [tfm_tool('macos_program.sh')],
                     'options': {'auto_return': True}})
```

Use `auto_return: True` for GUI apps that return control immediately, and the
default (`False`) for CLI tools whose output you want to read before returning.

## Related documentation

- [External Programs Feature](../EXTERNAL_PROGRAMS_FEATURE.md) — user documentation
- [Subshell System](SUBSHELL_SYSTEM.md) — interactive sub-shell details
- [Configuration System](CONFIGURATION_SYSTEM.md) — configuration management
