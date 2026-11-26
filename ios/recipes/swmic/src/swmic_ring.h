/*
 * Single-producer, single-consumer ring buffer of float samples.
 * The audio thread pushes, the Python thread pops; neither ever waits.
 * Plain C so it can be tested off the phone (see tests/test_ios.py).
 */
#ifndef SWMIC_RING_H
#define SWMIC_RING_H

#include <stdatomic.h>

#define RING_SIZE (1 << 17)          /* about 3 seconds at 44.1 kHz */
#define RING_MASK (RING_SIZE - 1)

static float ring[RING_SIZE];
static atomic_uint ring_write = 0;
static atomic_uint ring_read = 0;
static atomic_int ring_dropped = 0;

static inline void ring_reset(void) {
    atomic_store(&ring_read, 0);
    atomic_store(&ring_write, 0);
    atomic_store(&ring_dropped, 0);
}

/* Audio thread. If the reader has fallen behind, the newest samples are dropped. */
static inline void ring_push(const float *samples, unsigned int count) {
    unsigned int w = atomic_load_explicit(&ring_write, memory_order_relaxed);
    unsigned int r = atomic_load_explicit(&ring_read, memory_order_acquire);
    unsigned int space = RING_SIZE - (w - r);
    if (count > space) {
        atomic_fetch_add(&ring_dropped, (int)(count - space));
        count = space;
    }
    for (unsigned int i = 0; i < count; i++) {
        ring[(w + i) & RING_MASK] = samples[i];
    }
    atomic_store_explicit(&ring_write, w + count, memory_order_release);
}

/* Reader thread. Returns how many samples were copied into out. */
static inline int ring_pop(float *out, int max_count) {
    unsigned int r = atomic_load_explicit(&ring_read, memory_order_relaxed);
    unsigned int w = atomic_load_explicit(&ring_write, memory_order_acquire);
    unsigned int available = w - r;
    unsigned int count = available < (unsigned int)max_count ? available : (unsigned int)max_count;
    for (unsigned int i = 0; i < count; i++) {
        out[i] = ring[(r + i) & RING_MASK];
    }
    atomic_store_explicit(&ring_read, r + count, memory_order_release);
    return (int)count;
}

#endif
