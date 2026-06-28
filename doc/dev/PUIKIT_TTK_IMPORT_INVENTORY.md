# Phase 1 — `ttk` → PuiKit import inventory

Status: **reference** (input to Phase 1 of [PUIKIT_PORTING_PLAN.md](PUIKIT_PORTING_PLAN.md))
Last updated: 2026-06-28

Every `ttk` symbol imported anywhere in `src/`, with its PuiKit equivalent and
the migration shape. Generated from `grep -rn "import ttk\|from ttk" src/`.

Legend for **Effort**:
- **swap** — mechanical rename/import change, semantics identical.
- **adapt** — semantics differ; call sites need rewriting (not just the import).
- **gap** — no PuiKit equivalent; needs a carried-forward helper or a shim.

---

## 1. Symbol mapping table

### 1.1 Rendering / style

> **Altitude note — these are widget-internal, not app-level.** `ttk` and PuiKit
> sit at *different abstraction levels*. With `ttk`, TFM's app/controller called
> `draw_text`/`init_color_pair` directly. With PuiKit, **only widgets draw**, and
> they draw through `DrawContext` — `ctx.draw_text(style=Style(attr=…))`,
> `ctx.measure_text(…)`. So `TextAttribute`, `Style`, and width measurement
> belong **inside the custom widgets** (`FilePane`, `SyntaxTextView`, diff views),
> not in controller/business-logic code. Inside a widget the preferred tool is
> usually `ctx.measure_text` (correct on GUI proportional fonts); raw
> `display_width` is only for monospace grid-cell counting.

| `ttk` symbol | Source | PuiKit equivalent | Effort | Notes |
|---|---|---|---|---|
| `TextAttribute` | `ttk` / `ttk.renderer` | `puikit.TextAttribute` (via `Style.attr`) | **swap (widget-internal)** | Same members/values for `NORMAL/BOLD/UNDERLINE/REVERSE`. PuiKit is an `IntFlag` (ttk: `IntEnum`) and adds `DIM/BLINK/ITALIC`. Used only when a widget builds a `Style`. |
| color pairs (`init_color_pair`, integer pair ids) | `ttk.Renderer` | `puikit.Style(fg, bg, attr, font)` + `puikit.Theme` | **adapt** | TFM's whole color model (`tfm_colors.py`) changes from registered pairs to per-draw `Style` + semantic surface roles. Covered in plan Phase 2, not a 1:1 import swap. |

### 1.2 Text / wide-char utilities

`ttk.wide_char_utils` → `puikit.text`. **Most of this family should NOT become a
TFM shim.** These functions exist in `ttk` because TFM hand-rendered a character
grid; in PuiKit the same needs are met by the **layout system, the widget's draw
logic, and PuiKit's `text` module** — and some (`pad_to_width`) are actively
*wrong* on GUI proportional fonts. Each splits into one of three destinations:

| `ttk` function | Destination | Effort | Notes |
|---|---|---|---|
| `get_display_width(s)` | `puikit.text.display_width(s)` | **swap** | Rename. Grid-cell width; widgets prefer `ctx.measure_text` where a font is involved. |
| `truncate_to_width(s, w[, ellipsis])` | **enhance PuiKit `text`** | **upstream** | PuiKit's `truncate_to_width(s, w)` has no `ellipsis` arg and is grid-based. Add a measure-aware, ellipsis-capable truncate to `puikit.text` (general & backend-correct), rather than wrapping it in TFM. |
| `pad_to_width(s, w, align, fill)` | **widget/layout (drop)** | **drop** | Space-padding to align columns **breaks on GUI proportional fonts**. The FilePane widget aligns columns by *positioning* (`ctx.fill_rect` background + measured `ctx.draw_text` at an x-offset), exactly like PuiKit's `draw_list_row`. Not a text util at all. |
| `split_at_width(s, w)` | **widget (`wrap_text`/ScrollView)** | **drop** | Used by the text viewer for h-scroll/wrap. Handled inside `SyntaxTextView` via `puikit.text.wrap_text` / scroll offset, not a carried util. |
| `safe_get_display_width` / `get_safe_functions` | **harden PuiKit `display_width`** | **drop** | ttk's tolerate-bad-unicode + warn wrappers. PuiKit's `display_width` should simply be robust; if a real input breaks it, fix it upstream. No TFM "safe" layer. |
| `initialize_wide_char_utils(...)` | **drop** | **drop** | ttk global unicode-mode init. PuiKit has no global mode and shouldn't; remove from TFM startup. |

> **Net:** one **PuiKit enhancement** (measure-aware truncate-with-ellipsis),
> possibly one **PuiKit hardening** (robust `display_width`), and the rest become
> **widget/layout responsibilities** inside the custom widgets. The
> `tfm_text_compat.py` shim proposed in an earlier draft is **dropped** — it would
> just re-import the grid-era model we're replacing.

