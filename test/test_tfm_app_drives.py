"""
Drives picker data for the PuiKit TfmApp.

Covers the pane-independent row builders behind ``show_drives`` — local
locations/volumes and SSH hosts from ~/.ssh/config. The dialog itself (a
``show_filter_list`` modal) and the actual pane navigation are exercised
elsewhere; here we pin down the ``{name, path}`` rows the picker is fed.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))
sys.path.insert(0, os.path.join(_HERE, ".."))

import tfm  # noqa: E402


def _bare_app():
    """A TfmApp shell for the stateless row builders (no backend/UI needed)."""
    return tfm.TfmApp.__new__(tfm.TfmApp)


class LocalDrives(unittest.TestCase):
    def test_includes_home_and_root(self):
        rows = _bare_app()._local_drives()
        by_name = {r["name"]: r["path"] for r in rows}
        self.assertEqual(by_name.get("Home"), str(tfm.Path.home()))
        self.assertEqual(by_name.get("Root"), "/")

    def test_paths_are_unique(self):
        paths = [r["path"] for r in _bare_app()._local_drives()]
        self.assertEqual(len(paths), len(set(paths)))


class SshDrives(unittest.TestCase):
    def _with_hosts(self, hosts):
        parser = MagicMock()
        parser.parse.return_value = hosts
        return patch("tfm_ssh_config.SSHConfigParser", return_value=parser)

    def test_maps_hosts_to_ssh_urls(self):
        hosts = {
            "myhost": {"HostName": "h.example.com", "User": "bob"},
            "plain": {"HostName": "plain.example.com"},
        }
        with self._with_hosts(hosts):
            rows = _bare_app()._ssh_drives()

        by_path = {r["path"]: r["name"] for r in rows}
        self.assertEqual(by_path["ssh://myhost/"], "bob@h.example.com")
        self.assertEqual(by_path["ssh://plain/"], "plain.example.com")

    def test_uses_alias_when_no_hostname(self):
        with self._with_hosts({"box": {}}):
            rows = _bare_app()._ssh_drives()
        self.assertEqual(rows, [{"name": "box", "path": "ssh://box/"}])

    def test_empty_when_parser_unavailable(self):
        with patch("tfm_ssh_config.SSHConfigParser", side_effect=RuntimeError):
            self.assertEqual(_bare_app()._ssh_drives(), [])

    def test_empty_when_no_config(self):
        with self._with_hosts({}):
            self.assertEqual(_bare_app()._ssh_drives(), [])


if __name__ == "__main__":
    unittest.main()
