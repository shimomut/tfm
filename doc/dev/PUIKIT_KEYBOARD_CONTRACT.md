# PuiKit keyboard contract (proposal + evidence)

Status: **contract implemented (curses, macOS, Windows)** — defines the keyboard
semantics TFM needs; `tfm_config`'s matcher is ported onto it (inventory §1.3).
Last updated: 2026-06-28

The §3 backend changes are **landed on all three backends**, with the
printable-glyph rules consolidated into one shared helper
(`puikit.event.char_key_event`) so they can't drift per backend again. The
headless spec (`test/test_puikit_keyboard_contract.py`) passes (incl. a
cross-platform `char_key_event` suite that covers Windows on any OS), and the
full PuiKit suite still passes (677 passed, 3 skipped on macOS). The reference
matcher tests confirm the §2 contract expresses TFM's hard bindings (`a` vs
`Shift-A`, `?`, `Shift-SPACE`, GUI-only `Cmd-Enter`). The interactive probe
(`tools/puikit_key_probe.py`) drives a real keyboard for terminal/GUI sanity
checks.

PuiKit's event model has driven mouse/focus flows (the demo catalog) but **not a
full keyboard-driven keymap**. TFM is the first real user with ~80 bindings
spanning Shift/Ctrl/Alt/Cmd and punctuation. This document (a) records what the
two implemented backends produce **today**, (b) proposes the contract, and
(c) lists the concrete PuiKit changes required. Evidence is reproduced by
[../../tools/puikit_key_probe.py](../../tools/puikit_key_probe.py) (interactive,
real keyboard) and asserted by
[../../test/test_puikit_keyboard_contract.py](../../test/test_puikit_keyboard_contract.py)
(headless).

---

## 1. Current behavior (measured)

Driving `CursesBackend._translate_char` and `macos_backend.translate_key`
directly with synthetic input:

| Input | curses → `(key, char, mods)` | macOS → `(key, char, mods)` | Agree? |
|---|---|---|---|
| `a` | `("a", "a", [])` | `("a", "a", [])` | ✅ |
| `Shift`+`a` (→ `A`) | `("A", "A", [])` | `("A", "A", ["shift"])` | ❌ **shift modifier differs; key not normalized** |
| `Ctrl`+`a` | `("a", None, ["ctrl"])` | `("a", "a", ["ctrl"])` | ⚠️ key/mods agree; `char` differs |
| `?` (Shift+/) | `("?", "?", [])` | was `("?", "?", ["shift"])`, now `("?", "?", [])` | ✅ **fixed** — macOS drops `shift` for non-letter printables (Rule 3) |
| `=` | `("=", "=", [])` | `("=", "=", [])` | ✅ |
| `Cmd`+`Enter` | *terminal cannot send* | `("enter", None, ["cmd"])` | ⚠️ GUI-only (OK) |
| `Alt`+`Enter` | *ESC-prefixed; unhandled* | `("enter", None, ["alt"])` | ⚠️ GUI-only (OK) |
| `F5` | **missing** (not in `_KEY_NAMES`) | **missing** (not in `_FUNCTION_KEYS`) | ❌ **F-keys absent on both** |

### Problems this surfaces

1. **Shift on letters is inconsistent.** curses: `key="A"`, no modifier. macOS:
   `key="A"`, `modifiers={"shift"}`. Neither normalizes `key` to lowercase, so a
   matcher can't reliably tell `a` from `Shift-A` the same way on both backends.
2. **Shift on punctuation is inconsistent.** macOS tagged `?` / `!` with `shift`;
   curses doesn't. *(Fixed: the GUI backend now drops `shift` for non-letter
   printables — see Rule 3. This was deferred as "optional" in an earlier pass
   and resurfaced via the Keys demo: `Shift+1` showed `("!", {shift})` on GUI but
   `("!", {})` in a terminal.)*
3. **F1–F12 are missing** from both backends' key tables. TFM binds `F5`
   (redraw); other apps will want function keys.
