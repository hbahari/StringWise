"""Record and Check: record a take with the click, then show what was right."""

from __future__ import annotations

import math
import threading
import time

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.spinner import Spinner

from ... import theme
from ...audio.metronome import BEATS_PER_BAR, TRACK_RATE
from ...audio.mic import SAMPLE_RATE, MicError
from ...audio.pitch import level_fraction
from ...content import metronome as text
from ...content.lessons import LESSON_BY_WEEK, LESSONS
from ...logic.takecheck import analyse
from ...music.pieces import PIECES
from ...music.rhythms import RHYTHMS
from ...theme import rgba
from .. import platform
from ..staff import StaffScroller
from ..widgets import Box, Btn, Meter, Txt, bold, bullets, card, row, small, subtitle, title
from .base import MIC_DENIED, PageScreen
from .playalong import PieceOption

NOTE_COLORS = {"right": theme.GOOD, "sharp": theme.WARN, "flat": theme.WARN, "wrong": theme.BAD}


def _menu():
    """Everything that can be recorded: each week's rhythm, then its pieces."""
    items = {}
    for lesson in LESSONS:
        study = lesson.timing
        if study is not None and study.rhythm:
            rhythm = RHYTHMS[study.rhythm]
            items[f"Week {lesson.week} rhythm: {study.title}"] = (rhythm.id, rhythm.notes, rhythm.subdivide)
        for piece_id in lesson.pieces:
            piece = PIECES[piece_id]
            items[f"Week {lesson.week}: {piece.title}"] = (piece.id, piece.notes, False)
    return items


