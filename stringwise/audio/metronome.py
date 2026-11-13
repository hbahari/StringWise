"""The metronome.

Clicks have to land exactly on the beat, so they are not fired one at a time by
a timer. A couple of minutes of clicks are rendered into one sound file with
every click placed to the sample, and that file is played on a loop.
"""

from __future__ import annotations

import glob
import os
import time

import numpy as np

BEATS_PER_BAR = 4
MIN_BPM, MAX_BPM = 40, 160
TRACK_RATE = 22050          # plenty for a click, and keeps the file small
TRACK_SECONDS = 120
GAP_CYCLE = (False, False, True, True)     # drop-out mode: two bars of click, two bars silent


def clamp_bpm(bpm: float) -> int:
    return int(max(MIN_BPM, min(MAX_BPM, round(bpm))))


def _click(sample_rate: int, kind: str) -> np.ndarray:
    """A short tick made of noise. Noise has no pitch, so a click picked up by the
    microphone is never mistaken for a note."""
    n = int(sample_rate * 0.03)
    rng = np.random.default_rng({"accent": 7, "beat": 11, "sub": 13}[kind])
    noise = rng.standard_normal(n + 1)
    t = np.arange(n) / sample_rate
    if kind == "accent":
        body, gain, decay = np.diff(noise), 0.95, 0.006          # bright and loud
    elif kind == "beat":
        body, gain, decay = (noise[1:] + noise[:-1]) / 2, 0.75, 0.005
    else:
        body, gain, decay = (noise[1:] + noise[:-1]) / 2, 0.30, 0.003
    body = body / np.max(np.abs(body))
    return gain * body * np.exp(-t / decay)


def render_click_track(bpm: float, bars: int, subdivide: bool = False, gaps: bool = False,
                       sample_rate: int = TRACK_RATE) -> np.ndarray:
    """``bars`` bars of clicks. Beat 1 is accented; ``subdivide`` adds the 'and' of each
    beat; ``gaps`` silences two bars in every four."""
    beat = 60.0 / bpm
    total = int(round(bars * BEATS_PER_BAR * beat * sample_rate))
    out = np.zeros(total)
    sounds = {kind: _click(sample_rate, kind) for kind in ("accent", "beat", "sub")}

    def place(when: float, kind: str) -> None:
        start = int(round(when * sample_rate))
        sound = sounds[kind][:max(0, total - start)]
        out[start:start + len(sound)] += sound

    for bar in range(bars):
        if gaps and GAP_CYCLE[bar % len(GAP_CYCLE)]:
            continue
        for b in range(BEATS_PER_BAR):
            when = (bar * BEATS_PER_BAR + b) * beat
            place(when, "accent" if b == 0 else "beat")
            if subdivide:
                place(when + beat / 2, "sub")
    return out


def loop_bars(bpm: float) -> int:
    """Whole bars (a multiple of four, so drop-out mode loops cleanly) in about two minutes."""
    bars = int(TRACK_SECONDS / (BEATS_PER_BAR * 60.0 / bpm))
    return max(4, bars - bars % 4)


class TapTempo:
    """Works out a tempo from the last few taps."""

    def __init__(self) -> None:
        self._taps: list[float] = []

    def tap(self, now: float | None = None) -> int | None:
        now = time.monotonic() if now is None else now
        if self._taps and now - self._taps[-1] > 2.0:
            self._taps.clear()                       # a long pause starts a new count
        self._taps.append(now)
        self._taps = self._taps[-5:]
        if len(self._taps) < 2:
            return None
        gaps = [b - a for a, b in zip(self._taps, self._taps[1:])]
        return clamp_bpm(60.0 / (sum(gaps) / len(gaps)))


