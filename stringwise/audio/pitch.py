"""Pitch detection for the violin's range, using the YIN algorithm.

YIN (de Cheveigne and Kawahara, 2002) copes well with the strong overtones of a
bowed string, where a plain autocorrelation tends to jump an octave. The search
is limited to notes a beginner can reach, which keeps it fast and stops low
rumble from being read as a pitch.
"""

from __future__ import annotations

import numpy as np

PITCH_MIN_HZ = 170.0     # a little under the open G (196 Hz)
PITCH_MAX_HZ = 1500.0
YIN_THRESHOLD = 0.15
YIN_FALLBACK = 0.35
RMS_GATE = 0.005         # level (after MIC_GAIN) treated as silence
MIC_GAIN = 4.0           # software boost so quiet phone microphones still register
WINDOW = 1024            # samples compared at each lag
FRAME_SIZE = 2048        # samples handed to detect_pitch


def detect_pitch(samples: np.ndarray, sample_rate: int) -> tuple[float | None, float, float]:
    """Return (frequency or None, rms level, clarity 0..1) for a mono float buffer."""
    n = len(samples)
    tau_min = max(2, int(sample_rate / PITCH_MAX_HZ))
    tau_max = min(int(sample_rate / PITCH_MIN_HZ), n // 2)
    window = min(WINDOW, n - tau_max)
    x = np.asarray(samples[n - (window + tau_max):], dtype=np.float64)   # newest samples

    rms = float(np.sqrt(np.mean(x * x)))
    if rms < RMS_GATE:
        return None, rms, 0.0

    # Difference function d(tau) = sum_j (x[j] - x[j + tau])^2 over the window,
    # expanded so the cross term is one correlation instead of a Python loop.
    squares = np.concatenate(([0.0], np.cumsum(x * x)))
    energy = squares[window:window + tau_max + 1] - squares[:tau_max + 1]
    cross = np.correlate(x, x[:window], mode="valid")
    d = energy[0] + energy - 2.0 * cross
    d[0] = 0.0
    np.maximum(d, 0.0, out=d)

    # Cumulative mean normalised difference.
    running = np.cumsum(d[1:])
    cmnd = np.ones(tau_max + 1)
    lags = np.arange(1, tau_max + 1)
    np.divide(d[1:] * lags, running, out=cmnd[1:], where=running > 0)

    tau = _first_dip(cmnd, tau_min, tau_max)
    if tau is None:
        tau = _fallback_dip(cmnd, tau_min, tau_max)
        if tau is None:
            return None, rms, 0.0
    clarity = float(1.0 - cmnd[tau])

    # Parabolic interpolation for sub-sample accuracy.
    better = float(tau)
    if 1 < tau < tau_max:
        s0, s1, s2 = cmnd[tau - 1], cmnd[tau], cmnd[tau + 1]
        denom = 2.0 * (2.0 * s1 - s2 - s0)
        if denom != 0:
            better = tau + (s2 - s0) / denom
    return sample_rate / better, rms, clarity


def _first_dip(cmnd: np.ndarray, tau_min: int, tau_max: int) -> int | None:
    below = np.nonzero(cmnd[tau_min:tau_max + 1] < YIN_THRESHOLD)[0]
    if len(below) == 0:
        return None
    tau = tau_min + int(below[0])
    while tau + 1 <= tau_max and cmnd[tau + 1] < cmnd[tau]:
        tau += 1
    return tau


def _fallback_dip(cmnd: np.ndarray, tau_min: int, tau_max: int) -> int | None:
    """No clean dip (quiet or noisy input): take the first local minimum that is
    nearly as deep as the deepest one, so noise cannot drag the answer an octave low."""
    lowest = float(cmnd[tau_min:tau_max + 1].min())
    if lowest >= YIN_FALLBACK:
        return None
    limit = lowest * 1.25 + 0.03
    for tau in range(max(tau_min, 2), tau_max):
        if cmnd[tau] <= limit and cmnd[tau] <= cmnd[tau - 1] and cmnd[tau] <= cmnd[tau + 1]:
            return tau
    return None


class MedianFilter:
    """Median of the last three readings. Drops a single stray value (an octave
    glitch, a bow-change blip) without adding lag you can feel."""

    def __init__(self) -> None:
        self._history: list[float] = []
        self._misses = 0

    def push(self, freq: float | None) -> float | None:
        if freq is None:
            self._misses += 1
            if self._misses >= 3:
                self._history.clear()
            return None
        self._misses = 0
        self._history.append(freq)
        if len(self._history) > 3:
            self._history.pop(0)
        if len(self._history) < 3:
            return freq
        return sorted(self._history)[1]

    def reset(self) -> None:
        self._history.clear()
        self._misses = 0


def level_fraction(rms: float) -> float:
    """Map an rms level to 0..1 for the input meter (-60 dB to -12 dB)."""
    db = 20.0 * np.log10(max(rms, 1e-5))
    return float(min(1.0, max(0.0, (db + 60.0) / 48.0)))
