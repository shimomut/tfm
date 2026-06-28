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

| `ttk` symbol | Source | PuiKit equivalent | Effort | Notes |
|---|---|---|---|---|
| `TextAttribute` | `ttk` / `ttk.renderer` | `puikit.TextAttribute` | **swap** | Same members/values for `NORMAL/BOLD/UNDERLINE/REVERSE`. PuiKit is an `IntFlag` (ttk: `IntEnum`) and adds `DIM/BLINK/ITALIC`. OR-able pattern preserved. |
| color pairs (`init_color_pair`, integer pair ids) | `ttk.Renderer` | `puikit.Style(fg, bg, attr, font)` + `puikit.Theme` | **adapt** | TFM's whole color model (`tfm_colors.py`) changes from registered pairs to per-draw `Style` + semantic surface roles. Covered in plan Phase 2, not a 1:1 import swap. |

### 1.2 Text / wide-char utilities

`ttk.wide_char_utils` → `puikit.text`. PuiKit covers the two core functions but
**not** the safe/fallback/pad/split family TFM relies on.

| `ttk` function | PuiKit equivalent | Effort | Notes |
|---|---|---|---|
| `get_display_width(s)` | `puikit.text.display_width(s)` | **swap** | Rename only. |
| `truncate_to_width(s, w[, ellipsis])` | `puikit.text.truncate_to_width(s, w)` | **adapt** | PuiKit signature has **no `ellipsis` arg** (ttk default `"…"`). Either extend PuiKit or wrap. |
| `safe_get_display_width` | — | **gap** | PuiKit has no "safe" variant (ttk's tolerate-bad-unicode + warn path). Likely fold into `display_width` or carry a tiny TFM helper. |
| `pad_to_width(s, w, align, fill)` | — | **gap** | No PuiKit equivalent. Carry forward (pure string op) or add to PuiKit `text`. |
| `split_at_width(s, w)` | — | **gap** | Used by `tfm_text_viewer`. Carry forward or add to PuiKit. |
| `get_safe_functions()` | — | **gap** | Returns the safe-function bundle; a TFM-internal convenience. Retire in favor of direct calls. |
| `initialize_wide_char_utils(...)` | — | **gap** | Global unicode-mode init (`tfm_main` startup). PuiKit has no global mode; review whether still needed. |

> **Decision needed (plan §9 Q3):** push the missing helpers (`pad_to_width`,
> `split_at_width`, ellipsis-aware truncate, safe widths) **into PuiKit's `text`
> module** (general, reusable) vs. keep a small `tfm.textutil` shim. Recommend
> upstreaming the pure ones; they're broadly useful and keep TFM thin.

### 1.3 Events

ttk's multi-class, scancode-centric model → PuiKit's single `Event` dataclass
with `EventType` and **symbolic string keys**. This is the largest *adapt*.

| `ttk` symbol | Source | PuiKit equivalent | Effort | Notes |
|---|---|---|---|---|
| `KeyEvent` | `ttk` / `ttk.input_event` | `puikit.Event` (`type == EventType.KEY`) | **adapt** | One unified event type; handlers branch on `event.type`. |
| `CharEvent` | `ttk` / `ttk.input_event` | `puikit.Event` (KEY with `event.char`) | **adapt** | PuiKit carries the printable char on the same KEY event (`event.char`); no separate char event. IME text arrives via `EventType.IME_COMPOSITION`. |
| `KeyCode` (enum: `ENTER`, `UP`, `A`, …) | `ttk` / `ttk.input_event` | `event.key` **strings** (`"enter"`, `"up"`, `"a"`) | **adapt** | No enum. Every `event.key_code == KeyCode.X` → `event.key == "x"`. Affects all key handlers **and** the key-binding config parser (`tfm_config.py`, `_config.py`). |
| `ModifierKey` (enum) | `ttk` | `event.modifiers` (`frozenset[str]`, e.g. `{"shift","ctrl"}`) | **adapt** | Membership test instead of bitmask/enum. |
| `SystemEvent` / `SystemEventType` | `ttk` | `puikit.Event` (`EventType.RESIZE`, …) | **adapt** | Resize etc. fold into the unified event stream. |
| `MenuEvent` | `ttk` | `puikit.menu.Menu` item `on_select` callbacks | **adapt** | Menu selection is a callback on the `Menu`/`MenuItem`, not an event class. |
| `EventCallback` (interface w/ `on_key_event`, …) | `ttk` | `Backend.run_event_loop(handler)` single handler | **adapt** | One `def on_event(event)`; routing/focus handled by `Panel.dispatch_event`. The `FileManagerCallback` class in `tfm_main` collapses. |

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
| `tfm_config.py` / `_config.py` | `KeyCode`, `ModifierKey` | logic | **Key.** Key-binding parser maps config strings → `KeyCode`. Re-target to PuiKit string keys + `modifiers`. Unblocks every key handler. |
| `tfm_text_layout.py` | `get_display_width`, `truncate_to_width` | logic | Swap to `puikit.text`; resolve ellipsis-truncate gap. |
| `tfm_colors.py` | `TextAttribute` (lazy) | logic→theme | Swap `TextAttribute`; full color-pair→Theme rework is Phase 2. |
| `tfm_logging_handlers.py` | `TextAttribute` (lazy) | logic | Swap. |
| `tfm_archive_operation_task.py` | `KeyEvent`, `KeyCode` (lazy) | logic | Adapt — small; only for an input prompt path. |
| `tfm_single_line_text_edit.py` | events + wide-char | UI→replaced | Superseded by `puikit.widgets.TextEdit`; no port, just delete after rewire. |
| `tfm_main.py` | the full set (events, wide-char, mouse, backends) | UI | Largest. The `EventCallback` class and direct-draw code dissolve into Panel + widgets (Phase 2). |
| dialogs: `tfm_base_list_dialog`, `tfm_list_dialog`, `tfm_info_dialog`, `tfm_about_dialog`, `tfm_drives_dialog`, `tfm_search_dialog`, `tfm_batch_rename_dialog`, `tfm_quick_choice_bar`, `tfm_quick_edit_bar`, `tfm_candidate_list_overlay` | events + wide-char + `TextAttribute` + `MouseEventType` | UI | Rewritten as `push_layer` widgets (Phase 3); not import-swapped. |
| viewers: `tfm_text_viewer`, `tfm_diff_viewer`, `tfm_directory_diff_viewer` | events + wide-char (`split_at_width`) + `MouseEventType` | UI | Rewritten (Phase 4). |

---

## 3. Compatibility-shim strategy for Phase 1

To let the **logic** modules (§3.1 of the plan) drop `ttk` *before* the UI is
ported, introduce a tiny internal module — `src/tfm_text_compat.py` (working
name) — that re-exports the text helpers from `puikit.text` and provides the
handful of **gap** functions (`pad_to_width`, `split_at_width`, ellipsis-aware
`truncate_to_width`, `safe_get_display_width`) until they're either upstreamed
to PuiKit or confirmed unnecessary. Logic modules import from there, not `ttk`.

Events/keys are **not** shimmed: the key-binding layer (`tfm_config`) is
re-targeted to PuiKit string keys directly, because a faithful `KeyCode` shim
would just preserve the model we're replacing.

### Suggested Phase-1 order

1. `tfm_text_compat.py` shim + resolve which gap helpers upstream to PuiKit.
2. `tfm_text_layout.py`, `tfm_colors.py`, `tfm_logging_handlers.py` → compat
   imports (`TextAttribute`, widths). Run logic tests.
3. `tfm_config.py` / `_config.py` key model → PuiKit string keys + `modifiers`.
   This is the gate for all later phases; do it deliberately, with tests.
4. `tfm_archive_operation_task.py` lazy event import → adapt.
5. Verify: `grep -rn "import ttk\|from ttk" src/` shows only UI files left
   (dialogs/viewers/`tfm_main`), which Phases 2–4 rewrite.
