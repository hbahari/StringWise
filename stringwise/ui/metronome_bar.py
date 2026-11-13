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
    """Four dots, one per beat. The current beat lights up; beat 1 is larger."""

    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(26), **kwargs)
        self.state = None
        self.bind(pos=self._draw, size=self._draw)

    def show(self, state):
        if state != self.state:
            self.state = state
            self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        beat, silent = self.state[:2] if self.state else (None, False)
        gap = dp(30)
        left = self.x + self.width / 2 - gap * (BEATS_PER_BAR - 1) / 2
        cy = self.y + self.height / 2
        with self.canvas:
            for i in range(BEATS_PER_BAR):
                radius = dp(9 if i == 0 else 7)
                cx = left + i * gap
                if i == beat:
                    # solid in a clicking bar, pale in a silent drop-out bar
                    Color(*rgba(theme.VARNISH, 0.35 if silent else 1.0))
                    Ellipse(pos=(cx - radius, cy - radius), size=(radius * 2, radius * 2))
                else:
                    Color(*rgba(theme.INK_SOFT, 0.45))
                    Line(circle=(cx, cy, radius), width=dp(1.1))


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
            _beat, silent, bar = state
            self._caption(f"silent bar {bar - 1} of 2. Keep the beat going." if silent
                          else f"click bar {bar + 1} of 2. Two silent bars follow.")

    def _caption(self, text):
        if self._caption_text != text:
            self._caption_text = text
            self.caption.set(text)
