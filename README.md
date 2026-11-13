# StringWise

A violin tutor for beginners, written in Python with [Kivy](https://kivy.org) and
packaged for Android with Buildozer.

- **Tuner** that listens through the microphone
- **Lessons**: a 12-week course planned for an hour of practice a day, with two pieces of sheet music and a timing lesson each week
- **Metronome** on its own tab, with tap tempo, eighth-note clicks and drop-out bars. It keeps running across tabs
- **Record and Check**: records a take with the click, then marks each note for pitch, tuning and timing
- **Play-Along**: follows the sheet music as you play and shows the note it hears on the staff
- **Fingers**: a first-position map with real string spacing, and a live check for any finger
- **Theory**, and a **Practice** tab with a rhythm of the day, a tempo ladder and a daily checklist

The app works offline. Its only permission is the microphone, and audio is analysed on the device.

## Project layout

```
main.py                     entry point
buildozer.spec              Android build settings
stringwise/
  app.py                    title bar, navigation, screen switching
  theme.py                  colours and fonts
  storage.py                saved progress (JSON)
  audio/                    pitch detection (YIN), microphone, reference tones, metronome
  music/                    notes, fingering, the 22 practice pieces, rhythm studies
  logic/                    tuner, finger check, play-along and take-checking rules (no UI code)
  content/                  all lesson, theory and practice text
  ui/                       widgets: dial, sheet music, fingerboard
  ui/screens/               one file per screen
  assets/                   fonts, icon, optional photos
tests/                      pytest suite for audio, music, content and logic
```

To change wording, edit the files in `stringwise/content/`. To add a piece, add it to
`stringwise/music/pieces.py`; the tests check that every bar adds up and every note is reachable.

## Run it on a computer

```
pip install -r requirements.txt
python main.py
python -m pytest tests
```

No violin to hand? `STRINGWISE_FAKE_MIC="440,494,554" python main.py` feeds the app those
notes, one a second.

## Build for Android with GitHub Actions

1. Push this folder to a GitHub repository.
2. Open the **Actions** tab, choose **Build Android**, and press **Run workflow**.
3. When it finishes, download the **stringwise-android** artifact. It contains a debug
   `.apk` you can install on your phone, and the signed `.aab` for Google Play if the
   signing secrets below are set.

The first build takes 30 to 40 minutes. Later builds reuse the cached toolchain.

### Signing secrets

Google Play only accepts an update signed with the same upload key as earlier
releases. That key is the `signing.keystore` file from the PWABuilder download, with its
alias and passwords in `signing-key-info.txt`.

Add four repository secrets under **Settings > Secrets and variables > Actions**:

| Secret | Value |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | the keystore file, base64 encoded (`base64 -w0 signing.keystore`) |
| `ANDROID_KEYSTORE_PASSWORD` | the keystore password |
| `ANDROID_KEY_ALIAS` | the key alias |
| `ANDROID_KEY_PASSWORD` | the key password |

Never commit the keystore itself. `.gitignore` already excludes `*.keystore`.

### Before each upload

In `buildozer.spec`, raise `android.numeric_version` by at least 1 and update `version`.
The package id, `golemapps.stringwise.app`, must stay as it is.

## Photos of hand positions

The Fingers screen shows photos above each checklist when these files exist in
`stringwise/assets/photos/`:

- Left hand: `hand-frame-front.jpg`, `hand-frame-side.jpg`, `thumb.jpg`, `place-1234.jpg`
- Bow hold: `bow-hold-side.jpg`, `bow-hold-top.jpg`, `bow-hold-end.jpg`

Landscape, about 1200 px wide.

## Credits

Headings are set in Crimson Text (SIL Open Font License, see `stringwise/assets/fonts/`).
Traditional tunes are simplified arrangements; the other studies were written for this course.
