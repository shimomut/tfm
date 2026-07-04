# Search Results Pane — Plan

Status: **draft — design agreed (feed results into a virtual pane), not yet
started.**

Branch: `puikit-port`
Goal: let TFM's full pane feature set (copy/move, archive, view/diff,
delete/rename, sort & filter, info, edit, run-command) act on the files returned
by the filename / content search, instead of the current navigate-only accept.

---

## 1. Goal & scope

Today the progressive search dialog is a **locator**: accepting a hit
(`on_accept`, [tfm.py:1535](../../tfm.py#L1535)) just navigates the active pane to
the file's directory and lands the cursor — one file, single directory, search
context discarded.

We want the search result **set** — which spans many directories — to become a
first-class collection that every existing pane operation can target. The chosen
approach (see §2) is to **feed the results into the active pane as a flat,
virtual listing** ("Search Results" pane, à la Total Commander's *Feed to
listbox*). Because nearly every operation already derives its source directory
from the entry itself (`entry.parent`, `entry.rename(...)`, `Path` objects out of
`selected_files`), a flat listing of scattered paths makes those operations Just
Work — the effort is in the *pane model*, not the operations.

Out of scope: a persistent/saved-search folder abstraction, S3/SSH-remote result
sets (first cut is local-filesystem results only), and a second in-dialog
operations surface (explicitly rejected in favor of reusing the pane).

---

## 2. Approach decision (settled)

Considered three:

- **A — navigate-then-operate** (status quo). One file, loses the set. Rejected:
  too thin.
- **B — act inside the search dialog** (marking + an action menu on
  `ProgressiveSearchDialog`). Rejected: rebuilds a second selection+operations
  surface that duplicates the pane's affordances.
- **C — feed results into a virtual pane** (**chosen**). Reuses the real
  selection UI, the real menu, and every existing op. Cost is concentrated in
  teaching the pane that its listing may be virtual.

The enabling fact for C: operations read their targets from `pane["files"]` +
`pane["selected_files"]` via `_selected_or_focused` ([tfm.py:1889](../../tfm.py#L1889))
and each target is a self-describing `Path`. Copy/move destination is the *other*
pane, so scattered sources are fine. The exceptions are enumerated in §5–6.

---

## 3. The virtual-pane data model

A pane becomes virtual by carrying a marker alongside its normal fields
([tfm_pane_manager.py:20](../../src/tfm_pane_manager.py#L20)):

```python
pane["virtual"] = {
    "kind": "search",
    "root": Path,        # search root the walk started from
    "mode": "filename" | "content",
    "query": str,
    "results": list[Path],   # the full, unsorted/unfiltered found set (source of truth)
}
```

When `pane["virtual"]` is set:

- `pane["files"]` holds the **currently displayed** view of the result set
  (after the pane's own sort + filter applied in memory — see §7). `results` is
  the immutable source; `files` is the derived view.
- `pane["path"]` is retained as the search **root** for display/context, but is
  *not* the parent of the entries and must never be re-listed while virtual.
- `selected_files`, `focused_index`, `scroll_offset` behave exactly as normal.

Non-virtual panes leave `pane.get("virtual")` as `None`; every guard below is a
`if pane.get("virtual")` branch, so real panes are untouched.

---

## 4. Subsystems that assume `files == children of path`

These are the only places the single-directory assumption is baked in; each needs
a virtual guard.

### 4.1 Listing / refresh — `_list_pane` / `_refresh` ([tfm.py:560](../../tfm.py#L560), [754](../../tfm.py#L754))
`_list_pane` unconditionally clears `files` and re-lists `pane["path"]` on a
worker. For a virtual pane this would **destroy the result set**. Guard: when
`pane.get("virtual")`, `_refresh` must *not* call `_list_pane`; instead
**re-stat** the surviving result paths (drop vanished ones — see §6) and re-apply
the in-memory sort/filter (§7).

### 4.2 File monitoring ([tfm_file_monitor_manager.py](../../src/tfm_file_monitor_manager.py))
Monitoring watches a single `pane["path"]` directory and reloads on FS events.
For a virtual pane there is no single directory to watch. First cut: **suspend
monitoring** for a virtual pane (stop its observer; the set is a snapshot). A
later iteration could watch each distinct parent, but that is out of scope.

### 4.3 Navigation that changes `path`
Enter-directory, go-up (`pane["path"].parent`, [tfm.py:976](../../tfm.py#L976)),
jump-to-favorite/drive/history, and any `_refresh`-after-navigate. Rule: **any
action that sets a real `pane["path"]` clears `pane["virtual"]` and returns the
pane to a normal listing.** This is the natural "exit" (see §8). Entering a
*directory* hit from within the virtual pane navigates into it normally (exits
virtual mode); entering a *file* hit does the current go-to-result behavior.

### 4.4 Header / status
The path header ([tfm.py:129](../../tfm.py#L129)) shows `pane["path"]`. For a
virtual pane, render a distinct banner — e.g. `⌕ "query" — 42 results (filename,
under <root>)` — so the user can tell this is a result set, not a directory, and
which pane an operation will hit.

---

## 5. Operations audit

`_selected_or_focused(pane)` returns scattered `Path`s; unless noted, the op
consumes that and works **unchanged** on a virtual pane.

| Op | Works free? | Notes |
|----|-------------|-------|
| Copy / move | ✓ (source) | Dest = other pane. Post-op re-stat (§6): moved sources vanish from the set. |
| Archive create | ✓ | Operates on an arbitrary path list already. Archive lands in the other pane. |
| View | ✓ | Focused entry `Path`. |
| Diff | ✓ | Pulls 2 selected `Path`s (already cross-pane, [tfm.py:1862](../../tfm.py#L1862)). |
| Delete | ✓ (source) | Post-op re-stat: deleted entries drop from the set. |
| Rename / batch-rename | ✓ (source) | Uses `entry.parent / name` ([tfm.py:1800](../../tfm.py#L1800)). Post-op re-stat; renamed path changes. |
| Info / details | ✓ | Reads `_selected_or_focused`. |
| Edit | ✓ | Opens editor on the focused `Path`. |
| **Sort** | ✗ needs work | Must re-sort the in-memory `results`, not re-list a dir (§7). |
| **Filter** | ✗ needs work | Must filter the in-memory `results`, not re-list a dir (§7). |
| **Run-command** | ✗ **broken** | Passes **bare names** with `cwd=pane["path"]` ([tfm.py:1701](../../tfm.py#L1701)); scattered files won't resolve. Must pass **absolute paths** for a virtual pane. Open question §9. |

---

## 6. Post-operation reconciliation

After a mutating op (move/delete/rename/batch-rename) a real pane calls
`_refresh(pane)` to re-list. A virtual pane can't re-list. Introduce a
`_refresh_virtual(pane)` that:

1. Re-stats each `Path` in `pane["virtual"]["results"]`; drops entries whose path
   no longer exists (moved/deleted), and updates a renamed entry's path if we can
   map it (batch-rename returns new names).
2. Re-applies the in-memory sort + filter (§7) to rebuild `pane["files"]`.
3. Clamps `focused_index` / `selected_files` to the survivors.

`_refresh` dispatches to `_refresh_virtual` when `pane.get("virtual")`, so every
existing `self._refresh(pane)` call site keeps working with no edits.

---

## 7. Sort & filter on the virtual set

Sort/filter currently flow through `compute_listing(path, …)` in
`_list_pane` — i.e. they re-list the directory. For a virtual pane:

- Keep `pane["sort_mode"]`, `sort_reverse`, `filter_pattern` as the same knobs.
- Derive `pane["files"]` = `sort(filter(results))` in memory. Reuse
  `FileListManager`'s comparator/predicate if they can be factored out of the
  directory-listing path; otherwise a small local sort/filter over the `Path`
  list (sort keys: name, ext, size, mtime — same modes as the real pane).
- The existing sort/filter *actions* just set the knobs and call `_refresh`,
  which now routes to `_refresh_virtual` — so no new key bindings.

---

## 8. Entry & exit UX

**Entry.** Change the search dialog's `on_accept` path. Two ways in:

- Accept a single row (Enter/click) → **keep today's behavior** (navigate to the
  file in its real directory). Least surprising for "I just want to find one
  file."
- A new "feed all results into the pane" action from the dialog — a distinct key
  (e.g. `Ctrl-Enter` / a labeled button) that closes the dialog and calls a new
  `TfmApp._feed_search_results(mode, query, root, results)` which sets
  `pane["virtual"]`, builds `files`, suspends monitoring, and renders.
  - The dialog already streams into `self.results` ([tfm_progressive_search_dialog.py:94](../../src/tfm_progressive_search_dialog.py#L94)); the feed action hands that list (its `Path`s / content-hit `path`s) to the app. For content mode, dedupe by file path (many line-hits → one entry).

**Exit.** Any navigation that sets a real `path` (§4.3), plus an explicit
"restore listing" (Esc / go-up) that clears `pane["virtual"]` and `_refresh`es
the real `pane["path"]`. Decide whether entering the virtual pane should first
snapshot the prior real listing to restore on exit, or simply re-list the root.

---

## 9. Open questions

1. **Run-command cwd.** For a virtual pane, what is the working directory and how
   are args passed? Options: (a) pass absolute paths, `cwd` = search root;
   (b) pass absolute paths, `cwd` = focused entry's parent; (c) disable
   run-command on a virtual pane for the first cut. Leaning (a).
2. **Content-mode entries.** A content search yields *line* hits. Feeding the
   pane should collapse to **one entry per file** (ops act on files, not lines);
   the line context is lost once fed. Acceptable? Or keep a side-map for
   "reopen at line" on view/edit?
3. **Exit-restore.** Snapshot-and-restore the prior listing, or just re-list the
   root on exit? Snapshot is nicer but adds state.
4. **Both panes virtual.** Copy/move needs a real destination directory. If the
   *other* pane is also virtual (unlikely but possible), block the op with a
   clear message.
5. **Result cap.** The dialog caps at `_RESULT_CAP = 1000`
   ([tfm_progressive_search_dialog.py:59](../../src/tfm_progressive_search_dialog.py#L59)).
   Feed the capped set, or re-run the walk uncapped when feeding? First cut: feed
   the capped set and note the cap in the header banner.

---

## 10. Slices

1. **Model + guards.** Add `pane["virtual"]`; guard `_list_pane`/`_refresh`
   (→ `_refresh_virtual`), monitoring suspend, header banner, and the
   navigation-clears-virtual rule. No ops yet — just enter (via a temporary test
   hook) and exit cleanly.
2. **Feed action + entry UX.** `Ctrl-Enter` in the dialog → `_feed_search_results`;
   content-mode dedupe; render.
3. **Sort & filter in memory** (§7).
4. **Post-op reconciliation** (§6) + verify the free ops (copy/move, archive,
   view/diff, delete, rename, info, edit) on a virtual pane.
5. **Run-command** per §9.1.

---

## 11. Testing

- Unit: feeding a known result set produces a virtual pane whose `files` match;
  navigation clears virtual; `_refresh_virtual` drops vanished paths and re-sorts.
- Integration (headless panel): feed → select a subset → copy to the other pane →
  assert files land and the virtual set re-stats; delete → assert survivors;
  batch-rename → assert renamed paths tracked.
- Guard regressions: real panes still list/refresh/monitor exactly as before
  (the `if pane.get("virtual")` branches must be inert when unset).
