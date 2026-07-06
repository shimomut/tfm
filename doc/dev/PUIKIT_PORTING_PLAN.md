# TFM → PuiKit Port

Status: **port essentially complete** — living document, tasks only.
Branch: `puikit-port` · Last updated: 2026-07-05

TFM's rendering/UI foundation has been moved off the in-repo **`ttk`** toolkit
onto **[PuiKit](https://github.com/...)**, a capability-based framework that runs
the same widget code on TUI (curses), macOS, and Windows backends. This doc
tracks what's **left**; the how/why of finished work lives in git history and the
keyboard-contract reference (§3 below).

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
  keys), pane-local filter, incremental search, theme colors.
- **Dialogs / menus** — `MenuBar` (native NSMenu on macOS, in-window strip on
  curses), message boxes, right-click context menus, the searchable
  filter-list picker (favorites / drives / programs / jump), and input dialogs
  (rename / mkdir / create), all as `push_layer` modals.
- **File operations** — copy / move / delete / rename / batch-rename, threaded
  with progress, wired through the context menu and keymap.
- **Search** — recursive filename and content (grep) search, bounded, results in
  the filter-list dialog.
- **Viewers** — text viewer (pygments, isearch), file diff viewer, directory-diff
  viewer, all ported.
- **Keyboard** — the cross-backend contract (§3) is implemented on curses /
  macOS / Windows and backed by live regression tests.
- **GUI polish** — text clips by measured width (not cell count); lines/frames
  draw as vectors in GUI mode; dialogs grow past the pane while staying
  pane-anchored; directory listing is always async so navigation never blocks.
- **edit_file / subshell** — terminal suspend/resume wired.

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

### 2.2 Windows backend bring-up
The PuiKit `WindowsBackend` exists and the keyboard contract is implemented for
it, but TFM has **never been run/tested on Windows**. Stand it up: launch, smoke-
test navigation/dialogs/viewers, fix backend-specific gaps. (New capability vs.
`ttk`, which was curses + macOS only.)

### 2.3 MenuItem shortcuts from the configured keymap
`MenuItem(..., shortcut="…")` labels in `tfm.py` (Go/File/View/… menus around
`tfm.py:971`+) are **hardcoded strings** (`"Enter"`, `"Shift-X"`, `"Cmd-Shift-C"`,
…). They drift from `KEY_BINDINGS` and ignore user rebindings. Derive each label
from the action instead: look up the bound key(s) via
`KeyBindings.get_keys_for_action(action)` and render with
`format_key_for_display()` (both already in `tfm_config.py`). Menu items that
already dispatch through `self._menu("<action>")` name their action directly;
the ones wired to bespoke callbacks need an action id (or an explicit mapping) so
the same lookup applies.

