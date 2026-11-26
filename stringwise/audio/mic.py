"""Microphone input.

Android uses the platform AudioRecord class through pyjnius. iOS uses our small
``swmic`` module (ios/recipes/swmic), built into the app by kivy-ios. On a desktop
the optional ``sounddevice`` package is used so the app can be run and tested
without a phone. Every backend hands back mono float32 samples in -1..1.
"""

from __future__ import annotations

import os
import time

import numpy as np

SAMPLE_RATE = 44100


class MicError(Exception):
    """Raised with a message that is safe to show to the user."""


class AndroidMic:
    def __init__(self) -> None:
        self._record = None
        self._buffer: list[int] = []

    def open(self) -> None:
        try:
            from jnius import autoclass
        except Exception as exc:  # pragma: no cover - only on a broken build
            raise MicError("The audio bridge did not load. Reinstall the app.") from exc

        AudioRecord = autoclass("android.media.AudioRecord")
        AudioFormat = autoclass("android.media.AudioFormat")
        channel = AudioFormat.CHANNEL_IN_MONO
        encoding = AudioFormat.ENCODING_PCM_16BIT
        minimum = AudioRecord.getMinBufferSize(SAMPLE_RATE, channel, encoding)
        if minimum <= 0:
            raise MicError("This device does not offer a 44.1 kHz microphone input.")
        size = max(minimum, 8192)

        # VOICE_RECOGNITION (6) asks the phone to skip automatic gain and noise
        # suppression, which would otherwise smear the pitch. MIC (1) is the fallback.
        last_error = None
        for source in (6, 1):
            try:
                record = AudioRecord(source, SAMPLE_RATE, channel, encoding, size)
                if record.getState() == AudioRecord.STATE_INITIALIZED:
                    record.startRecording()
                    self._record = record
                    return
                record.release()
            except Exception as exc:
                last_error = exc
        raise MicError("Could not open the microphone. Another app may be using it.") from last_error

    def read(self, count: int) -> np.ndarray:
        if len(self._buffer) != count:
            self._buffer = [0] * count
        got = self._record.read(self._buffer, 0, count)
        if got is None or got < 0:
            raise MicError("The microphone stopped responding.")
        if got == 0:
            time.sleep(0.005)
        return np.asarray(self._buffer[:got], dtype=np.float32) / 32768.0

    def close(self) -> None:
        record, self._record = self._record, None
        if record is not None:
            try:
                record.stop()
            finally:
                record.release()


class IosMic:
    """Reads from swmic, which records on iOS's audio thread into a ring buffer."""

    #: how long read() waits for the first samples before giving up
    timeout = 2.0

    def __init__(self, module=None) -> None:
        self._module = module
        self._open = False

    def open(self) -> None:
        if self._module is None:
            try:
                import swmic
            except Exception as exc:  # pragma: no cover - only on a broken build
                raise MicError("Microphone support is missing from this build.") from exc
            self._module = swmic
        if self._module.permission() == "denied":
            raise MicError("Microphone access is off. Allow it for StringWise in your phone's "
                           "Settings, under Apps, then try again.")
        code = self._module.start(float(SAMPLE_RATE))
        if code != 0:
            raise MicError(f"Could not open the microphone (code {code}). "
                           "Another app may be using it.")
        self._open = True

    def read(self, count: int) -> np.ndarray:
        waited = 0.0
        while self._open:
            data = self._module.read(count)
            if data:
                return np.frombuffer(data, dtype=np.float32).copy()
            if waited >= self.timeout:
                raise MicError("The microphone stopped responding.")
            time.sleep(0.005)
            waited += 0.005
        return np.zeros(0, dtype=np.float32)

    def close(self) -> None:
        if self._open:
            self._open = False
            self._module.stop()


class DesktopMic:
    def __init__(self) -> None:
        self._stream = None

    def open(self) -> None:
        try:
            import sounddevice
        except Exception as exc:
            raise MicError(
                "No microphone backend on this computer. Install it with: pip install sounddevice"
            ) from exc
        try:
            self._stream = sounddevice.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            self._stream.start()
        except Exception as exc:
            raise MicError("Could not open the microphone.") from exc

    def read(self, count: int) -> np.ndarray:
        data, _overflowed = self._stream.read(count)
        return data[:, 0]

    def close(self) -> None:
        stream, self._stream = self._stream, None
        if stream is not None:
            stream.stop()
            stream.close()


class SyntheticMic:
    """A fake microphone that 'plays' a list of frequencies, one per second.

    Used by the tests and for demos: set STRINGWISE_FAKE_MIC="440,494,554".
    A frequency of 0 gives a second of silence.
    """

    def __init__(self, freqs: list[float], seconds_each: float = 1.0, realtime: bool = True) -> None:
        self._freqs = freqs
        self._seconds_each = seconds_each
        self._realtime = realtime
        self._position = 0

    def open(self) -> None:
        self._position = 0

    def read(self, count: int) -> np.ndarray:
        if self._realtime:
            time.sleep(count / SAMPLE_RATE)
        t = (self._position + np.arange(count)) / SAMPLE_RATE
        index = int(self._position / SAMPLE_RATE / self._seconds_each) % len(self._freqs)
        freq = self._freqs[index]
        self._position += count
        if freq <= 0:
            return np.zeros(count, dtype=np.float32)
        # A few harmonics and a short fade-in, roughly like a bowed string.
        local = t % self._seconds_each
        wave = sum(np.sin(2 * np.pi * freq * k * t) / k for k in (1, 2, 3, 4))
        envelope = np.minimum(1.0, local / 0.03) * np.minimum(1.0, (self._seconds_each - local) / 0.08)
        return (0.05 * wave * envelope).astype(np.float32)

    def close(self) -> None:
        pass


def open_default_mic():
    """Pick the right backend for where the app is running."""
    fake = os.environ.get("STRINGWISE_FAKE_MIC")
    if fake:
        return SyntheticMic([float(f) for f in fake.split(",")])
    try:
        from kivy.utils import platform
    except Exception:  # pragma: no cover
        platform = "unknown"
    if platform == "android":
        return AndroidMic()
    if platform == "ios":
        return IosMic()
    return DesktopMic()
