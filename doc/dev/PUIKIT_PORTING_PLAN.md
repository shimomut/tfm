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

### 2.4 File / archive operations: threading, progress, cancellation, conflict resolution
The port did **not** reuse the ttk four-layer operation framework
(`BaseTask` + `FileOperationTask` / `Executor` / `UI` and the `ArchiveOperation*`
trio). Instead it **reimplemented copy / move / delete and archive create /
extract inline and synchronously** on `TfmApp`:

- copy / move → [`tfm.py` `_transfer()`](../../tfm.py) — conflict check, a
  `show_message_box` confirm, then a synchronous `run()` closure calling
  `Path.copy_to` / `Path.move_to`.
- delete → `delete_files` / `_delete_path` (recurse + `unlink` / `rmdir`).
- archive → `create_archive` / `_write_archive` / `_extract_archive` (stdlib
  `zipfile` / `tarfile`).

The heavy lifting — directory recursion and cross-storage (S3 / SSH) transfer —
is delegated to the storage-agnostic `Path` API (`tfm_path.py`), which the port
reuses unchanged. That is why the whole task framework became orphaned; it now
lives under **`legacy/src/`** (`tfm_file_operation_*.py`, `tfm_archive_operation_*.py`,
`tfm_base_task.py`) as **reference only** — consult it for the state-machine /
executor design when building the items below, but the port does not import it.
`tfm_progress_manager.py` / `tfm_progress_animator.py` remain live in `src/` but
the operation path does not currently wire into them.

Four capabilities the inline reimplementation dropped, to build back. **Three of
the four (threading, progress UI, cancellation) landed for copy / move / delete
in `tfm_file_operations.py` (the "Added progress dialog" commit); only conflict
resolution remains, and archive operations are not yet wired through the same
path.**

- **Threading** — DONE for copy / move / delete: the work runs on a daemon
  `tfm-op-*` thread driving a `ProgressManager`, and a per-frame tick pops the
  dialog + fires `on_complete` on the main thread (`_run`). Tests keep the
  synchronous inline path (`background=False`). *Archive create / extract still
  run synchronously on the UI thread.*
- **Progress UI** — DONE: `ProgressDialog` (`tfm_file_operations.py`) built on
  PuiKit's `ProgressBar`, reading the shared `ProgressManager` state during its
  own `draw` (item %, current item, byte progress via
  `update_file_byte_progress`). *Not yet: a second dedicated per-file byte bar /
  `BusyIndicator` fallback — currently the one determinate bar.*
- **Cancellation** — DONE: a `threading.Event` cancel flag the worker polls
  between items, set by `Esc` (`on_cancel=cancel.set`). *Not yet: a visible
  "cancelling…" state / a Cancel button (only `Esc`).*
- **Conflict resolution** — STILL the collapsed batch-wide three-button prompt
  (Overwrite / Skip existing / Cancel → a single `overwrite` bool for the whole
  batch, `_transfer`/`_run`). Restore richer per-conflict resolution (overwrite /
  skip / rename, with an "apply to all remaining" option), as the ttk
  `FileOperationUI` / `ArchiveOperationUI` offered, interleaved with the
  background execution. **This is the main remaining §2.4 work; §2.11 (keep both)
  folds into it.**

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

### 2.9 "Compare and select" (ttk `W` key)
Port the ttk **compare-selection** feature. The binding already exists —
`_config.py:147` `'compare_selection': ['W']` — but there is **no handler** in
`tfm.py` for it. Legacy behavior (`show_compare_selection` in
`legacy/src/tfm_list_dialog.py`): a small menu of three criteria —
**By filename**, **By filename and size**, **By filename, size, and timestamp** —
then it **marks** every active-pane entry that has a same-named, **same-type**
(file-vs-dir) counterpart in the other pane matching the chosen criteria (size
equal; mtime within 1s), after clearing the current selection, and logs a
summary (files / dirs counts). Names are NFC-normalised before comparison and
`stat()` is called only on name-matches (cheap).

Port shape:
- Add a `compare_selection` handler dispatched from the keymap; open the ported
  searchable list picker (the favorites/drives/programs/jump dialog) with the
  three criteria.
- On choice, run the comparison against the **inactive** pane's entries and set
  the active pane's `selected_files` (the same selection set the file ops read);
  `render()` + log the summary.
- Guard when the other pane is virtual (search results / archive) — no real
  listing to compare against — as the other cross-pane ops do.

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

### 2.11 Conflict resolution: "keep both" (auto-rename to a free name)
Add a conflict-resolution choice that writes the source under a new,
non-colliding name (`foo (1).txt`, then `foo (2).txt`, …) instead of overwriting
or skipping. Refines §2.4's conflict-resolution bullet.

Today (`tfm_file_operations.py`): the conflict prompt is Overwrite / Skip
existing / Cancel, collapsed to a single `overwrite` **bool** for the whole
batch; `_run` does `dest = dest_dir / t.name` and, when `dest.exists() and not
overwrite`, just increments `skipped`. There is **no** unique-name helper in the
port.

To build:
- A helper `_unique_dest(dest_dir, name)` that returns the first free name,
  inserting ` (N)` **before the extension** for files (`foo (1).txt`) and
  appended for directories / extension-less names (`foo (1)`), incrementing N.
- A new prompt button ("Keep both" / "Rename") on the conflict dialog.
- Widen the batch policy from the `overwrite` bool to a small mode
  (overwrite / skip / keep-both), threaded through `_transfer` → `_run`; on
  keep-both, per-target `dest = self._unique_dest(dest_dir, t.name)` and copy /
  move there (never `overwrite=True`).
- Fold into the richer **per-conflict** resolution §2.4 calls for (per-file
  choice + "apply to all remaining"), so keep-both is one of the per-conflict
  options, not only a batch-wide one.

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
