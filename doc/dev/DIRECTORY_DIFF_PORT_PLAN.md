# Directory Diff Viewer — PuiKit Port Plan

Status: **complete — all four slices landed; 28 headless tests pass (TUI+GUI).
Pending manual GUI verification on macOS + curses.**

Tree-line rendering is capability-split (`ctx.vector_shapes`): the GUI draws the
hierarchy connectors as thin `fill_rect` lines (1 device pixel, aligned to a
base-unit grid) with node names in the proportional UI font, elided to the
column by measured width; the terminal keeps box-drawing connectors on the
character grid. An earlier all-monospace pass fixed alignment but looked like a
terminal in the GUI — box-drawing glyphs are the wrong primitive for a
proportional font (same lesson as the MessageBox proportional-truncation bug).
Branch: `puikit-port`
Scope: port `legacy/src/tfm_directory_diff_viewer.py` (~4,527 lines) to a PuiKit
widget, the last major unported UI module (Phase 4 tentpole).

---

## 1. Goal & scope

Recreate the recursive directory diff — side-by-side tree of two directories,
progressively scanned, with per-node difference classification, expand/collapse,
next/prev-difference navigation, open-file-diff, copy/delete across sides, and
rescan — as a full-window modal PuiKit `Widget`, wired to the existing
`diff_directories` action (`Shift-EQUAL`, already in `_config.py:114` but not yet
handled in `tfm.py`).

Follow the `tfm_diff_viewer.py` porting pattern: a `Widget` pushed via a
`show_directory_diff_viewer(panel, left, right)` factory, reusing PuiKit chrome
(`Splitter`, `draw_scrollbar`, `draw_child`, `Theme`/`Style`) and the
already-ported `show_diff_viewer` for per-file diffs. Feature parity over
pixel-fidelity, per the master plan §1.

---

## 2. Reuse vs. rewrite

### 2.1 REUSE — backend-agnostic logic (mechanical import swaps)

These are pure data/algorithm/threading and carry over nearly verbatim; the only
edits are dropping the `ttk` imports (`KeyEvent`/`CharEvent`/`SystemEvent`/
`KeyCode`/`ModifierKey`/`TextAttribute`, `ttk.wide_char_utils`) in favor of
`puikit.text` (`display_width`/`truncate_to_width`) and stdlib:

- `DifferenceType`, `ScanPriority`, `FileInfo`, `ScanTask`, `ComparisonTask`,
  `TreeNode` (dataclasses/enums).
- `DirectoryScanner` (recursive scan, cancellation).
- `DiffEngine` (`build_tree`, `_add_path_to_tree`, `_sort_tree`,
  `_classify_tree`, `classify_node`, `compare_file_content`).
- Progressive-scan machinery: `_directory_scanner_worker`,
  `_file_comparator_worker`, `_priority_handler_worker`, the scan/compare
  queues, `_update_tree_node`, `_classify_*`, `_update_priorities`,
  `_queue_*`, `_mark_directories_pending`.
- Tree ops: `expand_node`, `collapse_node`, `_flatten_tree`,
  `_rebuild_node_index_map`, `_collect_*`, `_find_node_by_path`,
  `_propagate_difference_to_parents`, `_jump_to_{next,previous}_difference`,
  `_count_differences`, expansion-state save/restore, `_trigger_rescan`.
- Cross-side file ops: `_copy_focused_file`, `_delete_focused_file` (already use
  `tfm_path.Path` primitives; reuse `format_size` from `tfm_str_format`).

Threading (`threading`, `queue`, `subprocess`, `time`) is stdlib — reuse as-is.

### 2.2 REWRITE — rendering & events as a PuiKit widget

- `DirectoryDiffViewer(UILayer)` → `DirectoryDiffView(Widget)`, `focusable=True`,
  pushed full-window by `show_directory_diff_viewer` (mirror `show_diff_viewer`).
- `render` + all `_render_*` (`_render_header`, `_render_content`,
  `_render_details_pane`, `_render_status_bar`, progress/cancellation/error/
  loading screens, empty/identical message) → a single `draw(ctx)` drawing
  through `DrawContext`. Two tree columns in a `Splitter`; scrolling content in a
  clipped `_ScrollBody` child (reuse the `tfm_text_viewer` helper, as
  `DiffViewer` does) for smooth scroll; `draw_scrollbar` for the v-scrollbar.
- `handle_key_event`/`handle_char_event`/`handle_system_event`/
  `handle_mouse_event` → one `handle_event(event)` on the PuiKit `Event` model
  (`EventType.KEY`/`MOUSE_*`/`MOUSE_SCROLL`). Keys from the legacy map:
  ↑/↓/PgUp/PgDn/Home/End, ←/→ or Enter to expand/collapse, Tab to switch focused
  side, `n`/`N` next/prev diff, `d`/`Enter`-on-file open file diff, `c` copy,
  `x`/Del delete, `r` rescan, `?` help, `q`/Esc close.
