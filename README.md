# StringWise — Learn Violin

A self-contained, offline-capable web app for learning violin: a real-time
tuner, an animated finger-placement guide, music theory, a 12-week lesson
plan with real sheet music, and a live play-along tool that listens through
your microphone and follows you note by note.

No installs, no accounts, no ads, no tracking — everything runs in the
browser, and all audio processing happens locally on your device.

## Features

- **Tuner** — real-time pitch detection via the Web Audio API, with a
  colored arc dial (red/amber/green) and cents-off readout. Reference tones
  for each open string.
- **Finger Placement** — an interactive first-position fingerboard diagram,
  animated hand-form illustrations (left-hand frame and bow hold), and a
  live checker that listens to confirm whether the note you're actually
  playing matches the finger and string you picked.
- **Theory** — a collapsible reference covering staff reading, key
  signatures, rhythm, bowing vocabulary, dynamics and tempo, left-hand
  finger numbering, tuning, and ear training.
- **Lessons** — a 12-week beginner curriculum, one lesson per week, paced
  for about an hour of practice a day. Every week from Week 2 onward
  includes real hand-drawn sheet music for that week's piece.
- **Live Play-Along** — pick any piece from the curriculum and play it
  through; a live pitch cursor slides up and down the staff in real time,
  colored by how close you are to the target note, and the piece advances
  automatically as you get each note right.
- **Practice** — a daily checklist-based routine with progress saved
  between sessions.
- **Installable PWA** — works offline after the first load, and can be
  added to your phone's home screen like a native app.

## Try it

Once this repo is hosted (see below), just open the URL in a browser —
Chrome on Android or desktop works best for the microphone features. On
mobile, use the browser menu to "Add to Home Screen" for a full-screen,
app-like experience.

## Running it locally

This is a static site — no build step, no dependencies.

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
python3 -m http.server 8000
# then open http://localhost:8000
```

Note: microphone access requires a secure context. `localhost` counts as
one, so it works locally, but opening `index.html` directly as a `file://`
URL will not allow microphone access — always serve it over `http://` (for
local testing) or `https://` (once deployed).

## Hosting on GitHub Pages

1. Repo **Settings → Pages**
2. Source: **Deploy from a branch**, branch `main`, folder `/ (root)`
3. Your app will be live at `https://<your-username>.github.io/<repo-name>/`

## Building an Android app

This project is set up as an installable PWA (`manifest.json` +
`service-worker.js` + icons), which [PWABuilder](https://www.pwabuilder.com)
can package into a Trusted Web Activity for the Play Store — no Android
Studio required. See `PUBLISHING_GUIDE.md` in this repo for the full
walkthrough, from hosting through to a Play Console listing.

## Project structure

```
.
├── index.html            # the entire app — UI, styles, and logic
├── manifest.json         # PWA manifest
├── service-worker.js     # offline caching
├── icons/                # app icons (192, 512, and maskable)
├── PUBLISHING_GUIDE.md    # steps to host, package, and publish on Play Store
└── PRIVACY_POLICY.md      # privacy policy draft (fill in and host before publishing)
```

## Tech

Plain HTML, CSS, and JavaScript — no frameworks, no build tooling. Pitch
detection uses autocorrelation on the raw time-domain signal from the Web
Audio API's `AnalyserNode`. All sheet music is rendered as hand-built SVG,
not an image or external notation library.

## Privacy

Microphone audio is processed entirely on-device, in memory, for pitch
detection only. Nothing is recorded, stored, or transmitted anywhere. See
`PRIVACY_POLICY.md` for the full policy (fill in your details before using
it as a real published policy).

## License

Add a license of your choice here (e.g. MIT) before making this repo
public, if you haven't already — GitHub can generate one for you when
creating the repo, or add one via **Add file → Create new file → LICENSE**.

## Credits

All diagrams, icons, and sheet-music arrangements in this app are original,
made for this project. Traditional folk melodies referenced in the Lessons
tab (Hot Cross Buns, Mary Had a Little Lamb, Lightly Row, Long Long Ago)
are in the public domain.
