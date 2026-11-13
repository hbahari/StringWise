import datetime
import math

import numpy as np
import pytest

from stringwise.audio.metronome import (BEATS_PER_BAR, TRACK_RATE, TapTempo, clamp_bpm,
                                        loop_bars, render_click_track)
from stringwise.audio.mic import SAMPLE_RATE
from stringwise.audio.pitch import FRAME_SIZE, MIC_GAIN, detect_pitch
from stringwise.audio.tone import synthesize_melody, synthesize_rhythm_demo
from stringwise.content.lessons import LESSONS
from stringwise.content.timing import TIMING
from stringwise.music.notes import parse_sequence
from stringwise.music.pieces import bars
from stringwise.music.rhythms import RHYTHMS, rhythm_of_the_day
from stringwise.ui.staff_layout import layout


def click_starts(track, rate):
    """Sample index where each click begins."""
    loud = np.nonzero(np.abs(track) > 0.02)[0]
    return [int(loud[0])] + [int(b) for a, b in zip(loud, loud[1:]) if b - a > rate * 0.05]


@pytest.mark.parametrize("bpm", [40, 60, 66, 72, 97, 160])
def test_clicks_land_exactly_on_the_beat(bpm):
    track = render_click_track(bpm, 8)
    assert len(track) == round(8 * BEATS_PER_BAR * 60 / bpm * TRACK_RATE)
    starts = click_starts(track, TRACK_RATE)
    assert len(starts) == 32
    for beat, start in enumerate(starts):
        assert abs(start - beat * 60 / bpm * TRACK_RATE) <= 2      # within 0.1 ms


def test_first_beat_is_accented_and_eighths_are_quieter():
    track = render_click_track(60, 1, subdivide=True)
    peak = lambda t: float(np.max(np.abs(track[int(t * TRACK_RATE):int((t + 0.03) * TRACK_RATE)])))
    assert peak(0.0) > peak(1.0) > peak(0.5) > 0.1
    assert peak(0.25) == 0.0


def test_drop_out_bars_are_silent():
    bar = round(BEATS_PER_BAR * 60 / 72 * TRACK_RATE)
    track = render_click_track(72, 8, gaps=True)
    energy = [float(np.abs(track[i * bar:(i + 1) * bar]).sum()) for i in range(8)]
    assert [e > 0 for e in energy] == [True, True, False, False] * 2
    assert loop_bars(72) % 4 == 0 and loop_bars(40) % 4 == 0


def test_a_click_is_never_heard_as_a_note():
    """The microphone will pick the metronome up; it must not register as a pitch."""
    track = render_click_track(120, 4, subdivide=True, sample_rate=SAMPLE_RATE) * 0.3 * MIC_GAIN
    hits = 0
    for start in range(0, len(track) - FRAME_SIZE, 1024):
        freq, _, _ = detect_pitch(track[start:start + FRAME_SIZE].astype(np.float32), SAMPLE_RATE)
        hits += freq is not None
    assert hits == 0


def test_tap_tempo():
    taps = TapTempo()
    assert taps.tap(10.0) is None
    assert taps.tap(10.5) == 120
    assert taps.tap(11.0) == 120
    assert taps.tap(20.0) is None          # long pause: start again
    assert taps.tap(21.0) == 60
    assert clamp_bpm(500) == 160 and clamp_bpm(1) == 40


def test_rests_parse_and_are_silent():
    notes = parse_sequence("A4:1 R:1 A4:2")
    assert [n.is_rest for n in notes] == [False, True, False]
    audio = synthesize_melody(notes, 0.5)
    middle = audio[int(0.65 * SAMPLE_RATE):int(0.95 * SAMPLE_RATE)]
    assert float(np.max(np.abs(middle))) < 1e-6
    lay = layout(notes)
    assert lay.fingers[1] is None and len(lay.xs) == 3


@pytest.mark.parametrize("rhythm", RHYTHMS.values(), ids=lambda r: r.id)
def test_rhythm_bars_add_up(rhythm):
    class Holder:
        notes = rhythm.notes
    for bar in bars(Holder):
        assert math.isclose(sum(n.beats for n in bar), BEATS_PER_BAR), rhythm.id
    assert all(n.beats in (1, 2, 4) for n in rhythm.notes if n.is_rest)
    if any(n.beats in (0.5, 1.5) for n in rhythm.notes):
        assert rhythm.week >= 9 and rhythm.subdivide


def test_every_week_has_a_timing_lesson_inside_the_hour():
    tempos = []
    for lesson in LESSONS:
        study = lesson.timing
        assert study is TIMING[lesson.week]
        assert lesson.total_minutes == 60
        assert lesson.plan[1].title.startswith("Timing: ") and lesson.plan[1].minutes == 10
        assert study.tempos == tuple(sorted(study.tempos)) and 40 <= study.tempos[0] <= 80
        if study.rhythm:
            assert RHYTHMS[study.rhythm].week == lesson.week
        tempos.append(study.tempos[-1])
    assert TIMING[9].subdivide and TIMING[12].gaps
    assert tempos[0] == 60 and max(tempos) == 84


def test_rhythm_of_the_day():
    day = datetime.date(2026, 11, 12)
    assert rhythm_of_the_day(1, day).id == "w1"                       # only one to choose from
    for offset in range(40):
        rhythm = rhythm_of_the_day(4, day + datetime.timedelta(days=offset))
        assert rhythm.week <= 4
    seen = {rhythm_of_the_day(12, day + datetime.timedelta(days=i)).id for i in range(len(RHYTHMS))}
    assert seen == set(RHYTHMS)


def test_rhythm_demo_has_a_count_in_bar():
    notes = RHYTHMS["w5"].notes
    demo = synthesize_rhythm_demo(notes, 60)
    assert len(demo) >= 5 * BEATS_PER_BAR * SAMPLE_RATE              # 1 bar count-in + 4 bars
    assert np.max(np.abs(demo)) <= 1.0
    count_in = demo[int(0.2 * SAMPLE_RATE):int(0.9 * SAMPLE_RATE)]   # between clicks 1 and 2
    assert float(np.max(np.abs(count_in))) < 1e-6
