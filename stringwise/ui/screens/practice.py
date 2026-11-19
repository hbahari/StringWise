from __future__ import annotations

import datetime

from kivy.metrics import dp, sp
from kivy.uix.spinner import Spinner

from ... import theme
from ...content import practice as text
from ...content.lessons import piece_menu
from ...content.practice import ROUTINE
from ...music.rhythms import rhythm_menu, rhythm_of_the_day
from ...theme import rgba
from ..staff import StaffScroller
from ..widgets import Box, Btn, CheckRow, HearButton, Meter, Txt, card, small, subtitle, title
from .base import PageScreen
from .playalong import PieceOption

STORE_KEY = "practice"
LADDER_KEY = "tempo_best"
RHYTHMS_DONE_KEY = "rhythms_done"
TODAY = "Today's rhythm"


class PracticeScreen(PageScreen):
    def __init__(self, **kwargs):
        super().__init__(name="practice", **kwargs)
        self.done = set()
        self.rhythm = None
        metronome = self.app.metronome
        page = self.page
        page.add(title("Practice"))
        page.add(Txt(text.PRACTICE_INTRO, color=theme.INK_SOFT))

        panel = page.add(card(spacing=dp(8)))
        panel.add_widget(subtitle(text.RHYTHM_TITLE))
        panel.add_widget(small(text.RHYTHM_INTRO))
        self.rhythms_done = set(self.app.store.get(RHYTHMS_DONE_KEY, []))
        self.rhythm_choices = {}          # drop-down label -> rhythm, or None for today's
        self.rhythm_picker = Spinner(
            text=TODAY, values=[TODAY], option_cls=PieceOption, size_hint_y=None, height=dp(48),
            font_size=sp(15), bold=True, background_normal="", background_down="",
            background_color=rgba(theme.WOOD), color=rgba(theme.CREAM))
        self.rhythm_picker.bind(text=lambda *_: self._show_rhythm())
        panel.add_widget(self.rhythm_picker)
        self.rhythm_name = small("", color=theme.VARNISH_DARK)
        panel.add_widget(self.rhythm_name)
        self.rhythm_holder = Box()
        panel.add_widget(self.rhythm_holder)
        self.hear_button = HearButton(lambda: f"Hear it at {self.app.metronome.bpm}", self._hear_rhythm)
        panel.add_widget(self.hear_button)

        panel = page.add(card(spacing=dp(8)))
        panel.add_widget(subtitle(text.LADDER_TITLE))
        panel.add_widget(small(text.LADDER_INTRO))
        self.menu = piece_menu()
        self.best = dict(self.app.store.get(LADDER_KEY, {}))
        self.picker = Spinner(
            text=next(label for label, pid in self.menu.items() if pid == "scale"),
            values=list(self.menu), option_cls=PieceOption, size_hint_y=None, height=dp(48),
            font_size=sp(15), bold=True, background_normal="", background_down="",
            background_color=rgba(theme.WOOD), color=rgba(theme.CREAM))
        self.picker.bind(text=lambda *_: self.sync())
        panel.add_widget(self.picker)
        self.best_label = Txt("")
        panel.add_widget(self.best_label)
        panel.add_widget(Btn("Open this piece in Play-Along", kind="outline",
                             on_release=self._open_piece))
        self.save_button = Btn("", kind="outline", on_release=self._save_best)
        panel.add_widget(self.save_button)

        listing = page.add(card(spacing=dp(8)))
        listing.add_widget(subtitle(text.ROUTINE_TITLE))
        listing.add_widget(small(text.ROUTINE_INTRO))
        self.tally = Txt("")
        self.meter = Meter(track=theme.PAPER_LINE, fill=theme.GOOD, height=8)
        listing.add_widget(self.tally)
        listing.add_widget(self.meter)
        self.rows = {}
        for item in ROUTINE:
            check_row = CheckRow(item.title, item.text, minutes=item.minutes)
            check_row.bind(on_release=lambda _r, item_id=item.id: self._toggle(item_id))
            self.rows[item.id] = check_row
            listing.add_widget(check_row)
        listing.add_widget(small(f"{sum(item.minutes for item in ROUTINE)} minutes in all."))
        page.add(Btn("Clear today's list", kind="outline", on_release=self._reset))

        metronome.watch(self)
        self._load()

    def progress_reset(self):
        self.best = {}
        self.rhythms_done = set()
        self.rhythm = None
        self._load()

    def on_pre_enter(self, *_):
        self._load()          # a new day brings a new rhythm and clears yesterday's ticks

    # -- metronome watcher ------------------------------------------------------
    def sync(self):
        bpm = self.app.metronome.bpm
        piece_id = self.menu.get(self.picker.text)
        best = self.best.get(piece_id)
        self.best_label.set(f"Your best clean tempo: {best}" if best else "No tempo saved for this one yet.")
        self.save_button.set(f"Save {bpm} as my best")
        self.hear_button.refresh()

    def tick(self, _state):
        pass

    # -- rhythm of the day --------------------------------------------------------
    def _fill_rhythm_picker(self):
        """List today's rhythm first, then every rhythm by week, marking the ones done."""
        chosen = self.rhythm_choices.get(self.rhythm_picker.text)
        self.rhythm_choices = {TODAY: None}
        for rhythm in rhythm_menu():
            done = " (done)" if rhythm.id in self.rhythms_done else ""
            self.rhythm_choices[f"Week {rhythm.week}: {rhythm.name}{done}"] = rhythm
        self.rhythm_picker.values = list(self.rhythm_choices)
        if chosen is not None:            # keep the same rhythm selected if its label changed
            self.rhythm_picker.text = next(
                label for label, rhythm in self.rhythm_choices.items() if rhythm is chosen)

    def _show_rhythm(self):
        week = int(self.app.store.get("lessons", {}).get("current_week", 1))
        today = rhythm_of_the_day(week)
        rhythm = self.rhythm_choices.get(self.rhythm_picker.text) or today
        prefix = "Today: " if rhythm is today else ""
        done = " Done." if rhythm.id in self.rhythms_done else ""
        self.rhythm_name.set(f"{prefix}{rhythm.name}, from week {rhythm.week}.{done}")
        if self.rhythm is None or rhythm.id != self.rhythm.id:
            self.app.tones.stop()
            self.rhythm = rhythm
            self.rhythm_holder.clear_widgets()
            scroller = StaffScroller(rhythm.notes)
            scroller.staff.show_fingers = False
            scroller.staff._draw()
            self.rhythm_holder.add_widget(scroller)

    def _hear_rhythm(self, tag=None):
        """Keep the shared metronome running and bring the rhythm in on the next beat 1."""
        metronome = self.app.metronome
        metronome.ensure_running(subdivide=self.rhythm.subdivide)
        self.app.tones.play_melody(f"rhythm_{self.rhythm.id}", self.rhythm.notes, 60.0 / metronome.bpm,
                                   wait=metronome.seconds_to_next_bar, tag=tag)

    # -- tempo ladder -------------------------------------------------------------
    def _open_piece(self, *_):
        piece_id = self.menu.get(self.picker.text)
        if piece_id:
            self.app.open_play_along(piece_id)

    def _save_best(self, *_):
        piece_id = self.menu.get(self.picker.text)
        if piece_id:
            self.best[piece_id] = self.app.metronome.bpm
            self.app.store.set(LADDER_KEY, self.best)
            self.sync()

    # -- daily routine ------------------------------------------------------------
    def _load(self):
        saved = self.app.store.get(STORE_KEY, {})
        today = datetime.date.today().isoformat()
        self.done = set(saved.get("done", [])) if saved.get("date") == today else set()
        self._fill_rhythm_picker()
        self._show_rhythm()
        self._refresh()
        self.sync()

    def _save(self):
        self.app.store.set(STORE_KEY, {"date": datetime.date.today().isoformat(), "done": sorted(self.done)})

    def _toggle(self, item_id):
        self.done.symmetric_difference_update({item_id})
        if item_id == "timing" and item_id in self.done and self.rhythm is not None:
            # ticking Timing records the rhythm on screen as done
            self.rhythms_done.add(self.rhythm.id)
            self.app.store.set(RHYTHMS_DONE_KEY, sorted(self.rhythms_done))
            self._fill_rhythm_picker()
            self._show_rhythm()
        self._save()
        self._refresh()

    def _reset(self, *_):
        self.done = set()
        self._save()
        self._refresh()

    def _refresh(self):
        for item_id, check_row in self.rows.items():
            check_row.checked = item_id in self.done
        count = len(self.done & set(self.rows))
        self.tally.set(f"{count} of {len(ROUTINE)} done today")
        self.meter.value = count / len(ROUTINE)
