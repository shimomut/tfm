# Legacy TTK implementation (reference only)

This directory holds the original **ttk**-rendered TFM: kept for reference while
the app is ported to PuiKit (the top-level `tfm.py` + the `tfm_*` UI modules in
`src/`).

**It is frozen and not executed.** Imports here point at `src/` modules that no
longer sit on its path, so it will not run as-is — that is intentional. Consult
it for the old behaviour, not to launch it.

Contents:

- `ttk/` — the legacy terminal toolkit the old UI rendered through.
- `tfm.py` — the old launcher.
- `src/` — the 15 UI modules bound to the `ttk` renderer (`tfm_main`, the
  viewers, and the dialogs). All storage/business logic stayed in the top-level
  `src/` because the PuiKit port reuses it unchanged.
- `test/` — the tests that exercised those ttk-bound modules.

The boundary was mechanical: a module moved here iff it transitively imports
`ttk`; everything `ttk`-free stayed in `src/`. The one edge that used to blur the
line — an unused `from tfm_main import FileManager` inside
`tfm_file_list_manager` — was deleted, fully decoupling the port from TTK.
