"""Search / isearch match highlights track the active theme.

The file-pane isearch wash and the text-viewer search-match backgrounds were
fixed dark constants, so they read dark on the light themes. They are now
derived from the pane/content background, so a match highlight is a dark wash on
a dark theme and a pale one on a light theme.
"""

from tfm_file_pane import MATCH_HUE, MATCH_TINT, _mix
from tfm_text_viewer import _is_light, _match_bg

DARK = (30, 30, 38)
LIGHT = (255, 255, 255)


def _luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def test_is_light_polarity():
    assert _is_light(LIGHT)
    assert not _is_light(DARK)
    assert not _is_light(None)


def test_filepane_isearch_wash_tracks_theme_and_reads_green():
    dark = _mix(DARK, MATCH_HUE, MATCH_TINT)
    light = _mix(LIGHT, MATCH_HUE, MATCH_TINT)
    assert _luma(dark) < _luma(light)          # dark theme -> dark wash, light -> pale
    for band in (dark, light):
        assert band[1] > band[0] and band[1] > band[2]   # green-tinted on both


def test_text_match_backgrounds_track_theme():
    for current in (False, True):
        dark = _match_bg(DARK, current)
        light = _match_bg(LIGHT, current)
        assert _luma(dark) < _luma(light)
        # amber wash: red & green above blue on both polarities
        assert dark[0] > dark[2] and dark[1] > dark[2]
        assert light[0] > light[2] and light[1] > light[2]


def test_current_match_is_firmer_than_plain_match():
    # On a dark theme the current match is darker/more saturated (further from bg);
    # either way it is visually distinct from a plain match.
    assert _match_bg(DARK, True) != _match_bg(DARK, False)
    assert _match_bg(LIGHT, True) != _match_bg(LIGHT, False)
