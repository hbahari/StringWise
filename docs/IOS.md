# StringWise for iPhone

The iPhone app is built from the same Python code as the Android app, using
[kivy-ios](https://github.com/kivy/kivy-ios) instead of Buildozer. This page says
what is ready, what still has to be checked on an iPhone, and the steps once the
Apple Developer account exists.

## What is ready

| Part | Where | State |
| --- | --- | --- |
| Microphone | `ios/recipes/swmic` (Objective-C and Cython), `IosMic` in `stringwise/audio/mic.py` | Written. Ring buffer and Python wrapper tested on Linux; the iOS audio code itself is untested until the first Simulator run. |
| Microphone permission | `request_microphone` in `stringwise/ui/platform.py` | Asks with the iOS dialog, then waits for the answer. Wording is in `ios/configure_xcode.py`. |
| Metronome and microphone together | `SDL_AUDIO_CATEGORY` in `main.py`, session options in `swmic_ios.m` | Both use a play-and-record session with sound through the speaker. Needs a check on a real iPhone. |
| Links, feedback email, keep screen on, notch and home bar spacing, share sheet | `stringwise/ui/platform.py` | Written and tested against fakes. |
| Rate and Share buttons | `APP_STORE_ID` in `stringwise/content/settings.py` | Hidden on iPhone until the App Store ID is filled in. No Google Play wording appears on iPhone. |
| Sound files | `_cache_folder` in `stringwise/app.py` | Go to Library/Caches, as Apple asks, not Documents. |
| Xcode project | `ios/build.sh`, `ios/configure_xcode.py` | Name, bundle ID, version, portrait only, iPhone only, icon, launch screen colour. |
| App icon | `ios/assets/icon-1024.png` | Full-bleed 1024 px, no transparency (iOS rounds the corners itself). |
| Build on GitHub | `.github/workflows/build-ios.yml` | Builds for the Simulator, starts the app on a simulated iPhone and saves screenshots, then checks an unsigned iPhone build compiles. No Apple account needed. |
| Signed upload to TestFlight | `ios/release.sh`, switched-off job in the workflow | Written for later. |

## Try the build now (no Apple account needed)

1. Push the code to GitHub.
2. On GitHub open **Actions > Build iOS > Run workflow**.
3. The first run takes about an hour. Later runs reuse the compiled libraries.
4. Open the finished run and download **StringWise-ios-simulator-check**. It has screenshots of the app running on a simulated iPhone after 6, 20 and 45 seconds, and the app's logs. If the app stopped, `CRASHED.txt` is there too.

The repository is public, so GitHub's macOS runners are free for it.

## Still to check on a real iPhone

- The tuner hears the violin, at the right pitch, with the level bar moving.
- The metronome keeps playing through the speaker while the tuner or Record and Check listens. Record and Check finds the clicks in the recording.
- The beat dots line up with the click (`_output_delay` in `stringwise/app.py` is a guess of 0.04 s).
- The microphone question appears once and the app copes with Don't Allow.
- Nothing hides under the Dynamic Island or the home bar.
- The share sheet, feedback email and privacy link open.
- A phone call during listening, then coming back to the app.
- Whether iOS asks for the microphone at launch instead of at the first Start listening. If it does, the tour's first screen is a good moment for it anyway.

## Once the Apple Developer account exists

1. **Enrol** at developer.apple.com ($99 a year). Note the **Team ID** under Membership.
2. **Register the bundle ID** `golemapps.stringwise.app` under Certificates, Identifiers and Profiles > Identifiers. (Change `BUNDLE_ID` in `ios/configure_xcode.py` first if you want a different one. It cannot change after the first upload.)
3. **Create the app** in App Store Connect > Apps > New App, with that bundle ID. Copy its **Apple ID** number into `APP_STORE_ID` in `stringwise/content/settings.py`; that turns on Rate and Share.
4. **Make an API key** in App Store Connect > Users and Access > Integrations > App Store Connect API, with the **Admin** role (needed so Xcode can make the signing certificate itself). Download the `.p8` file; it can only be downloaded once.
5. **Add four GitHub secrets** (Settings > Secrets and variables > Actions):
   - `IOS_TEAM_ID`: the Team ID
   - `APP_STORE_API_KEY_ID`: the key's ID
   - `APP_STORE_API_ISSUER`: the Issuer ID shown above the keys
   - `APP_STORE_API_KEY_P8`: the whole text of the `.p8` file
6. **Switch on the release job**: in `.github/workflows/build-ios.yml`, remove the `# ` at the start of each line of the `release:` job.
7. **Run Build iOS**. The build goes to TestFlight. Install the TestFlight app on an iPhone to try it, and invite testers there.
8. **Store listing**: screenshots from a 6.9-inch iPhone (1320 x 2868), description, keywords, support URL, privacy policy URL, age rating, and the privacy questions (StringWise collects no data). Then submit for review.

The build number is the GitHub run number, so it goes up by itself with every run.

## Building on a Mac instead

```
brew install autoconf automake libtool pkg-config
ios/build.sh simulator        # or: ios/build.sh device, or just ios/build.sh to open it in Xcode
open ios/build/kivy-ios/stringwise-ios/stringwise.xcodeproj
```

## How the pieces fit

- `ios/build.sh` installs kivy-ios (pinned to a known commit), compiles Python, Kivy, NumPy, pyobjus and `swmic` for iOS, copies the app (without tests or Android files) to `ios/build/app`, creates the Xcode project and runs `ios/configure_xcode.py`.
- Everything under `ios/build/` is generated and is not committed.
- The Android build leaves the `ios` folder out (`source.exclude_dirs` in `buildozer.spec`), and the iOS build leaves out the Android files.
