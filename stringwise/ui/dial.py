"""The tuner needle: a half-dial showing 50 cents flat to 50 cents sharp."""

from __future__ import annotations

import math

from kivy.graphics import Color, Ellipse, Line, Triangle
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.widget import Widget

from .. import theme
from ..theme import rgba
from .widgets import draw_text

SWING = 45.0            # degrees of needle travel for 50 cents
ZONES = (               # (from angle, to angle, colour); green is +/-12 cents
    (-45.0, -31.5, theme.BAD_LIGHT),
    (-31.5, -10.8, theme.WARN_LIGHT),
    (-10.8, 10.8, theme.GOOD_LIGHT),
    (10.8, 31.5, theme.WARN_LIGHT),
    (31.5, 45.0, theme.BAD_LIGHT),
)
CAPTION_COLORS = {"in_tune": theme.GOOD_LIGHT, "correct": theme.GOOD_LIGHT,
                  "near": theme.WARN_LIGHT, "close": theme.WARN_LIGHT,
                  "far": theme.BAD_LIGHT, "off": theme.BAD_LIGHT}


class Dial(Widget):
    cents = NumericProperty(0.0, allownone=True)
    caption = StringProperty("")
    verdict = StringProperty("", allownone=True)

    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, **kwargs)
        self.bind(width=self._size, pos=self._draw, size=self._draw,
                  cents=self._draw, caption=self._draw, verdict=self._draw)

    def _size(self, *_):
        self.height = min(dp(210), self.width * 0.56)

    def show(self, cents, caption="", verdict=None):
        self.cents, self.caption, self.verdict = cents, caption, verdict or ""

    def _draw(self, *_):
        self.canvas.clear()
        cx = self.x + self.width / 2      # not center_x: that shortcut can lag during layout
        cy = self.y + dp(22)
        radius = min(self.height - dp(40), self.width * 0.46)
        if radius <= 0:
            return
        angle = 0.0 if self.cents is None else max(-50.0, min(50.0, self.cents)) / 50.0 * SWING
        with self.canvas:
            for start, end, color in ZONES:
                Color(*rgba(color))
                Line(circle=(cx, cy, radius, start, end), width=dp(6), cap="none")
            Color(*rgba(theme.ON_WOOD_SOFT, 0.35))
            Line(points=[cx, cy + radius - dp(14), cx, cy + radius * 0.2], width=1, dash_length=dp(3), dash_offset=dp(4))
            for sign, glyph in ((-1, "♭"), (1, "♯")):
                a = math.radians(sign * 60)
                draw_text(glyph, cx + radius * math.sin(a), cy + radius * math.cos(a),
                          dp(17), theme.ON_WOOD_SOFT, font=theme.FONT_SYMBOL)
            if self.caption:
                draw_text(self.caption, cx, cy + radius * 0.48, dp(15),
                          CAPTION_COLORS.get(self.verdict or "", theme.CREAM), is_bold=True)
            # needle
            a = math.radians(angle)
            length = radius - dp(12)
            tip = (cx + length * math.sin(a), cy + length * math.cos(a))
            half = dp(4)
            base_l = (cx - half * math.cos(a), cy + half * math.sin(a))
            base_r = (cx + half * math.cos(a), cy - half * math.sin(a))
            Color(*rgba(theme.CREAM))
            Triangle(points=[*base_l, *tip, *base_r])
            Color(*rgba(theme.WOOD_DEEP))
            Ellipse(pos=(cx - dp(10), cy - dp(10)), size=(dp(20), dp(20)))
            Color(*rgba(theme.ON_WOOD_SOFT))
            Line(circle=(cx, cy, dp(10)), width=1.2)
            Color(*rgba(theme.CREAM))
            Ellipse(pos=(cx - dp(3), cy - dp(3)), size=(dp(6), dp(6)))
