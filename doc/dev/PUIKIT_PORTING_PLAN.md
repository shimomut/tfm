# TFM → PuiKit Port

Status: **port essentially complete** — living document, tasks only.
Branch: `puikit-port` · Last updated: 2026-07-11

TFM's rendering/UI foundation has been moved off the in-repo **`ttk`** toolkit
onto **[PuiKit](https://github.com/...)**, a capability-based framework that runs
the same widget code on TUI (curses), macOS, and Windows backends. This doc
tracks what's **left**; the how/why of finished work lives in git history. (The
keyboard contract, once documented here, now lives in
`puikit/docs/keyboard_contract.md` and TFM's
`doc/dev/KEY_BINDINGS_IMPLEMENTATION.md`.)

---

## 1. Where the port stands

`ttk` is **fully removed from `src/`** (no `from ttk` / `import ttk` remains; the
`ttk/` package and the legacy UI modules — `tfm_single_line_text_edit`,
`tfm_base_list_dialog`, `tfm_quick_edit_bar`, … — are deleted). TFM runs on
PuiKit on curses + macOS.

Done and wired (Phases 1–4, plus the GUI-polish pass):

- **Shell** — dual `FilePane` widgets in a `Splitter(Splitter(left, right), log)`
  layout with per-pane header/footer, a tail-following `LogView` log pane, and a
  status bar. Virtualized draw, smooth/precise scroll, click/double-click, wheel,
  draggable splitters, scrollbars.
- **Interaction** — navigation, selection + focus marker, sort (incl. quick-sort
  keys), pane-local filter, incremental search, compare-and-select, theme colors.
- **Dialogs / menus** — `MenuBar` (native NSMenu on macOS, in-window strip on
  curses), message boxes, right-click context menus, the searchable
  filter-list picker (favorites / drives / programs / jump), and input dialogs
  (rename / mkdir / create), all as `push_layer` modals.
- **File operations** — copy / move / delete / rename / batch-rename, threaded
  with progress, per-conflict resolution (overwrite / skip / keep-both) and
  cooperative cancellation, wired through the context menu and keymap.
- **Search** — recursive filename and content (grep) search, bounded, results in
  the filter-list dialog.
- **Viewers** — text viewer (pygments, isearch), file diff viewer, directory-diff
  viewer, all ported.
- **Keyboard** — the cross-backend contract (`puikit/docs/keyboard_contract.md`)
  is implemented on curses / macOS / Windows and backed by live regression tests.
- **GUI polish** — text clips by measured width (not cell count); lines/frames
  draw as vectors in GUI mode; dialogs grow past the pane while staying
  pane-anchored; directory listing is always async so navigation never blocks.
- **edit_file / subshell** — terminal suspend/resume wired.
- **Theme palette** — light/dark-aware file-type, cursor, and syntax-highlight
  colors, all driven by the active theme and switched from one toggle.
- **GUI fonts** — configurable proportional UI + monospaced faces and size from
  `~/.tfm/config.py` (`UI_FONT_NAME` / `MONO_FONT_NAME` / `FONT_SIZE`), gui-gated.
- **macOS app bundle** — build system rebuilt on PuiKit (ttk copy steps removed);
  the bundle runs via PuiKit's PyObjC event loop.
- **Windows backend** — runs on Direct2D/DirectWrite (navigation, IME, both
  drag-and-drop directions); bring-up smoke tests and the keyboard contract pass
  live.

---

## 2. Remaining tasks

### 2.1 Async-listing gaps (low priority)
Directory *listing* runs off the UI thread everywhere it matters, but a few paths
still list **synchronously**. Fine for local dirs; only bites on genuinely slow
mounts. Route these through the async path (`_list_pane` in `tfm.py`) when worth
it:
- filter apply / clear,
- quick-sort re-list,
- post-file-operation reloads,
- the two startup refreshes (panel/queue not up yet — needs a deferred kick).

### 2.2 Draw the tree disclosure indicator as a vector chevron in GUI
The expand/collapse indicator on tree rows is a **glyph** today — `▸` (collapsed)
/ `▾` (expanded), drawn as text in both backends. In GUI it should instead be a
**line-drawn chevron** (a `>` that rotates to `⌄` when open), rendered with vector
primitives so it reads as UI chrome rather than a font character. The grid
backend keeps the `▸`/`▾` glyph (a vector chevron can't be drawn on a character
cell).

Where the marker is emitted today:
- **Directory Diff Viewer** — `_draw_side_vector` / `_draw_side_grid`
  (`tfm_directory_diff_viewer.py`) build `marker = "▾ "|"▸ "` and `draw_text` it,
  even on the vector path. This is TFM's live tree, so it's the primary target.
