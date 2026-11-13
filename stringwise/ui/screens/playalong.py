from __future__ import annotations

from kivy.metrics import dp, sp
from kivy.uix.spinner import Spinner, SpinnerOption

from ... import theme
from ...content.lessons import piece_menu
from ...logic.playalong import PlayAlong
from ...music.pieces import PIECES
from ...theme import rgba
from ..staff import StaffScroller
from ..widgets import Box, Btn, Meter, Txt, card, row, small, title
from .base import ListeningScreen

INTRO = ("Choose a piece and start listening. The dot on the staff is the note the app hears "
         "you playing. Land it on the highlighted note and the music moves on.")
LEGEND = "Green dot: right note. Amber: close. Red: a different note."


class PieceOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = self.background_down = ""
        self.background_color = rgba(theme.WOOD)
        self.color = rgba(theme.CREAM)
        self.font_size = sp(14)
        self.height = dp(46)
        self.halign = "left"
        self.valign = "middle"
        self.padding = (dp(14), 0)
        self.bind(size=lambda *_: setattr(self, "text_size", self.size))


class PlayAlongScreen(ListeningScreen):
    def __init__(self, **kwargs):
        super().__init__(name="playalong", **kwargs)
        self.labels = piece_menu()
        self.piece_id = next(iter(self.labels.values()))
        self.logic = PlayAlong(PIECES[self.piece_id], self.app.listener.frame_rate)
        self.scroller = None

        page = self.page
        page.add(Btn("Back to lessons", kind="outline", height=dp(40), size_hint_x=None, width=dp(170),
                     on_release=lambda _b: self.app.go_to("lessons")))
        page.add(title("Play-Along"))
        page.add(Txt(INTRO, color=theme.INK_SOFT))

        self.picker = Spinner(
            text=self._label_for(self.piece_id), values=list(self.labels), option_cls=PieceOption,
            size_hint_y=None, height=dp(48), font_size=sp(15), bold=True,
            background_normal="", background_down="", background_color=rgba(theme.WOOD),
            color=rgba(theme.CREAM))
        self.picker.bind(text=self._picked)
        page.add(self.picker)

        self.panel = page.add(card(spacing=dp(10)))
        self.info = small("")
        self.progress = small("", color=theme.VARNISH_DARK)
        self.staff_holder = Box()
        self.level_meter = Meter(track=theme.PAPER_LINE, fill=theme.GOOD)
        self.status = Txt("", color=theme.INK)
        for widget in (self.info, self.progress, self.staff_holder, self.level_meter, self.status):
            self.panel.add_widget(widget)
        self.mic_button = Btn("Start listening", on_release=self.toggle_listening)
        self.panel.add_widget(row(self.mic_button, Btn("Restart", kind="outline", on_release=self.restart)))
        self.hear_button = Btn("", kind="outline", on_release=self.hear)
        self.panel.add_widget(self.hear_button)
        self.panel.add_widget(row(
            Btn("\u2212 slower", kind="outline", height=dp(44), on_release=lambda _b: self._nudge(-4)),
            Btn("faster +", kind="outline", height=dp(44), on_release=lambda _b: self._nudge(4)),
            height=44, spacing=8))
        self.panel.add_widget(small(LEGEND))

        self.app.metronome.watch(self)
        self.sync()
        self._load_piece(self.piece_id)

    # -- metronome watcher -------------------------------------------------------
    def sync(self):
        self.hear_button.set(f"Hear the tune at {self.app.metronome.bpm}")

    def tick(self, _state):
        pass

    def _nudge(self, change):
        self.app.metronome.configure(bpm=self.app.metronome.bpm + change)

    def _label_for(self, piece_id):
        return next(label for label, pid in self.labels.items() if pid == piece_id)

    # -- choosing a piece ------------------------------------------------------
    def select(self, piece_id):
        """Called from a lesson to open a particular piece."""
        self.picker.text = self._label_for(piece_id)      # triggers _picked
        self.page.scroll_y = 1

    def _picked(self, _spinner, label):
        piece_id = self.labels.get(label)
        if piece_id and piece_id != self.piece_id:
            self._load_piece(piece_id)

    def _load_piece(self, piece_id):
        self.stop_listening()
        self.app.tones.stop()
        self.piece_id = piece_id
        piece = PIECES[piece_id]
        self.logic = PlayAlong(piece, self.app.listener.frame_rate)
        self.info.set(piece.info)
        self.staff_holder.clear_widgets()
        self.scroller = StaffScroller(piece.notes, scale=1.2)
        self.staff_holder.add_widget(self.scroller)
        self._followed = -1
        self.refresh()

    # -- actions ---------------------------------------------------------------
    def restart(self, *_):
        self.logic.restart()
        self._followed = -1
        self.refresh()

    def hear(self, *_):
        self.stop_listening()
        piece = PIECES[self.piece_id]
        metronome = self.app.metronome
        # If the click is running, leave it running and bring the tune in on the next beat 1.
        self.app.tones.play_melody(piece.id, piece.notes, 60.0 / metronome.bpm,
                                   wait=metronome.seconds_to_next_bar)
        if metronome.running:
            self.status.set("The tune starts on the next beat 1.")
        else:
            self.refresh()

    # -- listening ---------------------------------------------------------------
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
        total = len(self.logic.piece.notes)
        self.status.set(view.status, theme.GOOD if view.finished or view.status == "Correct!" else theme.INK)
        self.progress.set(f"All {total} notes played" if view.finished
                          else f"Note {view.index + 1} of {total}")
        self.scroller.staff.set_state(
            done=view.confirmed,
            current=None if view.finished else view.index,
            cursor_step=view.cursor_step if self.listening else None,
            cursor_kind=view.cursor_kind)
        if view.index != self._followed:
            self._followed = view.index
            self.scroller.follow(view.index)
