"""A short daily routine for days when you are not following a lesson plan."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoutineItem:
    id: str
    title: str
    text: str
    minutes: int


PRACTICE_INTRO = "A rhythm for today, a tempo ladder, and a short routine for days without a lesson plan."

ROUTINE_TITLE = "Daily routine"
ROUTINE_INTRO = "About half an hour. The list clears itself each morning."

RHYTHM_TITLE = "Rhythm of the day"
RHYTHM_INTRO = ("Clap it with the metronome, then play it on an open string. It changes every "
                "day and only uses rhythms from lessons you have reached. Hear it uses the tempo "
                "set on the Metro tab.")

LADDER_TITLE = "Tempo ladder"
LADDER_INTRO = ("Pick what you are working on and play it with the metronome. After two clean "
                "runs in a row, raise the tempo by 4 and go again. Save the fastest tempo you "
                "can play cleanly, and try to beat it next time. The metronome keeps running "
                "while you are on this tab.")

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
    RoutineItem("timing", "Timing",
                "Clap the rhythm of the day with the metronome, then play it on an open string.", 3),
    RoutineItem("scale", "Scale",
                "D major, one octave, with the metronome at 60. Listen to every note.", 5),
    RoutineItem("piece", "Your piece",
                "A few bars at a time, slowly. Play it at full speed only when the slow version is clean.", 10),
    RoutineItem("listen", "Listen back",
                "Record a short clip and listen for tone and tuning.", 2),
)