- **PuiKit `TreeView`** (`puikit/widgets/tree.py`, `_EXPANDED`/`_COLLAPSED`) — the
  reusable widget carries the same glyph; give it the same GUI chevron so the
  behavior is shared, not re-bespoked per viewer.

**Key sub-decision — how to draw the diagonal.** `DrawContext` currently exposes
**only `fill_rect`** (axis-aligned); there is no line / polyline / polygon /
triangle primitive, so the diff viewer's existing vector connectors are all
horizontal / vertical bars. A chevron needs diagonals. Two routes:
- approximate the chevron with a short **staircase of `fill_rect`s** (a few
  device-pixel steps) — no new PuiKit surface, but crisp only at small sizes; or
- add a real vector primitive to PuiKit (`draw_line` with arbitrary endpoints, or
  a `fill_polygon` for a filled triangle) — the cleaner long-term primitive, also
  reusable for a filled-triangle disclosure look, but a new backend seam (macOS +
  memory + curses no-op) with its own regression test.
Prefer the primitive if a filled triangle / smooth chevron is wanted; the
staircase if a 1–2px hairline `>` is enough. Decide with a small spike.

Reserve the same marker-column width so the label origin (`label_x`) and the
expander hit region are unchanged; only the mark's rendering swaps.

### 2.3 Directory Diff Viewer — add content margins
Everything in the viewer is drawn **flush to the edges**, so text hugs the window
border and the centre gutter with no breathing room. Add consistent insets. In
`tfm_directory_diff_viewer.py` `draw` / the column geometry:
- **left / right window margins** — the left column starts at `_left_x = 0.0` and
  header paths / details / footer all `draw_text` at `x = 0`; the right column
  runs up to the scrollbar. Inset the content from both edges.
- **inner gutter padding** — column text abuts the `_GUTTER_W` splitter band on
  both sides; add a small pad between the left column's text and the gutter, and
  between the gutter and the right column's text.
- (Optional) a top/bottom pad between the header/footer chrome bars and the body.

The real work is **threading one margin constant through all the geometry and
hit-testing consistently**, not the draw calls themselves: `_left_x`, `_right_x`,
`_left_w`, `_right_w`, `_sep_x`, `_avail`, the split clamp (`_MIN_PANE`), the
scrollbar x, the body child rect, and the pointer hit-tests / gutter-drag band
(`_hit`, `in_gutter`, `_drag_offset`) all derive from the current flush layout and
must shift together, or the split drag and row clicks will land off by the margin.
Keep it a single named constant (e.g. `_MARGIN`) so it's tunable in one place.

### 2.4 Filepath TAB completion in input dialogs
Complete paths with TAB in the text-input prompts. `jump_to_path` in `tfm.py`
even notes it: *"(TAB path completion is a later phase.)"* — the primary target,
with the save-as / name prompts (`create_file`, `create_directory`,
`create_archive`, `rename`) as secondary consumers.

Today: `show_input` / `InputDialog` (`tfm_input_dialog.py`) wraps PuiKit's
`TextEdit`; `handle_event` intercepts only `enter` / `escape` and forwards
everything else (including `tab`) to the field, which ignores it. There is **no
completion hook**.

Reference: the ttk `tfm_single_line_text_edit.py` (now under `legacy/src/`) had a
pluggable `Completer` + `handle_tab_completion` — insert the **longest common
prefix** of the matches, and show a **candidate list** on TAB (repeated TAB to
keep going). Reuse that design.

To build:
- A `completer` / `on_tab` hook on `InputDialog` (and a `show_input` parameter):
  given `(text, caret)`, return the completed text + new caret + candidate list.
  Intercept `tab` in `InputDialog.handle_event` (like `enter` / `escape`) so it
  no longer falls through to the field.
- A **path completer**: resolve the partial path with the same `~` / relative /
  absolute logic `jump_to_path.resolve` already uses, list the parent directory's
  matching entries, insert their longest common prefix, and append `/` when the
  completion is a unique directory (so descent continues — matches the
  trailing-separator prefill). A mode flag: **directories only** for jump,
  **files + dirs** for the save-as prompts.
- Render candidates when ambiguous — an extra row / small list under the field in
  the dialog (grows the modal), or cycle on repeated TAB; pick one (the ttk list
  behaviour is the reference).
- Keep it **local-first** and bounded so completion never blocks on a slow mount
  (the listing is synchronous inside the keystroke); case sensitivity per the
  platform.
- Remove the "later phase" note from `jump_to_path` once wired.
