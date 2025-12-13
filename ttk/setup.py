"""
Setup script for TTK (TUI Toolkit) library.

This setup.py provides an alternative to pyproject.toml for building
the TTK package. It handles the flat package layout where package files
are in the same directory as the setup script.
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
with open(readme_path, 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ttk',
    version='0.1.0',
    description='TUI Toolkit - A generic rendering library for character-grid-based applications',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='TFM Development Team',
    license='MIT',
    python_requires='>=3.8',
    
    # Package configuration
    # This is a flat-layout package where the package root is the current directory
    # We need to explicitly tell setuptools about the package structure
    packages=['ttk', 'ttk.backends', 'ttk.serialization', 'ttk.utils'],
    package_dir={
        'ttk': '.',
    },
    
    # Package data - include py.typed for type checking support
    package_data={
        'ttk': ['py.typed'],
    },
    
    # Include package files explicitly
    include_package_data=True,
    
    # Dependencies
    install_requires=[
        # curses is built-in for Unix-like systems
    ],
    
    # Optional dependencies
    extras_require={
        'coregraphics': [
            'pyobjc-framework-Cocoa>=9.0; sys_platform == "darwin"',
            'pyobjc-framework-CoreText>=9.0; sys_platform == "darwin"',
        ],
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=4.0',
            'hypothesis>=6.0',
        ],
    },
    
    # Classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Terminals',
    ],
    
    # Keywords
    keywords='tui terminal rendering curses coregraphics gui',
    
    # Project URLs
    project_urls={
        'Homepage': 'https://github.com/tfm/ttk',
        'Documentation': 'https://github.com/tfm/ttk/blob/main/README.md',
        'Repository': 'https://github.com/tfm/ttk',
        'Issues': 'https://github.com/tfm/ttk/issues',
    },
)
