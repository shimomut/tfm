# TFM → PuiKit Port

Status: **port essentially complete** — living document, tasks only.
Branch: `puikit-port` · Last updated: 2026-07-04

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

Four capabilities the inline reimplementation dropped, to build back:

- **Threading** — operations run synchronously on the UI thread today, so a large
  copy / delete / archive freezes the app until it finishes. Move the work onto a
  background worker (as the legacy executors did), keeping the `Path` calls but
  driving them from a thread; marshal results back to the UI thread for the
  refresh / summary.
- **Progress UI** — no visible surface during an operation. Add a modal progress
  dialog (pushed like other dialogs via the `push_layer` / `show_message_box`
  pattern) built on PuiKit's `ProgressBar`: an overall determinate bar (items
  processed / total), plus a second per-file byte bar for large / SSH copies,
  falling back to an indeterminate `BusyIndicator` when no total is known. Reuse
  `ProgressManager` for the accounting (item + byte progress, error count,
  spinner, `get_progress_segments`) rather than rebuilding it. The dialog must
  *read* the shared `ProgressManager` state during its own `draw`, never be
  mutated from the worker.
- **Cancellation** — none today. Add a Cancel button + `Esc` that set a
  cooperative cancel flag the worker polls between items (the legacy
  `BaseTask.request_cancellation()` / `is_cancelled()` pattern), showing a
  "cancelling…" state until the worker unwinds, then popping the dialog.
- **Conflict resolution** — the port collapses conflicts to a single up-front
  three-button prompt (Overwrite / Skip existing / Cancel) applied to the whole
  batch. Restore richer per-conflict resolution (overwrite / skip / rename, with
  an "apply to all remaining" option), as the ttk `FileOperationUI` /
  `ArchiveOperationUI` offered, interleaved with the background execution.

### 2.5 Make the Directory Diff Viewer scan more progressively (ttk parity) — DONE
**Done.** `_scan_worker`'s two-phase full-walk was replaced with the
breadth-first, queue-driven progressive scan described below:
`_scan_coordinator` seeds the roots' top level (items appear at once), then a
`_scanner_worker` pulls directory levels off a `_scan_q` priority queue and
inserts nodes into the shared tree as they're discovered (`_insert_children_locked`
/ `_reclassify_self_and_ancestors_locked`); a decoupled `_comparator_worker`
resolves file-content verdicts off a `_cmp_q`. `_update_priorities` re-enqueues
on-screen two-sided directories at `_PRIO_VISIBLE` on scroll / expand / collapse;
one-sided branches are scanned lazily on expand (`_PRIO_IMMEDIATE` / `_lazy_scan`).
The footer reports scan/compare queue depth + percentage. The `background=False`
synchronous full-build path is retained for tests, and the existing
`_lock` / `_dirty` / `_tick` / `request_animation_ticks` redraw loop is reused
unchanged. Covered by new tests in `test/test_directory_diff_viewer.py`
(breadth-first convergence, empty-dir classification, lazy one-sided scan,
`scan_level`, queue-progress footer).

*Original problem statement (for reference):* the ported viewer was threaded, but
its progressive model was **coarser** than the ttk original. `_scan_worker`:
scans the **whole** left tree, then the **whole** right tree, builds the entire
tree in one shot (`DiffEngine(...).build_tree()`), and only then compares files
sequentially. So on a large / slow tree the user sees only `Scanning… (N items)`
and the tree **appears all at once** after both full walks — no live top-down
growth, and no bias toward what's on screen.

**What ttk did (restore this feel)** — `legacy/src/tfm_directory_diff_viewer.py`
is queue-driven and incremental:
- `_queue_initial_scan_tasks` seeds a `scan_queue`; `_directory_scanner_worker`
  pulls one directory level, scans it, enqueues child dirs (breadth-first), and
  calls `_update_tree_node` to **insert nodes into the tree as they're
  discovered** — the tree grows level-by-level, live.
- A separate `comparison_queue` + comparator worker resolves file-content
  verdicts, decoupled from scanning.
- `ScanPriority` + `_update_priorities` push **visible / expanded** nodes to the
  front, so what the user is looking at fills in first.
- The status bar reports queue depth + a percentage (`scan_queue.qsize()` /
  `comparison_queue.qsize()` vs. their initial sizes).

**Scope of the change:**
- Replace the two-phase `_scan_worker` with the breadth-first, queue-driven
  scan + incremental `_update_tree_node` insertion (this machinery was earmarked
  "reuse" in `DIRECTORY_DIFF_PORT_PLAN.md` §2.1 but got simplified away).
- Split comparison onto its own queue; add visible-first prioritisation
  (re-prioritise on scroll / expand / collapse).
- Reuse the **existing** main-thread redraw loop as-is — the `_lock` /
  `_dirty` flag, `_tick`, and `panel.request_animation_ticks` wiring already
  work; only the worker/queue structure and the incremental tree mutation
  change. Keep the `background=False` synchronous path for tests.
- Surface scan/compare queue depth (+ %) in the status/progress line.

### 2.6 Draw the tree disclosure indicator as a vector chevron in GUI
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

### 2.7 Directory Diff Viewer — add content margins
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

### 2.8 Help dialogs for all viewers (Markdown widget)
Give every viewer a consistent, discoverable help overlay built on PuiKit's
`MarkdownView`, via the existing `show_markdown(panel, source, title=, z=)` helper
(`tfm_text_dialog.py`) — the same one the app's main `show_help` (`tfm.py:2768`)
already uses, so the chrome, scrolling, and dismissal match.

Current state per viewer:
- **Directory Diff Viewer** — has help (`_show_help`, bound to `?`) but renders a
  **plain-text** keys table through `show_message_box`. **Convert** it to
  `show_markdown` (a Markdown table / definition list), keeping the dynamic key
  labels it already derives from `KEY_BINDINGS` via `_keys_label`.
- **Text Viewer** (`tfm_text_viewer.py`) and **File Diff Viewer**
  (`tfm_diff_viewer.py`) — **no help at all**. Add a `?` case in `handle_event`
  and a `_show_help` that pushes `show_markdown` with that viewer's key map
  (scroll / search / navigation / next-diff / close, etc.).

Notes:
- Author each help as **Markdown** (headings + a key/description table) rather
  than space-padded monospace columns, so it lays out as rich text.
- Push the dialog above the viewer's own modal layer (the dir-diff viewer already
  passes `z=self._child_z`); do the same for the others so the overlay stacks on
  top of the full-window viewer.
- Prefer deriving key labels from the configured keymap (the `_keys_label` /
  `get_keys_for_action` pattern) wherever a viewer's keys are user-rebindable, so
  help stays truthful — same spirit as §2.3.

### 2.9 Markdown for file-operation confirmation dialogs
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
