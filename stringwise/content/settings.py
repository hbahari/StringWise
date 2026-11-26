"""Text and links for the Settings screen."""

SUPPORT_EMAIL = "golemapps1@gmail.com"
PACKAGE = "golemapps.stringwise.app"
STORE_APP_LINK = f"market://details?id={PACKAGE}"
STORE_WEB_LINK = f"https://play.google.com/store/apps/details?id={PACKAGE}"
PRIVACY_LINK = "https://github.com/hbahari/StringWise/blob/main/PRIVACY_POLICY.md"

# The number App Store Connect shows as "Apple ID" once the iOS app has been created
# there. Until it is filled in, the iPhone app hides Rate and Share, because there is
# no App Store page to point to yet.
APP_STORE_ID = ""

PITCH_TITLE = "Tuning pitch"
PITCH_TEXT = ("The note A that everything is tuned to. Leave it at 440 unless your teacher or "
              "orchestra tunes higher. It changes the tuner, the finger check, Play-Along and "
              "every note the app plays.")

FEEDBACK_TITLE = "Feedback and sharing"
FEEDBACK_TEXT = ("Found a problem or have an idea? Send an email and it goes straight to the "
                 "developer. Your app version and phone model are added so problems are easier "
                 "to track down.")
FEEDBACK_SUBJECT = "StringWise feedback"
FEEDBACK_BODY = "\n\n\n---\nStringWise {version}\n{device}\n"
SHARE_SUBJECT = "StringWise"
SHARE_INTRO = ("I'm learning violin with StringWise. It has weekly lessons, a tuner and sheet "
               "music that listens as you play: ")
SHARE_MESSAGE = SHARE_INTRO + STORE_WEB_LINK
SHARE_COPIED = "The link has been copied, ready to paste."
SHARE_FAILED = "Sharing isn't available on this device. The link is " + STORE_WEB_LINK
TOUR_BUTTON = "Show the app tour again"
NO_EMAIL_APP = "No email app was found. You can write to " + SUPPORT_EMAIL + " from any device."
NO_BROWSER = "That link could not be opened on this device."

SCREEN_TITLE = "Screen"
SCREEN_ON = "Keep the screen on"
SCREEN_HINT = "Uses more battery."

PROGRESS_TITLE = "Progress"
PROGRESS_TEXT = ("Clears your lesson ticks, completed weeks, saved tempos and finished rhythms, "
                 "and goes back to week 1. Your settings are kept.")
RESET_CONFIRM_TITLE = "Reset all progress?"
RESET_CONFIRM = ("This clears every tick, completed week, saved tempo and finished rhythm. "
                 "It cannot be undone.")
RESET_DONE = "Progress cleared. You are back at week 1."

ABOUT_TITLE = "About"
ABOUT_TEXT = ("StringWise works offline and needs no account. Sound from the microphone is "
              "analysed on this phone and never leaves it.")


def store_for(ios: bool):
    """Where Rate and Share point on this platform, or None if there is no store page yet."""
    if not ios:
        return {"rate_label": "Rate StringWise on Google Play", "rate": STORE_APP_LINK,
                "rate_fallback": STORE_WEB_LINK, "web": STORE_WEB_LINK}
    if not APP_STORE_ID:
        return None
    web = f"https://apps.apple.com/app/id{APP_STORE_ID}"
    return {"rate_label": "Rate StringWise on the App Store",
            "rate": f"itms-apps://apps.apple.com/app/id{APP_STORE_ID}?action=write-review",
            "rate_fallback": web + "?action=write-review", "web": web}


def share_message(store) -> str:
    return SHARE_INTRO + store["web"]


def share_failed(store) -> str:
    return "Sharing isn't available on this device. The link is " + store["web"]
