"""Where things go on a line of sheet music. Pure arithmetic, no drawing.

All distances are in staff units; the widget multiplies them by its scale.
One staff space (line to line) is 12 units.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..music.fingering import fingering_for
from ..music.notes import Note
from ..music.pieces import BEATS_PER_BAR

HALF_SPACE = 6
BASE_Y = 44              # height of the bottom staff line (E4) above the widget's bottom edge
HEIGHT = 140
FINGER_ROW_Y = BASE_Y + 8 * HALF_SPACE + 31
CLEF_X = 14
TIME_X = 62
FIRST_NOTE_X = 98
STEM = 36
ADVANCE = {0.5: 32, 1.0: 42, 1.5: 52, 2.0: 56, 3.0: 66, 4.0: 76}


def y_for_step(step: float) -> float:
    return BASE_Y + step * HALF_SPACE


@dataclass
class StaffLayout:
    xs: list[float] = field(default_factory=list)          # centre of each note head
    stems_up: list[bool] = field(default_factory=list)
    barlines: list[float] = field(default_factory=list)
    beams: list[tuple[int, int]] = field(default_factory=list)   # pairs of eighth notes
    flags: set[int] = field(default_factory=set)            # lone eighth notes
    fingers: list[int | None] = field(default_factory=list)
    end_x: float = 0.0
    width: float = 0.0


def layout(notes: list[Note] | tuple[Note, ...]) -> StaffLayout:
    result = StaffLayout()
    x = FIRST_NOTE_X
    beat = 0.0
    beamed_with_previous = False
    for i, note in enumerate(notes):
        result.xs.append(x)
        result.stems_up.append(note.staff_step < 4)
        fingering = fingering_for(note)
        result.fingers.append(fingering[1] if fingering else None)

        if note.beats == 0.5:
            following = notes[i + 1] if i + 1 < len(notes) else None
            on_the_beat = abs(beat - round(beat)) < 1e-9
            if beamed_with_previous:
                beamed_with_previous = False
            elif on_the_beat and following is not None and following.beats == 0.5:
                result.beams.append((i, i + 1))
                up = (note.staff_step + following.staff_step) / 2 < 4
                result.stems_up[i] = up
                beamed_with_previous = True
            else:
                result.flags.add(i)
        if i > 0 and result.beams and result.beams[-1][1] == i:
            result.stems_up[i] = result.stems_up[i - 1]

        advance = ADVANCE[note.beats]
        beat += note.beats
        last = i == len(notes) - 1
        if beat >= BEATS_PER_BAR - 1e-9:
            beat = 0.0
            bar_x = x + advance * 0.62 + 4
            if last:
                result.end_x = bar_x + 4
            else:
                result.barlines.append(bar_x)
                x = bar_x + 22
        else:
            x += advance
            if last:
                result.end_x = x
    result.width = result.end_x + 14
    return result
