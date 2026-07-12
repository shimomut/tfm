# Duplicate — Implementation

In-place duplication (GitHub issue #192) is a thin `"duplicate"` operation kind
layered onto the shared copy engine, plus app wiring for the two entry points.
No new copy/rename logic was written — it reuses `_unique_dest()` and the
existing threaded task pipeline.

## Engine — `src/tfm_file_operations.py`

`"duplicate"` is registered alongside `copy`/`move`/`delete`:

- `_VERB["duplicate"] = "Duplicate"`, `_OP_TYPE["duplicate"] = OperationType.COPY`.
- `FileOperationService.duplicate(panel, targets, dest_dir, …)` mirrors `copy()`
  and calls `_start(..., "duplicate", ...)`. `dest_dir` is the source's own
  directory.

It differs from copy in exactly one place — plan building in `_run()`. A
duplicate always collides with itself, so it **never prompts**; instead every
target is pre-planned to a fresh ` (N)` name up front:

```python
elif kind == "duplicate":
    plan = [(t, _unique_dest(dest_dir, t.name, is_dir=t.is_dir()), False)
            for t in targets]
    result["created"] = [dest.name for _t, dest, _o in plan]
```

Because distinct targets in one directory have distinct names, computing all
destinations against the pre-op filesystem state is collision-free (unlike
duplicating the *same* file twice, which cannot happen — targets are distinct
list entries). `result["created"]` carries the new names back to the caller for
cursor placement.

Everything else falls through the copy path: `_count()` walks the plan,
`_execute_one()` routes to `_copy_tree()` (the `if kind == "move"`
source-delete is skipped, so the original is never removed), and the per-file
log line reads "Duplicated" via the verb map
`{"move": "Moved", "duplicate": "Duplicated"}.get(kind, "Copied")`.

The confirm prompt in `_start()` gets a duplicate-specific line
("Duplicate **N** item(s) in `<dir>`?") and honors `CONFIRM_DUPLICATE` through
the existing `getattr(config, f"CONFIRM_{verb.upper()}", True)` — no special
casing needed. `CONFIRM_DUPLICATE = True` lives in `src/_config.py`.

## App wiring — `tfm.py`

Two entry points, one shared runner:

- `duplicate_files()` — guards (virtual pane, read-only archive, empty targets),
  gathers `_selected_or_focused(pane)`, then delegates to `_run_duplicate`.
  Returns `True` on a synchronous guard bail, `False` after handoff — same
  contract as `copy_files()`.
- `_run_duplicate(pane, targets)` — calls `self._fileops.duplicate(...)` with
  `pane["path"]` as the destination. `on_complete` clears the source selection,
  refreshes via `_refresh(pane, on_ready=lambda p: _select_by_name(p, created[0]))`
  so the cursor lands on the new copy, logs `format_op_summary("Duplicate", …)`,
  and reports failures.

Reachability (no default key binding):

- Dispatch: `elif action == "duplicate_files": return self.duplicate_files()` —
  so a user-defined `duplicate_files` key binding works.
- Menu bar (`_build_menu` → File menu) and right-click context menu
  (`_show_context_menu`): a **Duplicate** item after **Rename…**.

The same-directory copy relaxation lives in `_transfer()`: when
`dest_dir == src_pane["path"]` and `kind == "copy"`, it routes to
`_run_duplicate(src_pane, targets)` instead of logging the old
"source and destination are the same directory" error. Move keeps that error.

## Tests

`test/test_file_operations.py` — the `cfg` fixture sets
`CONFIRM_DUPLICATE = False` for headless runs; new tests exercise file, directory,
and multi-target duplication (each getting its own ` (N)`) plus the "Duplicated"
log line, all via the existing `_run_sync(svc, svc.duplicate, …)` harness.
