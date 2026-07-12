# Archived developer docs (pre-PuiKit toolkit internals)

These documents describe the **rendering / event / backend internals of the old
in-repo `ttk` toolkit** — the layer that was replaced by the external
[PuiKit](https://github.com/crftwr/puikit) framework during the PuiKit port.

They are kept **for historical reference only**. They are *not* accurate for the
current codebase:

- The code they describe (`ttk/renderer.py`, `ttk/input_event.py`,
  `ttk/backends/*`, the CoreGraphics backend, the callback/event loop, the
  dirty-region and adaptive-FPS render optimizations, etc.) no longer lives in
  this repo. Its successor lives in the **PuiKit repository**.
- Some also reference TFM UI modules that are now frozen under `../../../legacy/`
  (e.g. `tfm_main.py`, `tfm_menu_manager.py`).

**For current information:**

- The port itself → [`../PROJECT_HISTORY.md`](../PROJECT_HISTORY.md); remaining follow-up work is tracked as GitHub issues
- Rendering / backend / event internals → the PuiKit repo's own documentation
- TFM-layer feature behavior → the corresponding `*_FEATURE.md` / `*_IMPLEMENTATION.md` that remain in `doc/` and `doc/dev/`

Nothing here should be treated as a description of how TFM works today.
