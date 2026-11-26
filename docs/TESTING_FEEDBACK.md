# StringWise: feedback and changes by version

Every piece of feedback on StringWise since the first closed test, grouped by the version that answered it, with what changed.

## Where the feedback came from

- **Testers**: reported by the people in the Google Play closed test, including the written Testers Community report of 22 November 2026.
- **Developer**: found by the developer while testing builds on a phone and a computer.
- **Google Play**: raised by Google Play Console's own checks on an uploaded build.

## Versions at a glance

| Version | Play version code | Date | Main changes |
| --- | --- | --- | --- |
| 1.0.0 | 1 | Oct 2026 | First closed-test release (web app in an Android wrapper) |
| 1.1.x | 2 to 4 | early Nov 2026 | More responsive tuner, two pieces a week, Play link verification |
| 2.0.0 | 5 to 7 | 12 Nov 2026 | Rebuilt as a native app; corrected lessons; metronome, timing lessons, Record and Check |
| 2.2.0 | 8 | 13 Nov 2026 | Help buttons, Pause/Resume on every screen, tune lines up with the click |
| 2.3.0 | 9 | 15 Nov 2026 | Hear buttons turn into Stop, one shared metronome, rhythm picker |
| 2.3.1 | 10 | 18 Nov 2026 | Installable on tablets and Chromebooks; tuner and Record and Check layout fixes |
| 2.4.0 | 11 | 19 Nov 2026 | Settings page: feedback email, rating, tuning pitch, reset progress |
| 2.5.0 | 12 | 22 Nov 2026 | First-launch tour, Share button (Testers Community report) |
| 2.6.0 | 13 | 24 Nov 2026 | Keep the screen on |

## Version 1.1.x

| Feedback | From | What changed |
| --- | --- | --- |
| The tuner sometimes felt slow, and now and then it did not pick up a note at all. | Testers | Replaced the pitch detection with a method better suited to the violin, boosted quiet microphone input, and added a level bar so you can see whether the app is hearing you. |
| One practice piece a week in Play-Along was not enough. | Testers | Every week from week 2 now has two pieces, 22 in all. |
| The app's link to its website could not be verified ("Digital Asset Links"). | Google Play | Fixed the verification file on the website so Google Play can confirm the app and the site belong together. |

## Version 2.0.0

| Feedback | From | What changed |
| --- | --- | --- |
| The app was a website in a wrapper, and it felt like one. | Developer | Rebuilt as a native Android app. It works fully offline and asks for one permission, the microphone. |
| Some of the lesson and theory text was wrong or confusing, and it read stiffly. | Developer | Every lesson and theory section was checked and rewritten in plainer language. Fixed: which fingers sit close together, the note the fourth finger plays, the staff diagram of the open strings, and the advice on pegs and fine tuners. |
| Two of the tunes did not sound like the songs they were named after. | Developer | Lightly Row and Long, Long Ago were replaced with the real melodies. Six pieces with bars of the wrong length were corrected. |
| The week on new rhythms had no pieces that used those rhythms. | Developer | Week 9's pieces now include eighth notes and dotted notes. |
| The dial on the Fingers tab sat off to one side until you started listening. | Developer | Fixed. It is centred from the start. |
| "Hear the tune" sounded robotic, with a gap after every note. | Developer | Notes now run into each other the way a bow plays them, with a clear re-start when the same note repeats. |
| The app teaches the right notes but not how to play in time. | Developer | Added a metronome, a ten-minute timing lesson in every week, a rhythm of the day, and a tempo ladder that remembers your best clean tempo for each piece. Sheet music now shows rests. |
| The metronome should be easy to reach and should not stop when you change tab. | Developer | The metronome has its own tab and keeps running across the app. |
| I want to record myself and be told what I got wrong. | Developer | Added Record and Check. It records a take with the click, then marks each note as right, out of tune, wrong or missed, and as early, late or on the beat. It also says whether you sped up or slowed down. |
| It was unclear what "Drop-out bars" did. | Developer | The metronome now says which bar you are in ("click bar 1 of 2", "silent bar 1 of 2") and the beat dot changes during silent bars. |
| "Hear the tune" did not say how fast it was playing. | Developer | The button shows the tempo ("Hear the tune at 72") and follows the metronome's setting, with slower and faster buttons beside it. |

## Version 2.2.0

| Feedback | From | What changed |
| --- | --- | --- |
| The Metronome and Tuner screens had too much text around the controls. | Developer | The explanations moved into a Help button at the top right of each screen. The screens now show only the controls. |
| The lessons had a full copy of the metronome, which crowded the page now that there is a Metronome tab. | Developer | Each timing lesson now has one button that starts the metronome at the right tempo for that lesson. |
| Once the click was stopped from the top of the screen, the button vanished and you had to go back to the Metronome tab to restart it. | Developer | After the metronome has been started once, a Pause/Resume button and four beat dots stay at the top of every screen. Resume carries on at the same tempo. |
| The four beat dots were plain. | Developer | The current beat swells on the click and settles back, beat 1 is larger, and the dots sit next to the Pause button. |
| Pressing "Hear the tune" in Play-Along switched the metronome off. | Developer | The metronome keeps going. If it is running, the tune waits and comes in on the next beat 1, so it lines up with the click. |
| The Resume button was hard to see against the dark bar. | Developer | Resume is now a pale button with dark text. Pause keeps its warm colour. |

