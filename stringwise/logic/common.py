"""Shared pieces for the three listening tools."""

from __future__ import annotations

from ..audio.pitch import RMS_GATE

IDLE_AFTER = 0.7     # seconds without a clear pitch before the display clears
HINT_AFTER = 2.5     # seconds before we suggest what to try

HINT_QUIET = "I can't hear much. Move closer to the microphone or play a bit louder."
HINT_UNCLEAR = "I can hear sound but no clear note. Try one long, steady bow."


def frames(seconds: float, frame_rate: float) -> int:
    return max(1, round(seconds * frame_rate))


def silence_hint(rms: float) -> str:
    return HINT_QUIET if rms < RMS_GATE else HINT_UNCLEAR


def in_range(freq: float | None) -> bool:
    return freq is not None and 60.0 < freq < 2000.0
