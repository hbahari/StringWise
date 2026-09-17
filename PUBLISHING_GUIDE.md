# Publishing StringWise on Google Play — a practical guide

This covers three things: trying the app on your phone right now, turning it
into a real Android package, and the business side of listing and selling it.

---

## 1. Try it on your phone today (no build step)

The app is now a proper installable **PWA** (Progressive Web App) — that's
what the `manifest.json`, `service-worker.js`, and `icons/` folder are for.
To try it on your phone right now:

1. Put the `stringwise-app` folder somewhere it can be served over HTTPS. The
   fastest free options:
   - **GitHub Pages** — push the folder to a repo, enable Pages in repo
     settings, done in a couple of minutes.
   - **Netlify Drop** ([app.netlify.com/drop](https://app.netlify.com/drop))
     — drag the folder in, get a live HTTPS URL instantly, no account
     strictly required.
   - **Vercel** or **Firebase Hosting** — similar, both free at this scale.
2. Open that URL on your phone in Chrome.
3. Tap the menu (⋮) → **"Add to Home Screen"** (or Chrome may prompt you
   automatically). It installs like a real app: its own icon, its own
   window, no browser bar, works offline after the first load.

This is genuinely the same app you'll eventually publish — same code, same
icon. It's a good way to test on a real device (especially the mic-based
Tuner and Live Finger Check) before going further.

## 2. Turning it into an APK/AAB for the Play Store

**Being upfront about a limitation:** I built and validated the app itself
in this conversation, but I can't compile an actual signed `.apk` from
inside this sandbox — the Android build toolchain needs Google's Maven
repositories (`dl.google.com`, `maven.google.com`) to download the Android
SDK and Gradle plugins, and my network access here doesn't extend to those
domains. Rather than hand you a broken or fake file, here's the real path:

### Recommended: PWABuilder (no Android Studio needed)

1. Go to **[pwabuilder.com](https://www.pwabuilder.com)**.
2. Paste in the public HTTPS URL from step 1 above.
3. PWABuilder reads your `manifest.json` and service worker, scores the PWA,
   and lets you generate an **Android package** (a Trusted Web Activity —
   essentially your PWA running full-screen, backed by Chrome, with a real
   Android app icon and identity).
4. Download the generated **AAB** (Android App Bundle — what Play Store
   wants) or **APK** (good for testing directly on your phone via
   `adb install` or just opening the file).
5. PWABuilder can either sign it for you with a generated keystore, or you
   can supply your own. **Save that keystore file somewhere safe** — you
   need the exact same one for every future update, or Play Store will
   reject it.

This whole process takes maybe 10–15 minutes once the site is hosted, and
needs no local Android setup at all.

### Alternative: Bubblewrap CLI (if you want to do it locally)

Same underlying technology as PWABuilder, run from your own machine's
terminal (which has full internet access, unlike this sandbox):

```
npm install -g @bubblewrap/cli
bubblewrap init --manifest https://your-hosted-url.com/manifest.json
bubblewrap build
```

Requires a JDK and the Android SDK — the `init` command will offer to
download these for you.

### If you want a more "native" shell later

Both routes above wrap your web app in a **Trusted Web Activity**, which is
the right choice here — it's lightweight, and microphone access works
exactly like it does in Chrome (no extra native permission plumbing needed).
If you later want deeper native integration (e.g. background audio, native
share sheets), **Capacitor** is the natural next step, but it's not needed
to publish what you have now.

---

## 3. Setting up Google Play

1. **Developer account** — [play.google.com/console](https://play.google.com/console),
   one-time $25 fee. Google now requires identity verification (personal or
   organization) before you can publish, which can take a day or two — worth
   starting early.
2. **New-account testing requirement** — Google currently requires new
   personal developer accounts to run a **closed test** (a set number of
   opted-in testers, currently in the range of ~12–20 people, over at least
   14 days) before a first app can go to full production. Policy specifics
   change, so check the current requirement in Play Console when you get
   there — but plan for this step, it's not optional for new accounts.
3. **Store listing assets you'll need:**
   - App icon: 512×512 PNG (you have this — `icons/icon-512.png`)
   - Feature graphic: 1024×500 PNG/JPG (a simple wood-tone banner with the
     app name would fit your existing look — happy to design one if you
     want it)
   - At least 2 phone screenshots (the Tuner dial, the Lessons tab, and the
     Live Finger Check are your strongest ones)
   - Short description (80 chars) and full description (up to 4000 chars)
   - Privacy policy URL — **required**, especially since you request
     microphone access. Use `PRIVACY_POLICY.md` in this folder as a
     starting draft: fill in the bracketed placeholders, host it as a
     public page (a GitHub Pages page or even a Google Doc published to the
     web both work), and link it in Play Console.
4. **Content rating questionnaire** — straightforward for this app (no
   violence, no user-generated content, no ads); should land in the
   lowest/broadest rating tier.
5. **Data safety section** — this is where the local-only audio processing
   pays off. You can honestly declare that microphone data is collected but
   **not stored or transmitted**, and that you don't share data with third
   parties — a much simpler disclosure than apps that send audio to a
   server. Keeping that architecture (rather than adding cloud features
   later without updating this section) keeps you compliant.

---

## 4. Monetization ideas

A few realistic options, roughly in order of how simple they are to set up:

**A. One-time paid app (simplest)**
Set a price directly on the Play Store listing — no billing code needed at
all for a TWA. Comparable violin/tuner apps tend to sit in the $2.99–$9.99
range for a one-time purchase; given the breadth here (tuner + live
intonation checker + structured 12-week curriculum), the higher end of that
range is reasonable if the store listing makes the curriculum depth clear.

**B. Freemium with an unlock**
Free: Tuner + Finger Placement (including the live checker) + Theory.
Paid unlock: the full 12-week Lessons curriculum.
This needs **Google Play Billing** integration for the in-app purchase,
which is more setup (Play Billing Library on the native side, or the
**Digital Goods API** on the web side of a TWA) — more work than option A,
but lets people try the tuner before committing to buy.

**C. Subscription**
Makes more sense once there's a reason for recurring value — e.g. if you
plan to keep adding new lesson weeks, repertoire, or content over time.
Not worth the complexity for a static, finished curriculum.

**Given the app doesn't use ads and processes everything locally** (a real
differentiator worth stating in your listing description), a straightforward
paid app (A) is the easiest to ship first; you can always add a freemium
tier in a later update once you see how people respond.

## 5. A few honest legal/content notes

- All the tunes referenced in the Lessons tab (Twinkle Twinkle, Mary Had a
  Little Lamb, Hot Cross Buns, Lightly Row, Long, Long Ago) are traditional
  folk melodies in the public domain — safe to reference by name.
- All diagrams and icons in the app are original artwork made for this
  project, not sourced from elsewhere — no image licensing to worry about.
- "Violin" and "tuner" are generic terms, fine to use in your app name and
  description; just avoid naming your app something that collides with an
  existing trademarked app name when you pick a final title.

## 6. Positioning / ASO (App Store Optimization)

- **Title ideas:** "StringWise: Learn Violin", "StringWise — Violin Tuner
  & Lessons"
- **Keywords to work into your description:** violin tuner, learn violin,
  violin for beginners, violin finger placement, violin lessons app,
  violin practice
- **Your real differentiator** versus generic tuner apps: this isn't just a
  tuner — it's a tuner *plus* a live intonation checker tied to actual
  finger positions, *plus* a structured week-by-week course. Lead with that
  combination in your description and first screenshot rather than the
  tuner alone, since tuner apps are a crowded category on their own.

---

### Suggested order of operations

1. Host the `stringwise-app` folder (GitHub Pages/Netlify) → test via "Add to
   Home Screen" on your phone.
2. Run it through PWABuilder → get a working APK, sideload it and try it as
   a real installed app.
3. Fill in and host `PRIVACY_POLICY.md`.
4. Register the Play Console account (start this early — verification takes
   time).
5. Prepare store listing assets (screenshots, feature graphic, description).
6. Decide pricing (start with option A — one-time paid — for simplicity).
7. Run the required closed test, then submit for production review.