### 1.3 Events — **compare first; likely enrich PuiKit, do not adapt TFM down**

This is **not** a simple "adapt TFM to PuiKit" item. TFM/ttk's keyboard model is
**battle-tested across ~80 keybindings with modifiers and case rules**; PuiKit's
event model is **unverified for real keyboard-driven control** (it has driven the
demo catalog's mouse/focus flows, not a full keymap). The proven spec is TFM's;
the work is to **define and verify PuiKit's keyboard contract by importing ttk's
concepts**, then port TFM's matcher onto it. TFM is the verification PuiKit lacks.

**The vocabularies already match.** `ttk.KeyCode` is a **`StrEnum`** whose values
are exactly `"a"`, `"enter"`, `"page_up"`, … — the same strings PuiKit puts in
`event.key`. So this is about *modifier/case semantics*, not the key names.

| Aspect | ttk (proven) | PuiKit (current, unverified) | Gap to close |
|---|---|---|---|
| Key identity | `KeyCode` StrEnum (`"a"`, `"enter"`) | `event.key` string (same values) | none — vocabularies align |
| Letter + Shift | `KeyCode.A` + `ModifierKey.SHIFT`; `"A"`(=a) distinct from `"Shift-A"` | curses folds case **into the char**: `'A'` → `key="A"`, **no** shift modifier | **PuiKit can't express "Shift-A" as a modifier today.** Pick & document one contract (e.g. lowercase key + `shift` modifier) and implement on every backend. |
| Modifiers | `ModifierKey` bitflags: SHIFT/CONTROL/ALT/COMMAND | `event.modifiers` frozenset (`{"shift","ctrl","alt","cmd"}`) | frozenset is fine/cleaner; **but Command/Alt across letters is untested** on PuiKit GUI backends. |
| Punctuation | matched on `char`, case-sensitive, modifier-agnostic | `event.char` present on KEY events | align matcher; confirm PuiKit sets `char` consistently |
| Char vs key | separate `CharEvent` | char rides the KEY event (`event.char`); IME via `IME_COMPOSITION` | reconcile in matcher |

| `ttk` symbol | PuiKit equivalent | Effort | Notes |
|---|---|---|---|
| `KeyEvent` / `CharEvent` | `puikit.Event` (KEY; char on `event.char`) | **adapt** | Unified event; matcher branches on `event.type`. |
| `KeyCode` (StrEnum) | `event.key` strings (same values) | **swap-ish** | Same vocabulary; keep TFM's name→key mapping, source from `event.key`. |
| `ModifierKey` (bitflags) | `event.modifiers` (`frozenset[str]`) | **adapt + verify** | Bitmask→set is mechanical; the *coverage* (Command/Alt/Shift on all backends) is the unverified part. |
| `SystemEvent` / `SystemEventType` | `EventType.RESIZE`, … | **adapt** | Folds into the unified stream. |
| `MenuEvent` | `Menu`/`MenuItem` `on_select` callbacks | **adapt** | Selection is a callback, not an event. |
| `EventCallback` (interface) | `run_event_loop(handler)` + `Panel.dispatch_event` | **adapt** | One `on_event(event)`; `FileManagerCallback` collapses. |

> **Recommended approach:**
> 1. Treat TFM's `_parse_key_expression` / `_match_key_event` as the spec.
> 2. **Decide PuiKit's keyboard contract** for the Shift/case question and rich
>    modifiers, importing ttk's `ModifierKey` semantics into PuiKit's frozenset
>    model; document it in `puikit` and implement consistently per backend.
> 3. Port TFM's matcher onto `(event.key, event.modifiers)` — it already keys on
>    exactly that pair; only the field source and the case contract change.
> 4. **Verify with TFM's real keymap** on curses + macOS (+ Windows). Upstream
>    any modifier-normalization that belongs in PuiKit.

### 1.4 Mouse

| `ttk` symbol | Source | PuiKit equivalent | Effort | Notes |
|---|---|---|---|---|
| `MouseEventType` (enum) | `ttk.ttk_mouse_event` | `EventType.MOUSE_DOWN/UP/CLICK/DRAG/MOVE/SCROLL` | **adapt** | PuiKit's Panel owns the press→click gesture; widgets handle `MOUSE_DOWN` (drag-select) or `MOUSE_CLICK` (activate). |
| `transform_grid_to_screen` | `ttk.ttk_mouse_event` | — (Panel routes in widget-local coords) | **gap→drop** | Coordinate transforms are the Panel's job; per-widget events arrive already translated (`Event.translated`). Drop the manual transform. |

### 1.5 Backends / entry point

| `ttk` symbol | Source | PuiKit equivalent | Effort | Notes |
|---|---|---|---|---|
| `CursesBackend` | `ttk.backends.curses_backend` | `puikit.backends.curses_backend.CursesBackend` | **adapt** | Different constructor/API (`Backend.open()`, `Panel(backend)`). Entry-point rewrite in `tfm_main.main`. |
| `CoreGraphicsBackend` | `ttk.backends.coregraphics_backend` | `puikit.backends.macos_backend.MacOSBackend` | **adapt** | Renamed + new API. Plus a **new** `WindowsBackend` option. |
| `ttk_coregraphics_render` (C++ ext) | top-level | (internal to `MacOSBackend`) | **drop** | PuiKit owns its compiled layer; TFM no longer imports it. |
| `tfm_backend_selector.select_backend` | `src/` | rewrite around PuiKit backends | **adapt** | TFM-side selector updated for the new backend set. |

---

## 2. Per-file impact

Ordered roughly by how much the file changes. "logic" = §3.1 reuse module (goal:
zero `ttk` after Phase 1); "UI" = rewritten in later phases anyway.

| File | Imports | Class | Phase-1 action |
|---|---|---|---|
| `tfm_config.py` / `_config.py` | `KeyCode`, `ModifierKey` | logic | **Key & gating.** Keep TFM's matcher (the proven spec). First **decide/verify PuiKit's keyboard contract** (§1.3), then source `(key, modifiers)` from `puikit.Event`. Same key-name vocabulary; the Shift/case + rich-modifier contract is the real work. |
| `tfm_text_layout.py` | `get_display_width`, `truncate_to_width` | logic | `display_width` → swap; ellipsis truncate → **PuiKit `text` enhancement** (§1.2), not a TFM wrapper. |
| `tfm_colors.py` | `TextAttribute` (lazy) | logic→theme | Swap `TextAttribute`; full color-pair→Theme rework is Phase 2. |
| `tfm_logging_handlers.py` | `TextAttribute` (lazy) | logic | Swap. |
| `tfm_archive_operation_task.py` | `KeyEvent`, `KeyCode` (lazy) | logic | Adapt — small; only for an input prompt path. |
| `tfm_single_line_text_edit.py` | events + wide-char | UI→replaced | Superseded by `puikit.widgets.TextEdit`; no port, just delete after rewire. |
| `tfm_main.py` | the full set (events, wide-char, mouse, backends) | UI | Largest. The `EventCallback` class and direct-draw code dissolve into Panel + widgets (Phase 2). |
| dialogs: `tfm_base_list_dialog`, `tfm_list_dialog`, `tfm_info_dialog`, `tfm_about_dialog`, `tfm_drives_dialog`, `tfm_search_dialog`, `tfm_batch_rename_dialog`, `tfm_quick_choice_bar`, `tfm_quick_edit_bar`, `tfm_candidate_list_overlay` | events + wide-char + `TextAttribute` + `MouseEventType` | UI | Rewritten as `push_layer` widgets (Phase 3); not import-swapped. |
| viewers: `tfm_text_viewer`, `tfm_diff_viewer`, `tfm_directory_diff_viewer` | events + wide-char (`split_at_width`) + `MouseEventType` | UI | Rewritten (Phase 4). |

---

## 3. Phase-1 strategy (no TFM compat shim)

An earlier draft proposed a `tfm_text_compat.py` shim; it is **dropped**. The
text helpers split cleanly into PuiKit enhancements vs. widget responsibilities
(§1.2), and the event model is a *contract* question, not a re-import (§1.3).
Carrying a shim would preserve the grid-era model we're replacing.

Two pieces of work feed Phase 1, both partly **in PuiKit**:

- **PuiKit text:** add measure-aware truncate-with-ellipsis; harden
  `display_width` if needed. Small, general, upstreamable.
- **PuiKit keyboard contract:** decide & document the Shift/case + rich-modifier
  semantics (importing ttk's `ModifierKey` concepts into the frozenset model),
  implement per backend, and **verify with TFM's real keymap**. This is the gate
  for every later phase.

### Suggested Phase-1 order

1. **PuiKit keyboard contract** (§1.3) — decide/document/implement; this gates
   all key handling. Verify on curses first, then macOS.
2. `tfm_config.py` / `_config.py` — point TFM's existing matcher at
   `puikit.Event` `(key, modifiers)`; run config + keybinding tests.
3. **PuiKit text** enhancement (ellipsis truncate); then `tfm_text_layout.py`,
   `tfm_colors.py`, `tfm_logging_handlers.py` → `puikit.text` / `Style.attr`.
   Run logic tests.
4. `tfm_archive_operation_task.py` lazy event import → adapt.
5. Verify: `grep -rn "import ttk\|from ttk" src/` shows only UI files left
   (dialogs/viewers/`tfm_main`), which Phases 2–4 rewrite as widgets.
