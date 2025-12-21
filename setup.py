#!/usr/bin/env python3
"""
TFM Setup Script
"""

import os
import sys
import platform
from setuptools import setup, find_packages, Extension
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

# Add Windows-specific requirements using environment markers
requirements.append('windows-curses; sys_platform == "win32"')

# Configure C++ extension module (macOS only)
ext_modules = []
if platform.system() == 'Darwin':  # macOS
    cpp_renderer = Extension(
        'cpp_renderer',
        sources=['src/cpp_renderer.cpp'],
        include_dirs=['/usr/include'],
        extra_compile_args=[
            '-std=c++17',           # C++17 standard
            '-O3',                  # Optimization level 3
            '-Wall',                # Enable all warnings
            '-Wextra',              # Enable extra warnings
            '-Wno-unused-parameter' # Suppress unused parameter warnings
        ],
        extra_link_args=[
            '-framework', 'CoreGraphics',
            '-framework', 'CoreText',
            '-framework', 'CoreFoundation'
        ],
        language='c++'
    )
    ext_modules.append(cpp_renderer)

setup(
    name="tfm",
    version="0.98",
    description="Terminal File Manager - A dual-pane file manager for the terminal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TFM Developer",
    url="https://github.com/shimomut/tfm",
    packages=["tfm"],
    package_dir={"tfm": "src"},
    package_data={
        "tfm": ["tools/*"],
    },
    entry_points={
        "console_scripts": [
            "tfm=tfm.tfm_main:cli_main",
        ],
    },
    install_requires=requirements,
    ext_modules=ext_modules,  # Add C++ extension modules
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console :: Curses",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
    keywords="file manager terminal curses dual-pane",
)