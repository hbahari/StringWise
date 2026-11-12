import numpy as np
import pytest

from stringwise.audio.listener import HOP, PitchListener
from stringwise.audio.mic import SAMPLE_RATE, SyntheticMic
from stringwise.audio.pitch import (FRAME_SIZE, PITCH_MAX_HZ, PITCH_MIN_HZ, WINDOW,
                                    MedianFilter, detect_pitch)
from stringwise.audio.tone import synthesize, synthesize_melody
from stringwise.music.fingering import STRINGS
from stringwise.music.notes import cents_between
from stringwise.music.pieces import PIECES


def violin_like(freq, amplitude=0.1, n=FRAME_SIZE, phase=0.3):
    t = np.arange(n) / SAMPLE_RATE
    wave = sum(np.sin(2 * np.pi * freq * k * t + phase * k) / k for k in range(1, 7))
    return (amplitude * wave).astype(np.float32)


@pytest.mark.parametrize("note", [n for s in STRINGS for n in s.notes], ids=lambda n: n.label)
def test_every_first_position_note_is_detected_within_3_cents(note):
    freq, rms, clarity = detect_pitch(violin_like(note.freq), SAMPLE_RATE)
    assert freq is not None
    assert abs(cents_between(freq, note.freq)) < 3
    assert clarity > 0.8


def test_quiet_note_still_detected():
    freq, _, _ = detect_pitch(violin_like(440.0, amplitude=0.006), SAMPLE_RATE)
    assert freq == pytest.approx(440.0, abs=1.0)


def test_silence_and_noise_give_no_pitch():
    assert detect_pitch(np.zeros(FRAME_SIZE, dtype=np.float32), SAMPLE_RATE)[0] is None
    rng = np.random.default_rng(1)
    hits = sum(detect_pitch((0.05 * rng.standard_normal(FRAME_SIZE)).astype(np.float32),
                            SAMPLE_RATE)[0] is not None for _ in range(200))
    assert hits <= 2


def test_matches_the_textbook_difference_function():
    """The fast difference function must equal the plain definition."""
    x = violin_like(330.0).astype(np.float64)
    tau_max = int(SAMPLE_RATE / PITCH_MIN_HZ)
    seg = x[len(x) - (WINDOW + tau_max):]
    slow = np.array([np.sum((seg[:WINDOW] - seg[tau:tau + WINDOW]) ** 2) for tau in range(tau_max + 1)])
    squares = np.concatenate(([0.0], np.cumsum(seg * seg)))
    energy = squares[WINDOW:WINDOW + tau_max + 1] - squares[:tau_max + 1]
    fast = energy[0] + energy - 2 * np.correlate(seg, seg[:WINDOW], mode="valid")
    assert np.allclose(slow, fast, atol=1e-8)
    assert PITCH_MAX_HZ > 1300


def test_median_filter_drops_one_glitch():
    f = MedianFilter()
    out = [f.push(v) for v in (440.0, 441.0, 880.0, 440.5, 440.2)]
    assert out[2] == 441.0 and out[3] == 441.0 and out[4] == 440.5
    assert f.push(None) is None


def test_tone_is_in_tune_and_not_clipped():
    samples = synthesize(293.66, 1.0)
    assert np.max(np.abs(samples)) <= 1.0
    freq, _, _ = detect_pitch(samples[20000:20000 + FRAME_SIZE].astype(np.float32), SAMPLE_RATE)
    assert abs(cents_between(freq, 293.66)) < 3


def _loudness(samples, at_seconds, width=0.03):
    middle = int(at_seconds * SAMPLE_RATE)
    half = int(width * SAMPLE_RATE / 2)
    return float(np.sqrt(np.mean(samples[middle - half:middle + half] ** 2)))


def test_melody_is_joined_up_like_bowing():
    notes = PIECES["hotcrossbuns"].notes           # C#, B, A(2), C#, B, A(2), A, A, B, B, ...
    beat = 0.5
    melody = synthesize_melody(notes, beat)
    assert len(melody) == pytest.approx((16 * beat + 0.35) * SAMPLE_RATE, abs=20)
    assert np.max(np.abs(melody)) <= 1.0
    steady = _loudness(melody, 0.25)
    assert _loudness(melody, 1 * beat) > 0.6 * steady      # C# into B: no gap
    assert _loudness(melody, 9 * beat, 0.01) < 0.3 * steady  # A repeated: a clear re-bow
    # still in tune in the middle of a note
    freq, _, _ = detect_pitch(melody[int(1.3 * SAMPLE_RATE):][:FRAME_SIZE].astype(np.float32), SAMPLE_RATE)
    assert abs(cents_between(freq, 440.0)) < 12


def test_listener_end_to_end():
    listener = PitchListener(lambda: SyntheticMic([440.0], realtime=False))
    listener.start()
    frames = []
    import time
    deadline = time.time() + 5
    while len(frames) < 20 and time.time() < deadline:
        frames += listener.poll()
        time.sleep(0.01)
    listener.stop()
    assert not listener.running and listener.error is None
    good = [f.freq for f in frames if f.freq]
    assert len(good) >= 10
    assert abs(cents_between(float(np.median(good)), 440.0)) < 5
    assert HOP == 1024