### 2.4 File operations: threading, progress, cancellation, conflict resolution — DONE
**Done.** Copy / move / delete now run through a small central task system built
fresh for PuiKit (the ttk `BaseTask` / `FileOperationTask` / `Executor` / `UI`
framework in `legacy/src/` was consulted for its *algorithms* but not imported —
its `Executor` batch API can't express per-item renames, and its UI is ttk-bound):

- **`tfm_task.py`** (new) — `Task` (`PENDING → RUNNING → DONE | CANCELLED |
  FAILED`) + `TaskManager` (central registry; `has_active()` / `active_tasks()` for
  future queued / non-modal tasks + a task UI) + a **blocking worker↔main UI
  bridge** (`Task.ask`) so an operation reads as one linear function instead of a
  state machine, + the generic `ProgressDialog` (drives off `Task` + the shared
  `ProgressManager`, so any task type reuses it).
- **`tfm_file_operations.py`** (rewritten) — `FileOperationService` submits a
  linear worker: **threaded recursive count** (files + bytes; `BusyIndicator`
  "Preparing…" phase) → **conflict resolution** → **per-file execute** with a
  determinate item bar, a **secondary byte bar**, and the current file name.
  `background=False` keeps the deterministic inline test path (conflicts resolve
  headlessly = skip).

The four rebuilt capabilities:
- **Threading** — the whole operation (count, conflict detection, IO) runs off the
  UI thread; the main thread only pumps the bridge + repaints on the tick.
- **Progress UI** — `BusyIndicator` while preparing, then a primary item
  `ProgressBar`, a **second per-file byte bar** (chunked local copies + cross-
  storage `copy_to(progress_callback=…)`), and the current file name.
- **Cancellation** — a cooperative `threading.Event` polled at per-file / per-chunk
  `checkpoint()`s; `Esc` opens a confirm box → "Cancelling…" → clean partial
  summary, dropping a partial file on mid-copy cancel.
- **Conflict resolution** — restored TTK **file-by-file** flow: detect all
  top-level conflicts up front, then a per-conflict `ConflictDialog`
  (Overwrite / Skip / **Keep both** / Cancel) with an **"apply to all remaining"**
  checkbox, resolved over the bridge before execution.

Covered by `test/test_file_operations.py` (count, `_unique_dest`, resolution +
apply-to-all, keep-both, cancel, the bridge, and background conflict/cancel with a
real `MemoryBackend`).

*Still open (separate items): archive create / extract are not yet routed through
this task path (§2.10 area); the `TaskManager` runs one modal task at a time —
background / queued execution + a task-management UI are future work.*

### 2.5 Draw the tree disclosure indicator as a vector chevron in GUI
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

### 2.6 Directory Diff Viewer — add content margins
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

### 2.7 Markdown for file-operation confirmation dialogs
The copy / move / delete confirm prompts in `tfm_file_operations.py` are built as
**plain text** with filenames and paths inlined, so the names don't stand out
from the surrounding prose:
- `delete` — `f"Delete {len(targets)} item(s)?\n{names}\nThis cannot be undone."`
  (`names` = comma-joined `t.name`).
- `_transfer` (copy / move + the conflict prompt) —
  `f"{verb} {len(targets)} item(s) to {dest_dir}?"` + a conflict-count line.

`show_message_box` already takes `markdown=True` (the archive create / extract
dialogs use it, e.g. ``f"Extract `{entry.name}` to `{target}`?"``). Do the same
here: pass `markdown=True` and rewrite the messages as Markdown so the **file
names** and **destination path** render as code spans (``` `name` ```), counts /
"cannot be undone" as bold/emphasis, and the multi-name preview as a bullet list
instead of a comma run. Keep it consistent with the archive dialogs' style.

Caveat: names can contain Markdown-special characters (`_ * [ ]` and backticks).
Code spans neutralise most, but a name containing a backtick needs escaping —
add a small helper (or reuse one) to wrap a filename safely as inline code.

### 2.8 Archive virtual-directory browsing
Let the user **enter an archive** (Enter on a `.zip` / `.tar.*`) and browse its
contents in the pane as if it were a directory — navigate in/out, view files,
extract out — rather than only create/extract as a whole (§2.4 / `create_archive`
/ `extract_archive`). The port currently has **no archive browsing** wired
(`tfm.py` only creates/extracts).

The backend already exists (ported from ttk, unhooked in the UI):
- `tfm_archive.py` — `ArchiveHandler` / `ZipHandler` (+ tar) with
  `list_entries(internal_path)`, `get_entry_info`, `extract_to_bytes` /
  `extract_to_file`, and the `ArchiveEntry` dataclass (`to_stat_result`).
- `tfm_path.py` — recognises the archive-entry URI
  `archive:///path/to/file.zip#internal/path.txt` (`get_scheme`, needs-extraction
  / caching / entry-type branches), and `archive://` is already in `tfm.py`'s
  `_REMOTE_SCHEMES`.

Wire it on top of the existing **virtual-pane** mechanism (the same
`pane["virtual"]` feed the search results use — see the header-label branch at
`tfm.py:130`+ and `_exit_virtual` / `_refresh_virtual`):
- Entering an archive sets the pane into an "archive" virtual mode carrying the
  archive path + current `internal_path`; the row list comes from
  `ArchiveHandler.list_entries(internal_path)` (async via the existing `_list_pane`
  worker, like other listings).
- Navigation updates `internal_path`; **up** from the archive root `_exit_virtual`s
  back to the real containing directory (mirrors leaving a search feed).
- Header label like the search feed's (a distinct icon + `archive.zip › sub/dir`)
  so it's clearly not a real directory.
- Opening a file extracts it (`extract_to_bytes` / a temp file) and hands it to
  the text / diff viewer; **read-only** first (no writing back into the archive);
  copy-out = extract. Reuse the entry cache in `ArchiveHandler`.
- Guard the write-side ops the way virtual panes already do (a virtual pane isn't
  a writable destination — see the `_transfer` virtual guard).

### 2.9 "Compare and select" (ttk `W` key) — DONE
**Done**, and generalised past the ttk three-way menu. Instead of the legacy
mutually-exclusive *filename / +size / +size+time* choices, each attribute is an
independent **relation** the other pane's counterpart must satisfy, which subsumes
the old menu and adds direction + content:

- **`tfm_compare_selection.py`** (new) — the pure, headless engine.
  `CompareCriteria` (`size` any/equal/differs · `mtime` any/same/newer/older ·
  `content` any/equal/differs · `include_missing` · `mode` replace/add) and
  `compute_compare_selection(current, other, criteria)` → `CompareResult`
  (`paths` + file/dir counts). Entries are joined on **NFC name + type** (a file
  never matches a same-named dir); an item is selected when every non-`any`
  relation holds (AND), and orphans are selected only with `include_missing`.
  `stat()` is called only on name-matches; content is a streaming byte compare
  that **short-circuits on a size mismatch**. `mtime` uses the ttk 1s tolerance.
- **`tfm_compare_dialog.py`** (new) — the `CompareSelectDialog` modal: a compact,
  keyboard-first list (no Tab, no buttons). Each attribute is a single-line
  `ConditionRow` — a real PuiKit `Checkbox` (enable) plus a segmented relation
  picker whose current segment is drawn with a filled highlight (`round_rect`: a
  rounded pill on vector / a block on a grid) in **color only**, never a
  font-weight change (which would reflow proportional text). **Space** toggles the
  checkbox (`any` = off), **←/→** choose the relation; **Up/Down** move focus over
  the three rows + a "Preserve current selection" checkbox (off = replace, on =
  add); **Enter** accepts, **Esc** cancels. The box height is measured from the
  rows and trimmed to fit (`_fit_height`) so there's no bottom slack on either
  backend. Orphan selection (`include_missing`) is intentionally not exposed — the
  engine still supports it.
- **`tfm.py`** — `compare_selection` handler (dispatched from the keymap `W` and a
  new **Select ▸ Compare & Select…** menu item). Stat-only criteria run inline;
  a **content** relation reads files, so it routes through the `tfm_task.py`
  worker with a cancellable progress dialog. Both panes must be real directories
  (virtual/search-results panes are blocked); the result folds into the active
  pane's `selected_files` (replace or add) with a files/dirs summary log.

Covered by `test/test_compare_selection.py` (engine relations, join, NFC,
short-circuit) and `test/test_compare_dialog.py` (app-integration: the keyboard
model — Up/Down focus, ←/→ options, Space toggle, Enter/Esc — plus
replace/preserve, cancel, and the content task path).

### 2.10 Color theme brush-up (file types, cursor, syntax)
The port's palette is thin in three places; brush them up into one coherent,
light/dark-aware scheme.

- **File / directory type colors.** `tfm_file_pane.py:411` colors rows with just
  `name_fg = theme.accent if is_dir else theme.text` — directory vs. everything
  else. Restore richer type coloring (executable, symlink, archive, image /
  media, source code, hidden, broken symlink, …) as ttk's `tfm_colors.py`
  (`get_file_color`, executables green, etc.) did. Decide the category source: an
  extension / mode → category map on the TFM side, keyed to the active theme.
- **Cursor color.** The row cursor cue is a **hardcoded red** constant in
  `tfm_file_pane.py` (`_CURSOR_*`, `_draw_cursor`) — not theme-driven and the
  same on light and dark. Promote it to a theme role (active vs. inactive pane
  variants) so it stays legible on either scheme and matches the palette.
- **Syntax highlighting.** `tfm_text_viewer.py`'s `_SYNTAX` / `_syntax_fg` is a
  **fixed VS-Code-dark** RGB map keyed by pygments token substring; it does not
  adapt to a light theme. Make it theme-aware (a light + dark token palette, or
  derive from theme roles), consistent with the rest of the UI.

Cross-cutting:
- **Where the palette lives** — the PuiKit `Theme` (`puikit/theme.py`) currently
  has **no** file-type / cursor / syntax roles (only accent / text / chrome).
  Decide: extend `Theme` with these roles (reusable, switches with the theme), or
  keep a TFM-side palette module (a revived `tfm_colors.py`) selected by the
  active scheme. Prefer whichever keeps the light/dark toggle (`toggle_color_scheme`)
  driving *all three* palettes from one switch.
- **Light + dark parity** — every new color needs both scheme values, not just a
  dark one; verify contrast on each.
- **Terminal quantization** — re-check the TUI palette on the VS Code integrated
  terminal specifically (suspected 256-color / palette quantization differs from
  Terminal.app); test there, not only in Terminal.app.

### 2.11 Conflict resolution: "keep both" (auto-rename to a free name) — DONE
**Done** (built with §2.4). `_unique_dest(dest_dir, name)`
(`tfm_file_operations.py`) returns the first free name — ` (N)` **before the
extension** for files (`foo (1).txt`), appended for directories / extension-less
names (`foo (1)`) — and **"Keep both"** is a per-conflict button in the
`ConflictDialog` (alongside Overwrite / Skip / Cancel), honoured by "apply to all
remaining" like the others. On keep-both the target copies/moves to the unique
dest (never `overwrite=True`). Covered by `test/test_file_operations.py`
(`_unique_dest` naming + `test_resolve_keep_both`).

### 2.12 Filepath TAB completion in input dialogs
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

### 2.13 macOS app bundle — port the build system from ttk to PuiKit
The `macos_app/` build system (`build.sh` + `collect_dependencies.py` +
`create_dmg.sh` + the Obj-C launcher in `macos_app/src/`) still packages the
**old ttk toolkit** and has never been rebuilt against PuiKit. `make macos-app`
will not produce a working bundle today. Stand it up so a 1.0 `.dmg` can ship.

Good news: **PuiKit is pure Python** — its macOS backend
(`puikit/backends/macos_backend.py`) is PyObjC (AppKit / Foundation / objc), with
**no compiled module**. So the whole ttk native-render path drops out; nothing new
has to be compiled, and `pyobjc` is already in `requirements.txt`.

Concrete stale points to fix:
- **Bundle PuiKit, not ttk.** `build.sh` copies `${PROJECT_ROOT}/ttk` →
  `Resources/ttk` (`build.sh:185`+, the `backends/serialization/utils` loop) — but
  `ttk/` no longer exists at the project root. Replace with a copy of the `puikit`
  package. **Decide the source:** PuiKit is an **editable** install
  (`.venv/…/__editable__.puikit-0.1.0.pth` → `/Users/crftwr/projects/puikit`), so
  `collect_dependencies.py` (site-packages walk) won't pick it up as a normal dir.
  Either copy `puikit/puikit/` from the sibling repo directly (like ttk was), or
  add it to `requirements.txt` as a path/VCS dependency and let the collector
  handle it. Prefer whatever keeps a single source of truth.
- **Drop the ttk native module.** `build.sh:230`+ copies
  `ttk_coregraphics_render.cpython-313-darwin.so` — a ttk-only compiled render lib.
  PuiKit has no equivalent; delete this whole step. (It's also ABI-stale: hardcoded
  `cpython-313` while the venv is now `cpython-314` — dead either way.)
- **Fix the launcher's ttk assumptions.** `macos_app/src/TFMAppDelegate.m` hard-
  errors if a `ttk/` dir is missing (`~:127`) and its comments/`sys.path` setup name
  ttk (`~:114`,`134`). Swap the existence check to `puikit` (or drop it); the
  `Resources` + `python_packages` `sys.path.insert`s and the `tfm.tfm_main` /
  `cli_main` import path are otherwise unchanged (tfm source still copies `src/*` →
  `Resources/tfm/`, `build.sh:171`+).
- **Bump the version.** `VERSION` defaults to `0.99` (`build.sh:104`, and the
  `Info.plist.template`); set the 1.0 string for release.

Risk to verify while standing it up: the Obj-C launcher creates its **own**
`NSApplication` and then embeds Python and calls `cli_main()`, which builds
PuiKit's PyObjC macOS backend — which *also* wants the shared `NSApp` / an
AppKit run loop. ttk's split (Obj-C owns the app, C++ `.so` only renders) may not
map cleanly onto PuiKit driving AppKit from Python. Confirm the single-process
launcher still hands control to the PuiKit event loop correctly (window shows,
menu bar is the native `NSMenu`, keyboard contract holds), or simplify the
launcher now that rendering is Python-side.

Then run the existing `macos_app/README.md` / `doc/dev/MACOS_APP_TESTING.md`
smoke tests against the rebuilt bundle, and update both docs + `build.sh`'s inline
comments (they still describe copying ttk).

### 2.14 Wire GUI fonts from config — proportional UI default + mono
`DESKTOP_FONT_NAME` / `DESKTOP_FONT_SIZE` (`src/_config.py`) are **dormant**: they
are declared and validated (`tfm_config.ConfigManager.validate_config`, itself only
ever called from tests), but nothing feeds them to the backend. `main` (`tfm.py`)
builds the GUI backend with only `frame_autosave_name`, so the macOS backend falls
back to its default base font — `Font(size=14.0, monospace=True)`, i.e. the system
mono face (SF Mono) at 14pt — and the config values never take effect. Today's GUI
is **not** running the configured Menlo 12.

PuiKit grounds the layout grid in a **base font that must be monospaced**, and
expresses per-widget faces through `Style.font` (a `puikit.Font`): `font=None` or an
unnamed `Font(monospace=True)` render on that grid, while a `Font(family=…)` renders
**proportionally** on the flow path (`puikit/docs/font_system.md` §6/§9). Missing
glyphs use the OS's native substitution — one family per font, no cascade list.

**Config shape (decided): two GUI fonts + one size.**
- `DESKTOP_UI_FONT_NAME` — **proportional**; TFM's **default** text face (file names,
  labels, prompts, dialog chrome).
