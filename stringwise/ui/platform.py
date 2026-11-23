"""The few things that differ between Android and a desktop."""

from __future__ import annotations

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

IS_ANDROID = platform == "android"


def request_microphone(callback) -> None:
    """Call ``callback(True or False)`` once we know whether we may record."""
    if not IS_ANDROID:
        callback(True)
        return
    try:
        from android.permissions import Permission, check_permission, request_permissions
    except Exception:
        callback(True)
        return
    if check_permission(Permission.RECORD_AUDIO):
        callback(True)
        return

    def answered(_permissions, grants):
        granted = bool(grants) and all(grants)
        Clock.schedule_once(lambda _dt: callback(granted))

    request_permissions([Permission.RECORD_AUDIO], answered)


def open_link(url: str, fallback: str | None = None) -> bool:
    """Open a web page or store link. Returns False if nothing could open it."""
    for target in (url, fallback):
        if not target:
            continue
        try:
            if IS_ANDROID:
                from jnius import autoclass
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(target))
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                autoclass("org.kivy.android.PythonActivity").mActivity.startActivity(intent)
            else:
                import webbrowser
                webbrowser.open(target)
            return True
        except Exception:
            continue
    return False


def send_email(address: str, subject: str, body: str) -> bool:
    """Open the phone's email app with a message ready to send. False if there is none."""
    try:
        if IS_ANDROID:
            from jnius import autoclass, cast
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            String = autoclass("java.lang.String")
            from urllib.parse import quote
            # The address, subject and body go in the mailto link, which every email app
            # reads; the extras repeat them for apps that prefer those.
            link = f"mailto:{address}?subject={quote(subject)}&body={quote(body)}"
            intent = Intent(Intent.ACTION_SENDTO, Uri.parse(link))
            intent.putExtra(Intent.EXTRA_SUBJECT, cast("java.lang.CharSequence", String(subject)))
            intent.putExtra(Intent.EXTRA_TEXT, cast("java.lang.CharSequence", String(body)))
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            autoclass("org.kivy.android.PythonActivity").mActivity.startActivity(intent)
        else:
            import webbrowser
            from urllib.parse import quote
            webbrowser.open(f"mailto:{address}?subject={quote(subject)}&body={quote(body)}")
        return True
    except Exception:
        return False


def share_text(subject: str, message: str) -> str:
    """Open the phone's share sheet. Returns "shared", "copied" (desktop) or "failed"."""
    try:
        if IS_ANDROID:
            from jnius import autoclass, cast
            Intent = autoclass("android.content.Intent")
            String = autoclass("java.lang.String")
            intent = Intent(Intent.ACTION_SEND)
            intent.setType("text/plain")
            intent.putExtra(Intent.EXTRA_SUBJECT, cast("java.lang.CharSequence", String(subject)))
            intent.putExtra(Intent.EXTRA_TEXT, cast("java.lang.CharSequence", String(message)))
            chooser = Intent.createChooser(intent, cast("java.lang.CharSequence", String(subject)))
            chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            autoclass("org.kivy.android.PythonActivity").mActivity.startActivity(chooser)
            return "shared"
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(message)
        return "copied"
    except Exception:
        return "failed"


def device_summary() -> str:
    """Phone model and Android version, for feedback emails."""
    if not IS_ANDROID:
        import platform as host
        return f"{host.system()} {host.release()}"
    try:
        from jnius import autoclass
        Build = autoclass("android.os.Build")
        Version = autoclass("android.os.Build$VERSION")
        return f"{Build.MANUFACTURER} {Build.MODEL}, Android {Version.RELEASE}"
    except Exception:
        return "Android"


def keep_screen_on(on: bool) -> None:
    """Stop the screen dimming while the app is listening."""
    try:
        Window.allow_screensaver = not on
    except Exception:
        pass


def safe_area() -> tuple[float, float]:
    """(top, bottom) space in pixels taken by the status and navigation bars.

    Recent Android versions draw apps edge to edge. If Kivy's window covers the
    whole screen we pad the layout so nothing hides under the system bars.
    """
    if not IS_ANDROID:
        return 0.0, 0.0
    try:
        from jnius import autoclass
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        decor = activity.getWindow().getDecorView()
        insets = decor.getRootWindowInsets()
        if insets is None or Window.height < decor.getHeight() - 2:
            return 0.0, 0.0      # the window already stops short of the bars
        return float(insets.getSystemWindowInsetTop()), float(insets.getSystemWindowInsetBottom())
    except Exception:
        return 0.0, 0.0
