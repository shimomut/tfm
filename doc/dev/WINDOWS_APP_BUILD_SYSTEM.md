# Windows Application Bundle — Build System

This document describes the `windows_app/` build system that packages TFM into a
self-contained Windows application folder (`TFM.exe` + embedded CPython + all
dependencies), the direct counterpart of the macOS `macos_app/` bundle.

It is the design-and-implementation reference; the source of truth is the code
under `windows_app/`.

---

## Goals

- A double-clickable `TFM.exe` that launches TFM in the native **Windows GUI
  backend** (PuiKit's Direct2D/DirectWrite renderer), with no console window.
- **Self-contained**: no dependency on a system Python, on the developer's
  `.venv`, or on any pip-installed package on the target machine.
- **Hand-rolled and transparent**, mirroring the macOS approach — no PyInstaller
  / cx_Freeze magic. Every file that lands in the bundle is put there by an
  explicit, readable step.

## Why this mirrors macOS so closely

The macOS bundle embeds a `Python.framework` and drives it from a small Obj-C
launcher (`macos_app/src/{main.m,TFMAppDelegate.m}`) that:

1. initializes CPython with `PyConfig` (Python home = the embedded runtime),
2. points `sys.path` at the bundled TFM source, PuiKit, and third-party packages,
3. sets `sys.argv = ["TFM", "--backend", "gui"]`, and
4. imports the `tfm` module and calls `tfm.main()`.

The Windows launcher (`windows_app/src/launcher.c`) does the **same four things**
against the CPython **embeddable** distribution. Crucially, there is **nothing to
compile in TFM or PuiKit**: PuiKit's Windows backend
(`puikit/backends/windows_backend.py`, `_win32_native.py`) is pure Python built
on `ctypes` + `numpy`, exactly as the macOS backend is pure PyObjC. The only
native code we build is the ~200-line launcher stub itself.

---

## Bundle layout

The build produces `windows_app/build/TFM/`, a self-contained folder (this whole
folder is what gets zipped for distribution):

```
TFM/                              <- bundle root = the .exe's directory
├── TFM.exe                       compiled C launcher (this repo)
├── TFM.ico                       app icon (also embedded into TFM.exe)
├── python3XX.dll                 embeddable CPython (implicitly linked by TFM.exe)
├── python3.dll                   stable-ABI forwarder (from embeddable)
├── python3XX.zip                 zipped standard library (from embeddable)
├── vcruntime140.dll, vcruntime140_1.dll
├── _ctypes.pyd, _socket.pyd, select.pyd, ...   stdlib C extensions (embeddable)
├── libffi-8.dll, libssl-3.dll, libcrypto-3.dll, ...  their support DLLs
├── app/                          TFM's own code (mirror of macOS Resources/)
│   ├── tfm.py                    entry script (imported as the `tfm` module)
│   ├── src/                      tfm_* business-logic modules
│   ├── puikit/                   PuiKit toolkit (copied from the sibling repo)
│   └── LICENSE
└── Lib/
    └── site-packages/            third-party deps: numpy, pygments, boto3, watchdog, ...
```

### Path resolution at runtime

The launcher computes `<root>` from `GetModuleFileNameW` (the directory
containing `TFM.exe`) and configures CPython **explicitly** — it does *not* rely
on a `python3XX._pth` file — so the layout is unambiguous:

- `PyConfig.home = <root>`
- `PyConfig.module_search_paths` (with `module_search_paths_set = 1`):
  1. `<root>\python3XX.zip`  — standard library
  2. `<root>`                — stdlib C extensions (`*.pyd`) and their DLLs
  3. `<root>\Lib\site-packages` — third-party deps
  4. `<root>\app`            — `tfm.py` and `puikit`
  5. `<root>\app\src`        — `tfm_*` modules (also self-inserted by `tfm.py`)
- `PyConfig.site_import = 0`, `user_site_directory = 0` — fully deterministic
  path; no `site.py` global-path guessing, no user site-packages leaking in
  (the equivalent of the macOS bundle's `sitecustomize.py`).
- `PyConfig.write_bytecode = 0` — the install dir may be read-only
  (e.g. `Program Files`); the standard library and app code are pre-compiled at
  build time instead.

`sys.argv` is set to `["TFM", "--backend", "gui"]` (via `PyConfig.argv` with
`parse_argv = 0`) so `tfm.main()`'s argparse selects the Windows GUI backend —
`create_backend("gui")` maps to `WindowsBackend` on `sys.platform == "win32"`.

---

## The launcher (`src/launcher.c`)

- **GUI subsystem** (`/SUBSYSTEM:WINDOWS`, `wWinMain` entry): no console window.
  Because there is no terminal, any failure *before* the UI is up is surfaced via
  `MessageBoxW`, not stderr:
  - CPython init failures are reported from the `PyStatus` error message in C.
  - Failures *after* init (import errors, exceptions from `tfm.main()`) are caught
    by a small Python bootstrap that formats the traceback and shows it in a
    message box (and writes `TFM-error.log` next to the exe).
- **No import library shipped**: `Python.h` auto-links `python3XX.lib` via
  `#pragma comment(lib, ...)`; the build only has to supply `/I<include>` and
  `/LIBPATH:<libs>` from the developer's full CPython install (`sys.base_prefix`).
  At runtime the exe loads `python3XX.dll` from its own directory (default DLL
  search includes the application directory).
- **Manifest** (`resources/TFM.manifest`): mirrors CPython 3.14's own
  `python.exe` manifest — `asInvoker`, the Vista→Win11 `supportedOS` GUIDs,
  `longPathAware`, and Common-Controls v6, and **deliberately no `dpiAware`
  setting**. TFM is developed and rendered against a DPI-*unaware* interpreter
  today (the backend has no DPI-scaling path and always sees 96 DPI while Windows
  bitmap-scales the window), so omitting `dpiAware` makes the bundle render
  **identically** to `python tfm.py --backend gui`. Per-monitor scaling is a
  future backend concern; this is the knob if it changes.

---

## The embedded runtime — CPython "embeddable" package

`build.ps1` downloads the official `python-<X.Y.Z>-embed-amd64.zip` from
python.org **matching the exact version of the developer's `.venv`** and extracts
it into the bundle root. This is the minimal, redistributable CPython: the DLL,
the zipped stdlib, and the stdlib C-extension `.pyd`s + their support DLLs
(`libffi`, `libssl`/`libcrypto`, etc.). `ctypes` (which the whole Windows backend
rides on) and its `libffi-8.dll` are included.

**Version lock:** compiled wheels in `.venv\Lib\site-packages` (notably `numpy`)
are built for the venv's Python ABI (`cp3XX`). The embeddable must be the same
`X.Y`, so `build.ps1` derives the download version from the venv interpreter and
refuses to mix ABIs.

**Coverage note:** the 3.14 embeddable ships a broad stdlib C-extension set —
including `_ctypes.pyd` + `libffi-8.dll` (which the whole Windows backend rides
on), `_ssl`/`_hashlib` + `libssl`/`libcrypto`, and `_sqlite3.pyd` + `sqlite3.dll`.
It omits `_tkinter` (and Tcl/Tk); TFM/PuiKit don't use it, so that's fine. If a
future dependency needs a module the embeddable leaves out, copy its `.pyd`
(+ any support DLL) from a full CPython install of the same version into the
bundle root.

---

## Dependency collection (`collect_dependencies.py`)

Same philosophy as the macOS collector: walk the venv `site-packages` and copy
everything into `Lib\site-packages`, skipping:

- build tools (`pip`, `setuptools`, `wheel`, `pkg_resources`, `_distutils_hack`),
- editable-install shims (`__editable__*`, `*.pth`) — PuiKit is installed
  editable, so its site-packages entry only *points at* the developer's checkout;
  the real `puikit/` source is copied separately by `build.ps1`,
- `pyobjc*` (macOS-only; not present on a Windows venv anyway).

`numpy` carries its own DLLs under `numpy/` and `numpy.libs/` and registers them
via `os.add_dll_directory` on import, so a plain directory copy is sufficient.

---

## The build script (`build.ps1`)

PowerShell orchestrator (invoked from the `Makefile` `windows-app` target or
directly). Steps:

1. **Locate the venv** (`.venv\Scripts\python.exe`); derive Python version,
   `base_prefix` (for `include/` + `libs/`), and the `python3XX` DLL/lib names.
2. **Locate the toolchain** — `cl.exe` + `rc.exe`. If not already on `PATH`, find
   Visual Studio via `vswhere` and import `VsDevCmd.bat`'s environment. If neither
   MSVC nor the Windows SDK is present, fail with install instructions (this is
   the Windows analog of the macOS build's Xcode Command Line Tools requirement).
3. **Fetch + extract** the matching embeddable CPython into the bundle root
   (cached under `windows_app/.cache/`).
4. **Assemble app code**: copy `tfm.py`, `src/`, the resolved `puikit/` package,
   and `LICENSE` into `app/`; `compileall` them.
5. **Collect dependencies** into `Lib\site-packages`.
6. **Generate resources**: `version_generated.h` (from `$VERSION` / tfm.py's
   `_VERSION`) and `TFM.ico` (via `make_icon.py`); compile `TFM.rc` → `TFM.res`.
7. **Compile** `launcher.c` + `TFM.res` → `TFM.exe` (GUI subsystem).
8. **(optional)** `-Zip` → `build\TFM-<version>-win64.zip` for distribution.

### Usage

```powershell
# from the project root (or windows_app/)
powershell -ExecutionPolicy Bypass -File windows_app\build.ps1
powershell -ExecutionPolicy Bypass -File windows_app\build.ps1 -Version 1.0.0 -Zip
powershell -ExecutionPolicy Bypass -File windows_app\build.ps1 -Clean

# or via make (Git-Bash):
make windows-app
make windows-app-zip
make windows-app-clean
```

---

## Build requirements

- **Windows 10/11 x64**, PowerShell 5.1+.
- A **full CPython** install backing the `.venv` (provides `Python.h` and
  `python3XX.lib` under `sys.base_prefix`). `make venv` already sets this up.
- **MSVC Build Tools** (or Visual Studio) with the **Windows 10/11 SDK** —
  supplies `cl.exe`, `rc.exe`, and `vcruntime`. Install the *"Desktop development
  with C++"* workload, or the standalone *Build Tools for Visual Studio*.
- Network access on first build (to download the embeddable package; cached
  afterward).

---

## Open items / future work

- **Code signing** — `signtool` pass over `TFM.exe` (and the zip), gated on a
  cert like the macOS build's optional `CODESIGN_IDENTITY`.
- **Installer** — an Inno Setup / MSIX wrapper around the folder for a Start-menu
  entry and uninstaller (the folder itself is already xcopy-deployable).
- **Per-monitor DPI** — real HiDPI scaling in the Windows backend; the manifest's
  `dpiAware` would then be switched on. Tracked as a backend concern, not here.

## Build gotchas (found live standing this up)

- **`user32.lib`** — the launcher calls `MessageBoxW`; with `WIN32_LEAN_AND_MEAN`
  it isn't auto-linked, so `launcher.c` carries `#pragma comment(lib,"user32.lib")`.
  (`python3XX.lib` and `kernel32` link automatically.)
- **No `--` in the manifest's XML comments.** XML forbids a double-hyphen inside
  a comment, and Windows' SxS manifest parser enforces it strictly (a lenient XML
  parser does not): an offending comment makes the loader report *"side-by-side
  configuration is incorrect / Invalid Xml syntax on line 1"* and the app won't
  start. Validate a manifest without launching the GUI via `CreateActCtx`
  (`ACTCTX_FLAG_RESOURCE_NAME_VALID` + resource id 1 to check the embedded copy).
- **`/MANIFEST:NO`** on the link line so the linker doesn't embed a second
  `RT_MANIFEST` alongside the one from `TFM.rc`.
- **A real app icon** — `make_icon.py` converts `macos_app/resources/TFM.icns`
  when Pillow is available, else emits a placeholder; a hand-authored multi-size
  `TFM.ico` can be dropped into `windows_app/resources/` to override.
