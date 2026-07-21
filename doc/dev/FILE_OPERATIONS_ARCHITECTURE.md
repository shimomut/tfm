# File Operations Architecture

## Overview

Copy, move, duplicate, and delete are provided by a single class, `FileOperationService` (`tfm_file_operations.py`). It confirms the operation on the main thread, then runs the actual work as a background **task** (see [Task Framework](TASK_FRAMEWORK_IMPLEMENTATION.md)) whose body is one **linear** function — prepare → resolve conflicts → count → execute, top to bottom. There is no state machine and no separate UI / executor / list-manager split; the earlier four-layer design was removed in the PuiKit port.

The same service instance serves any view. `TfmApp` owns one (`self._fileops = FileOperationService(config, self.tasks)`); a full-window modal such as the directory-diff viewer can construct its own and pass a higher `z` so its dialogs stack above itself.

## Copy operation — end to end

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant App as TfmApp
    participant Svc as FileOperationService
    participant Mgr as TaskManager + ProgressDialog
    participant W as worker thread — _run()

    U->>App: press C (copy)
    App->>Svc: copy(panel, targets, dest_dir, on_complete)
    Svc->>U: CONFIRM_COPY message box (if enabled)
    U-->>Svc: confirm
    Svc->>Mgr: submit(task, run=_run)
    Mgr->>U: show ProgressDialog (modal)
    Mgr->>W: spawn worker
    W->>W: _resolve() — build plan of survivors
    loop each colliding destination
        W->>U: ask() → ConflictDialog (via pump)
        U-->>W: Overwrite / Skip / Keep both / Cancel
    end
    W->>W: _count() → set progress total
    loop each planned target
        W->>W: checkpoint(); _execute_one(); update progress
    end
    W-->>Mgr: result {done, skipped, failed, items, errors, cancelled}
    Mgr->>U: close dialog
    Mgr->>App: on_complete(result) → summary in the log
```

## Public API

```python
FileOperationService(config, tasks: TaskManager | None = None)
```

Each entry point takes the `panel` to draw on plus keyword options (`on_complete`, `log`, `z`, `background`):

| Method | Destination | Confirm flag | Conflict handling |
|---|---|---|---|
| `copy(panel, targets, dest_dir, …)` | `dest_dir/name` | `CONFIRM_COPY` | per-file prompt |
| `move(panel, targets, dest_dir, …)` | `dest_dir/name` | `CONFIRM_MOVE` | per-file prompt |
| `duplicate(panel, targets, dest_dir, …)` | in place (source's own dir) | `CONFIRM_DUPLICATE` | none — always auto-renamed `name (N)` |
| `delete(panel, targets, …)` | — | `CONFIRM_DELETE` (default button = Cancel) | — |

`_start` shows the relevant `CONFIRM_*` message box (skipped when its config flag is off); on confirm, `_submit` builds a `Task` and hands it to `TaskManager.submit(run=self._run, …)`.

## The linear worker (`_run`)

Runs on the task thread, top to bottom:

1. **Plan.** Build a list of `(target, dest_base, overwrite)`:
   - **delete** — trivial (one entry per target).
   - **duplicate** — pre-plan a fresh ` (N)` name per target (an in-place copy always collides, so it never prompts).
   - **copy / move** — `_resolve` checks each destination for an existing file and prompts only for collisions.
2. **Count.** `_count` recursively totals the nodes and bytes to process, so the progress bar is determinate. A same-storage move is a single atomic rename, so it counts as one node and its subtree is never walked (`_is_atomic_move`).
3. **Execute.** For each planned target: `task.checkpoint()` (cancellation point), then `_execute_one`, updating `task.progress`. Per-target exceptions are recorded in `errors` and processing continues; a `Cancelled` unwinds the loop.

### Result summary

`_run` returns a dict the caller reports via `format_op_summary` / `format_op_errors`:

| Key | Meaning |
|---|---|
| `done` / `skipped` / `failed` | counts of **top-level targets** (what the user selected) |
| `items` | total individual entries actually processed (recursive) |
| `errors` | list of `(name, message)` for failed targets |
| `cancelled` | `True` if a checkpoint or a "Cancel" conflict choice unwound the run |

A top-level target is `done` if any of its entries succeeded; `failed` only if it produced nothing and raised. Inner file failures stay in `errors` without sinking the whole target.

## Conflict resolution (`ConflictDialog`)

For copy/move, `_resolve` prompts per collision through the task's UI bridge — `task.ask(_conflict_prompt(...))` pushes a `ConflictDialog` (a `FocusContainer` + `Widget`) that stacks just above the progress dialog. It offers four actions plus an **apply-to-all-remaining** checkbox, and reports `(action, apply_to_all)`:

| Action | Key | Effect |
|---|---|---|
| Overwrite | `o` | replace the destination (`overwrite=True`) |
| Skip | `s` | leave it; increment `skipped` |
| Keep both | `k` | write to a fresh `name (N)` (via `_unique_dest`) |
| Cancel | `c` / `Esc` | raise `Cancelled` — abort the whole operation |

`a` / Space toggles apply-to-all, Tab moves focus, Enter activates the focused button. When apply-to-all is checked, the chosen action is reused for every remaining collision without prompting.

## Helpers

- `recursive_delete(entry)` — delete a file or directory tree.
- `_unique_dest(dest_dir, name, is_dir=…)` — the shared ` (N)` non-colliding-name scheme (used by duplicate and "Keep both").
- `_is_atomic_move(kind, target, dest_dir)` — true when a move stays within one storage backend (a single rename); a cross-storage move copies the tree then deletes the source.
- `format_op_summary(verb, result)` / `format_op_errors(verb, result)` — human-readable reporting from the result dict.

## Integration

- `TfmApp.__init__` — `self.tasks = TaskManager()`, `self._fileops = FileOperationService(self.config, self.tasks)`.
- `TfmApp.copy_files()` / `move_files()` / `duplicate_files()` / `delete_files()` gather the active pane's selection and delegate to `self._fileops`, passing an `on_complete` that refreshes panes and logs the summary.

## References

- [Task Framework](TASK_FRAMEWORK_IMPLEMENTATION.md)
- [Task Cancellation](TASK_CANCELLATION_IMPLEMENTATION.md)
- [Progress Manager System](PROGRESS_MANAGER_SYSTEM.md)
- [Path Polymorphism System](PATH_POLYMORPHISM_SYSTEM.md) — storage-agnostic operations behind `Path`