## Version 2.3.0

| Feedback | From | What changed |
| --- | --- | --- |
| Once a tune or rhythm started playing there was no way to stop it or start it again. | Developer | Every "Hear the tune" and "Hear it" button turns into Stop while it plays. Press it to stop, and again to start from the beginning. |
| "Hear it at 60" in the timing lessons played its own click and ignored the metronome at the top. | Developer | There is now one metronome for the whole app. "Hear it" sets it to the lesson's tempo, leaves it running, and brings the rhythm in on the next beat 1. |
| The rhythm of the day could not be changed, and there was no way to go back to an earlier one. | Developer | The Practice tab has a drop-down listing every rhythm by week. Ticking Timing in the daily routine marks a rhythm as done, and done rhythms are labelled in the list. |
| Beginners saw the same rhythm of the day over and over. | Developer | Added six simple rhythms. There are now 21, with five to choose from in week 1 and eight by week 2. |
| In the tempo ladder, the button opened the metronome, when what you need next is the piece itself. | Developer | The button now opens the chosen piece in Play-Along, which also gained a Start click button. |

## Version 2.3.1

| Feedback | From | What changed |
| --- | --- | --- |
| The app could not be installed on many tablets, Chromebooks and Android XR devices. | Google Play | The app is portrait-only, and Android took that to mean the device must have a portrait screen. That requirement is now marked as optional. |
| On the tuner, the needle covered the words "in tune". | Developer | The label now sits above the dial, clear of the needle. The same applies to the finger check. |
| After a recorded take, the result appeared below the buttons, away from the marked music. | Developer | The result now appears directly under the marked music. |

## Version 2.4.0

| Feedback | From | What changed |
| --- | --- | --- |
| There was no way to contact the developer or report a problem from inside the app. | Developer, later also Testers | Added a Settings page, opened from a gear at the top right of every screen. Send feedback opens your email app with a message ready to send, including the app version and phone model. |
| There was no button to rate the app. | Developer, later also Testers | Settings has Rate StringWise on Google Play. |
| Players whose teacher or orchestra tunes higher than A = 440 could not tune to that. | Developer | Settings has a tuning pitch choice from A = 440 to A = 443. It changes the tuner, the finger check, Play-Along and every note the app plays. |
| There was no way to start the course again from the beginning. | Developer | Settings has Reset progress, with a confirmation step. |
| The privacy policy described the old web version and did not mention Record and Check. | Developer | Rewrote the privacy policy for the current app and linked it from Settings. |

## Version 2.5.0: Testers Community report

A written report from the closed-test group, based on an earlier build. They found no crashes or bugs on the devices they tested, and listed these improvements.

| Feedback | From | What changed |
| --- | --- | --- |
| New users get no guided introduction to the app's features. | Testers | Added a short tour that runs the first time the app opens. It highlights one part of the app at a time (tuner, metronome, lessons, finger map, theory, practice and settings) and explains it in a bubble, with Skip and Next buttons. It can be watched again from Settings. |
| There is no easy way to share the app with friends. | Testers | Added Share StringWise to Settings. It opens the phone's share menu with a short message and the Google Play link. |
| There is no button to rate the app. | Testers | Already in version 2.4.0. |
| Let users send feedback from inside the app. | Testers | Already in version 2.4.0. |
| The store description is short and lacks search keywords. | Testers | The store title became "StringWise: Learn Violin", and the short and full descriptions were rewritten with a full feature list and the terms beginners search for (store listing update, 23 November 2026). |
| Works well offline. | Testers | Kept. The app needs no internet connection except for the feedback, rate and share links. |
| Add new lessons and pieces over time, rewards for finishing lessons, and a community area. | Testers | Noted for later versions. |

## Version 2.6.0

| Feedback | From | What changed |
| --- | --- | --- |
| The phone screen dims or locks while playing a piece, so you have to put the bow down and tap it. | Developer | Added a Keep the screen on switch to Settings. It is off by default because it uses more battery. The screen still stays on while the app is listening, as before. |

## iPhone version (in progress, not released)

| Feedback | From | What changed |
| --- | --- | --- |
| Make an iPhone version too, ready for when the Apple Developer account is set up. | Developer | Started 25 November 2026. The same app builds for iOS on GitHub, without an Apple account, and is started on a simulated iPhone with screenshots saved. Added an iPhone microphone module, the iOS permission question, share sheet, links, keep screen on and notch spacing. On iPhone the Rate and Share buttons stay hidden until the App Store page exists, and there is no Google Play wording. Nothing changes on Android. Still needs checking on a real iPhone (see docs/IOS.md). |

## Still to do

- Photos of real hand positions for the Fingers tab.
- Check Record and Check with a real violin on several phones.
- iPhone: run the Build iOS workflow, check on a real iPhone, then TestFlight once the Apple account exists.
- New lessons and pieces, rewards and a community area, from the Testers Community report.
