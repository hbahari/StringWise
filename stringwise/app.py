"""The application shell: title bar, screens and the bottom navigation."""

from __future__ import annotations

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import NoTransition, ScreenManager
from kivy.uix.widget import Widget

from . import theme
from .audio.listener import PitchListener
from .audio.metronome import Metronome
from .audio.tone import TonePlayer
from .storage import ProgressStore
from .theme import rgba
from .ui import platform

TABS = (("tuner", "Tuner"), ("metronome", "Metro"), ("lessons", "Lessons"),
        ("fingers", "Fingers"), ("theory", "Theory"), ("practice", "Practice"))
SUB_SCREENS = {"playalong": "lessons", "take": "lessons"}     # screens opened from a tab
STORE_SETTINGS = "settings"


def _cache_folder(user_data_dir: str) -> str:
    """Where generated sound files go. They can always be made again.

    On iOS that must be Library/Caches: Apple asks that files which can be
    recreated stay out of Documents, which is backed up to iCloud.
    """
    if platform.IS_IOS:
        import os
        folder = os.path.expanduser("~/Library/Caches/stringwise")
        try:
            os.makedirs(folder, exist_ok=True)
            return folder
        except OSError:
            pass
    return user_data_dir


def _output_delay() -> float:
    """Rough time from starting a sound to hearing it, used to line up the beat dots."""
    if platform.IS_ANDROID:
        return 0.10
    if platform.IS_IOS:
        return 0.04     # a guess until it is measured on an iPhone
    return 0.03


class NavButton(ButtonBehavior, Label):
    def __init__(self, text, **kwargs):
        super().__init__(text=text, font_size=sp(12.5), bold=True, **kwargs)
        self.active = False
        with self.canvas.before:
            self._bar_color = Color(0, 0, 0, 0)
            self._bar = Rectangle()
        self.bind(pos=self._redraw, size=self._redraw)
        self.set_active(False)

    def set_active(self, active):
        self.active = active
        self.color = rgba(theme.CREAM if active else theme.ON_WOOD_SOFT, 1.0 if active else 0.75)
        self._bar_color.rgba = rgba(theme.VARNISH) if active else (0, 0, 0, 0)

    def _redraw(self, *_):
        self._bar.pos = (self.x + dp(10), self.top - dp(3))
        self._bar.size = (self.width - dp(20), dp(3))


class GearButton(ButtonBehavior, Widget):
    """A small cog drawn on the canvas. Opens Settings."""

    def __init__(self, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(34), dp(34)), pos_hint={"center_y": 0.5}, **kwargs)
        self.active = False
        self.bind(pos=self._draw, size=self._draw, state=self._draw)

    def _draw(self, *_):
        import math
        self.canvas.clear()
        cx, cy = self.x + self.width / 2, self.y + self.height / 2
        outer, inner, hole = dp(9.5), dp(7.2), dp(2.8)
        alpha = 1.0 if (self.active or self.state == "down") else 0.62
        points = []
        for i in range(8 * 4):
            angle = math.pi * 2 * i / 32
            radius = outer if (i % 4) in (0, 1) else inner     # eight teeth
            points += [cx + radius * math.cos(angle), cy + radius * math.sin(angle)]
        with self.canvas:
            Color(*rgba(theme.CREAM, alpha))
            Line(points=points, close=True, width=dp(1.3), joint="round")
            Line(circle=(cx, cy, hole), width=dp(1.3))


class HeaderMetronome(BoxLayout):
    """Beat dots and a pause/resume button in the title bar.

    It appears the first time the metronome is started and then stays, so the
    click can be paused and picked up again at the same tempo from any tab.
    """

    def __init__(self, metronome, **kwargs):
        super().__init__(orientation="horizontal", size_hint=(None, None), size=(dp(178), dp(36)),
                         spacing=dp(4), pos_hint={"center_y": 0.5}, **kwargs)
        from .ui.metronome_bar import BeatDots
        self.metronome = metronome
        self.dots = BeatDots(dark=True, gap=17, size=4.6, size_hint=(None, 1), width=dp(74))
        self.button = _HeaderButton(size_hint=(None, 1), width=dp(100))
        self.button.bind(on_release=lambda *_: metronome.toggle())
        self.add_widget(self.dots)
        self.add_widget(self.button)
        metronome.watch(self)
        self.sync()

    def sync(self):
        metronome = self.metronome
        self.opacity = 1.0 if metronome.used else 0.0
        self.disabled = not metronome.used
        self.button.show(f"{'Pause' if metronome.running else 'Resume'} {metronome.bpm}", metronome.running)
        if not metronome.running:
            self.dots.show(None)

    def tick(self, state):
        self.dots.show(state)


