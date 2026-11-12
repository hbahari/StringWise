"""A short daily routine for days when you are not following a lesson plan."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoutineItem:
    id: str
    title: str
    text: str
    minutes: int


PRACTICE_INTRO = ("A half-hour routine for days when you are not following a lesson plan. "
                  "The list clears itself each morning.")

ROUTINE: tuple[RoutineItem, ...] = (
    RoutineItem("posture", "Posture check",
                "Violin on the collarbone, jaw resting on the chinrest, shoulders down, left hand loose.", 2),
    RoutineItem("tuning", "Tune",
                "Check all four strings with the Tuner tab before you play anything else.", 3),
    RoutineItem("openbow", "Open strings",
                "Slow whole bows on G, D, A and E. Keep the bow parallel to the bridge.", 5),
    RoutineItem("fingerpattern", "Finger pattern",
                "On one string, put down fingers 1, 2, 3 and 4 in turn, then lift them one at a time. "
                "Repeat on the other strings.", 5),
    RoutineItem("scale", "Scale",
                "D major, one octave, slowly. Listen to every note.", 5),
    RoutineItem("piece", "Your piece",
                "A few bars at a time, slowly. Play it at full speed only when the slow version is clean.", 10),
    RoutineItem("listen", "Listen back",
                "Record a short clip and listen for tone and tuning.", 2),
)
