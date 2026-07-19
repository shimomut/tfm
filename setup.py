#!/usr/bin/env python3
"""
TFM Setup Script
"""

import os
import sys
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

# Platform-specific dependencies (pyobjc on macOS, windows-curses on Windows)
# are declared with environment markers in requirements.txt, which is the single
# source of truth for both `make venv` and install_requires here.

setup(
    name="tfm",
    version="0.99",
    description="Terminal File Manager - A dual-pane file manager for the terminal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TFM Developer",
    url="https://github.com/shimomut/tfm",
    # The application is the top-level ``tfm.py`` at the repo root; its flat
    # ``tfm_*`` modules live in ``src/`` and are shipped as the ``tfm_modules``
    # package dir. ``tfm.py`` puts that dir on sys.path at import time (see its
    # header), so ``from tfm_* import`` resolves once installed. The UI framework
    # (PuiKit) is a separate, editable-installed dependency and is not vendored
    # here — install it too (``pip install -e ../puikit``).
    py_modules=["tfm"],
    packages=["tfm_modules"],
    package_dir={"tfm_modules": "src"},
    package_data={
        "tfm_modules": ["tools/*"],
    },
    entry_points={
        "console_scripts": [
            "tfm=tfm:main",
        ],
    },
    install_requires=requirements,
    # PuiKit, TFM's UI framework, requires Python 3.10+, so TFM cannot claim 3.9.
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console :: Curses",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
    keywords="file manager terminal curses dual-pane",
)