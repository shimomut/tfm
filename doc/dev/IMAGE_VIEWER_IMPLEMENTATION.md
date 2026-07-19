# Image Viewer — Implementation

The built-in image viewer (`src/tfm_image_viewer.py`) is the fourth full-window
modal viewer, after text / file diff / directory diff. This note covers the
parts that are not obvious from the source: where zoom and pan actually happen,
how a terminal ends up drawing pixels at all, and which pieces landed in PuiKit
rather than here.

User-facing behavior is in `doc/IMAGE_VIEWER_FEATURE.md`.

## Split across the two repos

Rendering is PuiKit's job (per `CLAUDE.md`), so the work divides:

| Layer | Piece |
|-------|-------|
| PuiKit | `image.zoom_window()` — zoom + pan center → normalized source window |
| PuiKit | `src` hint on `draw_image` — the crop the backend samples |
| PuiKit | `backends/_terminal_graphics.py` — kitty / iTerm2 / sixel |
| PuiKit | `CursesBackend` phase-3 image emission; `images` capability |
| PuiKit | `DrawContext.images` — lets a widget pick a richer fallback |
| TFM | `tfm_image_viewer.py` — the modal, state, keys, chrome, navigation |
| TFM | dispatch in `tfm.py`, bindings + associations in `_config.py` |

## Zoom and pan are geometry, not pixels

The viewer never re-encodes an image to zoom. It holds three numbers — `zoom`,
and a pan center `cx`/`cy` in normalized image coordinates — and turns them into
a **source window** via `puikit.image.zoom_window()`, handed to the backend as the
`src` hint:

```python
ctx.draw_image(pad_x, head_h, self._local,
               hints={"w": iw, "h": body_h, "fit": "contain",
                      "src": self._source(), "alt": "🖼"})
```

`fit` shapes the *destination*; `src` picks how much of the source feeds it. The
two are orthogonal, which is what makes the combination correct:

- `contain` gives a destination box aspect-locked to the image.
- `zoom_window` returns a window that also keeps the image's aspect ratio
  (it is square in *fraction* space, `w == h == 1/zoom`).

So nothing is distorted at any zoom, and only the sampled region changes.

Both GUI backends already computed a `(dest, source)` pair for the `cover` fit,
so honoring an explicit `src` was a small extension to
`MacOSBackend._fit_rects` / `WindowsBackend._fit_image_rects`.

### `src` is normalized, not pixels — and why

`src` is **normalized fractions** (`0..1`, top-left origin), not pixels. That is
not cosmetic: a backend does not measure an image in the units the caller thinks
in. A macOS `NSImage.size()` returns *points* derived from the file's DPI, so a
Retina 2422×1610 image reports **1211×805** — half. Direct2D and Pillow use true
pixels. A pixel-space crop computed against 2422×1610 is therefore off by 2× on
macOS: the source rect lands twice the size of the image and offset off its
bottom edge, and Cocoa draws only the top-left overlap — the picture renders
tiny in the top-left corner. (This was a real bug during development; the
symptom is that exact.)

Normalizing sidesteps it entirely: each backend multiplies the fractions by *its
own* measured size — points on macOS, pixels on Direct2D and Pillow — so the DPI
gap never leaves the backend. Two per-backend details remain: **Cocoa's source
rect is bottom-left origin**, so a top band `(y, h)` maps to `(1 - y - h)` from
the bottom; Direct2D and Pillow are top-left, unflipped.

At the fit level the viewer sends `src=None`, not a full-image crop, so the
backend takes its plain whole-image path with no source rect to get wrong.

### Why clamping slides instead of shrinking

`zoom_window` clamps a pan that runs past an edge by *sliding* the window back
inside the image, keeping its extent. Shrinking it instead would silently drop
the zoom level whenever you panned into a corner — you would pan to the edge of
a 8× view and arrive at something closer to 5×. The test
`test_pan_at_an_edge_preserves_the_zoom_level` pins this.

