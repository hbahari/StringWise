"""The twelve-week course. One lesson a week, planned for an hour of practice a day."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .timing import TIMING, TimingStudy


@dataclass(frozen=True)
class PlanItem:
    minutes: int
    title: str
    text: str


@dataclass(frozen=True)
class Lesson:
    week: int
    title: str
    goals: tuple[str, ...]
    body: tuple[str, ...]
    plan: tuple[PlanItem, ...]
    pieces: tuple[str, ...] = ()
    timing: TimingStudy | None = None

    @property
    def total_minutes(self) -> int:
        return sum(item.minutes for item in self.plan)


def _plan(*items: tuple[int, str, str]) -> tuple[PlanItem, ...]:
    return tuple(PlanItem(*item) for item in items)


LESSONS: tuple[Lesson, ...] = (
    Lesson(
        week=1,
        title="Meeting the instrument",
        goals=(
            "Hold the violin on your collarbone without the left hand propping it up",
            "Hold the bow with a loose, curved hand",
            "Get a clear sound from each of the four open strings",
        ),
        body=(
            "Nothing this week involves reading music or pressing a string down. The job is to "
            "get comfortable holding the violin and the bow, because tension you learn now is "
            "hard to unlearn later.",
            "Rest the violin on your left collarbone and let your jaw sit on the chinrest. A "
            "shoulder rest fills the gap between the instrument and your shoulder. With it in "
            "place you should be able to take your left hand away for a moment without the "
            "violin slipping.",
            "For the bow, bend your thumb and rest its tip on the stick next to the frog, across "
            "from your middle finger. Let the other fingers hang over the stick, with the tip of "
            "your little finger curved on top. You are balancing the bow more than gripping it. "
            "If your knuckles turn white, shake your hand out and start again.",
            "Pluck the open strings first, from low to high: G, D, A, E. Plucking is called "
            "pizzicato. Once the strings are familiar, try short, slow bow strokes on the D and "
            "A strings, which are the easiest to reach.",
        ),
        plan=_plan(
            (10, "Hold check", "Bring the violin up, settle your jaw, drop your shoulders. Use a mirror if you have one."),
            (10, "Plucked open strings", "Pluck each string four times, slowly. Say its name as you go."),
            (15, "Bow hold and first strokes", "Set the bow hold with the bow in the air, then play short, slow strokes on D and A."),
            (10, "Tuner", "Open the Tuner tab and check all four strings. Get used to the sound of a string that is in tune."),
            (5, "Rest", "Put the violin down and shake out your hands and shoulders."),
        ),
    ),
    Lesson(
        week=2,
        title="Full bows and steady tone",
        pieces=("openwarmup", "crossings"),
        goals=(
            "Draw a whole bow, frog to tip, on every string",
            "Keep the sound even from one end of the bow to the other",
            "Know a down-bow from an up-bow",
        ),
        body=(
            "No new notes this week. All of the work is in the right arm.",
            "A down-bow starts at the frog and travels to the tip. An up-bow comes back. For a "
            "clean sound the bow has to stay parallel to the bridge the whole way, about halfway "
            "between the bridge and the end of the fingerboard. Near the tip the bow tends to "
            "swing back over the fingerboard, so watch yourself in a mirror or film a few "
            "strokes on your phone.",
            "If the sound crunches, you are pressing too hard for how slowly the bow is moving. "
            "If it sounds thin or whistles, let more of your arm's weight sink into the string. "
            "In both cases the fix comes from the arm. Squeezing with the fingers only makes it "
            "worse.",
        ),
        plan=_plan(
            (10, "Warm-up", "Pluck the open strings, then play a few slow bows to loosen up."),
            (15, "Whole bows", "Four slow down-bows and up-bows on each string. Count to four on each stroke."),
            (15, "String crossings", "Play Open String Crossings below. Your elbow rises for the lower strings and drops for the higher ones."),
            (5, "Tuner", "Check all four strings again. New strings drift a lot in the first weeks."),
            (5, "Listen", "One slow bow on each string. Is the sound the same at the frog, the middle and the tip?"),
        ),
    ),
    Lesson(
        week=3,
        title="The first finger pattern",
        pieces=("firstpattern", "skips"),
        goals=(
            "Place fingers 1, 2 and 3 on the A string",
            "Play each note in tune, checking with the app",
            "Keep the left hand loose between notes",
        ),
        body=(
            "The left hand starts work this week. On the A string, finger 1 (index) plays B, "
            "finger 2 (middle) plays C♯ and finger 3 (ring) plays D. The Fingers tab shows "
            "where each one lands.",
            "The spacing matters more than anything else here. There is a gap between the open "
            "string and finger 1, and another between fingers 1 and 2. Fingers 2 and 3 sit right "
            "next to each other, close enough to touch. Musicians call the wide gap a whole step "
            "and the narrow one a half step.",
            "Keep your fingers curved so that each one comes down on its tip, and let the "
            "fingers you are not using hover just above the string. When you put finger 2 down, "
            "leave finger 1 where it is. It will all feel clumsy for a few days. Go slowly and "
            "aim for the right pitch every time.",
        ),
        plan=_plan(
            (10, "Warm-up bows", "Whole bows on all four open strings."),
            (15, "Finger drill, plucked", "A string. Put finger 1 down, pluck, and check the note with the live checker on the Fingers tab. Add finger 2, then finger 3."),
            (10, "Same drill with the bow", "One slow bow for each note: open, 1, 2, 3 and back down."),
            (10, "This week's pieces", "Play First Pattern Warm-Up, then Steps and Skips."),
            (5, "Rest", "Shake out your left hand. Sore fingertips are normal this week."),
        ),
    ),
    Lesson(
        week=4,
        title="Adding the fourth finger",
        pieces=("hotcrossbuns", "ode"),
        goals=(
            "Add finger 4 on the A string",
            "Match finger 4 to the open E string",
            "Play a whole tune from start to finish",
        ),
        body=(
            "Your little finger is finger 4. On the A string it plays E, the same E as the open "
            "E string next door. That gives you a built-in test: play finger 4 on the A string, "
            "then the open E. If the two notes match, your hand is in the right place.",
            "Finger 4 is the weakest finger and it has the longest reach, a whole step past "
            "finger 3. Keep it curved. If it can't reach without the other fingers lifting, "
            "bring your left elbow a little further under the violin.",
            "There are two tunes this week. Hot Cross Buns needs only the open string and "
            "fingers 1 and 2. Ode to Joy uses all four fingers.",
        ),
        plan=_plan(
            (10, "Warm-up", "Open strings, then last week's pattern: open, 1, 2, 3 on the A string."),
            (10, "Finger 4", "Play finger 3, then finger 4, then the open E string. Adjust finger 4 until it matches the open E."),
            (15, "Hot Cross Buns", "Learn it one bar at a time from the music below, then join the bars together."),
            (10, "Ode to Joy", "Start it once Hot Cross Buns is steady. The first two bars are enough for today."),
            (5, "Play through", "Play one tune from beginning to end without stopping, wrong notes and all."),
        ),
    ),
    Lesson(
        week=5,
        title="The D string",
        pieces=("mary", "twinkle"),
        goals=(
            "Use the same finger pattern on the D string",
            "Play tunes that cross between the D and A strings",
            "Cross strings without a bump in the sound",
        ),
        body=(
            "The finger spacing you learned on the A string works on every string. On the D "
            "string the open note is D, finger 1 plays E, finger 2 plays F♯, finger 3 plays "
            "G and finger 4 plays A. Fingers 2 and 3 are still the close pair.",
            "To get there, keep the shape of your hand and swing your left elbow slightly to "
            "the right, which carries the fingers over to the lower string. Your bow arm moves "
            "too: the elbow sits a little higher for the D string than for the A.",
            "Mary Had a Little Lamb stays on the D string except for two open A notes. Twinkle "
            "crosses back and forth more often and uses finger 1 on the A string.",
        ),
        plan=_plan(
            (10, "Warm-up", "Open strings, then the A string pattern from memory."),
            (10, "D string pattern", "Open, 1, 2, 3, 4 on the D string, checking each note with the live checker. Finger 4 should match the open A."),
            (15, "Mary Had a Little Lamb", "One bar at a time, then the whole tune."),
            (10, "Twinkle", "Watch the jump from open D to open A at the start. Move the bow to the new string before you play it."),
            (5, "Play through", "One slow run of whichever tune is going better."),
        ),
    ),
    Lesson(
        week=6,
        title="The G and E strings",
        pieces=("auclair", "lightlyrow"),
        goals=(
            "Play the finger pattern on the G and E strings",
            "Reach the G string without the bow touching the D string",
            "Know the name of every note you can now play",
        ),
        body=(
            "Two strings to go. On the G string the notes are G, A, B, C and D. On the E string "
            "they are E, F♯, G♯, A and B. The spacing under your fingers is the same "
            "as before.",
            "The G string is the thickest and the slowest to speak. Give it a slower bow with a "
            "bit more weight, and lift your right elbow so the bow clears the D string. The E "
            "string is the opposite. It needs very little weight and it squeals if you press.",
            "Au Clair de la Lune sits entirely on the G string. Lightly Row is on the A string "
            "and reaches up to the open E for its top note.",
        ),
        plan=_plan(
            (10, "Warm-up", "Open strings, then the A and D string patterns."),
            (10, "G and E patterns", "Open, 1, 2, 3, 4 on the G string, then on the E string. Check each note with the live checker."),
            (10, "Au Clair de la Lune", "Slow bows. Listen for the D string sounding by accident."),
            (15, "Lightly Row", "Play the top E as an open string first. Later, try it with finger 4 on the A string."),
            (5, "Play through", "One tune, start to finish."),
        ),
    ),
    Lesson(
        week=7,
        title="Reading it on paper",
        pieces=("oldmac", "reading"),
        goals=(
            "Find the four open strings on the staff",
            "Name the notes of the D and A strings from the page",
            "Play a tune you know while reading it",
        ),
        body=(
            "You have been reading a little already, every time you followed the music under a "
            "lesson. This week you slow down and learn what the page is telling you.",
            "Open the Theory tab and read the first section, Reading the staff. Each line and "
            "each space is one letter, and the letters run in order as you climb. The open D "
            "hangs just under the bottom line. The open A sits in the second space up.",
            "Old MacDonald is here because you already know how it sounds, so your eyes can "
            "follow the notes while your ear checks them. The Reading Study is new. Say the "
            "note names aloud before you play it.",
        ),
        plan=_plan(
            (10, "Warm-up", "Open strings and the finger pattern on all four strings."),
            (10, "Staff study", "Read Reading the staff on the Theory tab. Then point to notes in this week's music and name them."),
            (15, "Old MacDonald", "Play it from the page. Keep your eyes on the music and off your fingers."),
            (10, "Reading Study", "Name the notes, clap the rhythm, then play."),
            (5, "Notes to self", "Which notes did you have to stop and work out? Write them down."),
        ),
    ),
    Lesson(
        week=8,
        title="Bow control: strokes and volume",
        pieces=("dynamics", "london"),
        goals=(
            "Play one smooth, separate bow stroke per note",
            "Play loud and soft on purpose",
            "Change bow direction without a bump",
        ),
        body=(
            "Back to the bow. The basic stroke is called détaché: one note per bow, "
            "changing direction smoothly with no gap and no accent. You have been doing a rough "
            "version of it since week 2.",
            "Loud and soft are called forte and piano. Three things control volume on a violin: "
            "how fast the bow moves, how much arm weight goes into the string, and how close "
            "the bow is to the bridge. For forte, use more bow and more weight and move a "
            "little toward the bridge. For piano, use less bow and less weight, and drift "
            "toward the fingerboard.",
            "Grip is not on that list. Your bow hold should feel the same at every volume.",
        ),
        plan=_plan(
            (10, "Warm-up", "Open strings. Listen to the moment the bow changes direction and try to make it disappear."),
            (10, "Détaché", "Play the D string pattern up and down, one bow per note, all the notes the same length."),
            (15, "Loud and Soft Study", "Play it forte, then piano. Notice what your arm does differently."),
            (10, "London Bridge", "Play each two-bar phrase forte, then repeat it piano like an echo."),
            (5, "Wind down", "One slow, quiet bow on each open string."),
        ),
    ),
    Lesson(
        week=9,
        title="New rhythms",
        pieces=("rhythmecho", "longlongago"),
        goals=(
            "Play eighth notes evenly, two to a beat",
            "Play a dotted quarter note followed by an eighth",
            "Hold a steady beat through a whole tune",
        ),
        body=(
            "Until now every note has lasted one beat or longer. An eighth note lasts half a "
            "beat, so two of them fit in the time of one quarter note. Count them \"1 and 2 and\".",
            "A dotted quarter note lasts a beat and a half. It is nearly always followed by a "
            "single eighth note, and together they fill two beats. Count \"1, 2 and\": hold the "
            "long note through the 2 and play the eighth on the \"and\".",
            "Clap each rhythm while you count aloud before you pick up the violin. Use short "
            "bows for eighth notes, about half the length you use for a quarter. Most people "
            "speed up when the notes get shorter, so set the metronome to 60 and stay with it.",
        ),
        plan=_plan(
            (10, "Warm-up", "Open strings and finger patterns."),
            (20, "Rhythm Echo", "Play it at a slow, even beat. Short bows on the eighth notes."),
            (15, "Long, Long Ago", "The rhythm is long, short, short, over and over. The F♯ is finger 1 on the E string."),
            (5, "Play through", "Play one piece along with a metronome at 60."),
        ),
    ),
    Lesson(
        week=10,
        title="A first scale",
        pieces=("scale", "thirds"),
        goals=(
            "Play a one-octave D major scale from memory",
            "Hear when a scale note is out of tune",
            "Slur two notes in one bow",
        ),
        body=(
            "A scale is a ladder of notes, and D major is the easiest one on the violin: D, E, "
            "F♯, G on the D string, then A, B, C♯, D on the A string. It is the finger "
            "pattern you already know, played on two strings in a row.",
            "Play it slowly and listen to each step. The two half steps, F♯ to G and "
            "C♯ to D, are where the close fingers go. If finger 3 sounds dull, it is "
            "probably flat. Check it against the open string below, which is the same note an "
            "octave lower.",
            "A slur is a curved line over two or more different notes, and it means you play "
            "them in one bow. Start with two notes to a bow: D and E on a down-bow, F♯ and "
            "G on an up-bow. Change finger exactly halfway through the stroke.",
        ),
        plan=_plan(
            (10, "Warm-up", "Open strings, then the D and A string patterns."),
            (15, "D major scale", "One bow per note, up and down. Check F♯ and C♯ with the live checker."),
            (10, "Slurs", "The same scale, two notes to a bow."),
            (10, "Scale in thirds", "Play D Major Scale in Thirds below. Every pair skips one note of the scale."),
            (5, "From memory", "Put the phone down and play the scale up and down once."),
        ),
    ),
    Lesson(
        week=11,
        title="Polishing a piece",
        pieces=("etude", "andante"),
        goals=(
            "Choose one piece and get it ready to play for someone",
            "Find its two or three hardest spots and fix them",
            "Play it through at one steady speed",
        ),
        body=(
            "Nothing new this week. Pick one piece to polish: Etude in D or Andante in D below, "
            "or a favorite from an earlier week.",
            "Play it through once and mark the places where you stumble. There are usually two "
            "or three. Practice those spots alone, a few notes at a time and at half speed, "
            "until you can play each one correctly three times in a row. Then add the bar "
            "before and the bar after.",
            "Starting from the top every time you make a mistake feels productive, but it "
            "mostly rehearses the parts you can already play.",
        ),
        plan=_plan(
            (10, "Warm-up", "Open strings and the D major scale."),
            (10, "Find the hard spots", "Play your piece once and note where it falls apart."),
            (15, "Spot practice", "Loop each hard spot slowly. Three correct tries in a row, then move on."),
            (10, "Run-throughs", "Play the whole piece twice at a speed you can keep up all the way through."),
            (5, "Record", "Record one run-through and listen back. Pick one thing to fix tomorrow."),
        ),
    ),
    Lesson(
        week=12,
        title="Putting it together",
        pieces=("recital", "arpeggio"),
        goals=(
            "Play a piece from memory for another person",
            "Tune by ear, then confirm with the tuner",
            "Decide what to learn next",
        ),
        body=(
            "In twelve weeks you have learned to hold the violin and bow, play in tune on all "
            "four strings in first position, read simple music, count basic rhythms and play a "
            "scale. That is a solid start.",
            "Try tuning by ear this week. Tune the A string with the tuner, then play A and D "
            "together and turn the D string's fine tuner until the two notes ring smoothly, "
            "with no wobble in the sound. Do the same for D with G, then A with E. Check your "
            "work with the tuner afterwards.",
            "Then play for someone. A friend, a family member or your phone's camera all count. "
            "Playing for a listener is a skill of its own and it only improves with practice.",
            "After this course, the usual next steps are the low second finger (which opens up "
            "G major and C major across all the strings), longer slurs, and later third position "
            "and vibrato. A teacher will get you through those faster than an app can, because "
            "a teacher can see your posture and hear your tone.",
        ),
        plan=_plan(
            (10, "Tune by ear", "A from the tuner, the other three by ear, then check them."),
            (10, "Review", "D major scale, then the finger pattern on all four strings."),
            (15, "Performance", "Play your polished piece from memory, twice. Record the second one."),
            (10, "This week's pieces", "Recital Piece and D Major Arpeggio. The arpeggio goes up to A on the E string."),
            (5, "Look back", "Play something from week 4. Notice how much easier it has become."),
        ),
    ),
)



def _with_timing(lesson: Lesson) -> Lesson:
    """Attach the week's timing study and slot it into the plan after the warm-up."""
    study = TIMING[lesson.week]
    item = PlanItem(10, f"Timing: {study.title}", study.plan_text)
    return replace(lesson, timing=study, plan=(lesson.plan[0], item, *lesson.plan[1:]))


LESSONS = tuple(_with_timing(lesson) for lesson in LESSONS)
LESSON_BY_WEEK = {lesson.week: lesson for lesson in LESSONS}



def piece_menu() -> dict[str, str]:
    """'Week 4: Hot Cross Buns' -> piece id, in course order."""
    from ..music.pieces import PIECES
    return {f"Week {lesson.week}: {PIECES[piece_id].title}": piece_id
            for lesson in LESSONS for piece_id in lesson.pieces}


LESSONS_INTRO = ("One lesson a week, planned for an hour of practice a day. "
                 "Take them in order, because each one builds on the last.")
