from __future__ import annotations

from kivy.metrics import dp

from ... import theme
from ...content import tuner as text
from ...logic.tuner import Tuner
from ...music.fingering import STRINGS
from ..dial import Dial
from ..widgets import Btn, Chip, Meter, Txt, row, small, title, wood_card
from .base import ListeningScreen

ADVICE_COLORS = {"in_tune": theme.GOOD_LIGHT, "near": theme.WARN_LIGHT, "far": theme.WARN_LIGHT}


class TunerScreen(ListeningScreen):
    def __init__(self, **kwargs):
        super().__init__(name="tuner", **kwargs)
        self.logic = Tuner(self.app.listener.frame_rate)
        self.reference = STRINGS[2]            # the A string

        page = self.page
        page.add(title("Tuner"))
        page.add(Txt(text.INTRO, color=theme.INK_SOFT))

        panel = page.add(wood_card(spacing=dp(8)))
        self.status = Txt("", size=13, color=theme.ON_WOOD_SOFT, halign="center")
        panel.add_widget(self.status)
        self.level_meter = Meter()
        panel.add_widget(self.level_meter)
        self.note = Txt("–", size=64, font=theme.FONT_HEAD, color=theme.CREAM, halign="center")
        panel.add_widget(self.note)
        self.detail = Txt(" ", size=13, color=theme.ON_WOOD_SOFT, halign="center")
        panel.add_widget(self.detail)
        self.dial = Dial()
        panel.add_widget(self.dial)
        self.advice = Txt(" ", size=15, color=theme.CREAM, halign="center")
        panel.add_widget(self.advice)

        self.mic_button = Btn("Start listening", on_release=self.toggle_listening)
        self.play_button = Btn("", kind="outline_dark", on_release=self.play_reference)
        panel.add_widget(row(self.mic_button, self.play_button))

        self.chips = {}
        chip_row = row(height=58, spacing=8)
        for string in STRINGS:
            chip = Chip(f"[size=20sp]{string.name}[/size]\n[size=11sp]{string.open_hz:.1f} Hz[/size]",
                        dark=True, height=dp(58))
            chip.bind(on_release=lambda _c, s=string: self.choose_string(s))
            self.chips[string.name] = chip
            chip_row.add_widget(chip)
        panel.add_widget(chip_row)

        for paragraph in text.HELP:
            page.add(small(paragraph))
        page.add(small(text.FOOTER, color=theme.VARNISH_DARK))

        self.choose_string(self.reference, play=False)
        self.refresh()

    def choose_string(self, string, play=True):
        self.reference = string
        for name, chip in self.chips.items():
            chip.selected = name == string.name
        self.play_button.set(f"Play {string.name}")
        if play:
            self.play_reference()

    def play_reference(self, *_):
        self.app.tones.play_tone(self.reference.open_hz, 1.6)

    # -- listening -----------------------------------------------------------
    def listening_started(self):
        self.logic.start()
        self.refresh()

    def listening_stopped(self):
        self.logic.stop()
        self.refresh()

    def handle_frame(self, frame):
        self.logic.feed(frame.freq, frame.rms)

    def show_status(self, message):
        self.status.set(message)

    def refresh(self):
        view = self.logic.view
        self.status.set(view.status)
        self.note.set(view.note or "–")
        self.detail.set(view.detail or " ")
        self.dial.show(view.cents, view.caption, view.verdict)
        self.advice.set(view.advice or " ", ADVICE_COLORS.get(view.verdict, theme.CREAM))