- `DESKTOP_MONO_FONT_NAME` — **monospaced**; used where alignment matters (file
  size/date columns, the text viewer, diff / dir-diff). It is *also* the backend **base
  font**, so it must be monospaced.
- `DESKTOP_FONT_SIZE` — one size applied to **both**: the base unit is derived from the
  mono font at this size, and the UI font renders at the same size within those rows.

This supersedes the earlier single-`DESKTOP_FONT_NAME` plan; that key splits into the
two above (each still one family).

**The load-bearing constraint:** the base font (grid grounding) *cannot* be the
proportional one — a proportional base would make the grid path force every glyph into
a fixed base-unit cell. So "default proportional" is a **drawing convention**, not a
base-font swap: the mono font stays the invisible grid grounding, and TFM draws general
text with `Style(font=UI)` (flow / proportional) while reserving the bare `Style()` /
base grid font for aligned content. PuiKit's default `Style()` is a *grid* style, so
**every default-text draw must carry the UI font explicitly** — this is the bulk of the
work, not the wiring.

**TUI has no font feature:** curses has one terminal font; family and size are ignored
and everything folds to the grid. Gate all of this on the `gui` backend.

To build:
- **Base (mono) font.** The config is now loaded via `get_config()` in
  `TfmApp.__init__`, but the backend is created earlier in `main` — so `main` must
  also `get_config()` (cheap; the singleton is cached) to build, for the `gui`
  backend, `Font(family=config.DESKTOP_MONO_FONT_NAME, size=config.DESKTOP_FONT_SIZE,
  monospace=True)` and pass it as `base_font` in `backend_kwargs`. The macOS and Windows
  backend constructors already accept `base_font`; **curses does not** (`__init__(self,
  pointer_shape=False)`), so keep this gui-gated exactly like `frame_autosave_name`.
