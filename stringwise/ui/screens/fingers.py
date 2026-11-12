from __future__ import annotations

import os

from kivy.metrics import dp
from kivy.uix.image import Image

from ... import theme
from ...content import fingers as text
from ...logic.fingercheck import FingerCheck
from ...music.fingering import STRINGS, target_note
from ...music.notes import pretty
from ..dial import Dial
from ..fingerboard import Fingerboard
from ..widgets import Btn, Chip, Meter, Txt, bullets, card, row, small, subtitle, title, wood_card
from .base import ListeningScreen

VERDICT_COLORS = {"correct": theme.GOOD_LIGHT, "close": theme.WARN_LIGHT, "off": theme.BAD_LIGHT}


class FingersScreen(ListeningScreen):
    def __init__(self, **kwargs):
        super().__init__(name="fingers", **kwargs)
        self.logic = FingerCheck(self.app.listener.frame_rate)

        page = self.page
        page.add(title("Finger Placement"))
        page.add(Txt(text.INTRO, color=theme.INK_SOFT))
        page.add(Fingerboard(on_note=self._tapped))
        page.add(small(text.CAPTION))
        page.add(Txt(text.SPACING))

        page.add(self._hand_card(text.LEFT_HAND_TITLE, text.LEFT_HAND, text.LEFT_HAND_PHOTOS))
        page.add(self._hand_card(text.BOW_HOLD_TITLE, text.BOW_HOLD, text.BOW_HOLD_PHOTOS))

        page.add(subtitle(text.CHECKER_TITLE))
        page.add(Txt(text.CHECKER_INTRO, color=theme.INK_SOFT))
        panel = page.add(wood_card(spacing=dp(8)))

        panel.add_widget(small("String", color=theme.ON_WOOD_SOFT))
        self.string_chips = {}
        chips = row(height=40, spacing=8)
        for string in STRINGS:
            chip = Chip(string.name, dark=True)
            chip.bind(on_release=lambda _c, name=string.name: self._choose(string=name))
            self.string_chips[string.name] = chip
            chips.add_widget(chip)
        panel.add_widget(chips)

        panel.add_widget(small("Finger (0 is the open string)", color=theme.ON_WOOD_SOFT))
        self.finger_chips = {}
        chips = row(height=40, spacing=8)
        for finger in range(5):
            chip = Chip(str(finger), dark=True)
            chip.bind(on_release=lambda _c, f=finger: self._choose(finger=f))
            self.finger_chips[finger] = chip
            chips.add_widget(chip)
        panel.add_widget(chips)

        self.target = Txt("", size=17, color=theme.CREAM, halign="center")
        self.status = Txt("", size=13, color=theme.ON_WOOD_SOFT, halign="center")
        self.heard = Txt(" ", size=13, color=theme.ON_WOOD_SOFT, halign="center")
        self.level_meter = Meter()
        self.dial = Dial()
        self.verdict = Txt(" ", size=15, color=theme.CREAM, halign="center")
        for widget in (self.target, self.status, self.heard, self.level_meter, self.dial, self.verdict):
            panel.add_widget(widget)
        self.mic_button = Btn("Start listening", on_release=self.toggle_listening)
        panel.add_widget(row(self.mic_button,
                             Btn("Hear the note", kind="outline_dark", on_release=self._hear_target)))
        self._choose()

    def _hand_card(self, heading, points, photo_names):
        panel = card()
        panel.add_widget(subtitle(heading))
        for name in photo_names:
            path = theme.asset("photos", name)
            if os.path.exists(path):
                image = Image(source=path, size_hint_y=None, fit_mode="contain")
                image.bind(width=lambda widget, width: setattr(
                    widget, "height", width / max(widget.image_ratio, 0.1)))
                panel.add_widget(image)
        panel.add_widget(bullets(points))
        return panel

    # -- fingerboard and selectors ------------------------------------------------
    def _tapped(self, string, finger):
        self.app.tones.play_tone(target_note(string, finger).freq, 0.9)

    def _choose(self, string=None, finger=None):
        self.logic.choose(string, finger)
        for name, chip in self.string_chips.items():
            chip.selected = name == self.logic.string
        for number, chip in self.finger_chips.items():
            chip.selected = number == self.logic.finger
        note = self.logic.target
        self.target.set(f"Play {pretty(note.name)} ({note.freq:.1f} Hz)")
        self.refresh()

    def _hear_target(self, *_):
        self.app.tones.play_tone(self.logic.target.freq)

    # -- listening ------------------------------------------------------------------
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
        self.heard.set(view.heard or " ")
        self.dial.show(view.cents, view.caption, view.verdict)
        self.verdict.set(view.message or " ", VERDICT_COLORS.get(view.verdict, theme.CREAM))
