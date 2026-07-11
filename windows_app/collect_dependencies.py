#!/usr/bin/env python3
"""
TFM Windows dependency collector.

Copies the third-party packages TFM needs from the build virtual environment's
site-packages into the bundle's ``Lib\\site-packages`` directory, so the app is
self-contained and never touches the developer's ``.venv`` or a system Python at
runtime.

Philosophy matches the macOS ``collect_dependencies.py``: walk site-packages and
copy everything, skipping only what must not ship:

  - build tools (pip / setuptools / wheel / pkg_resources / _distutils_hack),
  - editable-install shims (``__editable__*``, ``*.pth``) - PuiKit is installed
    editable, so its site-packages entry only points at the developer's checkout;
    build.ps1 copies the real ``puikit`` source into ``app\\puikit`` separately,
  - macOS-only PyObjC packages (not present on a Windows venv anyway).

numpy carries its own DLLs under ``numpy\\`` and ``numpy.libs\\`` and registers
them via ``os.add_dll_directory`` on import, so a plain directory copy is enough.

Usage:
    python collect_dependencies.py --site-packages <venv-site-packages> --dest <bundle>\\Lib\\site-packages
"""

import argparse
import shutil
import sys
from pathlib import Path


def log_info(msg):
    print(f"[INFO] {msg}")


def log_warning(msg):
    print(f"[WARNING] {msg}")


def log_error(msg):
    print(f"[ERROR] {msg}", file=sys.stderr)


def log_success(msg):
    print(f"[SUCCESS] {msg}")


# Exact directory/file names to skip.
_SKIP_EXACT = {
    "pip",
    "setuptools",
    "wheel",
    "pkg_resources",
    "_distutils_hack",
    "puikit",          # editable shim target; real source copied by build.ps1
    "PIL",             # Pillow: build-time only (make_icon.py), not a runtime dep
    "PIL.libs",
}

# Name prefixes to skip (dist-info/egg-info of the build tools above, and the
# editable puikit's own metadata). PyObjC never installs on Windows but is
# skipped defensively in case a venv was seeded oddly.
_SKIP_PREFIXES = (
    "pip-",
    "pip_",
    "setuptools-",
    "wheel-",
    "puikit-",
    "puikit.",
    "pyobjc",
    "PyObjC",
    "pillow-",
    "Pillow-",
    "__editable__",
)


def should_skip(name: str) -> bool:
    if name in _SKIP_EXACT:
        return True
    # dunder dirs (e.g. __pycache__) and .pth path shims.
    if name.startswith("__pycache__"):
        return True
    if name.endswith(".pth"):
        return True
    for prefix in _SKIP_PREFIXES:
        if name.startswith(prefix):
            return True
    return False


def collect(site_packages: Path, dest: Path) -> bool:
    if not site_packages.is_dir():
        log_error(f"site-packages not found: {site_packages}")
        return False

    dest.mkdir(parents=True, exist_ok=True)
    log_info(f"Source: {site_packages}")
    log_info(f"Dest:   {dest}")

    copied = 0
    skipped = 0
    saw_numpy = False

    for item in sorted(site_packages.iterdir()):
        if should_skip(item.name):
            log_info(f"Skipping: {item.name}")
            skipped += 1
            continue

        if item.name == "numpy" or item.name.startswith("numpy.") or item.name.startswith("numpy-"):
            saw_numpy = True

        target = dest / item.name
        try:
            if item.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                # Copy without bytecode caches; they are recompiled at build time
                # against the bundled interpreter.
                shutil.copytree(item, target, ignore=shutil.ignore_patterns("__pycache__"))
                log_info(f"Copied dir:  {item.name}")
            else:
                shutil.copy2(item, target)
                log_info(f"Copied file: {item.name}")
            copied += 1
        except Exception as exc:  # noqa: BLE001 - report and keep going
            log_warning(f"Failed to copy {item.name}: {exc}")

    log_success(f"Copied {copied} items ({skipped} skipped)")

    if not saw_numpy:
        # numpy underpins the whole Windows Direct2D backend (pixel buffers);
        # its absence means the venv is incomplete.
        log_warning("numpy was not found in site-packages - the Windows GUI "
                    "backend will fail to import. Install it: pip install numpy")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect TFM Windows bundle dependencies")
    parser.add_argument("--site-packages", required=True, help="venv site-packages directory")
    parser.add_argument("--dest", required=True, help="destination Lib\\site-packages directory")
    args = parser.parse_args()

    ok = collect(Path(args.site_packages).resolve(), Path(args.dest).resolve())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
