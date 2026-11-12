"""Practice pieces. Two per week from week 2 onward.

Traditional tunes are simplified arrangements. Everything else was written for
this course. Every piece stays inside the first-position pattern in
``fingering.py`` and every bar adds up to four beats; the tests check both.
"""

from __future__ import annotations

from dataclasses import dataclass

from .notes import Note, parse_sequence

BEATS_PER_BAR = 4


@dataclass(frozen=True)
class Piece:
    id: str
    title: str
    info: str
    notes: tuple[Note, ...]


def _piece(id: str, title: str, info: str, sequence: str) -> Piece:
    return Piece(id, title, info, tuple(parse_sequence(sequence)))


_ALL = [
    _piece("openwarmup", "Open String Warm-Up",
           "All four open strings, low to high and back.",
           "G3:2 D4:2 | A4:2 E5:2 | E5:2 A4:2 | D4:2 G3:2 | G3:4"),
    _piece("crossings", "Open String Crossings",
           "Open strings only. Keep the bow moving at one speed while your elbow changes level.",
           "A4:1 A4:1 D4:1 D4:1 | A4:1 A4:1 E5:1 E5:1 | D4:1 D4:1 G3:1 G3:1 | D4:1 A4:1 E5:1 A4:1 | A4:4"),
    _piece("firstpattern", "First Pattern Warm-Up",
           "A string: open, then fingers 1, 2 and 3.",
           "A4:1 B4:1 C#5:1 D5:1 | D5:1 C#5:1 B4:2 | A4:4"),
    _piece("skips", "Steps and Skips",
           "A string, open to finger 3. Some notes move to the next finger, some jump over one.",
           "A4:1 B4:1 C#5:2 | D5:1 C#5:1 B4:2 | A4:1 C#5:1 B4:1 D5:1 | C#5:1 B4:1 A4:2"),
    _piece("hotcrossbuns", "Hot Cross Buns",
           "A string: open, finger 1 and finger 2.",
           "C#5:1 B4:1 A4:2 | C#5:1 B4:1 A4:2 | A4:1 A4:1 B4:1 B4:1 | C#5:1 B4:1 A4:2"),
    _piece("ode", "Ode to Joy",
           "A string, open to finger 4. The top note, E, is your fourth finger. Rhythm slightly simplified.",
           "C#5:1 C#5:1 D5:1 E5:1 | E5:1 D5:1 C#5:1 B4:1 | A4:1 A4:1 B4:1 C#5:1 | C#5:1 B4:1 B4:2 | "
           "C#5:1 C#5:1 D5:1 E5:1 | E5:1 D5:1 C#5:1 B4:1 | A4:1 A4:1 B4:1 C#5:1 | B4:1 A4:1 A4:2"),
    _piece("mary", "Mary Had a Little Lamb",
           "D string: open, finger 1 and finger 2, with one visit to the open A.",
           "F#4:1 E4:1 D4:1 E4:1 | F#4:1 F#4:1 F#4:2 | E4:1 E4:1 E4:2 | F#4:1 A4:1 A4:2 | "
           "F#4:1 E4:1 D4:1 E4:1 | F#4:1 F#4:1 F#4:1 F#4:1 | E4:1 E4:1 F#4:1 E4:1 | D4:4"),
    _piece("twinkle", "Twinkle, Twinkle, Little Star",
           "D and A strings. The first half of the tune, in D major.",
           "D4:1 D4:1 A4:1 A4:1 | B4:1 B4:1 A4:2 | G4:1 G4:1 F#4:1 F#4:1 | E4:1 E4:1 D4:2"),
    _piece("lightlyrow", "Lightly Row",
           "A string, plus the open E for the top note.",
           "E5:1 C#5:1 C#5:2 | D5:1 B4:1 B4:2 | A4:1 B4:1 C#5:1 D5:1 | E5:1 E5:1 E5:2 | "
           "E5:1 C#5:1 C#5:2 | D5:1 B4:1 B4:2 | A4:1 C#5:1 E5:1 E5:1 | A4:4"),
    _piece("auclair", "Au Clair de la Lune",
           "G string only: open, finger 1 and finger 2.",
           "G3:1 G3:1 G3:1 A3:1 | B3:2 A3:2 | G3:1 B3:1 A3:1 A3:1 | G3:4"),
    _piece("reading", "Reading Study",
           "D and A strings. A short study written for this week. Name each note before you play it.",
           "D4:1 E4:1 F#4:1 G4:1 | A4:1 G4:1 F#4:1 E4:1 | D4:2 F#4:1 A4:1 | G4:1 F#4:1 E4:2 | D4:4"),
    _piece("oldmac", "Old MacDonald",
           "D and A strings. You know how it goes, so let your eyes follow the page.",
           "D4:1 D4:1 D4:1 A4:1 | B4:1 B4:1 A4:2 | F#4:1 F#4:1 E4:1 E4:1 | D4:4"),
    _piece("dynamics", "Loud and Soft Study",
           "A string. Play it through once forte and once piano.",
           "A4:1 B4:1 C#5:1 B4:1 | A4:4 | C#5:1 D5:1 C#5:1 B4:1 | A4:4"),
    _piece("london", "London Bridge",
           "D and A strings, rhythm simplified. Try each phrase loud, then repeat it soft like an echo.",
           "A4:1 B4:1 A4:1 G4:1 | F#4:1 G4:1 A4:2 | E4:1 F#4:1 G4:2 | F#4:1 G4:1 A4:2 | "
           "A4:1 B4:1 A4:1 G4:1 | F#4:1 G4:1 A4:2 | E4:2 A4:2 | F#4:2 D4:2"),
    _piece("rhythmecho", "Rhythm Echo",
           "A string. Eighth notes in the first two bars, dotted quarters in the third. Clap it first.",
           "A4:1 A4:.5 A4:.5 B4:1 B4:.5 B4:.5 | C#5:1 C#5:.5 C#5:.5 D5:2 | "
           "D5:1.5 C#5:.5 B4:1.5 A4:.5 | B4:1 C#5:.5 B4:.5 A4:2"),
    _piece("longlongago", "Long, Long Ago",
           "A and E strings. The long-short-short rhythm repeats all the way through.",
           "A4:1 A4:.5 B4:.5 C#5:1 C#5:.5 D5:.5 | E5:1 F#5:.5 E5:.5 C#5:2 | "
           "E5:1 D5:.5 C#5:.5 B4:2 | D5:1 C#5:.5 B4:.5 A4:2"),
    _piece("scale", "D Major Scale",
           "One octave. D string open to finger 3, then A string open to finger 3, and back down.",
           "D4:1 E4:1 F#4:1 G4:1 | A4:1 B4:1 C#5:1 D5:1 | D5:1 C#5:1 B4:1 A4:1 | G4:1 F#4:1 E4:1 D4:1 | D4:4"),
    _piece("thirds", "D Major Scale in Thirds",
           "D and A strings. The same scale, skipping a note each time.",
           "D4:1 F#4:1 E4:1 G4:1 | F#4:1 A4:1 G4:1 B4:1 | A4:1 C#5:1 B4:1 D5:1 | D5:4"),
    _piece("etude", "Etude in D",
           "D and A strings. Built on the notes of the D major chord.",
           "D4:1 F#4:1 A4:1 D5:1 | D5:2 A4:2 | F#4:1 A4:1 D5:1 F#4:1 | D4:4"),
    _piece("andante", "Andante in D",
           "D and A strings. A slow tune for long, smooth bows.",
           "D4:1 F#4:1 A4:1 F#4:1 | G4:1 B4:1 A4:2 | F#4:1 A4:1 D5:1 A4:1 | B4:1 G4:1 F#4:2 | "
           "E4:1 G4:1 F#4:1 E4:1 | D4:4"),
    _piece("recital", "Recital Piece",
           "All four strings. It climbs from the open G to the open E, then comes home.",
           "G3:1 A3:1 B3:1 C4:1 | D4:1 E4:1 F#4:1 G4:1 | A4:1 B4:1 C#5:1 D5:1 | E5:2 B4:2 | G4:2 D4:2 | G3:4"),
    _piece("arpeggio", "D Major Arpeggio",
           "D, A and E strings. The D major chord from open D up to A on the E string and back.",
           "D4:1 F#4:1 A4:1 D5:1 | F#5:1 A5:1 F#5:1 D5:1 | A4:1 F#4:1 D4:2"),
]

PIECES: dict[str, Piece] = {p.id: p for p in _ALL}


def bars(piece: Piece) -> list[list[Note]]:
    """Split a piece into bars of four beats."""
    result, current, total = [], [], 0.0
    for note in piece.notes:
        current.append(note)
        total += note.beats
        if total >= BEATS_PER_BAR - 1e-9:
            result.append(current)
            current, total = [], 0.0
    if current:
        result.append(current)
    return result
