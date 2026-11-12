"""A map of first position. Tap a dot to hear its note."""

from __future__ import annotations

from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.widget import Widget

from .. import theme
from ..music.fingering import FINGER_POSITIONS, STRINGS
from ..music.notes import pretty
from ..theme import rgba
from .widgets import draw_text

ROW = 54        # dp between strings
TOP = 40        # dp above the first string, room for the spacing labels
DOT = 13        # dp dot radius


class Fingerboard(Widget):
    def __init__(self, on_note=None, **kwargs):
        super().__init__(size_hint_y=None, height=dp(TOP + ROW * 4 + 6), **kwargs)
        self.on_note = on_note
        self._pressed = None
        self._dots = []          # (x, y, string name, finger)
        self.bind(pos=self._draw, size=self._draw)

    def _dot_xs(self):
        """x of the nut line and of the five dots. Fingers are spaced as on a real string."""
        right = self.x + self.width
        open_x = self.x + dp(62)
        nut = open_x + dp(DOT + 9)
        scale = (right - dp(DOT + 12) - nut) / FINGER_POSITIONS[4]
        return nut, [open_x] + [nut + FINGER_POSITIONS[f] * scale for f in (1, 2, 3, 4)]

    def _draw(self, *_):
        self.canvas.clear()
        self._dots = []
        if self.width < dp(200):
            return
        nut, xs = self._dot_xs()
        right, top = self.x + self.width, self.y + self.height
        with self.canvas:
            Color(*rgba(theme.WOOD))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
            Color(*rgba(theme.WOOD_DEEP))
            RoundedRectangle(pos=(nut, self.y + dp(8)), size=(right - nut - dp(8), self.height - dp(TOP) + dp(4)),
                             radius=[dp(4)])

            # spacing labels above the top string
            label_y = top - dp(15)
            for a, b, text in ((1, 2, "whole"), (2, 3, "half"), (3, 4, "whole")):
                mid = (xs[a] + xs[b]) / 2
                emphasised = text == "half"
                color = theme.WARN_LIGHT if emphasised else theme.ON_WOOD_SOFT
                draw_text(text, mid, label_y, dp(11.5), color, is_bold=emphasised)
                Color(*rgba(color, 0.9 if emphasised else 0.45))
                Line(points=[xs[a] + dp(4), label_y - dp(10), xs[b] - dp(4), label_y - dp(10)], width=1)
            draw_text("nut", nut, label_y, dp(11.5), theme.ON_WOOD_SOFT)

            for row_index, string in enumerate(reversed(STRINGS)):       # E at the top
                y = top - dp(TOP) - dp(ROW) * row_index - dp(14)
                Color(*rgba(theme.STRING_COLORS[string.name]))
                Line(points=[xs[0], y, right - dp(8), y], width=dp(0.8 + 0.3 * row_index))
                draw_text(string.name, self.x + dp(22), y, dp(19), theme.CREAM, font=theme.FONT_HEAD)
                for finger, x in enumerate(xs):
                    note = string.notes[finger]
                    pressed = self._pressed == (string.name, finger)
                    Color(*rgba(theme.FINGER_COLORS[finger]))
                    Ellipse(pos=(x - dp(DOT), y - dp(DOT)), size=(dp(DOT * 2), dp(DOT * 2)))
                    Color(*rgba(theme.CREAM, 1.0 if pressed else 0.55))
                    Line(circle=(x, y, dp(DOT + (3 if pressed else 0))), width=dp(1.6 if pressed else 1))
                    draw_text(str(finger), x, y, dp(14), theme.INK if finger == 0 else theme.PAPER, is_bold=True)
                    draw_text(pretty(note.name), x, y - dp(DOT + 10), dp(11.5), theme.ON_WOOD_SOFT,
                              font=theme.FONT_SYMBOL)
                    self._dots.append((x, y, string.name, finger))
            Color(*rgba(theme.CREAM))
            Line(points=[nut, self.y + dp(8), nut, top - dp(TOP) + dp(12)], width=dp(1.5), cap="none")

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        reach = dp(DOT + 10) ** 2
        for x, y, string, finger in self._dots:
            if (touch.x - x) ** 2 + (touch.y - y) ** 2 <= reach:
                self._pressed = (string, finger)
                self._draw()
                Clock.schedule_once(self._release, 0.35)
                if self.on_note:
                    self.on_note(string, finger)
                return True
        return super().on_touch_down(touch)

    def _release(self, _dt):
        self._pressed = None
        self._draw()
