"""
Test entry point functionality for TFM

Run with: PYTHONPATH=.:src:ttk pytest test/test_entry_point.py -v
"""

import os
import sys
import unittest

_REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


class TestEntryPoint(unittest.TestCase):
    """Test entry point functionality"""

    def setUp(self):
        # Make ``import tfm`` resolve to the top-level tfm.py module. Two hazards
        # come from pytest prepending the repo's *parent* to sys.path (the repo
        # has an __init__.py, so pytest treats it as a package): (1) ``tfm`` binds
        # to the repo package __init__.py, which has no entry-point functions, and
        # (2) the sibling ``puikit`` source dir shadows the editable puikit install
        # as an empty namespace package. Drop that parent entry, put repo-root
        # first, and clear the cached bindings so both re-resolve cleanly.
        # sys.path / sys.modules are process-global, so snapshot and restore in
        # tearDown — otherwise these tweaks would leak into every later test.
        self._saved_path = list(sys.path)
        self._saved_modules = {n: sys.modules.get(n) for n in ("tfm", "puikit")}
        repo_root = os.path.realpath(_REPO_ROOT)
        parent = os.path.dirname(repo_root)
        while parent in sys.path:
            sys.path.remove(parent)
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        sys.modules.pop("tfm", None)
        sys.modules.pop("puikit", None)

    def tearDown(self):
        sys.path[:] = self._saved_path
        for name, mod in self._saved_modules.items():
            if mod is not None:
                sys.modules[name] = mod
            else:
                sys.modules.pop(name, None)

    def test_import_main_function(self):
        """Test that we can import the main function from tfm.py"""
        try:
            from tfm import main
            self.assertTrue(callable(main), "main should be callable")
        except ImportError as e:
            self.fail(f"Failed to import main function: {e}")
    
    def test_import_parser_function(self):
        """Test that we can import the create_parser function"""
        try:
            from tfm import create_parser
            parser = create_parser()
            self.assertIsNotNone(parser, "Parser should not be None")
            
            # Test that parser has the expected arguments
            help_text = parser.format_help()
            self.assertIn('--version', help_text)
            self.assertIn('--help', help_text)
            
        except ImportError as e:
            self.fail(f"Failed to import create_parser function: {e}")
