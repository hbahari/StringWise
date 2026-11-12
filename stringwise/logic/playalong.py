"""Play-along: follows a piece note by note as the player gets each one right."""

from __future__ import annotations

from dataclasses import dataclass

from ..audio.pitch import MedianFilter
from ..music.notes import cents_between, nearest_note
from ..music.pieces import Piece
from .common import frames, in_range, silence_hint

CORRECT_CENTS = 30      # within this counts as the right note
WRONG_CENTS = 60        # beyond this is plainly a different note
CONFIRM_SECONDS = 0.10  # the note must hold this long to count
FLASH_SECONDS = 0.22    # pause on a correct note before moving on
CURSOR_HIDE_SECONDS = 0.17
HINT_SECONDS = 3.0
DIP_RATIO = 0.5         # drop in loudness that counts as a fresh bow stroke

STATUS_READY = "Press Start listening, then play the first note."
STATUS_PLAY = "Listening. Play the highlighted note."
STATUS_FIRST = "Listening. Play the first note."
STATUS_CORRECT = "Correct!"
STATUS_REPEAT = "Same note again. Stop the bow or change direction, then play it once more."
STATUS_DONE = "That's the whole piece. Well played. Restart to go again."


@dataclass
class PlayAlongView:
    status: str = STATUS_READY
    index: int = 0                  # the note being asked for
    confirmed: int = 0              # notes drawn as done (index, or index + 1 during the flash)
    cursor_step: int | None = None  # staff position of the pitch being heard
    cursor_kind: str = "close"      # "correct", "close" or "wrong"
    finished: bool = False


class PlayAlong:
    def __init__(self, piece: Piece, frame_rate: float) -> None:
        self.piece = piece
        self._filter = MedianFilter()
        self._confirm_frames = frames(CONFIRM_SECONDS, frame_rate)
        self._flash_frames = frames(FLASH_SECONDS, frame_rate)
        self._cursor_hide_frames = frames(CURSOR_HIDE_SECONDS, frame_rate)
        self._hint_frames = frames(HINT_SECONDS, frame_rate)
        self._listening = False
        self.restart()

    # -- control ---------------------------------------------------------
    def restart(self) -> None:
        self._index = 0
        self._streak = 0
        self._silence = 0
        self._flash = 0
        self._same_as_previous = False
        self._dip_seen = False
        self._peak = 0.0
        self.view = PlayAlongView(status=STATUS_FIRST if self._listening else STATUS_READY)

    def start(self) -> None:
        self._listening = True
        self._filter.reset()
        self._streak = self._silence = self._flash = 0
        self._same_as_previous = False
        self._dip_seen = False
        self._peak = 0.0
        self.view = self._make_view(STATUS_DONE if self.finished else
                                    (STATUS_FIRST if self._index == 0 else STATUS_PLAY))

    def stop(self) -> None:
        self._listening = False
        if self._flash:
            self._flash = 0
            self._index += 1
        self.view = self._make_view(STATUS_DONE if self.finished else STATUS_READY)

    @property
    def finished(self) -> bool:
        return self._index >= len(self.piece.notes)

    # -- audio in --------------------------------------------------------
    def feed(self, freq: float | None, rms: float) -> PlayAlongView:
        freq = self._filter.push(freq)
        status = self.view.status
        cursor_step, cursor_kind = None, "close"

        if self._flash:
            self._flash -= 1
            if self._flash == 0:
                self._index += 1
                self._streak = 0
                status = STATUS_DONE if self.finished else STATUS_PLAY

        if self.finished:
            self.view = self._make_view(STATUS_DONE)
            return self.view

        if in_range(freq):
            self._silence = 0
            # Evidence of a new bow stroke since the last confirmed note.
            self._peak = max(self._peak, rms)
            if self._peak > 0 and rms < self._peak * DIP_RATIO:
                self._dip_seen = True

            target = self.piece.notes[min(self._index + (1 if self._flash else 0),
                                          len(self.piece.notes) - 1)]
            off_by = abs(cents_between(freq, target.freq))
            waiting = self._same_as_previous and not self._dip_seen
            cursor_step = nearest_note(freq).staff_step
            if waiting:
                cursor_kind = "close"
            elif off_by <= CORRECT_CENTS:
                cursor_kind = "correct"
            elif off_by >= WRONG_CENTS:
                cursor_kind = "wrong"

            if not self._flash:
                if waiting:
                    self._streak = 0
                    status = STATUS_REPEAT
                elif off_by <= CORRECT_CENTS:
                    self._streak += 1
                    if self._streak >= self._confirm_frames:
                        self._confirm(rms)
                        status = STATUS_CORRECT
                else:
                    self._streak = 0
                    if status == STATUS_REPEAT:
                        status = STATUS_PLAY
        else:
            self._silence += 1
            if self._silence >= 2:
                self._dip_seen = True          # the last note stopped: a new one may start
            if self._silence < self._cursor_hide_frames:
                cursor_step, cursor_kind = self.view.cursor_step, self.view.cursor_kind
            if not self._flash:
                if self._silence == self._cursor_hide_frames and status == STATUS_REPEAT:
                    status = STATUS_PLAY
                if self._silence == self._hint_frames:
                    status = silence_hint(rms)

        self.view = self._make_view(status, cursor_step, cursor_kind)
        return self.view

    # -- internals -------------------------------------------------------
    def _confirm(self, rms: float) -> None:
        notes = self.piece.notes
        current = notes[self._index]
        upcoming = notes[self._index + 1] if self._index + 1 < len(notes) else None
        self._same_as_previous = upcoming is not None and upcoming.same_pitch(current)
        self._dip_seen = False
        self._peak = rms
        self._flash = self._flash_frames

    def _make_view(self, status: str, cursor_step: int | None = None,
                   cursor_kind: str = "close") -> PlayAlongView:
        return PlayAlongView(
            status=status,
            index=self._index,
            confirmed=self._index + (1 if self._flash else 0),
            cursor_step=cursor_step,
            cursor_kind=cursor_kind,
            finished=self.finished,
        )
