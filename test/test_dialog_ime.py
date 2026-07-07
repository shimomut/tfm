"""IME composition is forwarded to the text field of every text-input dialog.

A modal layer receives *every* event exclusively (the Panel routes to the top
layer), so a dialog that hosts a ``TextEdit`` must relay ``IME_COMPOSITION``
events to its field itself — otherwise CJK preedit (the in-progress, underlined
composition) is swallowed and the user sees nothing until the text commits. Each
dialog's ``handle_event`` is driven directly here with a composition event and the
field's ``_preedit`` is checked, pinning the forwarding for all five dialogs.
"""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))
sys.path.insert(0, os.path.join(_HERE, ".."))

from puikit.event import Event, EventType  # noqa: E402

from tfm_input_dialog import InputDialog  # noqa: E402
from tfm_filter_list_dialog import FilterListDialog  # noqa: E402
from tfm_progressive_search_dialog import ProgressiveSearchDialog  # noqa: E402
from tfm_batch_rename_dialog import BatchRenameDialog  # noqa: E402
from tfm_isearch_bar import ISearchBar  # noqa: E402


def _compose(text="にほん", caret=3):
    return Event(type=EventType.IME_COMPOSITION, hints={"preedit": text, "caret": caret})


class DialogImeForwarding(unittest.TestCase):
    def _assert_forwards(self, dialog, field):
        self.assertEqual(field._preedit, "")  # nothing composed yet
        handled = dialog.handle_event(_compose("にほん", 3))
        self.assertTrue(handled)
        self.assertEqual(field._preedit, "にほん")
        self.assertEqual(field._preedit_caret, 3)
        # A commit (empty preedit) clears it again.
        dialog.handle_event(_compose("", 0))
        self.assertEqual(field._preedit, "")

    def test_input_dialog(self):
        dlg = InputDialog(title="t", prompt="Name:", text="")
        self._assert_forwards(dlg, dlg.edit)

    def test_filter_list_dialog(self):
        dlg = FilterListDialog(items=["alpha", "beta"], title="Pick")
        self._assert_forwards(dlg, dlg.filter_edit)

    def test_progressive_search_dialog(self):
        dlg = ProgressiveSearchDialog(
            search_iter=lambda mode, q, cancel: iter(()),
            to_label=lambda mode, v: str(v),
        )
        self._assert_forwards(dlg, dlg.query_edit)

    def test_batch_rename_dialog(self):
        class _Entry:  # the dialog reads only .name off each file
            def __init__(self, name):
                self.name = name

        dlg = BatchRenameDialog(files=[_Entry("a.txt"), _Entry("b.txt")])
        # Composition lands in whichever field is active (Tab switches).
        self._assert_forwards(dlg, dlg.active)

    def test_isearch_bar(self):
        bar = ISearchBar()
        self._assert_forwards(bar, bar.edit)


if __name__ == "__main__":
    unittest.main()