class TakeScreen(PageScreen):
    def __init__(self, **kwargs):
        super().__init__(name="take", **kwargs)
        self.menu = _menu()
        self.state = "idle"            # idle, recording, checking
        self._events = []
        self._started = 0.0
        self._length = 0.0
        self._bars = 0

        page = self.page
        page.add(Btn("Back to lessons", kind="outline", height=dp(40), size_hint_x=None, width=dp(170),
                     on_release=lambda _b: self.app.go_to("lessons")))
        page.add(title(text.TAKE_TITLE))
        page.add(Txt(text.TAKE_INTRO, color=theme.INK_SOFT))

        self.picker = Spinner(
            text=next(iter(self.menu)), values=list(self.menu), option_cls=PieceOption,
            size_hint_y=None, height=dp(48), font_size=sp(15), bold=True,
            background_normal="", background_down="", background_color=rgba(theme.WOOD),
            color=rgba(theme.CREAM))
        self.picker.bind(text=lambda *_: self._load())
        page.add(self.picker)

        panel = page.add(card(spacing=dp(10)))
        self.staff_holder = Box()
        panel.add_widget(self.staff_holder)
        self.tempo = Txt("", halign="center")
        panel.add_widget(self.tempo)
        panel.add_widget(row(
            Btn("− slower", kind="outline", height=dp(44), on_release=lambda _b: self._nudge(-2)),
            Btn("faster +", kind="outline", height=dp(44), on_release=lambda _b: self._nudge(2)),
            height=44, spacing=8))
        self.level_meter = Meter(track=theme.PAPER_LINE, fill=theme.GOOD)
        panel.add_widget(self.level_meter)
        self.status = Txt("", halign="center")
        panel.add_widget(self.status)
        self.button = Btn("Start recording", on_release=self._pressed)
        panel.add_widget(self.button)

        self.results = page.add(Box())
        how = page.add(card())
        how.add_widget(subtitle("How to get a good check"))
        how.add_widget(bullets(text.TAKE_STEPS))
        how.add_widget(small(text.TAKE_PRIVACY))

        self.app.metronome.watch(self)
        self._load()

    # -- metronome watcher ---------------------------------------------------
    def sync(self):
        self.tempo.set(f"Tempo: {self.app.metronome.bpm} beats a minute")

    def tick(self, _state):
        pass

    def _nudge(self, change):
        if self.state == "idle":
            self.app.metronome.configure(bpm=self.app.metronome.bpm + change)

    # -- choosing --------------------------------------------------------------
    def select_week(self, week):
        """Open on the given week's rhythm, or its first piece if it has none."""
        lesson = LESSON_BY_WEEK[week]
        prefix = f"Week {week} rhythm:" if lesson.timing and lesson.timing.rhythm else f"Week {week}:"
        for label in self.menu:
            if label.startswith(prefix):
                self.picker.text = label
                break
        if lesson.timing:
            self.app.metronome.configure(bpm=lesson.timing.tempos[0])
        self.page.scroll_y = 1

    def _load(self):
        self._cancel()
        _key, notes, _subdivide = self.menu[self.picker.text]
        self.staff_holder.clear_widgets()
        self.scroller = StaffScroller(notes, scale=1.1)
        self.staff_holder.add_widget(self.scroller)
        self.results.clear_widgets()
        self.status.set("Press Start recording when you are ready.")
        self.sync()

    # -- recording ---------------------------------------------------------------
    def _pressed(self, *_):
        if self.state == "recording":
            self._finish()
        elif self.state == "idle":
            platform.request_microphone(self._begin)

    def _begin(self, granted):
        if not granted:
            self.status.set(MIC_DENIED)
            return
        if self.manager is None or self.manager.current != self.name or self.state != "idle":
            return
        app = self.app
        _key, notes, subdivide = self.menu[self.picker.text]
        app.metronome.stop()
        app.tones.stop()
        self.results.clear_widgets()
        self.scroller.staff.set_marks()
        self.scroller.scroll_x = 0

        piece_bars = math.ceil(sum(n.beats for n in notes) / BEATS_PER_BAR - 1e-9)
        self._bars = piece_bars
        path, self._length = app.metronome.write_take_track(app.metronome.bpm, piece_bars + 2, subdivide)
        try:
            app.listener.start(record=True)
        except MicError as exc:
            self.status.set(str(exc))
            return
        app.tones.play_file(path)
        platform.keep_screen_on(True)
        self._started = time.monotonic()
        self.state = "recording"
        self.button.set("Stop")
        self._events = [Clock.schedule_interval(self._poll, 1 / 20),
                        Clock.schedule_once(lambda _dt: self._finish(), self._length + 0.3)]

    def _poll(self, _dt):
        listener = self.app.listener
        frames = listener.poll()
        if listener.error:
            message = listener.error
            self._cancel()
            self.status.set(message)
            return
        if frames:
            self.level_meter.value = level_fraction(frames[-1].rms)
        beat = (time.monotonic() - self._started) / (60.0 / self.app.metronome.bpm)
        bar, count = int(beat // BEATS_PER_BAR), int(beat % BEATS_PER_BAR) + 1
        if bar == 0:
            self.status.set(f"Count-in: {count}")
        elif bar <= self._bars:
            self.status.set(f"Recording. Bar {bar} of {self._bars}, beat {count}")
        else:
            self.status.set("Finishing")

    def _stop_capture(self):
        for event in self._events:
            event.cancel()
        self._events = []
        self.app.listener.stop()
        self.app.tones.stop()
        platform.keep_screen_on(False)
        self.level_meter.value = 0
        self.button.set("Start recording")

    def _cancel(self):
        """Stop without checking anything (leaving the screen, changing piece)."""
        if self.state == "recording":
            self._stop_capture()
            self.app.listener.take_recording()
        self.state = "idle"

    def _finish(self):
        if self.state != "recording":
            return
        self._stop_capture()
        samples = self.app.listener.take_recording()
        _key, notes, _subdivide = self.menu[self.picker.text]
        bpm = self.app.metronome.bpm
        self.state = "checking"
        self.button.disabled = True
        self.status.set("Checking your take")

        def work():
            try:
                report = analyse(samples, SAMPLE_RATE, notes, bpm, TRACK_RATE)
            except Exception as exc:       # never leave the screen stuck on "Checking"
                report = exc
            Clock.schedule_once(lambda _dt: self._show(report))

        threading.Thread(target=work, name="take-check", daemon=True).start()

    # -- results -------------------------------------------------------------------
    def _show(self, report):
        self.state = "idle"
        self.button.disabled = False
        if isinstance(report, Exception):
            self.status.set("Something went wrong while checking that take. Please try again.")
            return
        self.status.set("Press Start recording to try again.")
        colors, marks = {}, {}
        for result in report.results:
            colors[result.index] = NOTE_COLORS.get(result.pitch, rgba(theme.INK_SOFT, 0.4))
            if result.timing != "missed":
                marks[result.index] = result.timing
        self.scroller.staff.set_marks(colors, marks)

        panel = card()
        panel.add_widget(Txt(bold(report.headline), is_markup=True, size=17))
        panel.add_widget(bullets(report.lines))
        if report.results and any(r.played for r in report.results):
            panel.add_widget(small(text.TAKE_LEGEND))
        self.results.clear_widgets()
        self.results.add_widget(panel)

    def on_leave(self, *_):
        self._cancel()
