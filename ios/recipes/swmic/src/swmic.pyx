# cython: language_level=3
"""Python side of the StringWise iOS microphone. See swmic_ios.m."""

cdef extern from "swmic_ios.h":
    int swmic_configure_session()
    int swmic_permission()
    void swmic_request_permission()
    int swmic_start(double sample_rate)
    void swmic_stop()
    int swmic_read(float *out, int max_count) nogil
    double swmic_hardware_rate()
    int swmic_dropped()

_STATES = ("unknown", "granted", "denied")


def configure_session():
    """Set the shared audio session to play and record. True when it worked."""
    return swmic_configure_session() == 0


def permission():
    """"unknown" before the user has answered, then "granted" or "denied"."""
    state = swmic_permission()
    return _STATES[state] if 0 <= state < 3 else "unknown"


def request_permission():
    """Show the system dialog. Poll permission() for the answer."""
    swmic_request_permission()


def start(double sample_rate=44100.0):
    """Start recording. Returns 0, or a negative code saying which step failed."""
    return swmic_start(sample_rate)


def stop():
    swmic_stop()


def read(int max_count):
    """Up to max_count new samples as float32 bytes (may be empty)."""
    cdef bytearray buffer = bytearray(max_count * 4)
    cdef char *data = buffer
    cdef int got
    with nogil:
        got = swmic_read(<float *>data, max_count)
    return bytes(buffer[:got * 4])


def hardware_rate():
    return swmic_hardware_rate()


def dropped():
    """Samples lost because Python read too slowly."""
    return swmic_dropped()