class Metronome:
    """Shared by every screen. Widgets register with ``watch`` to be told about changes."""

    def __init__(self, cache_dir: str, output_delay: float = 0.03) -> None:
        self._dir = os.path.join(cache_dir, "metronome")
        os.makedirs(self._dir, exist_ok=True)
        self.bpm = 72
        self.subdivide = False
        self.gaps = False
        self.running = False
        self.used = False            # True once it has been started; the title bar then keeps its control
        self._sound = None
        self._started = 0.0
        self._length = 0.0
        self._output_delay = output_delay
        self._taps = TapTempo()
        self._watchers = []          # weak references to widgets with sync() and tick()
        self._tick_event = None
        self._restart_event = None

    # -- watchers --------------------------------------------------------
    def watch(self, widget) -> None:
        import weakref
        self._watchers.append(weakref.ref(widget))

    def _each_watcher(self):
        alive = []
        for ref in self._watchers:
            widget = ref()
            if widget is not None:
                alive.append(ref)
                yield widget
        self._watchers = alive

    def _notify(self) -> None:
        for widget in list(self._each_watcher()):
            widget.sync()

    # -- settings ----------------------------------------------------------
    def configure(self, bpm=None, subdivide=None, gaps=None) -> None:
        before = (self.bpm, self.subdivide, self.gaps)
        if bpm is not None:
            self.bpm = clamp_bpm(bpm)
        if subdivide is not None:
            self.subdivide = bool(subdivide)
        if gaps is not None:
            self.gaps = bool(gaps)
        if (self.bpm, self.subdivide, self.gaps) != before and self.running:
            self._restart_soon()
        self._notify()

    def tap(self) -> None:
        bpm = self._taps.tap()
        if bpm is not None:
            self.configure(bpm=bpm)

    # -- transport ---------------------------------------------------------
    def toggle(self) -> None:
        self.stop() if self.running else self.start()

    def start(self) -> None:
        from kivy.clock import Clock
        self._play()
        self.running = True
        self.used = True
        if self._tick_event is None:
            self._tick_event = Clock.schedule_interval(self._tick, 1 / 30)
        self._notify()

    def stop(self) -> None:
        if self._tick_event is not None:
            self._tick_event.cancel()
            self._tick_event = None
        if self._restart_event is not None:
            self._restart_event.cancel()
            self._restart_event = None
        self._silence()
        was_running, self.running = self.running, False
        if was_running:
            self._notify()

    def beat_state(self) -> tuple[int, bool, int, float] | None:
        """(beat 0..3, whether this bar is a silent drop-out bar, bar 0..3 in the
        four-bar cycle, how far through the beat 0..1), or None when stopped."""
        if not self.running or self._length <= 0:
            return None
        elapsed = (time.monotonic() - self._started - self._output_delay) % self._length
        if elapsed < 0:
            return None
        beats = elapsed / (60.0 / self.bpm)
        bar = int(beats // BEATS_PER_BAR)
        cycle_bar = bar % len(GAP_CYCLE)
        return (int(beats) % BEATS_PER_BAR, self.gaps and GAP_CYCLE[cycle_bar], cycle_bar,
                beats - int(beats))

    def seconds_to_next_bar(self, at_least: float = 0.15) -> float:
        """How long until the next beat 1, so another sound can start in step with the click."""
        if not self.running or self._length <= 0:
            return 0.0
        bar = BEATS_PER_BAR * 60.0 / self.bpm
        into_bar = (time.monotonic() - self._started) % bar
        wait = bar - into_bar
        return wait if wait >= at_least else wait + bar

    def write_take_track(self, bpm: float, bars: int, subdivide: bool = False) -> tuple[str, float]:
        """A one-off click track for a recorded take. Returns (file path, length in seconds)."""
        from .tone import write_wav
        for old in glob.glob(os.path.join(self._dir, "take_*.wav")):
            try:
                os.remove(old)
            except OSError:
                pass
        path = os.path.join(self._dir, f"take_{int(time.time() * 1000)}.wav")
        track = render_click_track(bpm, bars, subdivide)
        write_wav(path, track, TRACK_RATE)
        return path, len(track) / TRACK_RATE

    # -- internals ---------------------------------------------------------
    def _restart_soon(self) -> None:
        from kivy.clock import Clock
        if self._restart_event is not None:
            self._restart_event.cancel()
        self._silence()
        self._restart_event = Clock.schedule_once(self._restart, 0.25)

    def _restart(self, _dt) -> None:
        self._restart_event = None
        if self.running:
            self._play()

    def _play(self) -> None:
        from kivy.core.audio import SoundLoader
        from .tone import write_wav
        self._silence()
        bars = loop_bars(self.bpm)
        name = f"click_{self.bpm}_{int(self.subdivide)}_{int(self.gaps)}.wav"
        path = os.path.join(self._dir, name)
        for old in glob.glob(os.path.join(self._dir, "click_*.wav")):
            if old != path:
                try:
                    os.remove(old)
                except OSError:
                    pass
        if not os.path.exists(path):
            write_wav(path, render_click_track(self.bpm, bars, self.subdivide, self.gaps), TRACK_RATE)
        self._length = bars * BEATS_PER_BAR * 60.0 / self.bpm
        sound = SoundLoader.load(path)
        if sound is not None:
            sound.loop = True
            sound.play()
            self._sound = sound
        self._started = time.monotonic()

    def _silence(self) -> None:
        sound, self._sound = self._sound, None
        if sound is not None:
            try:
                sound.stop()
                sound.unload()
            except Exception:
                pass

    def _tick(self, _dt) -> None:
        state = self.beat_state()
        for widget in list(self._each_watcher()):
            widget.tick(state)
