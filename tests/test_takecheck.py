"""The take checker, tested on simulated recordings: a synthetic violin, the real
click track as a phone speaker would play it, and room noise."""

import numpy as np
import pytest

from stringwise.audio.metronome import BEATS_PER_BAR, TRACK_RATE, render_click_track
from stringwise.audio.mic import SAMPLE_RATE
from stringwise.logic.takecheck import analyse, find_click_grid, find_notes
from stringwise.music.pieces import PIECES
from stringwise.music.rhythms import RHYTHMS


def bowed(freq, seconds):
    t = np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE
    wave = sum(np.sin(2 * np.pi * freq * k * t + 0.4 * k) / k for k in range(1, 7))
    envelope = np.minimum(1, t / 0.03) * np.minimum(1, (seconds - t) / 0.04)
    return 0.05 * wave * envelope


def record(notes, bpm, start_delay=0.23, clicks=True, shift=None, cents=None, skip=(),
           tempo_scale=1.0, noise=0.002, seed=3):
    """Simulate a take. ``shift`` = seconds late per note index, ``cents`` = tuning error."""
    shift, cents = shift or {}, cents or {}
    beat = 60.0 / bpm
    total_beats = BEATS_PER_BAR + sum(n.beats for n in notes) + BEATS_PER_BAR
    length = int((start_delay + total_beats * beat + 1.0) * SAMPLE_RATE)
    out = np.random.default_rng(seed).standard_normal(length) * noise
    if clicks:
        track = render_click_track(bpm, int(total_beats // BEATS_PER_BAR))
        positions = np.arange(len(track) * 2) / 2.0
        heard = np.interp(positions, np.arange(len(track)), track)          # 22.05k -> 44.1k
        heard = np.convolve(heard, [0.25, 0.5, 0.25], mode="same") * 0.2      # small speaker, some distance
        begin = int(start_delay * SAMPLE_RATE)
        out[begin:begin + len(heard)] += heard[:length - begin]
    position = float(BEATS_PER_BAR)
    for index, note in enumerate(notes):
        if not note.is_rest and index not in skip:
            when = start_delay + position * beat * tempo_scale + shift.get(index, 0.0)
            freq = note.freq * 2 ** (cents.get(index, 0.0) / 1200)
            # a late note is cut short by the next one, as it would be on a real string
            sound = bowed(freq, note.beats * beat * 0.92 - max(0.0, shift.get(index, 0.0)))
            begin = int(when * SAMPLE_RATE)
            out[begin:begin + len(sound)] += sound[:length - begin]
        position += note.beats
    return out.astype(np.float32)


def test_finds_every_note_and_when_it_started():
    notes = PIECES["hotcrossbuns"].notes
    audio = record(notes, 60, clicks=False)
    played = find_notes(audio, SAMPLE_RATE)
    assert len(played) == len(notes)
    position = float(BEATS_PER_BAR)
    for note, heard in zip(notes, played):
        assert abs(1200 * np.log2(heard.freq / note.freq)) < 8
        assert abs(heard.start - (0.23 + position)) < 0.03          # within 30 ms
        position += note.beats


@pytest.mark.parametrize("delay", [0.05, 0.23, 0.61])
def test_finds_the_click_under_the_violin(delay):
    notes = PIECES["scale"].notes
    audio = record(notes, 72, start_delay=delay)
    start, confidence = find_click_grid(audio, SAMPLE_RATE, 72, 28, TRACK_RATE)
    assert start is not None and abs(start - delay) < 0.004
    assert confidence > 8


def test_no_click_is_reported_as_no_click():
    audio = record(PIECES["scale"].notes, 72, clicks=False)
    start, _ = find_click_grid(audio, SAMPLE_RATE, 72, 28, TRACK_RATE)
    assert start is None


def test_clean_take():
    notes = PIECES["hotcrossbuns"].notes
    report = analyse(record(notes, 66), SAMPLE_RATE, notes, 66, TRACK_RATE)
    assert report.heard_click
    assert report.count(pitch="right") == len(notes)
    assert report.count(timing="on_time") == len(notes)
    assert report.extra_notes == 0
    assert report.headline.startswith("A clean take")
    assert abs(report.played_bpm - 66) < 1.5


def test_flags_late_early_wrong_and_out_of_tune_notes():
    notes = PIECES["hotcrossbuns"].notes            # C#5 B4 A4 | C#5 B4 A4 | A A B B | C# B A
    # note 3 follows a half note, so there is room for it to come in early
    audio = record(notes, 60, shift={1: 0.20, 3: -0.13}, cents={4: 45, 10: -300})
    report = analyse(audio, SAMPLE_RATE, notes, 60, TRACK_RATE)
    by_index = {r.index: r for r in report.results}
    assert by_index[1].timing == "late" and 0.15 < by_index[1].offset < 0.25
    assert by_index[3].timing == "early" and -0.17 < by_index[3].offset < -0.09
    assert by_index[4].pitch == "sharp"
    assert by_index[10].pitch == "wrong" and by_index[10].heard_name.startswith("A")   # C#5 down 3 semitones
    assert by_index[0].pitch == "right" and by_index[0].timing == "on_time"
    assert any("should be" in line for line in report.lines)


def test_missed_note_does_not_shift_the_rest():
    notes = PIECES["scale"].notes
    report = analyse(record(notes, 72, skip={5}), SAMPLE_RATE, notes, 72, TRACK_RATE)
    by_index = {r.index: r for r in report.results}
    assert by_index[5].pitch == "missed"
    assert sum(r.pitch == "right" and r.timing == "on_time" for r in report.results) == len(notes) - 1


def test_rushing_is_noticed():
    notes = PIECES["scale"].notes
    report = analyse(record(notes, 72, tempo_scale=0.93), SAMPLE_RATE, notes, 72, TRACK_RATE)
    assert report.played_bpm > 75
    assert any("sped up" in line for line in report.lines)
    assert report.count(timing="early") > 5


def test_rhythm_with_rests_and_repeated_notes():
    rhythm = RHYTHMS["w5"]                           # one pitch, with rests
    report = analyse(record(rhythm.notes, 66), SAMPLE_RATE, rhythm.notes, 66, TRACK_RATE)
    sounded = [n for n in rhythm.notes if not n.is_rest]
    assert report.total == len(sounded)
    assert report.count(pitch="right", timing="on_time") == len(sounded)


def test_without_the_click_timing_is_relative():
    notes = PIECES["hotcrossbuns"].notes
    audio = record(notes, 60, clicks=False, shift={6: 0.2})
    report = analyse(audio, SAMPLE_RATE, notes, 60, TRACK_RATE)
    assert not report.heard_click
    assert report.count(pitch="right") == len(notes)
    assert {r.index for r in report.results if r.timing == "late"} == {6}
    assert any("couldn't hear the click" in line for line in report.lines)


def test_silence():
    notes = PIECES["hotcrossbuns"].notes
    report = analyse(np.zeros(SAMPLE_RATE * 5, dtype=np.float32), SAMPLE_RATE, notes, 60, TRACK_RATE)
    assert report.headline.startswith("I couldn't hear any notes")
