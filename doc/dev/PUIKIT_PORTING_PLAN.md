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

### 2.4 Draw the tree disclosure indicator as a vector chevron in GUI
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

### 2.5 Directory Diff Viewer — add content margins
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

### 2.6 Markdown for file-operation confirmation dialogs
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

### 2.7 Archive virtual-directory browsing — DONE
Enter on a `.zip` / `.tar.*` browses it in the pane as a directory (navigate
in/out, view files, copy files/dirs out); the header shows `[archive.zip]/sub`;
writes into/within an archive are refused (read-only).

Implemented as **real `archive://…#` paths**, not the `pane["virtual"]` feed the
note originally suggested: `ArchivePathImpl` (`tfm_archive.py`) already implements
the full `Path` interface (`iterdir` / `is_dir` / `read_bytes` / `.parent`), so
`compute_listing` lists it, `_open`/`_go_parent` navigate it, and the text viewer
+ cross-storage copy read it — all unchanged. The only new code (all in `tfm.py`):
an `_open` branch that wraps a recognised archive file as `archive://{abs}#`
(skipping nested archives), the `_archive_header_label` formatter in
`PaneHeader.draw`, an `_is_archive` predicate, and read-only guards on
`_transfer` / create / rename / delete / archive / extract. Covered by
`test/test_tfm_app_archive_browse.py`. Not done (intentional): writing back into
archives, nested-archive entry, archive create/extract from *within* an archive.

### 2.8 Color theme brush-up (file types, cursor, syntax)
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

### 2.9 Filepath TAB completion in input dialogs
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

### 2.10 macOS app bundle — port the build system from ttk to PuiKit
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

### 2.11 Wire GUI fonts from config — docs + config-key sweep
**Status: essentially DONE** — GUI renders a configurable proportional UI face by
default and a configurable mono face for aligned content, both from `~/.tfm/config.py`
(`main` passes `base_font`/`ui_font` gui-gated in `backend_kwargs`; PuiKit's
`resolve_font` routes an unnamed `Font()` to `ui_font` and an unnamed
`Font(monospace=True)` to the mono `base_font`). Only the config-key/doc sweep and an
optional decision remain.

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

**The load-bearing constraint:** the base font (grid grounding) must be monospaced — a
proportional base would make the grid path force every glyph into a fixed base-unit
cell. But "default proportional" needs no drawing convention on TFM's side: the Panel
already substitutes `Font()` for `font=None` on GUI (above), so the mono base font stays
the invisible grid grounding while ordinary text flows proportionally on its own.

**TUI has no font feature:** curses has one terminal font; family and size are ignored
and everything folds to the grid. Gate all of this on the `gui` backend.

Remaining:
- **`MONO` mismatch — auto-fixed.** Because an unnamed `Font(monospace=True)` now
  resolves to `base_font`'s family, the size/date/viewer/diff columns follow
  `DESKTOP_MONO_FONT_NAME` with no per-site edits. Dropping the redundant `MONO`
  constants is optional cleanup; **do not** give a grid mono font a `family` (fails
  `_is_grid_font` → flow path → de-aligned columns, the `#62` case).
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
