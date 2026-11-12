"""Tuner: names the note being played and says how far off it is."""

from __future__ import annotations

from dataclasses import dataclass

from ..audio.pitch import MedianFilter
from ..music.notes import nearest_note, pretty
from .common import HINT_AFTER, IDLE_AFTER, frames, in_range, silence_hint

IN_TUNE_CENTS = 5
FAR_CENTS = 35

STATUS_READY = "Press Start listening, then play an open string."
STATUS_WAITING = "Listening. Play a note."
STATUS_HEARING = "Listening."


@dataclass
class TunerView:
    status: str = STATUS_READY
    note: str | None = None
    detail: str = ""           # "438.2 Hz, target 440.0 Hz"
    cents: float | None = None
    verdict: str | None = None  # "in_tune", "near" or "far"
    caption: str = ""           # "in tune", "sharp", "flat"
    advice: str = ""


class Tuner:
    def __init__(self, frame_rate: float) -> None:
        self._filter = MedianFilter()
        self._idle_frames = frames(IDLE_AFTER, frame_rate)
        self._hint_frames = frames(HINT_AFTER, frame_rate)
        self._silence = 0
        self.view = TunerView()

    def start(self) -> None:
        self._filter.reset()
        self._silence = 0
        self.view = TunerView(status=STATUS_WAITING)

    def stop(self) -> None:
        self.view = TunerView()

    def feed(self, freq: float | None, rms: float) -> TunerView:
        freq = self._filter.push(freq)
        if in_range(freq):
            self._silence = 0
            heard = nearest_note(freq)
            cents = round(heard.cents)
            view = TunerView(
                status=STATUS_HEARING,
                note=pretty(heard.name),
                detail=f"{freq:.1f} Hz, target {heard.target_hz:.1f} Hz",
                cents=heard.cents,
            )
            if abs(cents) <= IN_TUNE_CENTS:
                view.verdict, view.caption = "in_tune", "in tune"
                view.advice = f"In tune ({cents:+d} cents)"
            else:
                view.verdict = "far" if abs(cents) > FAR_CENTS else "near"
                view.caption = "sharp" if cents > 0 else "flat"
                view.advice = (f"{cents:+d} cents. Too high, tune down a little." if cents > 0
                               else f"{cents:+d} cents. Too low, tune up a little.")
            self.view = view
        else:
            self._silence += 1
            if self._silence == self._idle_frames:
                self.view = TunerView(status=STATUS_WAITING)
            elif self._silence == self._hint_frames:
                self.view = TunerView(status=silence_hint(rms))
        return self.view
