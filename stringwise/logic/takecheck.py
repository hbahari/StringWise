"""Checks a recorded take: which notes were played, how in tune, and how well in time.

The recording is made while the app's click plays through the speaker, so the
microphone hears the click and the violin together. Because the exact sound of
the click is known, it can be found in the recording even under the violin,
and that gives the true position of every beat with no guessing about audio
delays. If the click cannot be heard (headphones, a covered speaker), timing is
judged against the steadiest beat that fits the player's own notes instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..audio.metronome import BEATS_PER_BAR, _click
from ..audio.pitch import FRAME_SIZE, MIC_GAIN, WINDOW, detect_pitch
from ..music.notes import Note, cents_between, nearest_note, pretty

HOP_SECONDS = 0.010
MIN_NOTE_SECONDS = 0.07
SPLIT_CENTS = 70          # a jump this big between frames starts a new note
IN_TUNE_CENTS = 30
SAME_NOTE_CENTS = 60      # beyond this the player hit a different note
CLICK_CONFIDENCE = 5.0    # how far the click pattern must stand out to be trusted


# ---------------------------------------------------------------- note finding
@dataclass
class PlayedNote:
    start: float      # seconds from the start of the recording
    end: float
    freq: float


def find_notes(samples: np.ndarray, sample_rate: int) -> list[PlayedNote]:
    """Split a recording into the notes that were played."""
    hop = int(sample_rate * HOP_SECONDS)
    boosted = np.asarray(samples, dtype=np.float32) * MIC_GAIN
    # A reading describes the newest WINDOW-and-a-bit samples of its frame, so the
    # sound it reports began roughly this long before the frame ended.
    lookback = (WINDOW * 0.72) / sample_rate

    notes: list[PlayedNote] = []
    current: list[tuple[float, float, float]] = []      # (time, freq, rms)
    silent = 0
    strays = 0

    def close():
        nonlocal current
        if current and current[-1][0] - current[0][0] >= MIN_NOTE_SECONDS:
            freqs = [f for _, f, _ in current]
            notes.append(PlayedNote(current[0][0], current[-1][0] + HOP_SECONDS, float(np.median(freqs))))
        current = []

    for end in range(FRAME_SIZE, len(boosted) + 1, hop):
        freq, rms, _ = detect_pitch(boosted[end - FRAME_SIZE:end], sample_rate)
        when = end / sample_rate - lookback
        if freq is None or not 150 < freq < 1600:
            silent += 1
            if silent >= 3:
                close()
            continue
        silent = 0
        if not current:
            current, strays = [(when, freq, rms)], 0
            continue
        centre = float(np.median([f for _, f, _ in current[-8:]]))
        level = float(np.median([r for _, _, r in current]))
        peak = max(r for _, _, r in current[-12:])
        if abs(cents_between(freq, centre)) > SPLIT_CENTS:
            strays += 1
            if strays >= 2:                      # a real change of note, not a blip
                stray_time = when - HOP_SECONDS
                close()
                current, strays = [(stray_time, freq, rms), (when, freq, rms)], 0
            continue
        strays = 0
        # Same pitch again after a clear dip in loudness: a new bow stroke.
        dipped = min(r for _, _, r in current[-6:]) < 0.45 * level
        if dipped and rms > 0.8 * level and len(current) > 8 and current[-1][2] < rms and peak > 0:
            recent_low = int(np.argmin([r for _, _, r in current[-6:]]))
            split_at = len(current) - 6 + recent_low
            tail = current[split_at:]
            current = current[:split_at]
            close()
            current = tail + [(when, freq, rms)]
            continue
        current.append((when, freq, rms))
    close()
    return notes


# ---------------------------------------------------------------- click finding
def _template(kind: str, sample_rate: int, track_rate: int) -> np.ndarray:
    """The click as it sounds after the player resamples it to the recording rate."""
    click = _click(track_rate, kind)
    positions = np.arange(int(len(click) * sample_rate / track_rate)) * track_rate / sample_rate
    shaped = np.interp(positions, np.arange(len(click)), click)
    shaped = shaped[:int(sample_rate * 0.012)]            # the loud start carries the timing
    return shaped / np.sqrt(np.sum(shaped ** 2))


def find_click_grid(samples: np.ndarray, sample_rate: int, bpm: float, beats: int,
                    track_rate: int, search_seconds: float = 1.5) -> tuple[float | None, float]:
    """Find when beat 1 of the click track happens in the recording.

    Returns (time of the first click in seconds, confidence). The time is None
    when the clicks do not stand out clearly enough to trust.
    """
    x = np.asarray(samples, dtype=np.float64)
    x = np.diff(x, prepend=x[:1])                         # tilt toward the click's bright end
    beat = 60.0 / bpm * sample_rate
    search = int(search_seconds * sample_rate)
    envelopes = {}
    for kind in ("accent", "beat"):
        template = _template(kind, sample_rate, track_rate)
        template = np.diff(template, prepend=template[:1])
        envelopes[kind] = np.abs(np.correlate(x, template, mode="valid"))
    usable = min(len(e) for e in envelopes.values())
    score = np.zeros(search)
    counted = 0
    for k in range(beats):
        offset = int(round(k * beat))
        if offset + search > usable:
            break
        kind = "accent" if k % BEATS_PER_BAR == 0 else "beat"
        score += envelopes[kind][offset:offset + search]
        counted += 1
    if counted < 4:
        return None, 0.0
    best = int(np.argmax(score))
    floor = float(np.median(score)) + 1e-12
    confidence = float(score[best] / floor)
    if confidence < CLICK_CONFIDENCE:
        return None, confidence
    return best / sample_rate, confidence


# ---------------------------------------------------------------- matching
@dataclass
class NoteResult:
    index: int                    # position in the written piece
    note: Note
    played: PlayedNote | None = None
    cents: float | None = None
    offset: float | None = None   # seconds; negative is early
    pitch: str = "missed"         # "right", "sharp", "flat", "wrong", "missed"
    timing: str = "missed"        # "on_time", "early", "late", "missed"

    @property
    def heard_name(self) -> str:
        if self.played is None:
            return ""
        heard = nearest_note(self.played.freq)
        return f"{pretty(heard.name)}{heard.octave}"


@dataclass
class TakeReport:
    results: list[NoteResult] = field(default_factory=list)
    heard_click: bool = False
    extra_notes: int = 0
    bpm: float = 0.0
    played_bpm: float | None = None
    headline: str = ""
    lines: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    def count(self, **wanted) -> int:
        return sum(all(getattr(r, k) == v for k, v in wanted.items()) for r in self.results)


def _align(expected, played, grid_start, beat_seconds, time_weight):
    """Pair written notes with played notes in order, allowing misses and extras."""
    n, m = len(expected), len(played)
    miss, extra = 1.6, 1.0
    cost = np.full((n + 1, m + 1), np.inf)
    step = np.zeros((n + 1, m + 1), dtype=np.int8)
    cost[0, 0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            base = cost[i, j]
            if not np.isfinite(base):
                continue
            if i < n and base + miss < cost[i + 1, j]:
                cost[i + 1, j], step[i + 1, j] = base + miss, 1
            if j < m and base + extra < cost[i, j + 1]:
                cost[i, j + 1], step[i, j + 1] = base + extra, 2
            if i < n and j < m:
                _, note, when = expected[i]
                pitch = min(abs(cents_between(played[j].freq, note.freq)) / 100.0, 3.0)
                timing = 0.0
                if time_weight:
                    timing = min(abs(played[j].start - (grid_start + when)) / beat_seconds, 2.0)
                total = base + 0.6 * pitch + time_weight * timing
                if total < cost[i + 1, j + 1]:
                    cost[i + 1, j + 1], step[i + 1, j + 1] = total, 3
    pairs, i, j = {}, n, m
    while i > 0 or j > 0:
        move = step[i, j]
        if move == 3:
            pairs[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif move == 1:
            i -= 1
        else:
            j -= 1
    return pairs


def analyse(samples: np.ndarray, sample_rate: int, notes, bpm: float,
            track_rate: int, count_in_beats: int = BEATS_PER_BAR) -> TakeReport:
    """Compare a recording with the written ``notes`` played at ``bpm`` after a count-in."""
    beat = 60.0 / bpm
    expected, position = [], float(count_in_beats)
    for index, note in enumerate(notes):
        if not note.is_rest:
            expected.append((index, note, position * beat))
        position += note.beats
    total_beats = int(np.ceil(position))

    played = find_notes(samples, sample_rate)
    grid_start, _confidence = find_click_grid(samples, sample_rate, bpm, total_beats, track_rate)
    report = TakeReport(heard_click=grid_start is not None, bpm=bpm)

    if grid_start is not None:
        pairs = _align(expected, played, grid_start, beat, time_weight=1.0)
    else:
        pairs = _align(expected, played, 0.0, beat, time_weight=0.0)
        gaps = [played[j].start - expected[i][2] for i, j in pairs.items()]
        if gaps:
            # No click to go by: use the steady beat that best fits the player's own notes.
            grid_start = float(np.median(gaps))
            pairs = _align(expected, played, grid_start, beat, time_weight=1.0)

    tolerance = min(0.11, max(0.07, 0.10 * beat))
    for i, (index, note, when) in enumerate(expected):
        result = NoteResult(index, note)
        if i in pairs:
            heard = played[pairs[i]]
            result.played = heard
            result.cents = cents_between(heard.freq, note.freq)
            result.offset = heard.start - (grid_start + when)
            off = abs(result.cents)
            result.pitch = ("right" if off <= IN_TUNE_CENTS else
                            ("sharp" if result.cents > 0 else "flat") if off <= SAME_NOTE_CENTS else "wrong")
            result.timing = ("on_time" if abs(result.offset) <= tolerance else
                             "early" if result.offset < 0 else "late")
        report.results.append(result)
    report.extra_notes = len(played) - len(pairs)

    matched = [r for r in report.results if r.played is not None]
    if len(matched) >= 4:
        written = np.array([expected_time for (_, _, expected_time), r in zip(expected, report.results)
                            if r.played is not None])
        actual = np.array([r.played.start for r in matched])
        if np.ptp(written) > 0:
            slope = float(np.polyfit(written, actual, 1)[0])
            if 0.5 < slope < 2.0:
                report.played_bpm = bpm / slope
    _describe(report)
    return report


def _describe(report: TakeReport) -> None:
    total = report.total
    matched = [r for r in report.results if r.played is not None]
    if not matched:
        report.headline = "I couldn't hear any notes."
        report.lines = ["Move the phone closer, check the microphone is not covered, and try again."]
        return
    right_note = sum(r.pitch in ("right", "sharp", "flat") for r in report.results)
    in_tune = report.count(pitch="right")
    on_time = report.count(timing="on_time")
    early, late = report.count(timing="early"), report.count(timing="late")
    missed = total - len(matched)

    if right_note == total and in_tune == total and on_time == total:
        report.headline = "A clean take. Every note right, in tune and on the beat."
    elif right_note >= 0.8 * total and on_time >= 0.7 * total:
        report.headline = "A good take, with a few things to tidy."
    else:
        report.headline = "A useful take. Here is what to work on."

    lines = [f"Notes: {right_note} of {total} were the right note, and {in_tune} of those were in tune."]
    wrong = [r for r in report.results if r.pitch == "wrong"]
    if wrong:
        first = wrong[0]
        lines.append(f"Note {first.index + 1} should be {first.note.label}, but I heard {first.heard_name}.")
    sharp, flat = report.count(pitch="sharp"), report.count(pitch="flat")
    if sharp or flat:
        lines.append(f"Tuning: {sharp} a little sharp and {flat} a little flat. Check those fingers on the Fingers tab.")
    lines.append(f"Timing: {on_time} of {total} landed on the beat, {early} early and {late} late.")
    offsets = [r.offset for r in matched]
    typical = float(np.median(offsets)) * 1000        # the median ignores one or two stray notes
    if abs(typical) >= 40:
        lines.append(f"Most of your notes were about {abs(typical):.0f} milliseconds "
                     f"{'ahead of' if typical < 0 else 'behind'} the beat.")
    if report.played_bpm is not None:
        drift = report.played_bpm / report.bpm - 1
        if drift > 0.03:
            lines.append(f"You sped up: about {report.played_bpm:.0f} beats a minute against the click's {report.bpm:.0f}.")
        elif drift < -0.03:
            lines.append(f"You slowed down: about {report.played_bpm:.0f} beats a minute against the click's {report.bpm:.0f}.")
    if missed:
        lines.append(f"{missed} written {'note was' if missed == 1 else 'notes were'} not heard.")
    if report.extra_notes > 0:
        lines.append(f"{report.extra_notes} extra {'note' if report.extra_notes == 1 else 'notes'} that are not in the music.")
    if not report.heard_click:
        lines.append("I couldn't hear the click in the recording, so timing is measured against your own "
                     "steady beat. Play with the phone's speaker uncovered for a stricter check.")
    report.lines = lines
