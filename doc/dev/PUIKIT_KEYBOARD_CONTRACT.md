# PuiKit keyboard contract (proposal + evidence)

Status: **contract implemented** — defines the keyboard semantics TFM needs
before porting `tfm_config` (plan §9 item 1; inventory §1.3).
Last updated: 2026-06-28

The §3 backend changes are **landed**: the headless spec
(`test/test_puikit_keyboard_contract.py`) passes **17/17, 0 xfail**, and the
full PuiKit suite still passes (667 passed, 3 skipped on macOS). The reference
matcher tests confirm the §2 contract expresses TFM's hard bindings (`a` vs
`Shift-A`, `?`, `Shift-SPACE`, GUI-only `Cmd-Enter`). The interactive probe
(`tools/puikit_key_probe.py`) drives a real keyboard for terminal/GUI sanity
checks. **Next: port `tfm_config`'s matcher onto this contract.**

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
| `?` (Shift+/) | `("?", "?", [])` | `("?", "?", ["shift"])` | ❌ **macOS adds `shift` to punctuation** |
| `=` | `("=", "=", [])` | `("=", "=", [])` | ✅ |
| `Cmd`+`Enter` | *terminal cannot send* | `("enter", None, ["cmd"])` | ⚠️ GUI-only (OK) |
| `Alt`+`Enter` | *ESC-prefixed; unhandled* | `("enter", None, ["alt"])` | ⚠️ GUI-only (OK) |
| `F5` | **missing** (not in `_KEY_NAMES`) | **missing** (not in `_FUNCTION_KEYS`) | ❌ **F-keys absent on both** |

### Problems this surfaces

1. **Shift on letters is inconsistent.** curses: `key="A"`, no modifier. macOS:
   `key="A"`, `modifiers={"shift"}`. Neither normalizes `key` to lowercase, so a
   matcher can't reliably tell `a` from `Shift-A` the same way on both backends.
2. **Shift on punctuation is inconsistent.** macOS tags `?` with `shift`; curses
   doesn't. A matcher that compares modifier sets exactly would disagree.
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
`key` = `char` = the **literal produced character** (`"?"`, `"@"`, `"="`).
`"shift"` / `"alt"` are **not** part of the identity — the glyph already encodes
them — and the matcher **ignores** shift/alt for these. `ctrl`/`cmd` may still
appear (they don't change the glyph) and remain significant.
- Backends *may* still report `shift`/`alt` here (harmless); the **matcher**
  guarantees the contract by ignoring them for single non-letter chars.

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

Small, localized, and covered by the spec test (17 passing, 0 xfail). The full
PuiKit suite still passes (667 passed, 3 skipped on macOS).

**`puikit/backends/curses_backend.py`** — done
- `_translate_char`: uppercase ASCII letter → `Event(key=ch.lower(), char=ch,
  modifiers={"shift"})` (Rule 2); space → `Event(key="space", char=" ")`
  (named key). The `_translate` int path now delegates printable codes to
  `_translate_char`, so normalization lives in one place.
- `_KEY_NAMES`: F1–F12 added via `curses.KEY_F1…KEY_F12 → "f1"…"f12"` (Rule 1).

**`puikit/backends/macos_backend.py`** — done
- `translate_key`: letter → lowercase `key` (keep `char` as typed, keep the
  `shift` flag) (Rule 2); space → `key="space", char=" "`. Other printables keep
  the literal char as identity (Rule 3); the matcher ignores their shift/alt.
- `_FUNCTION_KEYS`: F1–F12 (`0xF704…0xF70F`) → `"f1"…"f12"` added.

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