4. **Name vocabulary differs from ttk/TFM.** PuiKit uses concatenated names
   (`pageup`, `pagedown`) and **literal punctuation** (`"["`, `"="`, `";"`);
   ttk's `KeyCode` StrEnum uses `page_up`, and TFM's config tokens are
   `PAGE_UP`, `LEFT_BRACKET`, `EQUAL`, `SEMICOLON`, … This is reconciled in
   TFM's binding parser (it already maps tokens → identities), **not** by
   changing PuiKit — but the mapping must be written down (see §3).

---

## 2. Proposed contract

A KEY event carries: `key` (canonical identity string), `char` (the printable
character produced, or `None`), `modifiers` (subset of
`{"shift","ctrl","alt","cmd"}`).

### Rule 1 — Named non-text keys
`key` ∈ the canonical set:
`enter, escape, tab, backspace, delete, insert, up, down, left, right,
home, end, pageup, pagedown, f1…f12`. `char` is `None`. `modifiers` carries
whatever the backend detects. **Keep PuiKit's existing concatenated names** —
do not churn them to ttk's underscore style; TFM's parser adapts.

### Rule 2 — Letters `a`–`z`
`key` is **always the lowercase letter**; `char` is the literal typed glyph
(`"a"` or `"A"`); `modifiers` includes `"shift"` **iff** the shift form was
produced. So **Shift-A is `key="a", modifiers={"shift"}` on every backend.**
- curses **infers** `shift` from an uppercase letter (it cannot see the physical
  modifier) and lowercases `key`.
- macOS **lowercases** `key` while keeping its real `shift` flag.

### Rule 3 — Other printable characters (digits, punctuation, shifted symbols)
`key` = `char` = the **literal produced character** (`"?"`, `"@"`, `"="`, `"!"`).
The shifted symbol *is* the identity — you bind `"!"`, never `"Shift-1"`.
- **`shift` must NOT appear in `modifiers`.** The shift is already baked into the
  produced glyph, so a backend that knows shift was held (a GUI window) **drops
  it** here, so `Shift+1` reports `("!", {})` on the GUI exactly as a terminal
  reports it (a terminal never knew shift was held). Otherwise the same keypress
  would read `("!", {shift})` on one backend and `("!", {})` on another —
  breaking the "same Event everywhere" guarantee. (macOS: `translate_key` strips
  `shift` for non-letter printables, since `charactersIgnoringModifiers` keeps
  Shift in the glyph.)
- `alt` (Option) is **kept**: `charactersIgnoringModifiers` *ignores* Option, so
  the glyph is the base character and `alt` is a genuine separate modifier
  (`Alt+1` → `("1", {alt})`).
- `ctrl`/`cmd` are **kept** (they don't change the glyph): `Shift+Cmd+1` →
  `("!", {cmd})`. The matcher honors ctrl/cmd for these and ignores shift/alt.

### Rule 4 — Ctrl/Cmd + letter
`key` = lowercase letter, `modifiers ⊇ {"ctrl"}` (or `{"cmd"}`). Already holds.

### Rule 5 — Terminal limits are explicit
curses cannot deliver `cmd`, and `alt`/Option combos are unreliable. Bindings
that require them (TFM `open_with_os` = `Cmd-ENTER`, `reveal_in_os` =
`Alt-ENTER`) are **GUI-only**; they simply never fire on TUI. Apps must not
depend on those chords on a terminal backend.

### Matcher rules (TFM side; mirrors ttk's proven logic)
A binding token resolves to `(identity, required_mods)`:
- **letter / named-key identity:** match iff `event.key == identity` **and**
  `event.modifiers == required_mods` (exact — `shift` is significant; lets
  `Shift-A` differ from `a`).
- **single punctuation identity:** match iff `event.char == identity`
  (case-sensitive), **ignoring** `shift`/`alt`; `ctrl`/`cmd` still significant if
  the binding names them.

This is exactly TFM's current `_match_key_event` distinction, now resting on a
documented PuiKit contract instead of ttk's `KeyCode`/`ModifierKey`.

---

## 3. Concrete PuiKit changes — **LANDED** ✅

The printable-glyph contract (space-as-named, letter-lowercase + Shift, Rule-3
shift-drop) lives in **one shared helper** so every backend agrees by
construction — the duplicated-per-backend version drifted (curses and macOS were
fixed first; **Windows** kept reporting `("!", {shift})` for `Shift+1` and
`key="A"` for `Shift+a` until this consolidation). Covered by the spec test (the
full PuiKit suite passes, 677 passed / 3 skipped on macOS).

**`puikit/event.py` — `char_key_event(char, modifiers)`** (the shared contract)
- space → `("space", char=" ")`; letter → lowercase `key`, `char` as typed, Shift
  kept (Rule 2); other printable → glyph identity with Shift **dropped**, ctrl/
  alt/cmd kept (Rule 3). Pure and platform-neutral, so it is unit-tested on any
  OS — including on Windows's behalf (its backend module can't import off-Windows).

