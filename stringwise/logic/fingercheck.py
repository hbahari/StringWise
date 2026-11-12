"""Finger check: compares what the microphone hears with one chosen string and finger."""

from __future__ import annotations

from dataclasses import dataclass

from ..audio.pitch import MedianFilter
from ..music.fingering import target_note
from ..music.notes import cents_between, nearest_note, pretty
from .common import HINT_AFTER, IDLE_AFTER, frames, in_range, silence_hint

CORRECT_CENTS = 12     # close enough to call the placement right
CLOSE_CENTS = 45       # same note, but the finger needs to move
HOLD_SECONDS = 0.35    # how long it must stay right before we call it settled

STATUS_READY = "Press Start listening, then play that note."
STATUS_WAITING = "Listening. Play the note."
STATUS_HEARING = "Listening."


@dataclass
class FingerCheckView:
    status: str = STATUS_READY
    heard: str = ""
    cents: float | None = None
    verdict: str | None = None   # "correct", "close" or "off"
    caption: str = ""
    message: str = ""
    settled: bool = False


class FingerCheck:
    def __init__(self, frame_rate: float) -> None:
        self._filter = MedianFilter()
        self._idle_frames = frames(IDLE_AFTER, frame_rate)
        self._hint_frames = frames(HINT_AFTER, frame_rate)
        self._hold_frames = frames(HOLD_SECONDS, frame_rate)
        self._silence = 0
        self._streak = 0
        self._listening = False
        self.string = "A"
        self.finger = 1
        self.view = FingerCheckView()

    @property
    def target(self):
        return target_note(self.string, self.finger)

    def choose(self, string: str | None = None, finger: int | None = None) -> None:
        if string is not None:
            self.string = string
        if finger is not None:
            self.finger = finger
        self._streak = 0
        self.view = FingerCheckView(status=STATUS_WAITING if self._listening else STATUS_READY)

    def start(self) -> None:
        self._filter.reset()
        self._silence = self._streak = 0
        self._listening = True
        self.view = FingerCheckView(status=STATUS_WAITING)

    def stop(self) -> None:
        self._listening = False
        self._streak = 0
        self.view = FingerCheckView()

    def feed(self, freq: float | None, rms: float) -> FingerCheckView:
        freq = self._filter.push(freq)
        if in_range(freq):
            self._silence = 0
            heard = nearest_note(freq)
            cents = cents_between(freq, self.target.freq)
            view = FingerCheckView(
                status=STATUS_HEARING,
                heard=f"Hearing {pretty(heard.name)}{heard.octave}, {freq:.1f} Hz",
                cents=cents,
            )
            off_by = abs(cents)
            if off_by <= CORRECT_CENTS:
                self._streak += 1
                view.verdict, view.caption = "correct", "in tune"
                view.settled = self._streak >= self._hold_frames
                view.message = "Correct, and nicely in tune." if view.settled else "Correct."
            else:
                self._streak = 0
                view.caption = "sharp" if cents > 0 else "flat"
                if off_by <= CLOSE_CENTS:
                    view.verdict = "close"
                    view.message = (
                        f"{round(off_by)} cents sharp. Slide the finger a touch toward the scroll."
                        if cents > 0 else
                        f"{round(off_by)} cents flat. Slide the finger a touch toward the bridge.")
                else:
                    view.verdict = "off"
                    view.message = "That's a different note. Check the string and the finger."
            self.view = view
        else:
            self._silence += 1
            if self._silence == self._idle_frames:
                self._streak = 0
                self.view = FingerCheckView(status=STATUS_WAITING)
            elif self._silence == self._hint_frames:
                self.view = FingerCheckView(status=silence_hint(rms))
        return self.view