- **UI (proportional) font as the default.** Define a TFM-level
  `UI = Font(family=config.DESKTOP_UI_FONT_NAME, size=config.DESKTOP_FONT_SIZE)`
  (`monospace=False` → flow path) and switch the general-text draws — today a bare
  `Style()` that renders on the grid: file names/headers (`tfm_file_pane.py`) and the
  dialog chrome (`tfm_input_dialog`, `tfm_isearch_bar`, `tfm_batch_rename_dialog`,
  `tfm_progressive_search_dialog`, `tfm_filter_list_dialog`, `tfm_text_dialog`,
  `tfm_task`, `tfm_file_operations`, `tfm_compare_dialog`) — to carry `font=UI`. Because
  proportional text flows by measured width, those sites must measure with
  `ctx.measure_text(s, Style(font=UI))` wherever they currently assume a column count
  (the file pane already measures its name; the dialogs mostly left-align, so most need
  only the font, not new measuring). This is the largest piece.
- **Mono content follows `DESKTOP_MONO_FONT_NAME`.** The size/date/viewer/diff columns
  render in the mono font — which *is* the base font — so draw them on the base grid
  (`font=None`), not `MONO = Font(monospace=True)` (that hardcodes system SF Mono and
  ignores the config; once the UI/mono split lands it would be a third face). `font=None`
  and the base font are the same grid face kerned to `base_w`, so alignment / column-count
  measuring are unchanged; the columns just follow the configured mono family. **Do not**
  give a grid mono font a `family`: a `Font` with `family` set fails `_is_grid_font`,
  drops onto the flow path, and de-aligns the columns (the `#62` case in
  `macos_backend._is_grid_font`). Drop the now-redundant `MONO` constant.
