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
