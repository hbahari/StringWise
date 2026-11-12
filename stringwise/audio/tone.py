"""Reference tones. Each tone is synthesised once, saved as a WAV and played back."""

from __future__ import annotations

import os
import wave

import numpy as np

SAMPLE_RATE = 44100
_HARMONICS = ((1, 1.00), (2, 0.55), (3, 0.34), (4, 0.20), (5, 0.12), (6, 0.07))
VIBRATO_HZ = 5.5
SLUR = 0.07      # seconds of overlap between two different notes
REBOW = 0.035    # fade either side of a repeated note
TAIL = 0.35      # fade at the very end of a piece


def synthesize(freq: float, duration: float = 1.1) -> np.ndarray:
    """A warm, steady tone with a soft start and end, as float samples in -1..1."""
    t = np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE
    wave_sum = np.zeros_like(t)
    for multiple, gain in _HARMONICS:
        if freq * multiple < SAMPLE_RATE / 2:
            wave_sum += gain * np.sin(2 * np.pi * freq * multiple * t)
    wave_sum /= sum(g for _, g in _HARMONICS)
    attack = np.minimum(1.0, t / 0.05)
    release_start = duration * 0.55
    release = np.where(t < release_start, 1.0,
                       np.exp(-5.0 * (t - release_start) / (duration - release_start)))
    tail = np.minimum(1.0, (duration - t) / 0.02)
    return 0.6 * wave_sum * attack * release * tail


def _bowed(freq: float, seconds: float, vibrato: bool) -> np.ndarray:
    """A sustained note at full strength, with a little vibrato once it has settled."""
    t = np.arange(int(round(SAMPLE_RATE * seconds))) / SAMPLE_RATE
    wobble = 0.0
    if vibrato:
        depth = 0.004 * np.clip((t - 0.15) / 0.25, 0.0, 1.0)      # eases in after the start
        wobble = (freq * depth / VIBRATO_HZ) * np.sin(2 * np.pi * VIBRATO_HZ * t)
    out = np.zeros_like(t)
    for multiple, gain in _HARMONICS:
        if freq * multiple < SAMPLE_RATE / 2:
            out += gain * np.sin(multiple * (2 * np.pi * freq * t + wobble))
    out /= sum(g for _, g in _HARMONICS)
    swell = 0.85 + 0.15 * np.sin(np.pi * np.clip(t / max(seconds, 1e-6), 0.0, 1.0))   # gentle bow swell
    return 0.6 * out * swell


def synthesize_melody(notes, seconds_per_beat: float = 0.6) -> np.ndarray:
    """Play a piece the way a bow would: each note runs into the next.

    Neighbouring notes overlap in a short crossfade, so there is no gap between
    them. When the same pitch is repeated there is a brief dip instead, like a
    change of bow, so the two notes can still be told apart.
    """
    notes = list(notes)
    total = int(round(sum(n.beats for n in notes) * seconds_per_beat * SAMPLE_RATE))
    out = np.zeros(total + int(TAIL * SAMPLE_RATE))
    start = 0.0
    for i, note in enumerate(notes):
        length = note.beats * seconds_per_beat
        previous = notes[i - 1] if i > 0 else None
        following = notes[i + 1] if i + 1 < len(notes) else None
        fade_in = REBOW if previous is not None and previous.same_pitch(note) else (
            SLUR if previous is not None else 0.04)
        if following is None:
            fade_out, extra = TAIL, TAIL                     # let the last note die away
        elif following.same_pitch(note):
            fade_out, extra = REBOW, 0.0                     # dip, then a fresh stroke
        else:
            fade_out, extra = SLUR, SLUR                     # overlap into the next note
        segment = _bowed(note.freq, length + extra, vibrato=length >= 0.5)
        n = len(segment)
        t = np.arange(n) / SAMPLE_RATE
        rise = 0.5 - 0.5 * np.cos(np.pi * np.clip(t / fade_in, 0.0, 1.0))
        fall = 0.5 - 0.5 * np.cos(np.pi * np.clip((n / SAMPLE_RATE - t) / fade_out, 0.0, 1.0))
        begin = int(round(start * SAMPLE_RATE))
        end = min(begin + n, len(out))
        out[begin:end] += (segment * rise * fall)[:end - begin]
        start += length
    return out


def write_wav(path: str, samples: np.ndarray) -> None:
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(path, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(pcm.tobytes())


class TonePlayer:
    """Plays tones through Kivy's sound loader, caching the WAV files on disk."""

    def __init__(self, cache_dir: str) -> None:
        self._dir = os.path.join(cache_dir, "tones")
        os.makedirs(self._dir, exist_ok=True)
        self._current = None

    def play_tone(self, freq: float, duration: float = 1.1) -> None:
        path = os.path.join(self._dir, f"tone_{freq:.2f}_{duration:.2f}.wav")
        if not os.path.exists(path):
            write_wav(path, synthesize(freq, duration))
        self._play(path)

    def play_melody(self, key: str, notes, seconds_per_beat: float = 0.6) -> None:
        path = os.path.join(self._dir, f"melody2_{key}_{seconds_per_beat:.2f}.wav")
        if not os.path.exists(path):
            write_wav(path, synthesize_melody(notes, seconds_per_beat))
        self._play(path)

    def stop(self) -> None:
        if self._current is not None:
            try:
                self._current.stop()
            except Exception:
                pass
            self._current = None

    @property
    def playing(self) -> bool:
        return self._current is not None and self._current.state == "play"

    def _play(self, path: str) -> None:
        from kivy.core.audio import SoundLoader
        self.stop()
        sound = SoundLoader.load(path)
        if sound is not None:
            sound.play()
            self._current = sound
