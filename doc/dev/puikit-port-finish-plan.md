# PuiKit Port — Finishing Plan

Four polish items to close out the PuiKit port. Each is scoped against the
current code with concrete file/line targets, approach, risk, and test notes.
Items are independent; recommended order is **1 → 4 → 2 → 3** (small/high-payoff
first, threading last).

Legend: **puikit** = `/Users/crftwr/projects/puikit`, **tfm** = this repo.

---

## 1. Stop truncating text by monospace cell count — ✅ DONE

**Implemented (categories A + B below):**
- puikit `widgets/list.py`, `widgets/tree.py` — rows clip by `ctx.measure_text`.
- puikit `widgets/_selection.py` — click→glyph hit-test measures real width to
  match the highlight; `_set_selection_rows` gained a `measure` arg, passed by
  `label.py` and `text_block.py`.
- puikit `widgets/busy_indicator.py` — spinner→label offset uses `measure_text`.
- tfm `tfm_file_pane.py` — the `(empty)`/error message elides with `measure`.
- New test `test_widgets.py::test_listview_clips_by_measured_width_not_column_count`;
  full puikit suite green (684 passed).
- Not needed: `tfm_progress_manager.py` / `tfm_text_layout.py` — progress is not
  wired into any GUI draw path (only tracked by the file-op executors), and
  `get_progress_text` is the flat-text/log helper. Revisit if progress is drawn.

Original analysis follows.

**Status: infrastructure already exists; two call sites remain.**