class _HeaderButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super().__init__(font_size=sp(13), bold=True, **kwargs)
        with self.canvas.before:
            self._fill_color = Color(0, 0, 0, 0)
            self._fill = RoundedRectangle(radius=[dp(18)])
            self._line_color = Color(0, 0, 0, 0)
            self._line = Line(width=1.2)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self._fill.pos, self._fill.size = self.pos, self.size
        self._line.rounded_rectangle = (*self.pos, *self.size, dp(18))

    def show(self, text, running):
        self.text = text
        # Pause is the warm varnish colour; Resume is pale, so the two states are easy to tell apart.
        self.color = self.disabled_color = rgba(theme.PAPER if running else theme.WOOD)
        self._fill_color.rgba = rgba(theme.VARNISH if running else theme.CREAM)
        self._line_color.rgba = (0, 0, 0, 0)


class Shell(BoxLayout):
    """Title bar on top, the current screen in the middle, tabs at the bottom."""

    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        with self.canvas.before:
            Color(*rgba(theme.WOOD))
            self._backdrop = Rectangle()
        self.bind(pos=self._redraw, size=self._redraw)

        header = BoxLayout(size_hint_y=None, height=dp(52), padding=(0, 0, dp(6), 0), spacing=dp(2))
        name = Label(text="StringWise", font_name=theme.FONT_HEAD, font_size=sp(23),
                     color=rgba(theme.CREAM), halign="left", valign="middle", padding=(dp(14), 0))
        name.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        header.add_widget(name)
        self.header_metronome = HeaderMetronome(app.metronome)
        header.add_widget(self.header_metronome)
        self.gear = GearButton()
        self.gear.bind(on_release=lambda *_: app.open_settings())
        header.add_widget(self.gear)
        self.add_widget(header)

        self.manager = ScreenManager(transition=NoTransition())
        with self.manager.canvas.before:
            Color(*rgba(theme.PARCHMENT))
            self._paper = Rectangle()
        self.manager.bind(pos=self._redraw, size=self._redraw)
        self.add_widget(self.manager)

        nav = BoxLayout(size_hint_y=None, height=dp(54))
        self.nav_buttons = {}
        for name, label in TABS:
            button = NavButton(label)
            button.bind(on_release=lambda _b, name=name: app.go_to(name))
            self.nav_buttons[name] = button
            nav.add_widget(button)
        self.add_widget(nav)

    def _redraw(self, *_):
        self._backdrop.pos, self._backdrop.size = self.pos, self.size
        self._paper.pos, self._paper.size = self.manager.pos, self.manager.size

    def highlight(self, name):
        tab = SUB_SCREENS.get(name, name)
        self.gear.active = name == "settings"
        self.gear._draw()
        for key, button in self.nav_buttons.items():
            button.set_active(key == tab)


