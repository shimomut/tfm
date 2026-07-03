# PuiKit Port — Finishing Plan

Four polish items to close out the PuiKit port. Each is scoped against the
current code with concrete file/line targets, approach, risk, and test notes.
Items are independent; recommended order is **1 → 4 → 2 → 3** (small/high-payoff
first, threading last).

Legend: **puikit** = `/Users/crftwr/projects/puikit`, **tfm** = this repo.

---

## 1. Stop truncating text by monospace cell count

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

## 2. Stop drawing lines/frames with characters in GUI mode

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

## 3. Threading for file-IO and network access

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

## 4. Dialog sizing — larger than the pane, still pane-anchored

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
