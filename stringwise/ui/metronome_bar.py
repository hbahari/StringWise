"""Controls for the shared metronome. Any number of these can be on screen."""

from __future__ import annotations

from kivy.app import App
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.uix.widget import Widget

from .. import theme
from ..audio.metronome import BEATS_PER_BAR
from ..theme import rgba
from .widgets import Box, Btn, Chip, Txt, row, small


class BeatDots(Widget):
    """Four dots, one per beat. The current one swells on the click and settles
    back before the next. Beat 1 is larger. In a silent drop-out bar the moving
    dot is hollow."""

    def __init__(self, dark=False, gap=30, size=7.0, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(30))
        super().__init__(**kwargs)
        self.state = None
        self._gap, self._size = dp(gap), dp(size)
        self._idle = theme.ON_WOOD_SOFT if dark else theme.INK_SOFT
        self._live = theme.CREAM if dark else theme.VARNISH
        self._first = theme.WARN_LIGHT if dark else theme.VARNISH_DARK
        self.bind(pos=self._draw, size=self._draw)

    def show(self, state):
        if state != self.state:
            self.state = state
            self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        beat, silent, phase = (self.state[0], self.state[1], self.state[3]) if self.state else (None, False, 0.0)
        left = self.x + self.width / 2 - self._gap * (BEATS_PER_BAR - 1) / 2
        cy = self.y + self.height / 2
        with self.canvas:
            for i in range(BEATS_PER_BAR):
                base = self._size * (1.25 if i == 0 else 1.0)
                cx = left + i * self._gap
                if i != beat:
                    Color(*rgba(self._idle, 0.38))
                    radius = base * 0.62
                    Ellipse(pos=(cx - radius, cy - radius), size=(radius * 2, radius * 2))
                    continue
                radius = base * (1.3 - 0.45 * min(1.0, phase * 1.6))      # swell, then settle
                color = self._first if i == 0 else self._live
                if silent:
                    Color(*rgba(color, 0.8))
                    Line(circle=(cx, cy, radius), width=dp(1.4))
                else:
                    Color(*rgba(color, 0.22))
                    halo = radius * 1.45
                    Ellipse(pos=(cx - halo, cy - halo), size=(halo * 2, halo * 2))
                    Color(*rgba(color))
                    Ellipse(pos=(cx - radius, cy - radius), size=(radius * 2, radius * 2))


class MetronomeBar(Box):
    """Tempo display, start/stop, tap tempo and the two click options.

    ``presets`` adds quick tempo buttons. Tapping one also applies
    ``preset_subdivide`` and ``preset_gaps``, so a lesson can set the metronome
    up exactly as its study needs.
    """

    def __init__(self, presets=(), preset_subdivide=False, preset_gaps=False,
                 preset_label="{}", **kwargs):
        kwargs.setdefault("spacing", dp(10))
        super().__init__(**kwargs)
        self.metronome = App.get_running_app().metronome
        self._preset_flags = (preset_subdivide, preset_gaps)

        self.dots = BeatDots()
        self.add_widget(self.dots)
        self.tempo = Txt("", size=40, font=theme.FONT_HEAD, halign="center")
        self.add_widget(self.tempo)
        self._caption_text = "beats a minute"
        self.caption = small(self._caption_text, halign="center")
        self.add_widget(self.caption)

        self.add_widget(row(
            Btn("− slower", kind="outline", height=dp(44), on_release=lambda _b: self._nudge(-2)),
            Btn("faster +", kind="outline", height=dp(44), on_release=lambda _b: self._nudge(2)),
            Btn("Tap tempo", kind="outline", height=dp(44), on_release=lambda _b: self.metronome.tap()),
            height=44, spacing=8))

        self.preset_chips = {}
        if presets:
            chips = row(height=40, spacing=8)
            for bpm in presets:
                chip = Chip(preset_label.format(bpm))
                chip.bind(on_release=lambda _c, bpm=bpm: self._preset(bpm))
                self.preset_chips[bpm] = chip
                chips.add_widget(chip)
            self.add_widget(chips)

        self.eighths = Chip("Eighth notes")
        self.eighths.bind(on_release=lambda _c: self.metronome.configure(subdivide=not self.metronome.subdivide))
        self.dropout = Chip("Drop-out bars")
        self.dropout.bind(on_release=lambda _c: self.metronome.configure(gaps=not self.metronome.gaps))
        self.add_widget(row(self.eighths, self.dropout, height=40, spacing=8))

        self.toggle = Btn("", on_release=lambda _b: self.metronome.toggle())
        self.add_widget(self.toggle)

        self.metronome.watch(self)
        self.sync()

    def _nudge(self, change):
        self.metronome.configure(bpm=self.metronome.bpm + change)

    def _preset(self, bpm):
        subdivide, gaps = self._preset_flags
        self.metronome.configure(bpm=bpm, subdivide=subdivide, gaps=gaps)

    # -- called by the metronome -------------------------------------------
    def sync(self):
        metronome = self.metronome
        self.tempo.set(str(metronome.bpm))
        self.toggle.set("Stop metronome" if metronome.running else "Start metronome")
        self.eighths.selected = metronome.subdivide
        self.dropout.selected = metronome.gaps
        for bpm, chip in self.preset_chips.items():
            chip.selected = bpm == metronome.bpm
        if not metronome.running:
            self.dots.show(None)
            self._caption("beats a minute")

    def tick(self, state):
        self.dots.show(state)
        if state is None or not self.metronome.gaps:
            self._caption("beats a minute")
        else:
            _beat, silent, bar, _phase = state
            self._caption(f"silent bar {bar - 1} of 2. Keep the beat going." if silent
                          else f"click bar {bar + 1} of 2. Two silent bars follow.")

    def _caption(self, text):
        if self._caption_text != text:
            self._caption_text = text
            self.caption.set(text)