- Once wired, GUI default text becomes the proportional UI font and aligned content the
  configured mono font, both at `DESKTOP_FONT_SIZE`; refresh screenshots.
- Decide whether `DESKTOP_FONT_SIZE` stays startup-only or also drives the ttk-era
  Cmd-+/Cmd-- live font-size adjustment (`doc/FONT_SIZE_ADJUSTMENT_FEATURE.md`) —
  out of scope here, but the base-font seam is where it would hook in.
- Update `src/_config.py`, `tfm_config.ConfigManager.validate_config`, and
  `test/test_config_backend_settings.py` for the two new keys (`DESKTOP_UI_FONT_NAME`,
  `DESKTOP_MONO_FONT_NAME`), replacing the interim single `DESKTOP_FONT_NAME`. Decide
  the UI default: allow `None`/empty → the OS system UI font (`Font(family=None)`), or
  ship a concrete proportional family. Mono defaults to `Menlo`.
- Sweep the docs that still show the removed cascade-list form
  (`doc/CONFIGURATION_FEATURE.md`, `doc/TFM_USER_GUIDE.md`,
  `doc/FONT_SIZE_ADJUSTMENT_FEATURE.md`, `doc/DESKTOP_MODE_GUIDE.md`) to the two-key
  form, and update the user's own `~/.tfm/config.py`.

