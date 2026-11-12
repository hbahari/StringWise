"""Note maths: names, frequencies, staff positions and the compact piece notation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

A4_HZ = 440.0
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_LETTER_INDEX = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}
_PITCH_CLASS = {name: i for i, name in enumerate(NOTE_NAMES)}

# Beats a note may last, in quarter-note beats.
ALLOWED_BEATS = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0)

_TOKEN = re.compile(r"^([A-G]#?)(\d):(\d+(?:\.\d+)?|\.\d+)$")


@dataclass(frozen=True)
class Note:
    name: str      # "A", "C#", ...
    octave: int    # scientific pitch octave; A4 = 440 Hz
    beats: float = 1.0

    @property
    def midi(self) -> int:
        return (self.octave + 1) * 12 + _PITCH_CLASS[self.name]

    @property
    def freq(self) -> float:
        return A4_HZ * 2 ** ((self.midi - 69) / 12)

    @property
    def staff_step(self) -> int:
        """Position on the treble staff in half-spaces above the bottom line (E4).

        Even numbers sit on a line, odd numbers in a space.
        """
        return staff_step(self.name, self.octave)

    @property
    def is_sharp(self) -> bool:
        return len(self.name) > 1

    @property
    def label(self) -> str:
        return f"{pretty(self.name)}{self.octave}"

    def same_pitch(self, other: "Note") -> bool:
        return self.midi == other.midi


def staff_step(name: str, octave: int) -> int:
    return octave * 7 + _LETTER_INDEX[name[0]] - 30


def ledger_steps(step: int) -> list[int]:
    """Staff steps that need a ledger line drawn for a note at ``step``."""
    if step < 0:
        return list(range(-2, step - 1, -2))
    if step > 8:
        return list(range(10, step + 1, 2))
    return []


def pretty(name: str) -> str:
    """'C#' -> 'C♯' for display."""
    return name.replace("#", "♯")


def parse_sequence(text: str) -> list[Note]:
    """Parse 'A4:1 C#5:2 B4:.5' into notes. The number after the colon is beats."""
    notes = []
    for token in text.split():
        if token == "|":          # optional bar marks, for readability only
            continue
        match = _TOKEN.match(token)
        if not match:
            raise ValueError(f"Bad note token: {token!r}")
        beats = float(match.group(3))
        if beats not in ALLOWED_BEATS:
            raise ValueError(f"Unsupported note length in {token!r}")
        notes.append(Note(match.group(1), int(match.group(2)), beats))
    return notes


@dataclass(frozen=True)
class Heard:
    name: str
    octave: int
    cents: float        # deviation from the nearest equal-tempered note
    target_hz: float    # frequency of that nearest note

    @property
    def staff_step(self) -> int:
        return staff_step(self.name, self.octave)


def nearest_note(freq: float) -> Heard:
    """Nearest equal-tempered note to ``freq`` and how far off it is."""
    semitones = 12 * math.log2(freq / A4_HZ)
    rounded = round(semitones)
    cents = (semitones - rounded) * 100
    midi = 69 + rounded
    return Heard(
        name=NOTE_NAMES[midi % 12],
        octave=midi // 12 - 1,
        cents=cents,
        target_hz=A4_HZ * 2 ** (rounded / 12),
    )


def cents_between(freq: float, target: float) -> float:
    return 1200 * math.log2(freq / target)
