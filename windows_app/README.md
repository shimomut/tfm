# TFM Windows Application Bundle

Build system for a self-contained Windows build of TFM: a double-clickable
`TFM.exe` that launches TFM in PuiKit's native Direct2D/DirectWrite GUI backend,
with an embedded CPython and all dependencies — no system Python required.

It is the Windows counterpart of [`../macos_app/`](../macos_app/). Full design:
[`../doc/dev/WINDOWS_APP_BUILD_SYSTEM.md`](../doc/dev/WINDOWS_APP_BUILD_SYSTEM.md).

## Quick start

```powershell
# from the project root
make windows-app                 # or: powershell -ExecutionPolicy Bypass -File windows_app\build.ps1

# with a version + a distributable zip
powershell -ExecutionPolicy Bypass -File windows_app\build.ps1 -Version 1.0.0 -Zip

# clean
make windows-app-clean
```

Output: `windows_app\build\TFM\` (the self-contained folder) and, with `-Zip`,
`windows_app\build\TFM-<version>-win64.zip`.

Run it:

```powershell
& windows_app\build\TFM\TFM.exe
```

## Requirements

- **Windows 10/11 x64**, PowerShell 5.1+.
- A working `.venv` (`make venv`) backed by a full CPython install — this
  provides `Python.h` + `python3XX.lib` (under `sys.base_prefix`) that the
  launcher links against.
- **MSVC Build Tools** + **Windows 10/11 SDK** (`cl.exe`, `rc.exe`). Install the
  *"Desktop development with C++"* workload. `build.ps1` auto-imports the Visual
  Studio environment via `vswhere`/`VsDevCmd.bat` if the tools aren't already on
  `PATH`. This is the analog of the macOS build's Xcode Command Line Tools.
- Network access on the first build (downloads the CPython embeddable package,
  version-locked to your `.venv`; cached under `windows_app\.cache\`).

## Layout

```
windows_app/
├── README.md
├── build.ps1                 # orchestrator (see design doc for the 8 steps)
├── make_icon.py              # TFM.icns -> TFM.ico (Pillow), else a placeholder
├── src/
│   └── launcher.c            # the embedded-CPython launcher (-> TFM.exe)
├── resources/
│   ├── TFM.manifest          # app manifest (mirrors CPython's python.exe)
│   ├── TFM.rc                # icon + version resources
│   └── TFM.ico               # (optional) commit a real icon here to override
├── .cache/                   # downloaded embeddable zips (gitignored)
└── build/                    # build output (gitignored)
    ├── TFM/                  # the distributable folder
    ├── obj/                  # launcher intermediates
    └── TFM-<version>-win64.zip
```

Dependency collection and license notices are **not** duplicated here — `build.ps1`
reuses the shared, platform-agnostic `tools/collect_dependencies.py`
(`--include-deps-of puikit`, which pulls in `numpy`) and
`tools/generate_third_party_notices.py`, which writes `THIRD_PARTY_NOTICES.txt`
into the bundle root and fails the build if any bundled component lacks a license.

## Notes

- **Icon:** without Pillow the build embeds a placeholder icon. Install Pillow in
  the venv (`pip install pillow`) to convert `macos_app/resources/TFM.icns`, or
  drop a hand-authored multi-size `resources/TFM.ico` in to override.
- **Startup errors:** because `TFM.exe` is a GUI (no-console) app, a fatal error
  before the window appears is shown in a message box and written to
  `TFM-error.log` next to the exe.
- **DPI:** the bundle is DPI-unaware on purpose (matches the interpreter TFM is
  developed against); see the design doc.