`puikit/text.py` already supports proportional measurement — `truncate_to_width`,
`elide`, and `wrap_text` all take a `measure` callback, and callers that pass
`ctx.measure_text` truncate by *real rendered width* instead of column count.
Already correct: tfm's `PaneHeader`/`PaneFooter`/hint bar (`elide(..., measure=
ctx.measure_text)`), and puikit's `text_block`, `text_edit`, `button`, `menu`.

**The gap — two list widgets clip by column count with no `measure`:**

- `puikit/widgets/list.py:154` — `truncate_to_width(self.items[index], text_w)`
- `puikit/widgets/tree.py:129` — `truncate_to_width(content, max(1, text_w - int(text_x)))`

These back the file panes and most dialogs, so this is the visible offender in
GUI (proportional-font) mode: rows clip too early or overflow by a fraction.

### Approach
- Pass `measure=ctx.measure_text` to both calls, with the width expressed in
  base units (the same unit `measure_text` returns).
- `text_w` is already a base-unit column count; on a grid backend `measure_text`
  returns the column count so behavior is unchanged there. On GUI it becomes a
  true-width fit. Confirm `text_w` is the right budget (list) and that
  `text_w - text_x` stays ≥ 1 (tree).
- Audit for any other bare `truncate_to_width`/`display_width` clip sites in
  widgets that render user strings (grep already run: only these two lack a
  measure; the backends' internal `display_width` uses are grid-glyph layout and
  are correct to stay column-based).

### Risk / test
- Low risk; the grid path is unchanged by construction.
- Tests live in puikit's suite. Add/extend a widget test asserting that with a
  proportional `measure` (mock returning e.g. 0.5·len), a long row is clipped by
  measured width, not char count. Run puikit `make test`.
- Manual: run tfm in GUI (macOS) backend, put long filenames + CJK in a pane,
  verify no overflow / no premature clip.

---

## 2. Stop drawing lines/frames with characters in GUI mode — ✅ DONE

**Audit result: the codebase was already ~95% vector-guarded.** Confirmed already
correct: pane/layout + widget dividers (`hairline`), dialog frames (`draw_box` →
real rects), `Tabs`, `ProgressBar`, `Menu` separators, all scrollbars (the
`draw_scrollbar` backend primitive), and the directory-diff **tree connectors**
(`_draw_side_vector`). `MarkdownView` and the legacy glyph `tfm_scrollbar.py` are
not used by tfm.

**Only two residual char-lines reached a GUI backend; both fixed — via a new
Panel-layer intent primitive, not widget-level `vector_shapes` branches** (see
the architecture note below):
- puikit `panel.py` — added `DrawContext.draw_hairline(x, y, length, *, vertical,
  style)`, the intent primitive for a free-form separating line. It resolves the
  visible-vs-grid choice *inside the Panel layer* (vector → device-pixel
  `fill_rect` stroke; grid → `─`/`│` glyph run), mirroring `round_rect` /
  `draw_divider`. The across-axis coord is the centerline; the along-axis coord
  is the start.
- puikit `widgets/markdown_view.py` — the horizontal rule (`─`) and blockquote
  bar (`│ `) now call `ctx.draw_hairline`; the widget no longer reads
  `vector_shapes` at all (blockquote also gained a correct bar on every wrapped
  line). New tests `test_rule_and_quote_are_hairlines_not_glyphs_on_gui` /
  `..._glyphs_on_tui` (a `_VectorBackend` helper keeps `vector_shapes` on, which
  MemoryBackend otherwise forces off).
- puikit `widgets/menu.py` — the separator now calls `ctx.draw_hairline`, paying
  down the pre-existing `vector_shapes` branch there.
- tfm `tfm_directory_diff_viewer.py` — the header column-divider now calls
  `ctx.draw_hairline`; grid keeps a `│`, GUI gets a stroke. (Per-row `= < > ! ?`
  are verdict indicators — semantic content, left as text. The tree connectors'
  own `_draw_side_vector`/`_grid` split is a pre-existing, more-complex branch
  left as-is.)
- New primitive tests `test_draw_hairline_strokes_thin_rects_on_vector` /
  `..._uses_box_glyphs_on_grid`. Verification: puikit 688 passed; tfm diff 37.

**Architecture note (why the primitive, not a widget branch):** puikit's
`vector_shapes` property doc (`panel.py`) says widgets read it *only to drop
pixel-only ornamentation* — the hairline-vs-glyph *decision* belongs in the Panel
layer via an intent primitive (like `round_rect` / `draw_divider`). The first cut
branched on `ctx.vector_shapes` inside the widgets (matching existing debt in
`menu`/`tabs`/`progress_bar`); this was refactored to `draw_hairline` so the
switch lives in the Panel layer as the architecture intends. `tabs`/`progress_bar`
still branch because their vector path draws more than a hairline (a 4-side frame,
a rounded pill) — a future `draw_frame`/pill intent could absorb those too.

Original analysis follows.


**Status: mostly already done in puikit; remaining offenders are tfm-side.**

Already correct: `draw_box` on GUI backends draws real rectangles; layout and
widget dividers branch on the `hairline` capability
(`puikit/panel.py:757`, `:1304`) — box-drawing glyphs only on terminal backends.

**Remaining GUI char-drawing, all in tfm:**

- `tfm_directory_diff_viewer.py:546` — tree connectors `├─ └─ │` built as text.
- `tfm_directory_diff_viewer.py:743` — column separator drawn as `" │ "` text.
- The module header (`:857`) explicitly assumes a monospace cell grid.
- Scrollbar glyphs (`█` thumb / `│` track) — verify whether the GUI path already
  routes through `draw_scrollbar` (vector) or falls back to glyphs
  (`tfm_scrollbar.py`, and puikit `draw_scrollbar`).

### Approach
- **Diff-viewer tree lines:** mirror puikit's divider pattern — when
  `ctx.vector_shapes` / `hairline` is supported, draw the indent guides and the
  column separator with `fill_rect` hairlines (and the ├/└ elbows as short
  hairline segments), else keep the box-drawing text for terminal. Factor a
  small helper so the tree-connector logic branches once.
- Keep the *text/label* content unchanged; only the structural lines move to
  hairlines.
- **Scrollbar:** confirm `draw_scrollbar` is already vector on GUI backends; if
  tfm bypasses it with glyph drawing, route through the backend primitive.

### Risk / test
- Medium. The diff viewer's monospace assumption is baked into its layout math
  (column truncation at `:857`); the connectors are cosmetic but the separator
  x-position (`self._sep_x`) is a base-unit column, so a hairline at that x is a
  clean swap. Verify alignment on both backends.
- Manual check on macOS GUI: open directory-diff, confirm tree guides and the
  center separator render as crisp lines (no dotted/segmented glyph gaps), and
  terminal mode still shows connected box lines.

---

## 3. Threading for file-IO and network access — ✅ DONE (always-async)

**Implemented — every directory *listing* runs off the UI thread, so navigation
never blocks regardless of path kind (local, slow network mount, spun-down disk,
huge dir, or remote S3/SSH).** The first cut was remote-only (scheme check), but
a slow *local* mount would still freeze; `_is_local` classifies by scheme, not
latency, so it can't see NFS/SMB/autofs/sleeping-disk. Rather than an OS mount
probe (leaky: autofs/sleeping disks still slip through, and `statfs` can itself
hang on a dead mount), we made **all** listings async with a deferred indicator.

- `tfm_file_list_manager.py` — split `refresh_files` into `compute_listing`
  (pure, worker-safe: the blocking `iterdir` + per-entry `is_dir`/`stat`) and
  `apply_listing` (pane mutation on the UI thread). `refresh_files` = compute +
  apply, so all existing synchronous callers are unchanged (137 FLM-touching
  tests green).
- `tfm.py` — new `_list_pane(pane_name, *, on_ready)`: **always** computes on a
  daemon worker that posts `(pane_name, gen, result, on_ready)` to a new
  `_result_queue`, drained on the same animation tick as `reload_queue`
  (`_process_result_queue`). **Single-flight per pane** via a `_load_gen` counter
  — a newer navigation supersedes an in-flight listing, so stale results are
  dropped, never clobber. The worker only reads a snapshot of the pane inputs;
  the UI thread owns all pane mutation.
- **Deferred loading indicator** — `_list_pane` clears the pane and records a
  start time; `_pump_loading_indicator` (on the tick) reveals "Loading…" only
  once a listing has been pending past `_LOADING_INDICATOR_DELAY` (0.12s),
  forcing one re-render as it crosses. A fast (local) listing lands within a tick
  and swaps in with **no flash**; only a genuinely slow directory shows the
  indicator. `tfm_file_pane.py` shows blank-then-"Loading…" via the
  `_loading_shown` flag.
- `_settle_listings(timeout)` / `_listings_pending()` — block until in-flight
  listings complete and drain (the interactive UI never calls these; they let
  **tests** navigate then assert deterministically). Updated the navigate-then-
  assert tests (monitoring reloads, content-search, edit/subshell) to call
  `_settle_listings()`.
- Routed through the async path: every path-change navigation (`_refresh` →
  `_open`, `_go_parent`, `_go_to_result`/`_content_hit`/`drive`/`history`), the
  pane-sync actions, `toggle_hidden`, and the monitor reload
  (`_handle_reload_request`). Cursor-placement that depended on the freshly-listed
  files (`_go_parent` landing on child, `_select_by_name`) moved into `on_ready`
  callbacks that run when the result lands.
- **Left synchronous (documented follow-ups):** filter apply/clear and quick-sort
  (coupled to synchronous returns / current-dir re-list), post-file-operation
  reloads, and the two startup refreshes (panel/queue not up yet).
- Tests: new `test_tfm_app_async_listing.py` (7: async-install, deferred
  indicator reveal/idempotence/clear, two single-flight cases). Full suite:
  **1160 passed**, 1 pre-existing flaky (`test_remote_path_cleanup_optimization`
  — state-DB pollution, passes standalone, touches none of this code).

**Trade-off accepted:** a fast local listing now lands on the next idle tick
(≤50ms on curses, ~a frame on GUI) rather than truly inline — puikit exposes no
thread-safe event-loop wake, so a worker can't nudge the loop early. The deferred
indicator hides this (no flash); the payoff is the UI never freezes on any path.

Original analysis follows.

**Status: background *operations* already threaded; interactive *listing* is not.**

Already threaded: copy/move/delete (`tfm_file_operation_executor.py`), archive
ops (`tfm_archive_operation_executor.py`), S3 (`tfm_s3.py`), SSH connection/cache
(`tfm_ssh_connection.py`, `tfm_ssh_cache.py`), file monitor, state, logging.

**The gap — the interactive navigation path is synchronous:**

- `tfm_file_list_manager.py:61` — `refresh_files` does `list(pane_data['path']
  .iterdir())` on the UI thread. For an S3/SSH `tfm_path`, `iterdir()` hits the
  network, so **navigating into a remote directory blocks the UI** until the
  listing returns.

### Approach (decision deferred — pick scope before implementing)
Two options; **remote-only minimal** is recommended:

- **Remote-only (recommended):** detect remote paths (there is already an
  `_is_local` helper in `tfm.py`); for remote, dispatch the `iterdir()` +
  sort/filter to a worker thread and post the finished pane snapshot back to the
  UI via the same event-post mechanism the file monitor uses (see
  `tfm_file_monitor_manager` → app event queue at `tfm.py:265`). Show a
  lightweight "loading…" state on the pane while in flight. Keep local `iterdir`
  synchronous (fast enough; avoids a state-machine on every keypress).
- **All listings threaded:** route every `refresh_files` through the worker with
  a loading state. More uniform, but adds latency/flicker to instant local navs
  and touches every navigation path. Larger blast radius.

Either way needs:
- A single-flight guard per pane (a newer navigation supersedes an in-flight
  one; drop stale results by comparing the requested path to the pane's current
  path when the result lands).
- Thread-safe hand-off: worker does pure I/O + list building, UI thread does the
  assignment/redraw. No widget mutation off-thread.
- Cancellation / app-exit: ensure workers are daemonized or joined on quit
  (`tfm.py:389` teardown).

### Risk / test
- Highest risk of the four (concurrency + UI state). Keep it last.
- Tests: unit-test the single-flight/stale-drop logic with a fake slow path;
  assert a superseded listing does not clobber the current pane. Reuse the
  existing task-executor test patterns.
- Manual: nav quickly through an S3/SSH tree; UI stays responsive, no stale
  contents, cursor position sane.

---

## 4. Dialog sizing — larger than the pane, still pane-anchored — ✅ DONE

**Implemented:**
- New `src/tfm_dialog_geometry.py` — `pane_anchored_box(desired_w, screen_w,
  region, *, factor=1.4, margin=2.0) -> (w, x)`. The dialog grows up to 1.4× the
  pane width (never past its own desired width, never narrower than pane-fit),
  then a final on-screen cap keeps a 2-unit margin each side. Centered on the
  pane's center, so it leans over its target pane; near a screen edge the clamp
  shifts it inward but keeps it over the correct pane.
- `tfm_input_dialog.py` and `tfm_filter_list_dialog.py` both replaced their
  identical `w = min(w, region_w)` clamp with a call to the shared helper (fixed
  the filter docstring's "never wider than it").
- New `test/test_dialog_geometry.py` (7 cases: grow-past-pane, factor cap,
  interior centering, right-pane lean, screen-margin on a huge pane, narrow
  edge pane). Two caught real issues during development — a floor-vs-screen-cap
  ordering bug, and that an edge pane can't stay perfectly centered — both
  resolved. All 36 picker/dialog tests pass.

Original analysis follows.

**Status: small, localized change in two dialog helpers.**

Both dialogs currently hard-clamp width to the pane region:

- `tfm_input_dialog.py:216` — `w = min(w, region_w)`
- `tfm_filter_list_dialog.py:216` — `w = min(w, region_w)`

`region` comes from `TfmApp._active_pane_region()` (`tfm.py:1101`) = the exact
`(x, width)` column span of the active pane. Result: dialogs never exceed one
pane's width.

### Approach
- Let the dialog grow past the pane while staying centered on the **pane's
  center** (so it visibly leans toward the target pane):
  - Compute `center = region_x + region_w/2`.
  - Allow width up to `min(desired_w, region_w * FACTOR, sw - 2*MARGIN)` with
    `FACTOR ≈ 1.3–1.4` and a small screen margin.
  - Position `x = clamp(center - w/2, MARGIN, sw - w - MARGIN)`.
- Apply the same helper to both dialogs (and any other pane-anchored dialog —
  `show_batch_rename`, drives/search reuse `show_filter_list`, so they inherit).
- Keep the current behavior as the floor: if `desired_w ≤ region_w`, nothing
  changes.

### Risk / test
- Low. Pure geometry; no state.
- Test the placement math directly (given region + screen width → expected x/w),
  including the clamp at screen edges for a right-pane dialog.
- Manual: open filter/input over the right pane, confirm it overhangs slightly
  but is clearly centered over the right pane, and never runs off-screen.

---

## Suggested sequencing

1. **#1 truncation** — two-line change + a widget test. Immediate GUI win.
2. **#4 dialog sizing** — one geometry helper shared by both dialogs.
3. **#2 diff-viewer lines** — hairline branch mirroring puikit's divider pattern.
4. **#3 threading** — largest; decide remote-only vs all-listings first.

Items 1–2 touch **puikit**; 3–4 touch **tfm**. Item 2 spans both conceptually
but the code changes are tfm-side.

## Open decisions for review
- **#3 scope:** remote-only (recommended) vs all listings threaded?
- **#4 factor:** how much larger than the pane — 1.3×? 1.4×? capped at screen−margin.
- **#2 scrollbar:** in-scope, or defer if it already routes through `draw_scrollbar`?
