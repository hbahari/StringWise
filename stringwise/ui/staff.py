"""Sheet music drawn straight onto a Kivy canvas."""

from __future__ import annotations

from kivy.graphics import (Color, Ellipse, Line, PopMatrix, PushMatrix, Rectangle, Rotate)
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from .. import theme
from ..music.notes import ledger_steps
from ..theme import rgba
from . import staff_layout as sl
from .widgets import draw_text

CURSOR_COLORS = {"correct": theme.GOOD, "close": theme.WARN, "wrong": theme.BAD}
_clef_texture = None


def _clef():
    global _clef_texture
    if _clef_texture is None:
        _clef_texture = CoreImage(theme.asset("images", "treble-clef.png")).texture
    return _clef_texture


class Staff(Widget):
    """One line of music.

    ``done`` notes are drawn green, ``current`` gets a soft highlight, and
    ``cursor_step`` places a dot showing the pitch the microphone hears.
    """

    def __init__(self, notes, scale=1.0, paper=theme.PAPER, show_fingers=True, **kwargs):
        super().__init__(size_hint=(None, None), **kwargs)
        self.notes = list(notes)
        self.unit = dp(1) * scale
        self.paper = paper
        self.show_fingers = show_fingers
        self.layout = sl.layout(self.notes)
        self.size = (self.layout.width * self.unit, sl.HEIGHT * self.unit)
        self.done = 0
        self.current = None
        self.cursor_step = None
        self.cursor_kind = "close"
        self.bind(pos=self._draw)
        self._draw()

    # -- public ----------------------------------------------------------
    def set_state(self, done=0, current=None, cursor_step=None, cursor_kind="close"):
        state = (done, current, cursor_step, cursor_kind)
        if state != (self.done, self.current, self.cursor_step, self.cursor_kind):
            self.done, self.current, self.cursor_step, self.cursor_kind = state
            self._draw()

    def note_x(self, index: int) -> float:
        """Distance of a note from the left edge of the staff, in pixels."""
        index = max(0, min(index, len(self.notes) - 1))
        return self.layout.xs[index] * self.unit

    # -- drawing ---------------------------------------------------------
    def _draw(self, *_):
        u = self.unit
        ox, oy = self.x, self.y
        lay = self.layout
        ink = rgba(theme.INK)
        line_color = rgba(theme.WOOD_LINE, 0.8)

        def X(v):
            return ox + v * u

        def Y(step):
            return oy + sl.y_for_step(step) * u

        self.canvas.clear()
        with self.canvas:
            # staff lines, clef, time signature
            Color(*line_color)
            for step in (0, 2, 4, 6, 8):
                Line(points=[X(8), Y(step), X(lay.end_x), Y(step)], width=1)
            clef = _clef()
            clef_h = 88 * u
            Color(*rgba(theme.WOOD_LINE))
            Rectangle(texture=clef, pos=(X(sl.CLEF_X), Y(0) - 19 * u),
                      size=(clef_h * clef.width / clef.height, clef_h))
            for step in (6, 2):
                draw_text("4", X(sl.TIME_X), Y(step) + 1 * u, 30 * u, theme.WOOD_LINE, font=theme.FONT_HEAD)

            # bar lines
            Color(*line_color)
            for bar_x in lay.barlines:
                Line(points=[X(bar_x), Y(0), X(bar_x), Y(8)], width=1)
            Color(*ink)
            Line(points=[X(lay.end_x - 5), Y(0), X(lay.end_x - 5), Y(8)], width=1)
            Line(points=[X(lay.end_x), Y(0), X(lay.end_x), Y(8)], width=1.6 * u, cap="none")

            # highlight behind the note being asked for
            if self.current is not None and self.current < len(self.notes):
                cx = X(lay.xs[self.current])
                cy = Y(self.notes[self.current].staff_step)
                Color(*rgba(theme.VARNISH, 0.26))
                Ellipse(pos=(cx - 13 * u, cy - 13 * u), size=(26 * u, 26 * u))

            stem_ends = {}
            for i, note in enumerate(self.notes):
                color = rgba(theme.GOOD) if i < self.done else ink
                cx, step = X(lay.xs[i]), note.staff_step
                cy = Y(step)

                Color(*line_color)
                for ledger in ledger_steps(step):
                    Line(points=[cx - 11 * u, Y(ledger), cx + 11 * u, Y(ledger)], width=1)
                if note.is_sharp:
                    draw_text("♯", cx - 16 * u, cy, 17 * u, theme.INK, font=theme.FONT_SYMBOL)

                whole = note.beats == 4
                hollow = note.beats >= 2
                if not whole:
                    up = lay.stems_up[i]
                    sx = cx + (6.1 if up else -6.1) * u
                    end = cy + (sl.STEM if up else -sl.STEM) * u
                    stem_ends[i] = (sx, end, up)
                    Color(*color)
                    Line(points=[sx, cy + (1.5 if up else -1.5) * u, sx, end], width=0.8 * u, cap="none")
                    if i in lay.flags:
                        d = -1 if up else 1
                        Line(bezier=[sx, end, sx + 2 * u, end + d * 10 * u,
                                     sx + 12 * u, end + d * 14 * u, sx + 9 * u, end + d * 26 * u],
                             width=0.9 * u)

                self._head(cx, cy, 7.4 * u if whole else 6.6 * u, 4.9 * u, color, hollow, whole)

                if note.beats in (1.5, 3.0):
                    dot_y = cy + (sl.HALF_SPACE * u if step % 2 == 0 else 0)
                    Color(*color)
                    Ellipse(pos=(cx + 10 * u, dot_y - 1.8 * u), size=(3.6 * u, 3.6 * u))

                finger = lay.fingers[i]
                if self.show_fingers and finger is not None:
                    draw_text(str(finger), cx, oy + sl.FINGER_ROW_Y * u, 11.5 * u,
                              theme.INK_SOFT if finger == 0 else theme.FINGER_COLORS[finger], is_bold=True)

            # beams joining pairs of eighth notes
            for first, second in lay.beams:
                (x1, e1, up), (x2, e2, _) = stem_ends[first], stem_ends[second]
                level = max(e1, e2) if up else min(e1, e2)
                Color(*(rgba(theme.GOOD) if second < self.done else ink))
                for sx, cy_note in ((x1, Y(self.notes[first].staff_step)), (x2, Y(self.notes[second].staff_step))):
                    Line(points=[sx, cy_note, sx, level], width=0.8 * u, cap="none")
                thickness = 4.6 * u
                Rectangle(pos=(x1 - 0.8 * u, level - (thickness if up else 0)), size=(x2 - x1 + 1.6 * u, thickness))

            # the pitch being heard
            if self.cursor_step is not None and self.current is not None and self.current < len(self.notes):
                step = max(-8, min(13, self.cursor_step))
                cx, cy = X(lay.xs[self.current]), Y(step)
                Color(*line_color)
                for ledger in ledger_steps(step):
                    Line(points=[cx - 11 * u, Y(ledger), cx + 11 * u, Y(ledger)], width=1)
                Color(*rgba(CURSOR_COLORS[self.cursor_kind], 0.92))
                Ellipse(pos=(cx - 7 * u, cy - 7 * u), size=(14 * u, 14 * u))
                Color(*rgba(theme.PAPER, 0.9))
                Line(circle=(cx, cy, 7 * u), width=1)

    def _head(self, cx, cy, rx, ry, color, hollow, whole):
        PushMatrix()
        Rotate(angle=0 if whole else 20, origin=(cx, cy))
        Color(*color)
        Ellipse(pos=(cx - rx, cy - ry), size=(2 * rx, 2 * ry))
        PopMatrix()
        if hollow:
            PushMatrix()
            Rotate(angle=-35 if whole else 32, origin=(cx, cy))
            Color(*rgba(self.paper))
            inner_x, inner_y = (rx * 0.55, ry * 0.72) if whole else (rx * 0.80, ry * 0.46)
            Ellipse(pos=(cx - inner_x, cy - inner_y), size=(2 * inner_x, 2 * inner_y))
            PopMatrix()


class StaffScroller(ScrollView):
    """A staff that scrolls sideways and can keep one note in view."""

    def __init__(self, notes, scale=1.0, paper=theme.PAPER, **kwargs):
        self.staff = Staff(notes, scale=scale, paper=paper)
        super().__init__(do_scroll_y=False, size_hint_y=None, height=self.staff.height,
                         bar_width=dp(3), scroll_type=["bars", "content"], **kwargs)
        self.add_widget(self.staff)

    def follow(self, index: int) -> None:
        spare = self.staff.width - self.width
        if spare <= 0:
            self.scroll_x = 0
            return
        wanted = self.staff.note_x(index) - self.width * 0.35
        self.scroll_x = max(0.0, min(1.0, wanted / spare))