- `_get_node_colors` → `Theme` roles + `Style` (accent for focus, muted for tree
  lines, semantic tints for only-left/only-right/different — reuse the diff-tint
  palette already defined in `tfm_diff_viewer.py`).
- `_show_help_dialog` → `show_message_box` (or the ported help pattern in
  `tfm.py`'s `show_help`).
- Per-file diff (`open_file_diff`) → call the ported
  `show_diff_viewer(self._panel, left, right)`.
- `_launch_external_diff` → reuse `tfm_external_programs` launch path if trivial;
  otherwise defer (non-core).

---

## 3. The one real architecture decision — progressive scanning

The legacy viewer runs worker threads that mutate the tree **and** drive redraws
(`mark_dirty` + the ttk layer stack's dirty loop). The PuiKit port so far is
fully synchronous (explicit `panel.render()`); there is **no thread→UI wakeup**.

**Approach — DECIDED: keep the worker threads for I/O, decouple them from the
UI via `panel.request_animation_ticks`.**

- Worker threads do scanning/comparison exactly as today, but their only UI
  contact is mutating the tree and setting a thread-safe `self._dirty` flag
  (guard tree mutation with a `threading.Lock`; the draw reads under the same
  lock or a shallow snapshot of the flattened node list).
- On push, register an animation-tick callback via
  `panel.request_animation_ticks(cb)`. The callback runs on the **main thread**
  each idle wake / frame (curses idle-timer, macOS NSTimer — verified present in
  both backends). It checks `_dirty`; if set, clears it and calls
  `panel.render()`, then returns `True` while any worker is alive, `False` once
  scanning is complete and idle (ticking stops, no busy spin).
- This keeps all `DrawContext`/`render` calls on the main thread (no cross-thread
  UI), fits PuiKit's model, and preserves the progressive UX.

**Fallback if animation-tick redraw proves fiddly:** bounded synchronous scan up
front with a progress screen (the pattern the search port already uses), losing
live progressive updates but shipping parity on the result. Decide after a small
spike on slice 1.

---

## 4. Build slices (vertical, verify each headlessly on MemoryBackend)

1. **Static tree render.** Port the data model + `DiffEngine` + a *synchronous*
   full scan; render the flattened tree in a `Splitter` of two columns with
   classification colors, gutter, tree lines. No progressive scan, no nav yet.
   Wire `diff_directories` → `show_directory_diff_viewer`. *Exit: open on two
   dirs, see the classified tree, q/Esc closes.*
2. **Navigation + expand/collapse.** Cursor, scroll (`_ScrollBody` smooth
   scroll), v-scrollbar, expand/collapse, next/prev diff, focused-side switch,
   status bar + header. *Exit: browse/expand/collapse/jump.*
3. **Progressive scanning.** Introduce the worker threads +
   `request_animation_ticks` redraw (§3). Pending indicators, progress/cancel
   screens. *Exit: large trees populate live without blocking.*
4. **Actions.** Open file diff (reuse `show_diff_viewer`), copy/delete across
   sides (with confirm via `show_message_box`), rescan with expansion-state
   save/restore, details pane, help. *Exit: feature parity.*

---

## 5. PuiKit seams that may be needed

Prior port slices each needed 0–2 small PuiKit additions (`has_layers`,
`focused_leaf` modal fix). Anticipated here:

- `request_animation_ticks` already exists — confirm it's exposed on `Panel` and
  callable pre-first-frame, and that returning `False` cleanly stops ticks.
- Possibly a thread-safe "wake the loop now" so a finished scan renders without
  waiting for the next idle tick — only if idle-tick latency looks bad. Prefer
  not to add it unless observed.

Any new seam gets a PuiKit regression test, per the established pattern.

---

## 6. Testing — DECIDED: minimal (new headless tests only)

- New headless `MemoryBackend` tests for the widget only: tree classification
  (only-left/only-right/different/identical/contains-difference), flatten/expand/
  collapse index integrity, next/prev-diff jumps, copy/delete mutating the
  correct side, and the dirty-flag→tick→render loop (drive ticks manually).
- Do **not** port the legacy `test/test_directory_diff_*` suite.
- Manual GUI verification on macOS + curses (progressive scan is the thing
  headless tests can't fully exercise, per the keyboard-contract lesson).

---

## 7. Effort

Largest single port in the project (master plan §10: XL/high risk). Slices 1–2
are mechanical given the `DiffViewer` pattern; slice 3 (progressive scan +
tick-driven redraw) is the genuinely new/risky part and the reason to spike it
behind slices 1–2 rather than first.