The pan step is divided by the zoom (`_pan_by`), so one keypress always covers
the same share of the *visible* extent rather than of the whole image.

## Images in a terminal

A character grid has no pixels, and TFM's curses backend has a hard **256
color-pair ceiling** (`CursesBackend._color_pair`), so the half-block-mosaic
approach is a non-starter: a 60×30 image region wants ~1800 distinct (fg, bg)
pairs and would degrade to nearest-pair mush while starving the rest of the UI.

Instead the backend uses the emulator's **inline-image protocol**, which puts
real pixels on screen out-of-band, entirely outside the grid.

### Where it hooks in

`CursesBackend.present()` already had a two-phase shape for color emoji: commit
the text grid, `refresh()`, then overlay the deferred glyphs as isolated writes.
Images ride the same seam as **phase 3**:

1. `draw_image()` records a placement — it emits nothing.
2. `present()` commits text and emoji as before.
3. `_present_images()` writes the escape sequences last.

Ordering is the whole point: a `refresh()` after the pixels would paint grid
cells back over them. Nothing may follow phase 3.

### Erasing

Curses' diff refresh only resends cells whose `(glyph, pair#)` changed — it
cannot know pixels were painted over its grid, so it will never clear an image
on its own. `_present_images` therefore diffs this frame's placements against
last frame's and erases the stale ones:

- **kitty** has a real delete verb (`a=d,d=i,i=<id>`), keyed by a stable image
  id assigned in draw order.
- **iTerm2 / sixel** have none, so the backend forces `redrawwin()` and lets the
  repainted text cells overwrite the image. `_terminal_graphics.clear()`
  returning `""` for these is a real answer, not a stub.

Unchanged placements are left alone — retransmitting a few hundred KB per frame
would make panning crawl.

`close()` also erases: images live outside the grid, so `endwin()` does not take
them with it and they would otherwise be burned into the shell's scrollback.

### Detection

`detect_protocol()` reads **environment variables only** — `KITTY_WINDOW_ID`,
`KONSOLE_VERSION`, `TERM_PROGRAM`, then `TERM` substrings. The obvious
alternative, a Device Attributes query (`\x1b[c`), means writing to the tty and
blocking on a reply that a non-supporting emulator never sends: a startup hang
risk inside curses' raw mode, for a cosmetic capability. `PUIKIT_TERM_GRAPHICS`
overrides in both directions (a protocol name, or `none`).

When a protocol is found the backend flips `images: True` in its capability
profile, so `Panel.draw_image` stops substituting the alt glyph and the same
widget code renders pictures on curses and GUI alike.

### Sixel

kitty and iTerm2 both accept a PNG payload, so those encoders are mostly
base64 plus framing. Sixel has no such luxury and is encoded by hand in
`_sixel()`: six vertical pixels per band per byte, one pass per palette color
within a band (`$` returns to column 0 to overlay the next color, `-` advances
the band), run-compressed with `!<count>`.

Because a hand-written encoder can look well-formed and still render garbage,
`test_terminal_graphics.py` decodes the output back to pixels and compares them
to the source (`test_sixel_round_trips_to_the_original_pixels`).

## Pillow

Pillow is a **hard** dependency of the TFM viewer's picture rendering and an
**optional** one for PuiKit:

- It crops (`src`), scales to the target's pixel box, and re-encodes to the wire
  format — the terminal protocols have no backend-side source rect, so the crop
  must be applied before transmission.
- Scaling happens before transmission so the payload is proportional to the
  screen box, not the file: a 24-megapixel photo ships as a few hundred KB, and
  zooming re-crops from the original rather than upscaling a downscaled copy.
- `_terminal_graphics.detect_protocol()` returns `None` when Pillow is missing,
  so the capability never turns on and the alt-glyph path stands.

The viewer degrades to its metadata card rather than failing.

## The metadata card

