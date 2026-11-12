import math

import pytest

from stringwise.content.lessons import LESSONS
from stringwise.content.theory import SECTIONS
from stringwise.music import fingering
from stringwise.music.notes import Note, ledger_steps, nearest_note, parse_sequence
from stringwise.music.pieces import BEATS_PER_BAR, PIECES, bars


def test_note_frequencies():
    assert Note("A", 4).freq == pytest.approx(440.0)
    assert Note("G", 3).freq == pytest.approx(196.00, abs=0.01)
    assert Note("D", 4).freq == pytest.approx(293.66, abs=0.01)
    assert Note("E", 5).freq == pytest.approx(659.26, abs=0.01)


def test_open_strings_on_the_staff():
    # G3 hangs below two ledger lines, D4 just under the bottom line,
    # A4 in the second space, E5 in the top space.
    assert Note("G", 3).staff_step == -5 and ledger_steps(-5) == [-2, -4]
    assert Note("D", 4).staff_step == -1 and ledger_steps(-1) == []
    assert Note("A", 4).staff_step == 3
    assert Note("E", 5).staff_step == 7
    assert Note("A", 5).staff_step == 10 and ledger_steps(10) == [10]


def test_nearest_note():
    heard = nearest_note(440.0)
    assert (heard.name, heard.octave, round(heard.cents)) == ("A", 4, 0)
    heard = nearest_note(440.0 * 2 ** (20 / 1200))
    assert heard.name == "A" and round(heard.cents) == 20
    heard = nearest_note(196.0)
    assert (heard.name, heard.octave) == ("G", 3)


def test_finger_pattern_spacing():
    gaps = [b - a for a, b in zip(fingering.FINGER_OFFSETS, fingering.FINGER_OFFSETS[1:])]
    assert gaps == [2, 2, 1, 2]          # whole, whole, HALF, whole
    for string in fingering.STRINGS:
        for finger, note in enumerate(string.notes):
            assert note.midi - string.open_note.midi == fingering.FINGER_OFFSETS[finger]


def test_fourth_finger_matches_next_open_string():
    for lower, upper in zip(fingering.STRINGS, fingering.STRINGS[1:]):
        assert lower.notes[4].midi == upper.open_note.midi
    assert fingering.target_note("A", 4) == Note("E", 5)


def test_parse_sequence():
    notes = parse_sequence("A4:1 C#5:.5 | B4:1.5")
    assert [(n.name, n.octave, n.beats) for n in notes] == [("A", 4, 1), ("C#", 5, .5), ("B", 4, 1.5)]
    with pytest.raises(ValueError):
        parse_sequence("H4:1")


@pytest.mark.parametrize("piece", PIECES.values(), ids=lambda p: p.id)
def test_piece_is_playable_and_bars_add_up(piece):
    for bar in bars(piece):
        assert math.isclose(sum(n.beats for n in bar), BEATS_PER_BAR), piece.id
    for note in piece.notes:
        assert fingering.fingering_for(note) is not None, f"{piece.id}: {note.label} out of reach"


def test_lessons():
    assert [l.week for l in LESSONS] == list(range(1, 13))
    used = []
    for lesson in LESSONS:
        assert lesson.total_minutes == 60, lesson.week
        assert len(lesson.goals) == 3
        if lesson.week >= 2:
            assert len(lesson.pieces) == 2
        for piece_id in lesson.pieces:
            assert piece_id in PIECES
            used.append(piece_id)
    assert sorted(used) == sorted(PIECES)      # every piece is used exactly once


def test_pieces_only_use_strings_already_taught():
    # Week a string's fingered notes are introduced (open strings are fine from week 2).
    taught = {"A": 3, "D": 5, "G": 6, "E": 6}
    for lesson in LESSONS:
        for piece_id in lesson.pieces:
            for note in PIECES[piece_id].notes:
                string, finger = fingering.fingering_for(note)
                if finger:
                    assert lesson.week >= taught[string], (lesson.week, piece_id, note.label)
                if finger == 4:
                    assert lesson.week >= 4


def test_theory_blocks_are_well_formed():
    kinds = {"p", "h", "list", "terms", "open_strings"}
    for section in SECTIONS:
        assert section.blocks
        for block in section.blocks:
            assert block[0] in kinds
