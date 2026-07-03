"""
About box content for the PuiKit TfmApp.

The About/Info dialogs were largely already ported — Info's scrollable-panel
role is covered by ``show_text`` (used by help/file-details), and ``show_about``
existed but was a bare message box. This pins the enriched About body (name,
version, project URL) so it stays in sync with the constants.
"""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))
sys.path.insert(0, os.path.join(_HERE, ".."))

import tfm  # noqa: E402
from tfm_const import VERSION, GITHUB_URL  # noqa: E402


class AboutText(unittest.TestCase):
    def test_includes_version_and_url(self):
        text = tfm.TfmApp._about_text()
        self.assertIn(VERSION, text)
        self.assertIn(GITHUB_URL, text)

    def test_names_the_app(self):
        self.assertIn("TFM", tfm.TfmApp._about_text())


if __name__ == "__main__":
    unittest.main()
