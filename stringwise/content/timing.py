"""The weekly timing lesson: ten minutes a day with the metronome."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimingStudy:
    week: int
    title: str
    tempos: tuple[int, ...]      # metronome settings to use, slowest first
    body: tuple[str, ...]
    steps: tuple[str, ...]
    plan_text: str               # the line shown in the daily practice plan
    rhythm: str | None = None    # id in music/rhythms.py
    subdivide: bool = False      # click the eighth notes too
    gaps: bool = False           # two bars of click, two bars of silence


TIMING_INTRO = "Ten minutes a day with the metronome."

TIMING: dict[int, TimingStudy] = {s.week: s for s in (
    TimingStudy(
        1, "Clap the beat", (60,), rhythm="w1",
        body=(
            "A metronome clicks at a steady speed. The number is how many clicks it makes in a "
            "minute, so 60 is one click a second. Each click is one beat, and the louder click "
            "marks beat 1 of every bar.",
            "This week you clap. Put the violin down, start the metronome and count \"1, 2, 3, "
            "4\" aloud with the clicks. When your clap lands exactly on a click, the click "
            "seems to vanish. That is what being in time sounds like.",
        ),
        steps=(
            "Count aloud with the clicks for four bars before you clap anything.",
            "Clap the rhythm below. A half note is one clap held for two clicks.",
            "Tap Hear it if you are unsure how it goes.",
        ),
        plan_text="Metronome at 60. Count aloud, then clap this week's rhythm until your claps hide the clicks.",
    ),
    TimingStudy(
        2, "Long bows in time", (60,), rhythm="w2",
        body=(
            "Now the bow has to obey the click. A whole note lasts four clicks, so one bow "
            "stroke has to last all four: start at the frog on click 1 and arrive at the tip "
            "just as the next click 1 comes round.",
            "Running out of bow early means you moved too fast at the start. Aim to pass the "
            "middle of the bow on click 3.",
        ),
        steps=(
            "Open A string. One whole bow for four clicks, down then up.",
            "For the half notes, use the whole bow in two clicks. The bow moves twice as fast.",
            "Count aloud while you play.",
        ),
        plan_text="Metronome at 60. Whole bows that last exactly four clicks, then half notes in two.",
    ),
    TimingStudy(
        3, "Quarter notes on the click", (60,), rhythm="w3",
        body=(
            "A quarter note is one click. The bow changes direction exactly on each click, "
            "with no pause before it and no rush into it.",
            "New fingers tend to arrive late. Once the rhythm is steady on the open string, "
            "play it again with finger 1 down and keep the bow changes just as exact.",
        ),
        steps=(
            "Clap it first, counting aloud.",
            "Play it on the open A, using the middle of the bow for quarter notes.",
            "Play it again on B, with finger 1 down.",
        ),
        plan_text="Metronome at 60. Clap this week's rhythm, then play it on open A and on finger 1.",
    ),
    TimingStudy(
        4, "Mixing long and short", (60, 66), rhythm="w4",
        body=(
            "Most tunes mix note lengths, and the usual mistake is to cut the long notes "
            "short. A half note is not finished until the second click has sounded.",
            "In the third bar the half note sits in the middle of the bar, on beats 2 and 3. "
            "Keep counting through it.",
        ),
        steps=(
            "Clap it at 60, saying \"1, 2, 3, 4\" throughout.",
            "Play it on the open A at 60.",
            "Move the metronome up to 66 and play it again. It should feel only slightly quicker.",
        ),
        plan_text="Metronome at 60, then 66. This week's rhythm, holding every half note for its full two clicks.",
    ),
    TimingStudy(
        5, "Counting the silences", (66,), rhythm="w5",
        body=(
            "A rest is a beat you count but do not play. The zigzag sign is a quarter rest, "
            "worth one click. The small block sitting on the middle line is a half rest, worth "
            "two.",
            "Stop the bow on the string for a rest and leave it there. Whisper the number of "
            "the beat so the silence has a length. Coming in early after a rest is the mistake "
            "almost everyone makes.",
        ),
        steps=(
            "Clap it, whispering the count on the rests.",
            "Play it on the open D or A.",
            "Listen for the click in each rest. You should hear it clearly, on its own.",
        ),
        plan_text="Metronome at 66. Clap and play this week's rhythm, counting through every rest.",
    ),
    TimingStudy(
        6, "Crossing strings in time", (66, 72), rhythm="w6",
        body=(
            "Changing string takes a moment, and that moment usually gets stolen from the "
            "beat, so the first note on the new string arrives late.",
            "The cure is to move early. During the second half of a note, let your elbow "
            "start travelling toward the next string, so the bow is already there when the "
            "click comes.",
        ),
        steps=(
            "Open strings only. Play the study below at 66.",
            "Watch the third bar, where the string changes on every beat.",
            "When it is steady, try 72.",
        ),
        plan_text="Metronome at 66, then 72. Open-string crossings with every note on the click.",
    ),
    TimingStudy(
        7, "Read it, clap it, play it", (72,), rhythm="w7",
        body=(
            "Musicians sort out the rhythm before the notes. From now on, treat every new "
            "piece the same way: read the rhythm, clap it with the metronome, and only then "
            "pick up the violin.",
        ),
        steps=(
            "Look at the rhythm below and count it through in your head without tapping Hear it.",
            "Clap it with the metronome at 72.",
            "Now tap Hear it to check yourself.",
            "Do the same with Old MacDonald before you play it.",
        ),
        plan_text="Metronome at 72. Read this week's rhythm, clap it, then check it with Hear it.",
    ),
    TimingStudy(
        8, "Steady at any volume", (72,), rhythm="w8",
        body=(
            "Most players speed up when they play loud and slow down when they play soft. "
            "The metronome will tell you if you do.",
            "Play the first bar forte and the second bar piano. Your bow changes speed and "
            "weight between the two bars. The beat must not change at all.",
        ),
        steps=(
            "Open A. Bar 1 loud, bar 2 soft, then the two half notes loud and the last note soft.",
            "Swap it round: start soft.",
            "Try it with London Bridge, loud phrase then soft echo, with the click running.",
        ),
        plan_text="Metronome at 72. Loud bar, soft bar, same speed. Then London Bridge with the click.",
    ),
    TimingStudy(
        9, "Two notes to a click", (60, 72), rhythm="w9", subdivide=True,
        body=(
            "Turn on Eighth notes and the metronome adds a quiet click halfway between the "
            "beats. That quiet click is the \"and\". Eighth notes land on every click, loud "
            "and quiet alike.",
            "For a dotted quarter, hold through the next loud click and play the following "
            "eighth on the quiet click after it.",
        ),
        steps=(
            "Clap the rhythm below at 60 with Eighth notes on.",
            "Play it on the open A with short bows.",
            "Turn Eighth notes off and play it again. Now you have to feel the \"and\" yourself.",
            "Try 72 once 60 is comfortable.",
        ),
        plan_text="Metronome at 60 with Eighth notes on. Clap and play this week's rhythm, then try it at 72.",
    ),
    TimingStudy(
        10, "One scale, three speeds", (60, 72, 84),
        body=(
            "Tempo is the speed of the beat. Playing the same thing at several tempos shows "
            "you how well you really know it, because the fingers have less time to think at "
            "each step up.",
            "Keep the same amount of bow for each note as the speed rises. The bow moves "
            "faster. It does not get shorter and scratchier.",
        ),
        steps=(
            "D major scale at 60, one note to a click, up and down.",
            "Again at 72, then at 84.",
            "If a tempo falls apart, go back down one step and play it twice before trying again.",
            "Save your best clean tempo on the Practice tab.",
        ),
        plan_text="D major scale with the metronome at 60, 72 and 84. Only move up after a clean run.",
    ),
    TimingStudy(
        11, "Slow first, then up to speed", (60, 80),
        body=(
            "The quickest way to learn a piece at full speed is to play it slowly and "
            "correctly many times. Practicing fast with mistakes mostly teaches you the mistakes.",
            "Use the metronome as a ladder. Start well below the speed you want and climb a "
            "few clicks at a time.",
        ),
        steps=(
            "Play your piece at 60. If that is not clean, drop to 52.",
            "After two clean runs in a row, raise the metronome by 4.",
            "Stop climbing when the hard spots start to slip. That is today's tempo.",
            "Save it on the Practice tab and try to beat it tomorrow.",
        ),
        plan_text="Your piece with the metronome at 60. Two clean runs, then raise it by 4 and repeat.",
    ),
    TimingStudy(
        12, "Keeping the beat on your own", (72, 80), gaps=True,
        body=(
            "The aim of all this is a steady beat inside your own head, with no machine. Turn "
            "on Drop-out bars and the metronome clicks for two bars, then stays silent for two.",
            "Keep playing through the silence. When the click returns, you find out at once "
            "whether you rushed, dragged or stayed with it.",
        ),
        steps=(
            "Open A, quarter notes, at 72 with Drop-out bars on.",
            "If you arrive before the click comes back, you rushed. After it, you dragged.",
            "Then play the D major scale the same way, and then your piece.",
            "Try 80. Quicker tempos are easier to hold, and slow ones are the real test.",
        ),
        plan_text="Metronome at 72 with Drop-out bars on. Keep playing through the silent bars and land with the click.",
    ),
)}
