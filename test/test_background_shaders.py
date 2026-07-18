"""TFM's GPU background shaders: the registry, how a theme resolves one, and that
each shader actually compiles and draws.

The compile/draw tests use puikit's offscreen Metal path, so the real fragment
shader is built by the real Metal compiler with no window involved. They skip
where Metal is unavailable.

Run with: PYTHONPATH=.:src pytest test/test_background_shaders.py -v
"""

import unittest

import pytest

from puikit.background import SHADER_ENTRY, Background3D, Shader
from puikit.backends._metal import HAVE_METAL, MetalBackground

import tfm
from tfm_background_shaders import SHADER_KINDS

metal_only = pytest.mark.skipif(not HAVE_METAL, reason="Metal unavailable")

_INK, _BACKDROP = (200, 224, 245), (16, 30, 50)


def _shader(kind):
    return Shader(ink=_INK, backdrop=_BACKDROP, **SHADER_KINDS[kind])


class Registry(unittest.TestCase):

    def test_expected_shaders_are_offered(self):
        self.assertEqual(set(SHADER_KINDS), {"wave"})

    def test_each_entry_is_valid_shader_kwargs(self):
        # The dict is splatted straight into Shader(...), so a stray key would
        # only show up as a TypeError at theme-apply time.
        for kind, params in SHADER_KINDS.items():
            self.assertIn("source", params, kind)
            Shader(**params)

    def test_names_do_not_collide_with_the_segment_scenes(self):
        # Both kinds share the theme's ``animation`` namespace, so a name in both
        # would resolve ambiguously depending on which branch is checked first.
        from tfm_background_animations import ANIMATION_KINDS
        self.assertEqual(set(SHADER_KINDS) & set(ANIMATION_KINDS), set())

    def test_sources_define_the_entry_point(self):
        for kind, params in SHADER_KINDS.items():
            self.assertIn(SHADER_ENTRY, params["source"], kind)


class ThemeResolution(unittest.TestCase):
    """A theme names a scene; TFM picks the descriptor its renderer needs."""

    def _resolve(self, animation):
        return tfm._resolve_background(animation, None, color=_INK, backdrop=_BACKDROP)

    def test_a_shader_name_resolves_to_a_shader(self):
        bg = self._resolve("wave")
        self.assertIsInstance(bg, Shader)
        self.assertEqual(bg.ink, _INK)         # theme fg arrives as the ink uniform
        self.assertEqual(bg.backdrop, _BACKDROP)

    def test_a_segment_name_still_resolves_to_an_animation(self):
        self.assertIsInstance(self._resolve("starfield"), Background3D)

    def test_tuned_defaults_apply_to_shaders_too(self):
        bg = self._resolve("wave")
        self.assertEqual((bg.speed, bg.opacity),
                         (tfm._ANIM_DEFAULTS["speed"], tfm._ANIM_DEFAULTS["opacity"]))

    def test_params_dict_overrides_carry_through(self):
        bg = self._resolve({"type": "wave", "speed": 1.4, "opacity": 0.9})
        self.assertIsInstance(bg, Shader)
        self.assertEqual((bg.speed, bg.opacity), (1.4, 0.9))

    def test_scene_owned_fields_are_not_theme_overridable(self):
        # resolution_scale is a property of the scene (how much sharpness it can
        # give up), not of the theme, so it comes from the registry either way.
        bg = self._resolve({"type": "wave", "speed": 2.0})
        self.assertEqual(bg.resolution_scale, SHADER_KINDS["wave"]["resolution_scale"])

    def test_an_unknown_name_still_degrades_to_an_animation(self):
        # Unknown names must not crash startup; they resolve to a Background3D
        # whose kind simply is not registered, and the backend draws nothing.
        self.assertIsInstance(self._resolve("no-such-scene"), Background3D)


@metal_only
class Compilation(unittest.TestCase):
    """Every shipped shader must build with the real Metal compiler."""

    def test_every_shader_compiles(self):
        renderer = MetalBackground()
        for kind in SHADER_KINDS:
            ok = renderer.set_shader(_shader(kind))
            self.assertTrue(ok, f"{kind} failed to compile:\n{renderer.error}")

    def test_every_shader_draws_something(self):
        renderer = MetalBackground()
        for kind in SHADER_KINDS:
            self.assertTrue(renderer.set_shader(_shader(kind)), renderer.error)
            px = MetalBackground.texture_pixels(
                renderer.render_to_texture(160, 100, 3.0))
            distinct = {bytes(px[i:i + 4]) for i in range(0, len(px), 4)}
            self.assertGreater(len(distinct), 8, f"{kind} drew a flat frame")

    def test_wave_animates(self):
        renderer = MetalBackground()
        self.assertTrue(renderer.set_shader(_shader("wave")), renderer.error)
        a = MetalBackground.texture_pixels(renderer.render_to_texture(160, 100, 0.0))
        b = MetalBackground.texture_pixels(renderer.render_to_texture(160, 100, 3.0))
        self.assertNotEqual(bytes(a), bytes(b))

    def test_wave_is_frozen_at_zero_speed(self):
        # Same contract the segment scenes honour: speed scales the time uniform.
        renderer = MetalBackground()
        frozen = Shader(speed=0.0, ink=_INK, backdrop=_BACKDROP, **SHADER_KINDS["wave"])
        self.assertTrue(renderer.set_shader(frozen), renderer.error)
        a = MetalBackground.texture_pixels(renderer.render_to_texture(120, 80, 0.0))
        b = MetalBackground.texture_pixels(renderer.render_to_texture(120, 80, 9.0))
        self.assertEqual(bytes(a), bytes(b))

    def test_wave_follows_the_theme_ink(self):
        # The gradient is the ink pushed apart, not fixed colours, so a different
        # palette must produce a visibly different frame.
        renderer = MetalBackground()
        self.assertTrue(renderer.set_shader(
            Shader(ink=(200, 224, 245), backdrop=_BACKDROP, **SHADER_KINDS["wave"])))
        blue = MetalBackground.texture_pixels(renderer.render_to_texture(120, 80, 2.0))
        self.assertTrue(renderer.set_shader(
            Shader(ink=(51, 245, 121), backdrop=_BACKDROP, **SHADER_KINDS["wave"])))
        green = MetalBackground.texture_pixels(renderer.render_to_texture(120, 80, 2.0))
        self.assertNotEqual(bytes(blue), bytes(green))

    def test_wave_respects_the_backdrop(self):
        # Where the sheet is absent the frame must be the theme background, or a
        # light theme would show a dark void behind the panes.
        renderer = MetalBackground()
        self.assertTrue(renderer.set_shader(_shader("wave")), renderer.error)
        px = MetalBackground.texture_pixels(renderer.render_to_texture(120, 80, 2.0))
        top_left = (px[2], px[1], px[0])   # BGRA -> RGB; empty sky above the wave
        self.assertTrue(all(abs(a - b) <= 2 for a, b in zip(top_left, _BACKDROP)),
                        top_left)


if __name__ == "__main__":
    unittest.main()
