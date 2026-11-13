"""First-position fingering with a high second finger, the pattern the course teaches."""

from __future__ import annotations

from dataclasses import dataclass

from .notes import Note

# Semitones above the open string for: open, finger 1, 2, 3, 4.
# Gaps: open-1 whole, 1-2 whole, 2-3 HALF, 3-4 whole.
FINGER_OFFSETS = (0, 2, 4, 5, 7)


@dataclass(frozen=True)
class ViolinString:
    name: str
    open_note: Note
    notes: tuple[Note, ...]   # open, 1, 2, 3, 4

    @property
    def open_hz(self) -> float:
        return self.open_note.freq


def _build(name: str, octave: int, names: tuple[str, ...], octaves: tuple[int, ...]) -> ViolinString:
    notes = tuple(Note(n, o) for n, o in zip(names, octaves))
    return ViolinString(name, Note(name, octave), notes)


# Lowest string first.
STRINGS: tuple[ViolinString, ...] = (
    _build("G", 3, ("G", "A", "B", "C", "D"), (3, 3, 3, 4, 4)),
    _build("D", 4, ("D", "E", "F#", "G", "A"), (4, 4, 4, 4, 4)),
    _build("A", 4, ("A", "B", "C#", "D", "E"), (4, 4, 5, 5, 5)),
    _build("E", 5, ("E", "F#", "G#", "A", "B"), (5, 5, 5, 5, 5)),
)
STRING_BY_NAME = {s.name: s for s in STRINGS}

# How far along the string each finger lands, as a fraction of the string length
# from the nut. This is plain physics: a note n semitones up stops the string at
# 1 - 2^(-n/12) of its length.
FINGER_POSITIONS = tuple(1 - 2 ** (-n / 12) for n in FINGER_OFFSETS)


def target_note(string_name: str, finger: int) -> Note:
    return STRING_BY_NAME[string_name].notes[finger]


def fingering_for(note: Note) -> tuple[str, int] | None:
    """Where a beginner would play ``note``: (string name, finger), or None if out of reach.

    Open strings win over a fourth finger on the string below, which is how
    first tunes are normally fingered.
    """
    if note.is_rest:
        return None
    best = None
    for string in STRINGS:
        for finger, candidate in enumerate(string.notes):
            if candidate.midi == note.midi:
                if finger == 0:
                    return string.name, 0
                if best is None or finger < best[1]:
                    best = (string.name, finger)
    return best