---

## 3. Reference — PuiKit keyboard contract

The normative spec for keyboard semantics across backends. Implemented on curses,
macOS, and Windows via the shared helper `puikit.event.char_key_event`, and
asserted by `test/test_puikit_keyboard_contract.py` (per-backend translation) and
`test/test_keybindings_puikit_contract.py` (TFM's matcher on the real keymap). A
KEY event carries `key` (canonical identity), `char` (produced glyph or `None`),
and `modifiers ⊆ {"shift","ctrl","alt","cmd"}`.

**Rule 1 — Named non-text keys.** `key` ∈
`enter, escape, tab, backspace, delete, insert, up, down, left, right, home, end,
pageup, pagedown, f1…f12`; `char` is `None`; `modifiers` as detected. (PuiKit's
concatenated names — `pageup`, not `page_up` — are canonical; TFM's parser adapts.)

**Rule 2 — Letters `a`–`z`.** `key` is **always the lowercase letter**; `char` is
the literal typed glyph (`"a"`/`"A"`); `modifiers` includes `"shift"` **iff** the
shift form was produced. So **Shift-A is `key="a", modifiers={"shift"}` on every
backend.** curses *infers* `shift` from an uppercase letter and lowercases `key`;
macOS lowercases `key` while keeping its real shift flag.

**Rule 3 — Other printables (digits, punctuation, shifted symbols).**
`key = char =` the **literal produced character** (`"?"`, `"@"`, `"="`, `"!"`).
The shifted symbol *is* the identity — bind `"!"`, never `"Shift-1"`. **`shift`
must NOT appear in `modifiers`** (a GUI backend that knows shift was held drops
it, so `Shift+1` reports `("!", {})` everywhere). `alt` (Option) is **kept** (it
doesn't change the base glyph); `ctrl`/`cmd` are **kept**.

**Rule 4 — Ctrl/Cmd + letter.** `key` = lowercase letter,
`modifiers ⊇ {"ctrl"}` (or `{"cmd"}`).

**Rule 5 — Terminal limits are explicit.** curses cannot deliver `cmd`, and
`alt`/Option combos are unreliable. Bindings needing them (`open_with_os` =
`Cmd-ENTER`, `reveal_in_os` = `Alt-ENTER`) are **GUI-only** and simply never fire
on TUI.

**Matcher rules (TFM side).** A binding token resolves to `(identity,
required_mods)`:
- **letter / named-key identity:** match iff `event.key == identity` **and**
  `event.modifiers == required_mods` (exact — so `Shift-A` differs from `a`).
- **single punctuation identity:** match iff `event.char == identity`
  (case-sensitive), **ignoring** `shift`/`alt`; `ctrl`/`cmd` still significant if
  the binding names them.

> **SPACE** is a named key (`key="space"`, `char=" "` retained), so `Shift-SPACE`
> is distinguishable from `SPACE` like `Shift-A` from `a`.
>
> **Bare uppercase letters do not imply shift** — under Rule 2 a bare `'J'`
> parses to key `j` with shift *dropped* (identical to `'j'`); only `'Shift-J'`
> keeps the modifier. Alphabetical bindings are case-insensitive **by design**.

### 3.1 TFM token → identity map (in the binding parser)

| TFM token(s) | PuiKit `key` / `char` | Match on |
|---|---|---|
| `A`…`Z` | lowercase letter | `key` + mods (`Shift-` adds `shift`) |
| `ENTER, ESCAPE, TAB, BACKSPACE, DELETE, INSERT` | same lowercased | `key` + mods |
| `UP/DOWN/LEFT/RIGHT/HOME/END` | same lowercased | `key` + mods |
| `PAGE_UP / PAGE_DOWN` | `pageup` / `pagedown` | `key` + mods |
| `F1…F12` | `f1`…`f12` | `key` + mods |
| `MINUS, EQUAL, LEFT_BRACKET, RIGHT_BRACKET, BACKSLASH, SEMICOLON` | `- = [ ] \ ;` | `char` (ignore shift/alt) |
| `SPACE` | `key="space"`, `char=" "` | `key` + mods |
| punctuation literals (`?`, `.`, `:`, `;`, `{`, `}`, `[`, `]`) | the literal char | `char` |
| `Shift-X` | `x` + `shift` | `key` + mods |
| `Command-X` / `Alt-X` | `x` + `cmd`/`alt` | `key` + mods (GUI-only) |

### 3.2 Command keys vs. text input — focus-gated IME

A keypress is sometimes a **command** and sometimes **text**; a GUI's IME makes
this sharp (with a CJK source, every keystroke would otherwise start composition,
so single-letter bindings like `j`/`f`/`v` would compose instead of dispatch).
PuiKit keeps one `Event(KEY, key, char)` (+ `IME_COMPOSITION`) and gates on
**focus**:

- A text-editing widget declares `wants_text_input = True` (`TextEdit`,
  `ComboBox`). The Panel resolves the focused **leaf** each render and, on a
  transition, calls `backend.begin_text_input()` / `end_text_input()`.
- **Text widget focused** → macOS `keyDown` routes through `interpretKeyEvents`
  (insertText / IME / editing commands).
- **Anything else focused** → `keyDown` translates **directly** to a command KEY
  event and does **not** engage the IME, so `j` dispatches even under a Japanese
  input source. curses/Windows/memory backends inherit the no-op default.

`Panel.focused_leaf()` descends from the **top layer** when a modal is open, so a
`TextEdit` inside a pushed dialog engages the IME (same modal rule as event
dispatch). Covered by PuiKit's `tests/test_text_input_gating.py`.
