# Markdown Viewer — Implementation

End-user behavior: `doc/MARKDOWN_VIEWER_FEATURE.md`.

The Markdown viewer is **not** a new modal. It is a second *body renderer* inside
the existing full-window `TextViewer`, selected by file type and toggled in
place. This keeps one set of viewer chrome (header band, footer status bar,
resize/reflow, close/help) and makes future formatted viewers (JSON, CSV) a
matter of registering a renderer — no new modal, no chrome duplication.

## Pieces

### `src/tfm_viewer_registry.py` — the extensibility seam

A tiny registry mapping a file extension to an optional **rich renderer**:

```python
@dataclass(frozen=True)
class RichRenderer:
    name: str                              # shown in viewer chrome, e.g. "Markdown"
    build: Callable[..., Widget]           # build(source, *, style) -> puikit Widget

def rich_renderer_for(path) -> RichRenderer | None
```

Markdown is registered for `.md` / `.markdown`, building PuiKit's
`MarkdownView(source, style=...)`. `rich_renderer_for` returns `None` for a type
with no rendered view (the common case) — the raw text view is the universal
fallback, so an unregistered type simply has nothing to toggle to.

**Adding a viewer (JSON, CSV, …):** implement a `build(source, *, style)` that
returns a scrollable `puikit.widgets.base.Widget`, then
`register(RichRenderer("JSON", _build_json), ".json")`. Nothing else changes —
`TextViewer` picks it up through the registry and the same **M** toggle drives
it.

### `src/tfm_text_viewer.py` — raw + rich in one modal

`TextViewer` gained a small amount of state and three seams:

- `__init__`: `self._rich = rich_renderer_for(path)` (renderer or `None`),
  `self.mode` (`"text"` default — raw first, per the chosen UX), and
  `self._rich_widget` (the built widget, lazily created and cached).
- `_toggle_view_mode()`: flips `mode`. On the first switch to rich it reads the
  file source via `_read_source(path)` (backend-agnostic `tfm_path.Path`, same
  encoding ladder as `_read_lines`) and builds the renderer widget once, styled
  on the content surface colors captured by the last `draw`. The widget is
  cached, so **each mode keeps its own scroll position** across toggles. A no-op
  when `self._rich is None`; refuses (stays raw, logs) if the source can't be
  read as text.
- `draw()`: after the shared header, if `mode == "rich"` it delegates the whole
  body to `_draw_rich`, which draws the embedded widget via `ctx.draw_child(...)`
  in the area between header and footer and paints the footer's toggle-back hint.
  The renderer draws and scrolls itself (own scrollbar), so the raw gutter,
  h-scrollbar and row layout are skipped. Raw mode is unchanged.
- `handle_event()`: `quit` / `help` / the view toggle are handled in **both**
  modes. In rich mode every other key and mouse-scroll is **forwarded** to the
  embedded widget (it owns arrows / page / home / end / in-document link jumps).
  Incremental search and line wrap remain raw-text-only.

### Key binding

`toggle_view_mode` → `M`, added to `_config.py` (`M` is shared with
`move_files` / `create_directory`, which only apply in the file list; the viewer
matches its own action by name, the same pattern `toggle_wrap` uses for `W`).

Because `ConfigManager._copy_missing_fields` only merges whole **missing
attributes**, an existing user's `~/.tfm/config.py` — which already has a
`KEY_BINDINGS` dict — will **not** gain the new key automatically. So
`_view_mode_pressed()` mirrors `_wrap_pressed()`: it matches the
`toggle_view_mode` action, and, only when that action is unbound (an older
config), falls back to the literal `m` char. New/regenerated configs get `M` and
honor rebinds; old configs still get the toggle on `m`.

## Design notes / limitations

- **Why embed, not push a new layer.** The chosen UX is "toggle in place, raw by
  default." Embedding as a body renderer reuses `TextViewer`'s chrome and resize
  handling and keeps a single modal on the layer stack, so the toggle is a flag
  flip, not a push/pop.
- **Source is read twice** for a Markdown file that gets toggled (once as lines
  for the raw view in `__init__`, once as raw source on first toggle). The raw
  view is the default and most files are never toggled, so the second read is
  lazy and paid only on demand; the cost is negligible next to a modal file view.
- **Link clicks inside rendered Markdown are not wired yet.** Links *render*
  (styled/underlined) and keyboard navigation works, but `TextViewer` forwards
  events to the embedded widget without translating pointer coordinates into the
  child's local space, so `MarkdownView`'s click hit-testing (open URL / jump to
  heading) would be off. Deferred; needs the same widget-local pointer transform
  the splitter uses. Keyboard + wheel scrolling is fully functional.

## Tests

`test/test_markdown_viewer.py` (parametrized TUI + GUI profiles): the registry
mapping and plain-type fallback; a `.md` opening raw with a renderer available; a
plain file having no renderer (toggle no-op); toggle builds/caches the
`MarkdownView` and each mode keeps its scroll; the `M` key path (via the literal
fallback); both modes draw without crashing; rich-mode scroll forwarding; and
quit closing from rich mode.
