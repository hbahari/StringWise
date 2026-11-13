"""Background microphone reader that turns audio into a stream of pitch readings."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass

import numpy as np

from . import mic as mic_module
from .pitch import FRAME_SIZE, MIC_GAIN, detect_pitch

HOP = 1024    # new samples per reading: about 43 readings a second at 44.1 kHz


@dataclass(frozen=True)
class Frame:
    freq: float | None    # None when there is no clear pitch
    rms: float


class PitchListener:
    """Reads the microphone on its own thread and queues one Frame per hop.

    The UI drains the queue with ``poll()`` from the main thread, so no Kivy
    object is ever touched from the audio thread.
    """

    frame_rate = mic_module.SAMPLE_RATE / HOP

    def __init__(self, mic_factory=mic_module.open_default_mic) -> None:
        self._mic_factory = mic_factory
        self._mic = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._frames: deque[Frame] = deque(maxlen=256)
        self.error: str | None = None
        self._record = False
        self._chunks: list[np.ndarray] = []

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, record: bool = False) -> None:
        """Open the microphone and begin listening. Raises MicError on failure.

        With ``record`` the raw audio is also kept, for ``take_recording``.
        """
        if self.running:
            return
        self.error = None
        self._record = record
        self._chunks = []
        self._frames.clear()
        mic = self._mic_factory()
        mic.open()
        self._mic = mic
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="pitch-listener", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        mic, self._mic = self._mic, None
        if mic is not None:
            try:
                mic.close()
            except Exception:
                pass
        self._frames.clear()

    def take_recording(self) -> np.ndarray:
        """Everything recorded since ``start(record=True)``. Call after ``stop``."""
        chunks, self._chunks = self._chunks, []
        return np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)

    def poll(self) -> list[Frame]:
        frames = []
        while True:
            try:
                frames.append(self._frames.popleft())
            except IndexError:
                return frames

    def _run(self) -> None:
        ring = np.zeros(FRAME_SIZE, dtype=np.float32)
        pending = 0
        mic = self._mic
        try:
            while not self._stop.is_set():
                chunk = mic.read(HOP)
                if len(chunk) == 0:
                    continue
                if self._record:
                    self._chunks.append(np.array(chunk, dtype=np.float32))
                chunk = chunk[-FRAME_SIZE:] * MIC_GAIN
                ring = np.concatenate((ring[len(chunk):], chunk))
                pending += len(chunk)
                if pending < HOP:
                    continue
                pending = 0
                freq, rms, _clarity = detect_pitch(ring, mic_module.SAMPLE_RATE)
                self._frames.append(Frame(freq, rms))
        except mic_module.MicError as exc:
            self.error = str(exc)
        except Exception as exc:  # keep the app alive whatever the audio stack does
            self.error = f"Microphone error: {exc}"
        finally:
            _detach_from_jvm()


def _detach_from_jvm() -> None:
    """On Android a thread that has called into Java must detach before it ends."""
    try:
        from kivy.utils import platform
        if platform == "android":
            import jnius
            jnius.detach()
    except Exception:
        pass
