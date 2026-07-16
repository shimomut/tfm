# Encrypted-ZIP Support — Implementation

Implements issue #180: extract and browse password-protected ZIP archives.
Spans two repos — PuiKit gains a masked text field, TFM gains the password flow.

## Layers

### 1. PuiKit — masked `TextEdit` (`puikit/widgets/text_edit.py`)

`TextEdit(..., mask="•")` turns the field into a password field:

- `_display(s)` returns one mask glyph per character (`mask * len(s)`), so it is
  length-preserving — cursor, selection, view, and hit-test indices still map
  one-to-one onto the buffer (`self.text` keeps the real value).
- The mask is applied wherever the field's *content* is measured or drawn: the
  `draw()` display string, `_scroll_into_view()`, and `_index_at_column()`
  (click hit-testing). Editing, word motion, and IME logic operate on the real
  buffer unchanged.
- `_copy()` returns `False` when masked, disabling both copy and cut so the
  plaintext never reaches the clipboard.

Documented in `docs/widget_catalog.md`; tests in
`tests/test_input_widgets.py` (`test_textedit_mask_*`).

### 2. TFM — password prompt (`src/tfm_input_dialog.py`)

`InputDialog` / `show_input(..., password=True)` forwards `mask="•"` to the
`TextEdit`. That's the only change needed for a masked modal prompt.

### 3. TFM — archive password machinery (`src/tfm_archive.py`)

**Exceptions**
- `ArchivePasswordRequired` — a password is required or the one given is wrong.
- `ArchiveEncryptionUnsupported` — an unsupported scheme (WinZip AES).

**Session password registry** — a module-level `dict` keyed by the archive
file's absolute path, guarded by a lock:
- `set_archive_password` / `get_archive_password` / `clear_archive_password`.
- In-memory only; nothing is persisted.

**Classification / verification helpers**
- `zip_encryption_status(zf)` → `'none' | 'zipcrypto' | 'aes'`. AES is detected
  by compression method `99` on an encrypted entry (flag bit `0x1`).
- `zip_encryption_status_path(path)` — the same for a local file path (used by
  the extract flow, which works on a raw file rather than a handler).
- `verify_zip_password(zf, pwd)` — opens the smallest encrypted entry to validate
  the ZipCrypto password header cheaply; raises `RuntimeError` (missing/wrong) or
  `NotImplementedError` (AES); a no-op for unencrypted archives.

**`ZipHandler`** (the browse/read path)
- `extract_to_bytes` / `extract_to_file` pass `pwd=get_archive_password(...)` to
  `ZipFile.read`, and map `RuntimeError`→`ArchivePasswordRequired` (via
  `_read_runtime_error`) and `NotImplementedError`→`ArchiveEncryptionUnsupported`.
- `encryption_status()` and `verify_password(pwd)` expose the helpers per handler.

**UI-facing gate helpers** (keep the app out of `_impl`/cache internals)
- `get_member_archive_path(path)` — the archive file behind an `archive://`
  member Path, or `None` for an ordinary file.
- `archive_password_state(path)` → `'ok' | 'need' | 'aes'`. Ordinary paths return
  `'ok'` cheaply without opening anything, so every read can route through it.
- `try_archive_password(path, password)` — verify (UTF-8 encoded) and, on
  success, remember it; returns a bool.

### 4. TFM — flows (`tfm.py`)

**Extract (`extract_archive` / `_extract_archive`, the `U` key)**
- `_extract_archive(..., pwd=None)` calls `verify_zip_password` *before*
  `extractall(pwd=...)`, so a bad password raises before any file is written (no
  partial extraction).
- `extract_archive.go()` classifies the zip: `'aes'` → clear message and stop;
  `'zipcrypto'` → `prompt_password()`; otherwise extract directly.
- `do_extract(pwd)` catches `RuntimeError` → re-prompt with an error; a working
  password is stored in the registry so a later browse of the same file reuses it.

**Browse / view (`_ensure_archive_password`, used by `_open` and `view_file`)**
- Gates opening a file that may live in an encrypted zip. `'ok'` → run the
  `on_ready` callback (open the viewer) immediately; `'aes'` → clear message;
  `'need'` → masked prompt, verify via `try_archive_password`, re-prompt on
  failure, then `on_ready`. `on_ready` owns its own redraw because the prompt
  path reaches it from an async dialog callback.
- Browsing/listing an encrypted archive needs no password (the ZIP central
  directory is unencrypted); the prompt is deferred to the first file open.

## Why stdlib only (no `pyzipper`)

Python's `zipfile` decrypts legacy ZipCrypto but not AES, and adding a
dependency was out of scope for the issue. AES is therefore detected and
refused with a clear message rather than supported.

## Tests

- `test/test_archive_password.py` — classification, verification, the registry,
  the `ZipHandler` read path, and the gate helpers, against a hermetic
  base64-embedded ZipCrypto fixture (stdlib can read but not write ZipCrypto).
- `test/test_tfm_app_archive_password.py` — `_extract_archive`, the
  `extract_archive` UI flow (prompt, wrong-then-right retry, AES refusal, plain
  zip), and `_ensure_archive_password`.
- `puikit/tests/test_input_widgets.py` — masked-field rendering, edit-on-real-
  text, copy/cut disabled, and masked hit-testing.
