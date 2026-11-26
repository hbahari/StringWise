/* A stand-in for swmic_ios.m so the ring buffer and the Cython wrapper can be
   tested on Linux. "start(n)" pretends the microphone delivered n more samples,
   each equal to its position in the stream, so order and gaps are easy to check. */
#include "swmic_ios.h"
#include "swmic_ring.h"

static unsigned int counter = 0;
static int state = SWMIC_UNKNOWN;

int swmic_configure_session(void) { return 0; }
int swmic_permission(void) { return state; }
void swmic_request_permission(void) { state = SWMIC_GRANTED; }

int swmic_start(double samples) {
    float chunk[512];
    unsigned int left = (unsigned int)samples;
    while (left > 0) {
        unsigned int n = left < 512 ? left : 512;
        for (unsigned int i = 0; i < n; i++) chunk[i] = (float)(counter + i);
        counter += n;
        ring_push(chunk, n);
        left -= n;
    }
    return 0;
}

void swmic_stop(void) { ring_reset(); counter = 0; }
int swmic_read(float *out, int max_count) { return ring_pop(out, max_count); }
double swmic_hardware_rate(void) { return 48000.0; }
int swmic_dropped(void) { return atomic_load(&ring_dropped); }
