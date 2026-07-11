# TFM Project Structure

## Overview

TFM (Terminal File Manager) is organized so that the file-manager application,
its tests, and its documentation stay cleanly separated. Since the **PuiKit
port**, the rendering/UI toolkit is no longer vendored in this repo — TFM depends
on the external [PuiKit](https://github.com/crftwr/puikit) framework, and the old
in-repo `ttk` toolkit (plus the UI modules bound to it) is frozen under
`legacy/`.

## Directory Structure

```
tfm/
├── tfm.py                  # The application: FileManager + top-level UI (runs on PuiKit)
├── src/                    # TFM modules imported by tfm.py (tfm_*.py)
├── test/                   # Unit / integration tests (test_*.py), run with pytest
├── doc/                    # End-user docs (*_FEATURE.md, guides)
│   └── dev/                # Developer docs (*_IMPLEMENTATION.md, *_SYSTEM.md, plans)
│       └── _archived/      # Retired pre-PuiKit toolkit-internal docs (reference only)
├── tools/                  # Internal dev/build utilities (*.py, *.sh)
├── macos_app/              # macOS .app packaging (see MACOS_APP_BUILD_SYSTEM.md)
├── windows_app/            # Windows packaging (see WINDOWS_APP_BUILD_SYSTEM.md)
├── legacy/                 # Frozen pre-PuiKit code (old ttk toolkit + ttk-bound UI). Not executed.
├── temp/                   # Throwaway work-in-progress files
├── _archived/              # Retired Kiro specs
├── .kiro/                  # Historical Kiro design specs (reference, not authoritative)
├── setup.py                # Package setup for pip installation
├── Makefile                # Build automation (run, test, venv, install-puikit, macos-app, ...)
├── requirements.txt        # Python dependencies
└── README.md               # Project overview and user guide
```

PuiKit itself lives in its **own repository** (`../puikit`) and is installed
editable into `.venv/` via `make install-puikit` (`PUIKIT_DIR ?= ../puikit`). It
is not part of this tree.

## Application (`tfm.py` + `src/`)

The application entry point and the top-level UI (the `FileManager` shell, the
dual `FilePane` layout, menus, and the main loop) live in **`tfm.py`** at the
repo root. It imports PuiKit (`from puikit import ...`) and the `tfm_*` modules
in `src/`. The `src/` modules, grouped by concern:

### Configuration & appearance
- **`tfm_config.py`** — configuration system and user settings
- **`tfm_const.py`** — application constants and key definitions
- **`_config.py`** — default user-config template (copied to `~/.tfm/config.py`)
- **`tfm_colors.py`** — color schemes and theme colors

### Path & storage system
- **`tfm_path.py`** — extended `Path` supporting local, S3, and SSH/SFTP paths
- **`tfm_s3.py`** — AWS S3 integration with pathlib compatibility
- **`tfm_ssh.py`**, **`tfm_ssh_connection.py`**, **`tfm_ssh_config.py`**, **`tfm_ssh_cache.py`** — SSH/SFTP backend and connection/config caching
- **`tfm_archive.py`** — archive creation/extraction and archive virtual directories

### Panes & file listing
- **`tfm_file_pane.py`** — a single file pane widget (PuiKit `Widget`)
- **`tfm_pane_manager.py`** — dual-pane management and navigation
- **`tfm_file_list_manager.py`** — directory listing, sorting, filtering

### File operations, tasks & progress
- **`tfm_file_operations.py`** — copy / move / delete / rename operations
- **`tfm_task.py`** — central `Task` / `TaskManager` and worker for threaded operations
- **`tfm_progress_manager.py`** — progress tracking for long operations
- **`tfm_progress_animator.py`** — configurable progress animation

### File monitoring
- **`tfm_file_monitor_manager.py`**, **`tfm_file_monitor_observer.py`** — watchdog-based auto-reload of directory listings

### Dialogs & bars
- **`tfm_input_dialog.py`** — single-line input (rename / mkdir / create)
- **`tfm_text_dialog.py`** — scrollable text / message dialogs
- **`tfm_filter_list_dialog.py`** — searchable list picker (favorites / drives / programs / jump)
- **`tfm_batch_rename_dialog.py`** — batch rename with regex
- **`tfm_progressive_search_dialog.py`** — filename / content search dialog
- **`tfm_isearch_bar.py`** — incremental-search bar
- **`tfm_compare_dialog.py`**, **`tfm_compare_selection.py`** — compare-and-select
- **`tfm_dialog_geometry.py`** — shared dialog sizing/anchoring helpers

### Viewers
- **`tfm_text_viewer.py`** — text viewer with pygments highlighting and isearch
- **`tfm_diff_viewer.py`** — file diff viewer
- **`tfm_directory_diff_viewer.py`** — directory diff viewer
- **`tfm_text_layout.py`** — text measurement / wrapping / layout helpers

### Logging
- **`tfm_log_manager.py`** — unified logger (`getLogger`) with remote monitoring
- **`tfm_logging_handlers.py`** — logging handlers (in-app log pane, remote)

### Backend, state & misc
- **`tfm_backend_detector.py`** — selects the PuiKit backend (terminal vs. native)
- **`tfm_state_manager.py`** — application state persistence and restoration
- **`tfm_str_format.py`** — string / size / date formatting helpers
- **`src/tools/`** — end-user-facing external programs (preview, diff wrappers, ...)

## Tests (`test/`)

Unit and integration tests, discovered by pytest as `test_*.py`. Run them with
`src` (and the repo root, for the few tests that `import tfm`) on the path;
PuiKit is resolved through its editable install:

```bash
PYTHONPATH=.:src pytest test/                       # all
PYTHONPATH=.:src pytest test/test_tfm_path.py -v    # one file
```

`make test` runs the suite; `make test-quick` runs a fast subset. Interactive
demos are **not** here — the old TFM demos are retired under `legacy/demo/`, and
PuiKit ships its own demos in `../puikit/demo/`. Neither should be launched
non-interactively (they block).

## Documentation (`doc/`)

- **`doc/*_FEATURE.md`** — end-user feature docs (usage, behavior)
- **`doc/dev/*_IMPLEMENTATION.md`, `*_SYSTEM.md`** — developer docs (design, internals)
- **`doc/dev/PUIKIT_PORTING_PLAN.md`** — living record of the ttk→PuiKit port and remaining tasks
- **`doc/dev/PROJECT_HISTORY.md`** — project timeline
- **`doc/dev/_archived/`** — pre-PuiKit toolkit-internal docs (renderer / backend / event-system internals that now live in the PuiKit repo), kept for reference only

## Entry Points

- **`python tfm.py`** / **`make run`** — launch the file manager
- **`tfm`** console script — created on `pip install` (see `setup.py`)

## Build System (Makefile targets)

- `make venv` / `make install-puikit` — create the venv and install PuiKit editable from `../puikit`
- `make run` / `make run-gui` — run TFM (terminal / native)
- `make test` / `make test-quick` — run tests
- `make macos-app` / `make windows-app` — build platform packages
- `make clean` — clean temporary artifacts

## Dependencies

### Runtime
- Python 3.9+ (3.13 supported)
- **PuiKit** (external, editable from `../puikit`)
- `pygments` (syntax highlighting), `boto3` (S3), `watchdog` (file monitoring)
- Platform extras via environment markers: `pyobjc` (macOS native backend), `windows-curses` (Windows)

### Development
- `pytest` (tests), plus optional `flake8` / `black`

## Configuration

- User config at `~/.tfm/config.py`, created from `src/_config.py`
- Defaults / constants / colors in `src/tfm_config.py`, `src/tfm_const.py`, `src/tfm_colors.py`

## The `legacy/` boundary

A module moved to `legacy/` iff it transitively imported the old `ttk` toolkit;
everything `ttk`-free stayed in `src/`. `legacy/` is frozen and **not executed**
— its imports point at `src/` paths it no longer sits on. Consult it for old
behavior, not to run it. See `legacy/README.md`.
