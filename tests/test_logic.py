from stringwise.logic.fingercheck import FingerCheck
from stringwise.logic.playalong import (STATUS_DONE, STATUS_REPEAT, PlayAlong)
from stringwise.logic.tuner import Tuner
from stringwise.music.notes import Note
from stringwise.music.pieces import PIECES, Piece
from stringwise.ui.staff_layout import layout

RATE = 43.0
LOUD, QUIET = 0.1, 0.0


def play(session, freq, frames=12, rms=LOUD):
    view = None
    for _ in range(frames):
        view = session.feed(freq, rms)
    return view


def silence(session, frames=6):
    return play(session, None, frames, QUIET)


def sharp(freq, cents):
    return freq * 2 ** (cents / 1200)


def test_tuner_reads_note_and_direction():
    tuner = Tuner(RATE)
    tuner.start()
    view = play(tuner, 440.0)
    assert (view.note, view.verdict) == ("A", "in_tune")
    view = play(tuner, sharp(440.0, 20))
    assert view.caption == "sharp" and "tune down" in view.advice
    view = play(tuner, sharp(293.66, -40))
    assert view.note == "D" and view.caption == "flat" and view.verdict == "far"
    view = silence(tuner, 40)
    assert view.note is None


def test_finger_check_verdicts():
    check = FingerCheck(RATE)
    check.choose("A", 4)
    assert check.target == Note("E", 5)          # finger 4 on A is E, not D
    check.start()
    target = check.target.freq
    assert play(check, target, 30).settled
    view = play(check, sharp(target, 30))
    assert view.verdict == "close" and "scroll" in view.message      # sharp: move back toward the scroll
    view = play(check, sharp(target, -30))
    assert view.verdict == "close" and "bridge" in view.message
    assert play(check, sharp(target, 200)).verdict == "off"


def test_play_along_follows_a_whole_piece():
    piece = PIECES["hotcrossbuns"]
    session = PlayAlong(piece, RATE)
    session.start()
    for note in piece.notes:
        play(session, note.freq, 20)
        silence(session)
    assert session.finished and session.view.status == STATUS_DONE
    assert session.view.confirmed == len(piece.notes)


def test_play_along_ignores_wrong_notes():
    session = PlayAlong(PIECES["hotcrossbuns"], RATE)     # first note is C sharp
    session.start()
    view = play(session, 440.0, 30)
    assert view.index == 0 and view.cursor_kind == "wrong" and view.cursor_step == Note("A", 4).staff_step
    view = play(session, sharp(Note("C#", 5).freq, 45), 30)
    assert view.index == 0 and view.cursor_kind == "close"


def test_one_long_note_does_not_count_twice():
    piece = Piece("t", "t", "", (Note("A", 4), Note("A", 4), Note("B", 4)))
    session = PlayAlong(piece, RATE)
    session.start()
    view = play(session, 440.0, 80)                 # one long, unbroken A
    assert view.index == 1 and view.status == STATUS_REPEAT
    silence(session, 4)                              # bow stops
    assert play(session, 440.0, 20).index == 2       # second A now counts


def test_repeat_also_counts_after_a_dip_in_loudness():
    piece = Piece("t", "t", "", (Note("A", 4), Note("A", 4)))
    session = PlayAlong(piece, RATE)
    session.start()
    play(session, 440.0, 30)
    play(session, 440.0, 3, rms=LOUD * 0.3)          # bow change: quieter for a moment
    play(session, 440.0, 20)
    assert session.finished


def test_restart_and_stop():
    session = PlayAlong(PIECES["scale"], RATE)
    session.start()
    play(session, Note("D", 4).freq, 20)
    assert session.view.confirmed == 1
    session.restart()
    assert session.view.index == 0 and session.view.confirmed == 0
    session.stop()
    assert session.view.cursor_step is None


def test_staff_layout():
    for piece in PIECES.values():
        lay = layout(piece.notes)
        assert len(lay.xs) == len(piece.notes)
        assert lay.xs == sorted(lay.xs) and len(set(lay.xs)) == len(lay.xs)
        assert all(a < b for a, b in zip(lay.barlines, lay.barlines[1:]))
        assert lay.width > lay.xs[-1]
        eighths = {i for i, n in enumerate(piece.notes) if n.beats == 0.5}
        beamed = {i for pair in lay.beams for i in pair}
        assert beamed | lay.flags == eighths and not beamed & lay.flags
    echo = layout(PIECES["rhythmecho"].notes)
    assert len(echo.beams) == 4 and len(echo.flags) == 2      # two dotted-quarter + eighth pairs
