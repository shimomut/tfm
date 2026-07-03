# TFM → PuiKit Port

Status: **port essentially complete** — living document, tasks only.
Branch: `puikit-port` · Last updated: 2026-07-03

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
