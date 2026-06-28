# TFM → PuiKit Porting Project Plan

Status: **draft / living document**
Branch: `puikit-port`
Last updated: 2026-06-27

---

## 1. Goal

Replace TFM's rendering/UI foundation, currently built on the in-repo **`ttk`**
toolkit, with **[PuiKit](https://github.com/...)** — a capability-based UI
framework that runs the *same* widget code on TUI (curses), macOS, and Windows
backends, with Web/Linux/mobile planned.

PuiKit's own design document already names **tfm as its first real user** and
ships `examples/file_manager/` as a planned canonical example. This project
makes that real: TFM becomes a PuiKit application.

### What success looks like

- TFM runs on the curses backend and the macOS backend through PuiKit, with no
  `ttk` import remaining in `src/`.
- The macOS build additionally gains a real native window experience (native
  menus, drag-out, proportional fonts where it makes sense) for free from
  PuiKit's GUI backends, plus a path to a **Windows** build that `ttk` never had.
- Feature parity on the things that matter (see §3). The UI may be
  **redesigned** where a PuiKit-native approach is cleaner — pixel-perfect
  reproduction of the current curses screen is a non-goal.

### Explicit non-goals

- Preserving the `ttk` library (it is the predecessor; PuiKit supersedes it).
- Reproducing every curses rendering detail 1:1.
- Rewriting business logic that already works (storage backends, file
  operations, search, state). We **reuse** that wherever practical.

---

## 2. Two toolkits, side by side

### 2.1 `ttk` (current)

A character-grid renderer. The app owns *everything* above raw drawing
primitives.

- `ttk.renderer.Renderer` (ABC): `draw_text`, `draw_hline`, `draw_vline`,
  `draw_rect`, `clear`, `refresh`, `init_color_pair`, `move_cursor`,
  `run_event_loop` / `run_event_loop_iteration`, plus system integration
  (`set_menu_bar`, clipboard, drag session, `suspend`/`resume`).
- Backends: `CursesBackend`, `CoreGraphicsBackend` (Python + C++ extension
  `ttk_coregraphics_render`).
- Event model: `EventCallback` with `on_key_event` / `on_char_event` /
  `on_system_event` / `on_menu_event` / `on_mouse_event`; `KeyEvent`,
  `CharEvent`, `MouseEvent`, scancode-centric.
- Color: integer **color pairs** (fg+bg RGB) registered on the backend.
- **No widget layer, no layout, no layering.** TFM hand-rolls all of it.

### 2.2 PuiKit (target)

A capability-based framework with three layers: **App/Widget → Panel/Layout →
Backend**. Apps express *intent*; the Panel resolves *how* per backend
capability. Apps never branch on capabilities.

- `puikit.backend.Backend` (ABC): `draw_text`, `draw_box`, `fill_rect`,
  `dim_rect`, `draw_scrollbar`, `draw_icon`/`draw_image` (GUI; TUI falls back),
  `measure_text`, clipboard, menus, `begin_file_drag`, `run_event_loop`.
  `Style(fg, bg, attr, font)` replaces color pairs; `TextAttribute` is an
  `IntFlag` (same OR-able pattern as ttk).
- `puikit.panel.Panel`: layout (`set_layout(VSplit/HSplit/Item)`), layering
  (`push_layer(widget, z, hints)` with `shadow`/`dim_below`), focus
  (`focus_tab`, focus chain), event dispatch (`dispatch_event`), animation
  (`animate`), menus (`set_menu_bar`, `popup_menu`), and `DrawContext` — the
  only thing widgets draw through.
- `puikit.theme.Theme`: semantic **surface roles** (`content`, `sidebar`,
  `header`, `status`) + control palette (accent, selection fills, hover tints)
  → per-backend colors. Replaces TFM's color-pair scheme system.
- Widget library (`puikit/widgets/`): `Container`, `Label`, `TextBlock`,
  `Button`, `Checkbox`, `RadioGroup`, `DropDown`, `ComboBox`, `TextEdit`
  (full IME), `ProgressBar`, `BusyIndicator`, `Splitter`, **`ListView`**,
  **`LogView`** (virtualized, tail-follow, drag-select+copy), `MarkdownView`,
  **`TreeView`**, `Tabs`, `MenuBar`/`MenuPopup`, `MessageBox`, `ScrollBar`,
  `ScrollView`, `ImageView`, `LayoutView`.
- Backends: `CursesBackend`, `MacOSBackend` (PyObjC + C++), `WindowsBackend`
  (ctypes / Direct2D / DirectWrite), `MemoryBackend` (headless tests).

### 2.3 The key structural shift

| Concern | ttk (today) | PuiKit (target) |
|---|---|---|
| Drawing | app calls `draw_text`/`draw_rect` directly | widgets draw via `DrawContext` |
| Layout | hand-computed x/y/width in `tfm_main` | declarative `VSplit`/`HSplit`/`Item` |
| Modals/dialogs | `tfm_ui_layer.UILayerStack` (custom stack) | `Panel.push_layer` |
| Color | integer color pairs + `tfm_colors` schemes | `Style` + `Theme` surface roles |
| Focus | implicit (active pane / top layer) | `Panel` focus chain + `focus_tab` |
| Menus | `tfm_menu_manager` + `set_menu_bar` dict | `puikit.menu.Menu` intent |
| Text widgets | `tfm_single_line_text_edit` | `puikit.widgets.TextEdit` |
| Scrollbars | `tfm_scrollbar` | `puikit.widgets.ScrollBar` |

**TFM already has a Panel-shaped abstraction** in `tfm_ui_layer.UILayerStack`
(a LIFO layer stack with event routing to the top layer, dirty tracking, and
full-screen detection). This is the conceptual ancestor of `Panel.push_layer`
and is the cleanest seam to cut along: the layer stack maps almost directly onto
the Panel's layer model.

---

## 3. TFM feature inventory

Grouped by how the port treats each. The doc set in `doc/*.md` is the
authoritative feature catalog; this is the porting-relevant condensation.

### 3.1 Business logic — REUSE (storage/ops; little or no `ttk` coupling)

These modules implement *what TFM does*, independent of how it draws. They are
the crown jewels and should port with minimal change.

- **Path polymorphism** — `tfm_path.py` (1577), the storage-agnostic `Path`
  abstraction. Local, **S3** (`tfm_s3.py`), **SFTP/SSH**
  (`tfm_ssh*.py` — connection, cache, config), and **archive virtual
  directories** (`tfm_archive*.py`). See `doc/dev/PATH_POLYMORPHISM_SYSTEM.md`.
- **File operations** — `tfm_file_operation_executor.py` (1301),
  `tfm_file_operation_task.py` (1029): threaded copy/move/delete, cross-storage
  move, conflict resolution, fine-grained progress, cancellation.
- **Archive operations** — `tfm_archive_operation_executor.py` (1853),
  `tfm_archive_operation_task.py`: create/extract with progress.
- **Search** — content/filename search engine behind `tfm_search_dialog`
  (threaded, cancellable, works on remote + in archives).
- **State & config** — `tfm_state_manager.py`, `tfm_config.py`, `_config.py`
  (key bindings, favorites, programs), `tfm_cache_manager.py`.
- **File monitoring** — `tfm_file_monitor_manager.py`,
  `tfm_file_monitor_observer.py` (watchdog-based auto-reload).
- **Logging** — `tfm_log_manager.py`, `tfm_logging_handlers.py`, remote log
  monitoring server.
- **Progress / FPS / tasks** — `tfm_progress_manager.py`, `tfm_base_task.py`,
  `tfm_adaptive_fps.py`, `tfm_progress_animator.py`.
- **External programs / subshell** — `tfm_external_programs.py`,
  sub-shell env injection.

> Coupling caveat: several of these import `ttk` indirectly (e.g. text width
> via `ttk.wide_char_utils`, `TextAttribute`, key codes in callbacks). PuiKit
> provides equivalents (`puikit.text.display_width`, `TextAttribute`,
> symbolic key names) — these are mechanical swaps, catalogued in Phase 1.

### 3.2 UI layer — REWRITE on PuiKit widgets

The heart of the port. Everything below is `ttk`-coupled rendering code.

**Main shell** (`tfm_main.py`, 5829 lines — the `FileManager` god-class):
- Dual-pane file list with column layout (name/size/date), color coding by
  type, selection markers, focused-item marker, incremental-search match
  highlighting, horizontal scroll, wide-char/NFD handling.
- Header (path + sort/filter indicators), status bar (dynamic key hints),
  log pane (resizable, scrollable), pane boundary adjustment.
- Main key/mouse dispatch, double-click, mouse-wheel, drag-and-drop gesture.

**Dialogs / overlays** (each a `UILayer` today → a `push_layer` widget):
- `tfm_base_list_dialog.py` → list-style dialogs base (favorites, history,
  jump, drives, programs, settings menus). Maps to **`ListView` in a dialog**.
- `tfm_list_dialog.py`, `tfm_drives_dialog.py`, `tfm_info_dialog.py`,
  `tfm_about_dialog.py`.
- `tfm_search_dialog.py` (filename/content search w/ live results +
  animation).
- `tfm_batch_rename_dialog.py` (regex rename with live preview + match
  highlighting).
- `tfm_quick_choice_bar.py` (yes/no/cancel confirmation bar) → **`MessageBox`**
  or a thin custom bar.
- `tfm_quick_edit_bar.py` (single-line prompt: rename, mkdir, filter) →
  **`TextEdit`** in a bar.
- `tfm_candidate_list_overlay.py` (tab-completion popup) → floating
  `push_layer` list, like PuiKit's `DropDown` popup.
- Help dialog (`?`).

**Viewers** (full-screen layers):
- `tfm_text_viewer.py` (1267) — syntax-highlighted text viewer (pygments),
  line numbers, h-scroll, in-viewer isearch, tab handling, remote/in-archive.
- `tfm_diff_viewer.py` (1499) — two-file side-by-side diff.
- `tfm_directory_diff_viewer.py` (4527!) — recursive directory diff, the
  single largest UI module.

**Rendering support** (replace with PuiKit equivalents):
- `tfm_colors.py` (927) — color schemes → **`Theme`** + `Style`.
- `tfm_text_layout.py` (1429) — text wrapping/layout → PuiKit `text`/`TextBlock`
  / widget measuring (keep parts that encode TFM-specific layout rules).
- `tfm_str_format.py` — size/date formatting (pure, **reuse**).
- `tfm_scrollbar.py` → `puikit.widgets.ScrollBar`.
- `tfm_single_line_text_edit.py` (1163) → `puikit.widgets.TextEdit`.
- `tfm_menu_manager.py` → `puikit.menu.Menu`.
- `tfm_ui_layer.py` (UILayerStack) → `puikit.Panel` layers.
- `tfm_pane_manager.py`, `tfm_file_list_manager.py` — pane/list state; partly
  reusable (state), partly UI (rendering moves into widgets).

---

## 4. Gap analysis — custom widgets TFM needs

PuiKit's philosophy (widget_catalog.md §2): *configure/compose existing widgets
before adding new ones.* Applying that test:

| TFM need | PuiKit answer |
|---|---|
| Confirmation bars, alerts | `MessageBox` (configure) |
| Single-line prompts (rename, mkdir) | `TextEdit` in a one-row layer |
| Tab-completion popup | floating `ListView`/`DropDown`-style popup |
| Favorites / history / drives / programs / settings | `ListView` inside a dialog layer |
| Sort / view / settings menus | `Menu` (native on GUI, widget on TUI) |
| Log pane | **`LogView`** (already does virtualize + tail + copy) |
| Scrollbars | `ScrollBar` |
| Progress feedback | `ProgressBar` + `BusyIndicator` |
| Markdown help / about | `MarkdownView` |
| Directory diff tree | `TreeView` as a base, custom row rendering |

**Genuinely new widgets to build** (no adequate existing PuiKit widget):

1. **`FilePane`** — the dual-pane core. A virtualized, columnar, selectable list
   with: per-type color coding, selection + focus markers, incremental-search
   highlighting, horizontal scroll, wide-char/NFD-aware truncation, mouse
   click/double-click/drag. `ListView` is the starting point but the column
   model, selection semantics, and search highlighting are TFM-specific. This is
   the flagship custom widget and the one to prototype first (§6, Phase 2).
2. **`SyntaxTextView`** — text viewer with pygments highlighting, line numbers,
   in-view isearch. Could extend `ScrollView` + a custom content widget; the
   highlighting → `Style` runs per line is the new part.
3. **`DiffView`** / **`DirectoryDiffView`** — side-by-side and tree diff. Large;
   likely custom, possibly sharing a two-column scroll-synced base widget.

Each new widget is proposed to PuiKit upstream where it is general enough
(`FilePane` arguably is; the diff views are TFM-specific). Decide per widget
whether it lives in `puikit/widgets/` or in TFM's app code.

---

## 5. Target architecture

```
tfm.py / entry point
  └─ selects PuiKit backend (curses | macos | windows)
       └─ Panel(backend, theme)
            ├─ set_layout( VSplit(
            │     Item(MenuBar?,    size="content"),     # GUI: native, zero-space
            │     Item(HSplit(                            # dual pane
            │        Item(FilePane(left),  weight=…),
            │        Item(FilePane(right), weight=…),
            │        divider="subtle"), weight=1),
            │     Item(LogView,     size=log_h, surface="status"),
            │     Item(StatusBar,   size="content", surface="status"),
            │  ))
            └─ push_layer(...) for dialogs / viewers / menus

  TFM "controller" (slimmed FileManager): owns panes' business state, wires
  widget callbacks to reused business logic (file ops, search, nav, config).
```

Principles:
- **Widgets render; the controller orchestrates.** The 5829-line `FileManager`
  is decomposed: rendering moves into widgets, orchestration stays in a much
  smaller controller that holds `PaneManager`/`FileListManager` state and
  dispatches actions.
- **Dialogs/viewers are `push_layer` widgets**, replacing `UILayerStack`.
- **Theme replaces color schemes.** Dark/light become two `Theme`s; the
  `toggle_color_scheme` key swaps `panel.theme`.
- **Keep business logic backend-agnostic** — it already is, mostly.

---

## 6. Phased migration strategy

Incremental, keeping a runnable app at each phase end where feasible. Validate
on **curses first** (fastest loop, no compiled deps), then macOS, then Windows.

### Phase 0 — Foundations & spike *(de-risk)*
- Stand up `examples/file_manager/` skeleton in PuiKit (or a `puikit-port`
  entry in TFM) that opens a Panel with a two-pane layout + status bar showing
  **static** content on curses + macOS. Proves the layout/theme/run-loop wiring.
- Decide repo topology (§8) and the `ttk`→`puikit` compatibility shim strategy.
- Inventory every `from ttk …` import in `src/` and map each symbol to a PuiKit
  equivalent (text width, `TextAttribute`, key names, mouse events).
- **Exit:** empty dual-pane shell runs on curses and macOS.

### Phase 1 — Decouple business logic from `ttk`
- Introduce a thin `tfm.compat` (or adopt `puikit` directly) for: display
  width, key/char/mouse event shapes, `TextAttribute`. Replace `ttk` imports in
  the **reuse** modules (§3.1) so they no longer depend on `ttk`.
- Run the existing test suite against the decoupled logic (the bulk of the
  720+ tests target business logic and should keep passing).
- **Exit:** §3.1 modules import no `ttk`; logic tests green.

### Phase 2 — `FilePane` widget + main shell
- Build the **`FilePane`** custom widget (the flagship). Wire two of them +
  header/status into the Panel layout. Hook navigation, selection, sorting,
  filtering, incremental search highlighting to reused state managers.
- Replace `tfm_colors` usage with a `Theme` (dark + light).
- Port the **status bar** (dynamic key hints) and **log pane** (→ `LogView`).
- Mouse: click/double-click/wheel/pane-focus via Panel event dispatch.
- **Exit:** browse, navigate, select, sort, filter, isearch, switch panes,
  resize panes/log on curses + macOS. No dialogs yet.

### Phase 3 — Bars, dialogs & menus
- Quick-edit bar (rename/mkdir/create-file/filter) → `TextEdit` layer.
- Quick-choice/confirmation → `MessageBox`.
- List dialogs (favorites, history, jump, drives, programs) → `ListView` layers
  on a shared dialog base.
- Sort/view/settings menus + main menu bar → `puikit.menu.Menu` (native on
  macOS, widget on curses).
- Tab-completion overlay; help & about (`MarkdownView`).
- **Exit:** all non-viewer interactions work; file operations (copy/move/delete/
  rename/mkdir) fully wired with progress.

### Phase 4 — Viewers
- `SyntaxTextView` (text viewer + isearch + highlighting).
- File diff viewer.
- Directory diff viewer (largest; budget accordingly).
- Batch rename dialog (live preview).
- Search dialogs (filename/content with live results + animation).
- **Exit:** feature parity reached.

### Phase 5 — GUI polish, Windows, system integration
- Native macOS menus, drag-out (`begin_file_drag`), clipboard rich, file
  monitoring, window geometry persistence, fonts.
- Bring up the **Windows** backend (new capability vs ttk).
- Performance pass (adaptive FPS, virtualized rendering, profiling parity).
- **Exit:** macOS + Windows + curses all shippable.

### Phase 6 — Cleanup
- Delete `ttk/` and dead UI modules. Update docs, `setup.py`/`pyproject`,
  `macos_app/` build. Migrate/retire `demo/` scripts.

---

## 7. Testing strategy

- **Business logic tests** (most of the 720+) should survive Phase 1 largely
  intact — they don't touch rendering.
- **Widget tests** run headless on PuiKit's `MemoryBackend`, identically across
  backends (PuiKit policy). New widgets (`FilePane`, viewers) get such tests.
- **Replace** `ttk`-integration tests (`test_*_ttk_integration.py`,
  CoreGraphics tests) with PuiKit-backend equivalents; retire the rest.
- Keep `demo/` as manual verification scripts, ported opportunistically.

---

## 8. Resolved decisions

- **Repo topology — DECIDED.** PuiKit stays a **separate repo**; TFM will
  eventually depend on it from **PyPI** (`pip install puikit`). During this
  project both repos are edited together, so PuiKit is installed into TFM's venv
  in **editable mode**:
  ```bash
  .venv/bin/python -m pip install -e /Users/crftwr/projects/puikit
  ```
  This resolves `import puikit` straight to the sibling source tree
  (`/Users/crftwr/projects/puikit/puikit/`), so PuiKit edits are picked up live
  with **no reinstall** — reinstall is only needed if PuiKit's package layout or
  entry points in `pyproject.toml` change, not for ordinary code edits. Add this
  to TFM's dev setup (`Makefile` `venv` target / dev requirements) so the
  editable link is reproducible.
- **Where new widgets live — DECIDED.** `FilePane` and the other TFM-specific
  widgets (`SyntaxTextView`, diff views) live in **TFM's repo**, not upstream in
  PuiKit. They draw purely through `DrawContext`, so they remain backend-
  agnostic and could be proposed upstream later if they prove general — but the
  default home is TFM.

## 9. Open questions / decisions needed

1. **PuiKit keyboard contract (gating).** PuiKit's event model is unverified for
   real keyboard-driven control; TFM's ttk-based keymap is the proven spec.
   Before porting key handling we must decide & implement PuiKit's Shift/case +
   rich-modifier semantics (Command/Alt/Shift across all backends), importing
   ttk's `ModifierKey` concepts. See
   [PUIKIT_TTK_IMPORT_INVENTORY.md](PUIKIT_TTK_IMPORT_INVENTORY.md) §1.3.
   Recommendation: keep TFM's matcher; define the contract in PuiKit; verify
   with TFM's real keymap. This is the first Phase-1 task.
2. **`FileManager` decomposition depth.** How aggressively to break up the
   5829-line god-class — full MVC split vs. pragmatic "move rendering out,
   keep an orchestrator." Recommendation: pragmatic, guided by what the Panel
   model naturally pulls apart.
3. **Theme fidelity.** Reproduce TFM's existing color schemes as `Theme`s, or
   redesign around PuiKit's surface-role palette? Recommendation: start from
   PuiKit's defaults (VS Code-like flat), port the popular schemes later.
4. **Wide-char/NFD handling.** TFM has extensive macOS NFD normalization logic.
   Confirm PuiKit's `text` module covers it or carry TFM's helpers forward.
5. **Compiled backends.** macOS C++ extension and Windows ctypes layer are
   PuiKit's responsibility; confirm they're stable enough for TFM's needs early
   (Phase 0 spike).

---

## 10. Effort shape (rough)

| Phase | Relative size | Risk |
|---|---|---|
| 0 Foundations/spike | S | low |
| 1 Decouple logic | M | low–med |
| 2 FilePane + shell | **L** | **high** (flagship widget) |
| 3 Bars/dialogs/menus | L | med |
| 4 Viewers | **XL** | high (dir-diff is 4.5k lines) |
| 5 GUI/Windows/perf | L | med |
| 6 Cleanup | S | low |

The two tentpoles are **Phase 2 (`FilePane`)** and **Phase 4 (viewers,
especially directory diff)**. Everything else is comparatively mechanical once
the Panel/widget patterns are established in Phase 2.

---

## 11. Immediate next steps

1. ~~Resolve repo topology and widget home.~~ **Done** — see §8 (PyPI dependency,
   editable install for dev; new widgets live in TFM's repo).
2. ~~Pin down the PuiKit keyboard contract **and land the backend changes**.~~
   **Done** — see [PUIKIT_KEYBOARD_CONTRACT.md](PUIKIT_KEYBOARD_CONTRACT.md).
   The contract is defined, the 5 PuiKit-side changes (curses + macOS
   shift-letter normalization, F1–F12, SPACE-as-named) are implemented, and the
   spec (`test/test_puikit_keyboard_contract.py`) passes 17/17 with PuiKit's full
   suite still green.
3. ~~Port `tfm_config`'s matcher onto the contract.~~ **Done** — `tfm_config` is
   now ttk-free; matcher rewritten to the contract triple with a transitional
   ttk-event branch so the app keeps running pre-backend-swap. 23 keybinding
   tests pass (`test/test_keybindings_puikit_contract.py` + the legacy ttk one).
4. ~~Phase 1 logic decoupling — text/colors/logging/archive-task off ttk.~~
   **Done** — `puikit.text.truncate_to_width` gained `ellipsis`; `tfm_text_layout`,
   `tfm_colors`, `tfm_logging_handlers`, `tfm_archive_operation_task` are
   ttk-free. **No logic module imports ttk** — every remaining `from ttk` in
   `src/` is a UI module (dialogs/viewers/`tfm_main`) that Phases 2–4 rewrite as
   widgets. **Phase 1 complete.**
5. ~~Phase 0/2 spike — two-pane PuiKit shell.~~ **Done (first slice).** TFM runs
   on PuiKit for the first time: `tfm_puikit.py` (entry point + `TfmApp`
   controller + `StatusBar`) hosts two custom `FilePane` widgets
   (`src/tfm_file_pane.py`) in a `VSplit(HSplit(left, right, divider), status)`
   layout. It **reuses the decoupled business logic unchanged** — `tfm_path.Path`
   for listing, `PaneManager`/`FileListManager` for pane state, `tfm_config`'s
   contract keymap for dispatch — and the input foundation just built (command
   keys, IME-gated). Working: browse, cursor up/down/page/home/end, switch pane
   (Tab), descend (Enter), go-parent (Backspace, cursor lands on origin dir),
   toggle hidden, quit; name + size columns, dirs-first sort, theme colors.
   Verified headlessly on `MemoryBackend`; runs on curses + macOS.

   **Before keyboard-input work could even start, GUI testing surfaced (and we
   fixed) four cross-backend input bugs the headless tests couldn't catch:**
   macOS punctuation-shift, the whole Windows printable path, macOS `insertText`
   letter handling, and the always-on IME (now focus-gated). See
   [PUIKIT_KEYBOARD_CONTRACT.md](PUIKIT_KEYBOARD_CONTRACT.md) §§3,5.
6. **Next: Phase 2 continued** — selection (Space, select-all) with the
   focused-item marker; remaining columns/indicators (date, sort/filter header);
   mouse (click-to-focus, wheel, double-click); then Phase 3 bars/dialogs/menus
   (a `TextEdit` quick-edit bar exercises the focus-gated text input).
6. ~~Phase 1 import inventory.~~ **Done** — see
   [PUIKIT_TTK_IMPORT_INVENTORY.md](PUIKIT_TTK_IMPORT_INVENTORY.md): every `ttk`
   symbol used in `src/` mapped to its PuiKit equivalent, with a per-file
   strategy and a suggested Phase-1 execution order.
