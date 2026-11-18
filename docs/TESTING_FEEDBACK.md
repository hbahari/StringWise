# StringWise: testing feedback and what changed

A running log of feedback on StringWise since version 1.0.0, in plain language, with the
change made in response. Newest entries are at the bottom of each section, and new
sections are added as testing continues.

**Where the feedback came from**

- **Closed test**: reported by testers during the Google Play closed test.
- **Device testing**: found by the developer while testing builds on a phone and a computer.
- **Play Console**: raised by Google Play's own checks on an uploaded build.

Keeping the two apart matters when answering Google's questions about tester feedback.

---

## First closed test (version 1.0.x)

| Feedback | Source | What changed |
| --- | --- | --- |
| The tuner sometimes felt slow, and now and then it did not pick up a note at all. | Closed test | Replaced the pitch detection with a method better suited to the violin, boosted quiet microphone input, and added a level bar so you can see whether the app is hearing you. |
| One practice piece a week in Play-Along was not enough. | Closed test | Every week from week 2 now has two pieces, 22 in all. |

## 12 November 2026 (version 2.0.0)

| Feedback | Source | What changed |
| --- | --- | --- |
| The app was a website in a wrapper, and it felt like one. | Device testing | Rebuilt as a native Android app. It works fully offline and asks for one permission, the microphone. |
| Some of the lesson and theory text was wrong or confusing, and it read stiffly. | Device testing | Every lesson and theory section was checked and rewritten in plainer language. Fixed: which fingers sit close together, the note the fourth finger plays, the staff diagram of the open strings, and the advice on pegs and fine tuners. |
| Two of the tunes did not sound like the songs they were named after. | Device testing | Lightly Row and Long, Long Ago were replaced with the real melodies. Six pieces with bars of the wrong length were corrected. |
| The week on new rhythms had no pieces that used those rhythms. | Device testing | Week 9's pieces now include eighth notes and dotted notes. |
| The dial on the Fingers tab sat off to one side until you started listening. | Device testing | Fixed. It is centred from the start. |
| "Hear the tune" sounded robotic, with a gap after every note. | Device testing | Notes now run into each other the way a bow plays them, with a clear re-start when the same note repeats. |
| The app teaches the right notes but not how to play in time. | Device testing | Added a metronome, a ten-minute timing lesson in every week, a rhythm of the day, and a tempo ladder that remembers your best clean tempo for each piece. Sheet music now shows rests. |
| The metronome should be easy to reach and should not stop when I change tab. | Device testing | The metronome has its own tab and keeps running across the app. |
| I want to record myself and be told what I got wrong. | Device testing | Added Record and Check. It records a take with the click, then marks each note as right, out of tune, wrong or missed, and as early, late or on the beat. It also says whether you sped up or slowed down. |
| I could not tell what "Drop-out bars" did. | Device testing | The metronome now says which bar you are in ("click bar 1 of 2", "silent bar 1 of 2"), the beat dot changes during silent bars, and the Help pop-up explains it. |
| "Hear the tune" did not say how fast it was playing. | Device testing | The button shows the tempo ("Hear the tune at 72") and follows the metronome's setting, with slower and faster buttons beside it. |

## 13 November 2026

| Feedback | Source | What changed |
| --- | --- | --- |
| The Metronome and Tuner screens had too much text around the controls. | Device testing | The explanations moved into a Help button at the top right of each screen. The screens now show only the controls. |
| The lessons had a full copy of the metronome, which crowded the page now that there is a Metronome tab. | Device testing | Each timing lesson now has one button that starts the metronome at the right tempo for that lesson. Play-Along keeps only slower and faster buttons. |
| Once I stopped the click from the top of the screen, the button vanished and I had to go back to the Metronome tab to restart it. | Device testing | After the metronome has been started once, a Pause/Resume button and the four beat dots stay at the top of every screen. Resume carries on at the same tempo. |
| The four beat dots were plain. | Device testing | The current beat now swells on the click and settles back, beat 1 is larger, and the dots sit next to the Pause button so they are visible on every tab. |
| Pressing "Hear the tune" in Play-Along switched the metronome off. | Device testing | The metronome now keeps going. If it is running, the tune waits and comes in on the next beat 1, so it lines up with the click. |
| The Resume button at the top was hard to see against the dark bar. | Device testing | Resume is now a pale button with dark text. Pause keeps its warm colour, so the two are easy to tell apart. |
| Once a tune or rhythm started playing there was no way to stop it or start it again from the top. | Device testing | Every "Hear the tune" and "Hear it" button turns into Stop while it plays. Press it to stop, and again to start from the beginning. |
| "Hear it at 60" in the timing lessons played its own click and ignored the metronome shown at the top. | Device testing | There is now one metronome for the whole app. "Hear it" sets it to the lesson's tempo, leaves it running at the top of the screen, and brings the rhythm in on the next beat 1. |

## 15 November 2026

| Feedback | Source | What changed |
| --- | --- | --- |
| The rhythm of the day could not be changed, and there was no way to go back to an earlier one. | Device testing | The Practice tab has a drop-down listing every rhythm by week. You can pick any of them, or return to today's. Ticking Timing in the daily routine marks that rhythm as done, and done rhythms are labelled in the list. |
| Beginners saw the same rhythm of the day over and over. | Device testing | Added six more simple rhythms. There are now 21, with five to choose from in week 1 and eight by week 2, so the daily rhythm changes through the week. |
| In the tempo ladder, the button opened the metronome, when what you need next is the piece itself. | Device testing | The button now opens the chosen piece in Play-Along, where you can see the music, hear it and set the tempo. Play-Along also has a Start click button, so the metronome can be started without leaving the page. |

## 16 November 2026

| Feedback | Source | What changed |
| --- | --- | --- |
| On the tuner, the needle covered the words "in tune" when a string was in tune. | Device testing | The label now sits above the dial, clear of the needle. The same applies to the finger check. |
| After a recorded take, the result appeared below the buttons, away from the marked music. | Device testing | The result now appears directly under the marked music, and the page jumps back up to show both. |

## 18 November 2026

| Feedback | Source | What changed |
| --- | --- | --- |
| Google Play warned that the app could not be installed on some phones, tablets, Chromebooks and Android XR devices. | Play Console | The app is portrait-only, and Android took that to mean the device must have a portrait screen. That requirement is now marked as optional, so those devices can install it. |

---

## Still to do

- Photos of real hand positions for the Fingers tab.
- Check Record and Check with a real violin on several phones.
