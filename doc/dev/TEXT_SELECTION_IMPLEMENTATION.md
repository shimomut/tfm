# Text Selection & Clipboard Copy — Implementation (TFM side)

Mouse text selection + clipboard copy in TFM's modal file viewers, with rich
(HTML) copy from the Markdown viewer. The feature spans two repos:

- **PuiKit** owns the reusable framework pieces — the `clipboard_rich` capability
  (`set_clipboard_rich`) and `MarkdownView`'s own selection + rich-HTML copy.
  Those are documented on the PuiKit side: **`puikit/docs/widget_catalog.md`**
  (the `MarkdownView` → *"Selection + copy — shipped"* entry). Don't duplicate
  that detail here.
- **TFM** owns the viewer integration described below: the raw text viewer's own
  selection, and forwarding mouse/keys to the embedded `MarkdownView` in rich mode.

## Layers

```
TextViewer (tfm_text_viewer.py)         ← modal, full-window
├── raw text mode  → owns a (line, col) selection over source lines
└── rich mode      → embeds puikit MarkdownView, forwards mouse + keys to it
                         │
                         └── MarkdownView(selectable=True)   ← PuiKit widget
                                 └── Panel.set_clipboard_rich(text, html=…)
                                         └── macOS: NSPasteboard HTML + plain
                                             others: plain-text fallback
```

## PuiKit dependency (summary only)

- `Panel.set_clipboard_rich(text, *, html=None, rtf=None)` — plain text plus
  optional rich reps; a non-`clipboard_rich` backend drops the reps and writes
  plain, so callers never branch.
- `MarkdownView(..., selectable=True)` — enables drag-select / word / line /
  select-all / copy; exposes `selection_text()` and `selection_html()` and copies
  via `set_clipboard_rich`. Selection covers prose, headings, lists, fenced code
  **and tables** (cell-level, including partial text within a cell); a table copies
  as tab-separated columns (plain) and a real `<table>` (HTML).

TFM wiring: `src/tfm_viewer_registry.py` `_build_markdown` constructs the
file-viewer's `MarkdownView` with `selectable=True`. Help / message-box
MarkdownViews (`tfm_text_dialog.py`, `tfm_file_operations.py`) build without the
flag and stay inert.

## TFM: `TextViewer` (`src/tfm_text_viewer.py`)

Events reach `TextViewer.handle_event` in layer-local (full-window) coordinates;
the scrolling body is drawn inset at `(pad_x, head_h)`, captured each draw as
`self._body_rect` (both the raw and rich paths) so a mouse event can be mapped or
translated.

### Raw text mode

- **`_RawTextSelection`** — a small helper holding the `(line, col)` selection over
  source lines (monospace, so a column is a character), with `MultiClickTracker`
  and `word_bounds` (imported from PuiKit) for the word/line gestures. It is the
  local counterpart to PuiKit's `SelectableText` mixin, which can't be reused
  because the viewer scrolls vertically **and** horizontally and draws its own
  line-number gutter. Copy is plain text (`Panel.set_clipboard`).
- **`_pos_at(ex, ey)`** — maps a layer-local point through the body rect and the
  current `top` / `left` scroll (unwrapping `_row_map` when wrapping) to a
  `(line, col)`; the x is rounded to the nearest character boundary and clamped.
- **Highlight** — `_draw_selection` overlays the selected span of each visible
  display row, mirroring the existing search-match overlay (`_draw_matches`) and
  using `theme.text_selection_bg`.
- **Events** — `handle_event` now processes `MOUSE_DOWN/UP/DRAG` (it previously
  swallowed all non-key events) and `Cmd`/`Ctrl`+`C` (copy) / `Cmd`/`Ctrl`+`A`
  (select-all). A press outside the body clears the selection.

### Rich mode

- **`_forward_mouse_to_rich`** — translates a mouse event into the embedded
  `MarkdownView`'s coordinate space (`event.translated(-bx0, -by0)`) and forwards
  it, so the widget's own selection and link clicks work through this modal
  viewer. KEY events (including `Cmd+C`) were already forwarded to the rich widget
  in rich mode, so its copy path needs no extra wiring.

## Tests

- `test/test_viewer_selection.py` — raw-mode drag / multi-line / select-all /
  press-outside-clears, and rich-mode mouse + copy forwarding.
- PuiKit-side coverage (selection, `selection_html`, plain fallback, the
  capability) lives in `puikit/tests/test_markdown_view.py` and
  `puikit/tests/test_clipboard_rich.py`.

## Notes

- Images are not selectable (they carry no `spans` on the row); tables are
  (cell-level — see the PuiKit doc above).
- Terminal copy is plain text only (rich HTML is a desktop pasteboard feature);
  reaching the system clipboard on a terminal still depends on OSC 52.
- User-facing behavior: `doc/TEXT_SELECTION_FEATURE.md`.