`ctx.images` (added to `DrawContext` for this) tells the viewer whether a
picture can be drawn. Where it cannot, `_draw_card` centers the format,
dimensions, size, and the reason. This is why the viewer reads `ctx.images`
directly, against the usual rule that widgets should not branch on capability:
the Panel's fallback is a single centered glyph, and "opening an image tells you
nothing about it" is a worse outcome than a small, deliberate branch.

`_hint()` and the header follow suit — zoom and pan hints are omitted where
there is no picture, and prev/next where there are no siblings.

## Navigation and the sibling list

`TfmApp._open_viewer` filters the pane's `files` through `is_image_file` and
hands the result plus the index to `show_image_viewer`. Two deliberate choices:

- **`pane["files"]`, not a fresh listing.** It is already sorted and filtered by
  `tfm_file_list_manager` — the single choke point — so the viewer walks exactly
  what the user sees, in their order.
- **A snapshot, not a live reference.** The file monitor mutates `pane["files"]`
  in place on refresh, which would shift the index under an open viewer.
  `ImageViewer.__init__` copies the list; `test_sibling_list_is_snapshotted_not_referenced`
  pins it.

The constructor also re-derives the index from the path when the caller's index
disagrees, so a stale index cannot land the viewer on a different file.

Moving to another image resets zoom and pan — carrying a 20× crop across would
open the next file on an arbitrary corner of it.

## Non-local images

`draw_image` and Pillow both take a filesystem path, which an S3 / SSH /
in-archive `tfm_path.Path` does not have. `_resolve()` materializes those via
`read_bytes()` into a temp file for the life of the viewer, released on
navigation and on close. Failures are recorded in `_error` and shown on the card
rather than raised — one corrupt file should not make a directory unbrowsable.

## Dispatch and config

- `tfm.py` routes on `is_image_file` in `_open_viewer`, and the binary guard in
  `_enter_file` now exempts images (they *are* binary, but there is finally
  something that renders them). That guard's comment had predicted this seam.
- `_config.py` gains an `image_*` binding block. `-` and `_` intentionally share
  with `reset_pane_boundary` / `reset_log_height`: those are file-list-only, and
  each context matches its own action *by name* through `is_action_for_event`,
  the same pattern `toggle_wrap` uses to share `W`.
- `_pressed()` falls back to literal characters when an action is absent from
  `KEY_BINDINGS`, so a config merged from a template older than this viewer
  still works — mirroring `TextViewer._wrap_pressed`. Note the `[0]`:
  `get_keys_for_action` returns `(keys, selection_requirement)`, and testing the
  tuple's truthiness instead of the key list silently disables the fallback.
- The shipped `FILE_ASSOCIATIONS` image entry changed from `'open|view'` to
  `'open'` + `'view': None`, so `V` reaches the built-in viewer while
  `open_with_os` still hands off to Preview. **Existing user configs keep the
  old association** and will keep opening Preview until edited.

## Testing

`test/test_image_viewer.py` (41 tests) covers the file-type claim, zoom/pan
arithmetic and clamping, navigation and its snapshot semantics, the hints that
reach the backend, the TUI metadata card, modal behavior, app-level dispatch,
and remote-file materialization. Drawing is asserted against `MemoryBackend`
under both `PROFILE_TUI` and `PROFILE_GUI_DESKTOP`.

On the PuiKit side, `tests/test_terminal_graphics.py` and the additions to
`tests/test_image_widgets.py` cover detection, crop/scale, the three encoders,
and the sixel round-trip.

```bash
PYTHONPATH=.:src pytest test/test_image_viewer.py -v
(cd ../puikit && pytest tests/test_terminal_graphics.py tests/test_image_widgets.py -v)
```

Note that `test/test_image_viewer.py` binds `import tfm` at module scope. Both
the repo root and `test/` are packages, so once pytest prepends the repo's
*parent* to `sys.path`, a later `import tfm` resolves to the repo directory's
`__init__.py` instead of the `tfm.py` app entry.