class StringWiseApp(App):
    title = "StringWise"
    icon = theme.asset("images", "icon.png")

    def build(self):
        from .ui.screens.fingers import FingersScreen
        from .ui.screens.lessons import LessonsScreen
        from .ui.screens.metronome import MetronomeScreen
        from .ui.screens.settings import SettingsScreen
        from .ui.screens.take import TakeScreen
        from .ui.screens.playalong import PlayAlongScreen
        from .ui.screens.practice import PracticeScreen
        from .ui.screens.theory import TheoryScreen
        from .ui.screens.tuner import TunerScreen

        Window.clearcolor = rgba(theme.WOOD)
        self.store = ProgressStore(self.user_data_dir)
        self.cache_dir = _cache_folder(self.user_data_dir)
        from .music import notes
        notes.set_reference(self.store.get(STORE_SETTINGS, {}).get("reference", 440))
        platform.keep_screen_on(self.store.get(STORE_SETTINGS, {}).get("keep_awake", False), "setting")
        self._back_to = "tuner"
        self.listener = PitchListener()
        self.tones = TonePlayer(self.cache_dir)
        self.metronome = Metronome(self.cache_dir, output_delay=_output_delay())

        self.shell = Shell(self)
        for screen_class in (TunerScreen, MetronomeScreen, LessonsScreen, PlayAlongScreen,
                             TakeScreen, FingersScreen, TheoryScreen, PracticeScreen, SettingsScreen):
            self.shell.manager.add_widget(screen_class())
        self.go_to("tuner")

        Window.bind(on_keyboard=self._on_key, on_resize=lambda *_: self._apply_safe_area())
        Clock.schedule_once(lambda _dt: self._apply_safe_area(), 0.5)
        self.tour = None
        if not self.store.get("tour", {}).get("done"):
            Clock.schedule_once(lambda _dt: self.start_tour(), 0.9)      # first launch only
        return self.shell

    # -- tour --------------------------------------------------------------------
    def start_tour(self):
        if self.tour is not None:
            return
        from .ui.tour import Tour
        current = self.shell.manager.current
        screen = self.shell.manager.current_screen
        if hasattr(screen, "stop_listening"):
            screen.stop_listening()

        def finished(completed):
            self.tour = None
            if not completed:
                self.go_to(current)          # skipped: back to where the tour started

        self.tour = Tour(self, on_finish=finished)
        self.tour.start()

    # -- navigation ----------------------------------------------------------
    def go_to(self, name):
        if name != self.shell.manager.current:
            self.tones.stop()        # the metronome is left running on purpose
        self.shell.manager.current = name
        self.shell.highlight(name)

    def open_settings(self):
        current = self.shell.manager.current
        if current == "settings":
            self.go_to(self._back_to)          # the gear works as a toggle
            return
        self._back_to = current
        self.go_to("settings")

    def close_settings(self):
        self.go_to(self._back_to)

    # -- settings that affect other screens ------------------------------------
    def set_reference(self, hz):
        from .music import notes
        notes.set_reference(hz)
        settings = dict(self.store.get(STORE_SETTINGS, {}))
        settings["reference"] = int(notes.A4_HZ)
        self.store.set(STORE_SETTINGS, settings)
        self.tones.stop()
        for screen in self.shell.manager.screens:
            if hasattr(screen, "reference_changed"):
                screen.reference_changed()

    def set_keep_awake(self, on):
        settings = dict(self.store.get(STORE_SETTINGS, {}))
        settings["keep_awake"] = bool(on)
        self.store.set(STORE_SETTINGS, settings)
        platform.keep_screen_on(bool(on), "setting")

    @property
    def keep_awake(self):
        return bool(self.store.get(STORE_SETTINGS, {}).get("keep_awake", False))

    def reset_progress(self):
        for key in ("lessons", "practice", "tempo_best", "rhythms_done"):
            self.store.set(key, {} if key in ("lessons", "practice", "tempo_best") else [])
        for screen in self.shell.manager.screens:
            if hasattr(screen, "progress_reset"):
                screen.progress_reset()

    def open_play_along(self, piece_id):
        self.shell.manager.get_screen("playalong").select(piece_id)
        self.go_to("playalong")

    def open_take(self, week):
        self.shell.manager.get_screen("take").select_week(week)
        self.go_to("take")

    def _on_key(self, _window, key, *_):
        if key == 27 and self.tour is not None:                        # back closes the tour
            self.tour.finish(False)
            return True
        if key == 27 and self.shell.manager.current == "settings":     # Android back button
            self.close_settings()
            return True
        if key == 27 and self.shell.manager.current in SUB_SCREENS:
            self.go_to(SUB_SCREENS[self.shell.manager.current])
            return True
        return False

    def _apply_safe_area(self):
        top, bottom = platform.safe_area()
        self.shell.padding = (0, top, 0, bottom)

    # -- lifecycle -----------------------------------------------------------
    def _stop_audio(self):
        screen = self.shell.manager.current_screen
        if hasattr(screen, "stop_listening"):
            screen.stop_listening()
        self.listener.stop()
        self.tones.stop()
        self.metronome.stop()

    def on_pause(self):
        self._stop_audio()      # give the microphone back when the app is in the background
        return True

    def on_resume(self):
        # Android can drop the window flag while the app is in the background.
        platform.keep_screen_on(self.keep_awake, "setting")

    def on_stop(self):
        self._stop_audio()
