"""The first-launch tour: one step per stop, in order.

``target`` names the part of the app to highlight (see ui/tour.py), ``screen``
is the screen to show first and ``tab`` is the bottom tab to point at.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TourStep:
    title: str
    text: str
    target: str | None = None
    screen: str | None = None
    tab: str | None = None


STEPS: tuple[TourStep, ...] = (
    TourStep(
        "Welcome to StringWise",
        "A quick look around before you start. It takes about a minute, and you can skip it "
        "at any time.",
    ),
    TourStep(
        "Tune before you play",
        "Press Start listening and play one open string. The needle shows whether it is flat "
        "or sharp, and turns green when it is in tune. Tap G, D, A or E to hear each string.",
        target="tuner_dial", screen="tuner", tab="tuner",
    ),
    TourStep(
        "Keep a steady beat",
        "Set the tempo and start the click. It keeps going while you move around the rest "
        "of the app.",
        target="metronome", screen="metronome", tab="metronome",
    ),
    TourStep(
        "Pause it from anywhere",
        "Once the metronome is running, this Pause button and the four beat dots stay at the "
        "top of every screen. Pause stops the click and Resume picks it up at the same tempo.",
        target="header_metronome",
    ),
    TourStep(
        "Twelve weekly lessons",
        "One lesson a week, planned for about an hour a day. Each week has a practice plan "
        "to tick off, sheet music to play along with, and a timing lesson where the app can "
        "record you and check every note.",
        target="week_chips", screen="lessons", tab="lessons",
    ),
    TourStep(
        "See where each finger goes",
        "Tap a dot to hear its note. Further down, pick a string and a finger, play it, and "
        "the app tells you whether your finger is in the right place.",
        target="fingerboard", screen="fingers", tab="fingers",
    ),
    TourStep(
        "Theory when you need it",
        "Reading music, rhythm, bowing words and how the violin is tuned, in short sections "
        "you can open one at a time.",
        target="theory", screen="theory", tab="theory",
    ),
    TourStep(
        "A little practice every day",
        "A new rhythm to clap and play each day, a tempo ladder that saves your best speed "
        "for each piece, and a short daily routine.",
        target="rhythm", screen="practice", tab="practice",
    ),
    TourStep(
        "Settings and help",
        "Change the tuning pitch, send feedback, share the app, or watch this tour again.",
        target="gear",
    ),
    TourStep(
        "You're ready",
        "Start with week 1 on the Lessons tab. It covers how to hold the violin and the bow.",
    ),
)

SKIP = "Skip tour"
NEXT = "Next"
FIRST = "Show me around"
LAST = "Start week 1"
