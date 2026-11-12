"""The application shell: title bar, screens and the bottom navigation."""

from __future__ import annotations

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import NoTransition, ScreenManager

from . import theme
from .audio.listener import PitchListener
from .audio.tone import TonePlayer
from .storage import ProgressStore
from .theme import rgba
from .ui import platform

TABS = (("tuner", "Tuner"), ("lessons", "Lessons"), ("fingers", "Fingers"),
        ("theory", "Theory"), ("practice", "Practice"))


class NavButton(ButtonBehavior, Label):
    def __init__(self, text, **kwargs):
        super().__init__(text=text, font_size=sp(13), bold=True, **kwargs)
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


class Shell(BoxLayout):
    """Title bar on top, the current screen in the middle, tabs at the bottom."""

    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        with self.canvas.before:
            Color(*rgba(theme.WOOD))
            self._backdrop = Rectangle()
        self.bind(pos=self._redraw, size=self._redraw)

        header = Label(text="StringWise", font_name=theme.FONT_HEAD, font_size=sp(23),
                       color=rgba(theme.CREAM), size_hint_y=None, height=dp(52),
                       halign="left", valign="middle", padding=(dp(18), 0))
        header.bind(size=lambda widget, size: setattr(widget, "text_size", size))
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
        tab = "lessons" if name == "playalong" else name
        for key, button in self.nav_buttons.items():
            button.set_active(key == tab)


class StringWiseApp(App):
    title = "StringWise"
    icon = theme.asset("images", "icon.png")

    def build(self):
        from .ui.screens.fingers import FingersScreen
        from .ui.screens.lessons import LessonsScreen
        from .ui.screens.playalong import PlayAlongScreen
        from .ui.screens.practice import PracticeScreen
        from .ui.screens.theory import TheoryScreen
        from .ui.screens.tuner import TunerScreen

        Window.clearcolor = rgba(theme.WOOD)
        self.store = ProgressStore(self.user_data_dir)
        self.listener = PitchListener()
        self.tones = TonePlayer(self.user_data_dir)

        self.shell = Shell(self)
        for screen_class in (TunerScreen, LessonsScreen, PlayAlongScreen, FingersScreen,
                             TheoryScreen, PracticeScreen):
            self.shell.manager.add_widget(screen_class())
        self.go_to("tuner")

        Window.bind(on_keyboard=self._on_key, on_resize=lambda *_: self._apply_safe_area())
        Clock.schedule_once(lambda _dt: self._apply_safe_area(), 0.5)
        return self.shell

    # -- navigation ----------------------------------------------------------
    def go_to(self, name):
        self.shell.manager.current = name
        self.shell.highlight(name)

    def open_play_along(self, piece_id):
        self.shell.manager.get_screen("playalong").select(piece_id)
        self.go_to("playalong")

    def _on_key(self, _window, key, *_):
        if key == 27 and self.shell.manager.current == "playalong":    # Android back button
            self.go_to("lessons")
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

    def on_pause(self):
        self._stop_audio()      # give the microphone back when the app is in the background
        return True

    def on_stop(self):
        self._stop_audio()
