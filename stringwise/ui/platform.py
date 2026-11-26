"""The few things that differ between Android, iOS and a desktop.

The iOS branches use pyobjus (bundled with kivy-ios) and the small ``ios`` module
kivy-ios ships, plus our own ``swmic`` recipe for the microphone. None of them can
run outside an iPhone build, so every call is wrapped and falls back quietly.
"""

from __future__ import annotations

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

IS_ANDROID = platform == "android"
IS_IOS = platform == "ios"


def request_microphone(callback) -> None:
    """Call ``callback(True or False)`` once we know whether we may record."""
    if IS_IOS:
        _request_microphone_ios(callback)
        return
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


def _request_microphone_ios(callback) -> None:
    """iOS asks once with its own dialog; after that the answer lives in Settings."""
    try:
        import swmic
        state = swmic.permission()
    except Exception:
        callback(True)      # the microphone itself will report what is missing
        return
    if state != "unknown":
        callback(state == "granted")
        return
    swmic.request_permission()

    # The answer arrives on another thread, so check for it from the Kivy clock.
    def check(_dt):
        answer = swmic.permission()
        if answer == "unknown":
            return True
        callback(answer == "granted")
        return False

    Clock.schedule_interval(check, 0.25)


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
            elif IS_IOS:
                import ios
                ios.open_url(target)
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
        elif IS_IOS:
            from urllib.parse import quote
            # Mail (or whichever app the user picked for email) opens with this filled in.
            import ios
            ios.open_url(f"mailto:{address}?subject={quote(subject)}&body={quote(body)}")
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
        if IS_IOS:
            return "shared" if _share_ios(message) else "failed"
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(message)
        return "copied"
    except Exception:
        return "failed"


def _share_ios(message: str) -> bool:
    """Show the iOS share sheet over the app."""
    try:
        from pyobjus import autoclass, objc_str
        UIApplication = autoclass("UIApplication")
        NSArray = autoclass("NSArray")
        sheet = autoclass("UIActivityViewController").alloc().initWithActivityItems_applicationActivities_(
            NSArray.arrayWithObject_(objc_str(message)), None)
        controller = _ios_top_controller(UIApplication)
        if controller is None:
            return False
        # On an iPad the sheet is a popover and must be anchored, or iOS stops the app.
        popover = _objc_get(sheet, "popoverPresentationController")
        if popover is not None:
            popover.sourceView = _objc_get(controller, "view")
        controller.presentViewController_animated_completion_(sheet, True, None)
        return True
    except Exception:
        return False


def _ios_top_controller(UIApplication):
    """The view controller currently on screen, to present the share sheet from."""
    window = _objc_get(UIApplication.sharedApplication(), "keyWindow")
    if window is None:
        return None
    controller = _objc_get(window, "rootViewController")
    while controller is not None:
        shown = _objc_get(controller, "presentedViewController")
        if shown is None:
            break
        controller = shown
    return controller


def _objc_get(obj, name):
    """Read an Objective-C property. pyobjus offers some as attributes, some as methods."""
    value = getattr(obj, name)
    return value() if callable(value) else value


def device_summary() -> str:
    """Phone model and system version, for feedback emails."""
    if IS_IOS:
        try:
            from pyobjus import autoclass
            device = autoclass("UIDevice").currentDevice()
            return f"{_ios_model()}, {device.systemName().UTF8String()} {device.systemVersion().UTF8String()}"
        except Exception:
            return "iOS"
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


def _ios_model() -> str:
    """The hardware name, such as iPhone15,2. UIDevice only says "iPhone"."""
    try:
        import os
        return os.uname().machine
    except Exception:
        return "iPhone"


_awake_reasons: set[str] = set()


def keep_screen_on(on: bool, reason: str = "listening") -> None:
    """Ask for the screen to stay on (or let it sleep again) for one reason.

    Reasons are tracked separately: "listening" while the microphone is in use and
    "setting" for the Keep screen on option. The screen may sleep only when no
    reason is left, so stopping the tuner never undoes the user's setting.
    """
    if on:
        _awake_reasons.add(reason)
    else:
        _awake_reasons.discard(reason)
    _apply_awake(bool(_awake_reasons))


def screen_kept_on() -> bool:
    return bool(_awake_reasons)


def _apply_awake(awake: bool) -> None:
    try:
        Window.allow_screensaver = not awake
    except Exception:
        pass
    if IS_IOS:
        try:
            from pyobjus import autoclass
            autoclass("UIApplication").sharedApplication().setIdleTimerDisabled_(awake)
        except Exception:
            pass
        return
    if not IS_ANDROID:
        return
    try:
        # The window flag is what Android checks. It must be changed on the UI thread.
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        @run_on_ui_thread
        def set_flag():
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            flag = autoclass("android.view.WindowManager$LayoutParams").FLAG_KEEP_SCREEN_ON
            window = activity.getWindow()
            if awake:
                window.addFlags(flag)
            else:
                window.clearFlags(flag)

        set_flag()
    except Exception:
        pass


def safe_area() -> tuple[float, float]:
    """(top, bottom) space in pixels taken by the status and navigation bars.

    Recent Android versions draw apps edge to edge. If Kivy's window covers the
    whole screen we pad the layout so nothing hides under the system bars. On an
    iPhone the same space is the notch or Dynamic Island and the home bar.
    """
    if IS_IOS:
        try:
            import ios
            area = ios.get_safe_area()      # in points; Kivy's window is in pixels
            scale = ios.get_scale()
            return float(area["top"]) * scale, float(area["bottom"]) * scale
        except Exception:
            return 0.0, 0.0
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
