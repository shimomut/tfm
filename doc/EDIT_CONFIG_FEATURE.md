# Edit & Reload Configuration

## Overview

TFM keeps its settings in `~/.tfm/config.py` (see [Configuration](CONFIGURATION_FEATURE.md)).
You can now open that file in your editor **and** apply your changes without
leaving TFM or restarting it.

## Using it

Both actions live under the **Tools** menu:

- **Edit Configuration…** — opens `~/.tfm/config.py` in your configured
  `TEXT_EDITOR`. If you have never customized your config, the default file is
  created from the template first.
  - **Terminal mode** (e.g. `vim`): the editor takes over the terminal. When
    you save and quit, TFM reloads the config automatically.
  - **GUI mode** (e.g. VS Code): the editor opens in its own window and TFM
    keeps running. Because TFM can't tell when you've finished, it does **not**
    auto-reload — save your changes, then choose **Reload Configuration**.
- **Reload Configuration** — re-reads `~/.tfm/config.py` from disk and applies
  it, without opening an editor. Handy when you edit the file in a separate
  window.

Neither action is bound to a key by default. To bind one, add it to
`KEY_BINDINGS` in your config, e.g.:

```python
KEY_BINDINGS = {
    # ...
    'edit_config':   ['Y'],
    'reload_config': ['Ctrl-R'],
}
```

## What applies immediately, and what needs a restart

Reloading applies **live**:

- **Key bindings** — rebindings take effect at once.
- **File associations**, **external programs**, **favorite directories**,
  **confirmation prompts**, and the **text editor / diff tool** settings.

The following are read once when TFM starts and only fully apply on the **next
launch**:

- **Theme / colors** and **post effects**
- **Fonts** (desktop mode)
- **Pane split and log-pane height ratios**
- **File-monitoring intervals**

TFM prints a reminder to the log pane after each reload.

## Notes

- If your edited config has a mistake that stops Python from loading it, TFM
  falls back to built-in defaults (and logs the error) rather than crashing.
- Out-of-range values (e.g. an invalid sort mode) are still applied, but a
  `Config warning:` line is logged so you can spot the problem.