**`puikit/backends/curses_backend.py`** — done
- `_translate_char`: printable path infers Shift from an uppercase letter (a
  terminal can't report it) then defers to `char_key_event`. The `_translate` int
  path delegates printable codes here too, so it lives in one place.
- `_KEY_NAMES`: F1–F12 via `curses.KEY_F1…KEY_F12 → "f1"…"f12"` (Rule 1).

**`puikit/backends/macos_backend.py`** — done
- macOS routes input through `NSTextInputClient`, so there are **two** key paths
  and both now go through `char_key_event`: typed text commits via `insertText:`
  (letters, digits, punctuation, IME), and non-text keys via
  `doCommandBySelector:` → `translate_key` (arrows, enter, …). The `insertText:`
  path was the live one for letters and originally dispatched the raw glyph
  (`Shift+A` → `("A", {})`); it now applies the contract with modifiers decoded
  from the originating key event (`_modifier_names`), so `Shift+A` → `("a", "A",
  {shift})` like every backend.
- `translate_key`: printable path defers to `char_key_event` (`charactersIgnoring
  Modifiers` keeps Shift in the glyph but drops Cmd/Ctrl/Option, so those
  survive). F1–F12 (`0xF704…0xF70F`) added.

**`puikit/backends/windows_backend.py`** — done
- `_on_char`: printable WM_CHAR path defers to `char_key_event` (fixes letters
  not being lowercased, space not named, and Shift not dropped from shifted
  glyphs). `_VK_KEYS`: F1–F12 (`0x70…0x7B`) added.

**No new event types or fields.** The contract is expressible in the existing
`Event(key, char, modifiers)` shape — it only standardizes *what backends put
there*. Note PuiKit's widgets already anticipated this: `widgets/_input.py`
`is_activate` accepts `key in ("enter","space")` and `typed_char` keys off
`event.char`, so space-as-named-key did not disturb text input.

### TFM-side token → identity map (in the binding parser, not PuiKit)
TFM's config tokens map to PuiKit identities:

| TFM token(s) | PuiKit `key` / `char` | Match on |
|---|---|---|
| `A`…`Z` (alpha) | lowercase letter | `key` + mods (`Shift-` adds `shift`) |
| `ENTER, ESCAPE, TAB, BACKSPACE, DELETE, INSERT` | same lowercased | `key` + mods |
| `UP/DOWN/LEFT/RIGHT/HOME/END` | same lowercased | `key` + mods |
| `PAGE_UP / PAGE_DOWN` | `pageup` / `pagedown` | `key` + mods |
| `F1…F12` | `f1`…`f12` | `key` + mods |
| `MINUS, EQUAL, LEFT_BRACKET, RIGHT_BRACKET, BACKSLASH, SEMICOLON` | `- = [ ] \ ;` | `char` (ignore shift/alt) |
| `SPACE` | `key="space"`, `char=" "` | `key` + mods |
| punctuation literals (`?`, `.`, `:`, `;`, `{`, `}`, `[`, `]`) | the literal char | `char` |
| `Shift-X` | `x` + `shift` | `key` + mods |
| `Command-X` / `Alt-X` | `x` + `cmd`/`alt` | `key` + mods (GUI-only) |

> **Sub-decision — `SPACE` — RESOLVED.** Space is a **named key**
> (`key="space"`, with `char=" "` retained so text fields still insert it), so
> `Shift-SPACE` (TFM select-up) is distinguishable from `SPACE` (select) like
> `Shift-A` from `a`. Implemented on both backends; PuiKit's `is_activate`
> already accepted `"space"`.

---

## 4. Verification

1. **Headless spec** — `test/test_puikit_keyboard_contract.py` encodes §2 against
   both backends' translation functions. **Passing 17/17** now that §3 landed;
   it stays as a regression guard (the matcher rules and per-backend output are
   asserted, so a future backend change that breaks the contract fails loudly).
2. **Interactive probe** — `tools/puikit_key_probe.py` opens a backend and
   prints, for each real keypress, the raw `Event`, the contract-normalized
   form, and the TFM action it matches. Run it in a real terminal (modifier
   reporting varies by emulator) and on macOS to sanity-check live input.
3. ~~Port `tfm_config`'s matcher onto the contract.~~ **DONE.**
   `_parse_key_expression` now yields `(identity, modifiers, mode)`,
   `_event_identity` reads the contract triple from a `puikit.Event` (with a
   transitional ttk-event branch so the app keeps running until the runtime is
   swapped), and `_matches` implements §2. `tfm_config` imports no `ttk`.
   Verified by `test/test_keybindings_puikit_contract.py` (14, PuiKit events,
   real default keymap) and the legacy `test_key_bindings_input_event.py` (9,
   ttk events). The transitional ttk branch is removed once the runtime emits
   PuiKit events (Phase 2).

---

## 5. Command keys vs. text input — focus-gated IME

A keyboard contract is only half the story: a key press is sometimes a **command**
(navigate a list, trigger an action, fire a shortcut) and sometimes **text** (a
character typed into a field). They must not be conflated, and a GUI's input
method (IME) makes this sharp: with a CJK input source selected, *every* keystroke
fed to the IME starts composition — so a file manager's single-letter bindings
(`j`, `f`, `v`) would compose instead of dispatch.

**How TTK did it (reference).** ttk's CoreGraphics backend kept `KeyEvent` and
`CharEvent` as *distinct* types and used a **consume-first** `keyDown`: translate
to a `KeyEvent`, offer it to the app as a command; only if **unconsumed** pass it
to `interpretKeyEvents` (→ `insertText` → `CharEvent`, or IME composition); while
composing, keystrokes bypass the app entirely. The consumption decision did the
gating — the backend never needed to know widget types.

**How PuiKit does it (chosen: focus-gated, single event type).** PuiKit keeps one
`Event(KEY, key, char)` (+ `IME_COMPOSITION`) and gates on **focus** instead:

- A widget that edits text declares `wants_text_input = True` (`TextEdit`,
  `ComboBox`). The Panel resolves the focused **leaf** (`Panel.focused_leaf`,
  descending through focus containers) every render and, on a transition, calls
  `backend.begin_text_input()` / `end_text_input()` (new `Backend` methods;
  default no-op).
- **Text widget focused** → macOS `keyDown` routes through `interpretKeyEvents`
  (insertText / IME composition / editing commands), the full text path.
- **Anything else focused** → macOS `keyDown` translates **directly** to a command
  KEY event (`translate_key(charactersIgnoringModifiers, modifierFlags)`) and does
  **not** engage the IME. So `j` dispatches as a command even under a Japanese
  input source. `end_text_input` also tears down any marked text so a half-finished
  composition can't leak into the next field.

This is more foolproof than consume-first for non-text contexts (the IME is simply
*off* there, not relying on every widget remembering to consume) and needs no new
event type — a non-text widget reads `key`+`modifiers`, a text widget reads `char`.
curses/Windows/memory backends inherit the no-op default (a terminal has no IME;
Windows IME is deferred). Covered by `tests/test_text_input_gating.py` in PuiKit
(focus transitions toggle `begin`/`end`; the leaf resolver descends into
containers).
