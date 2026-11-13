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


class HeaderMetronome(BoxLayout):
    """Beat dots and a pause/resume button in the title bar.

    It appears the first time the metronome is started and then stays, so the
    click can be paused and picked up again at the same tempo from any tab.
    """

    def __init__(self, metronome, **kwargs):
        super().__init__(orientation="horizontal", size_hint=(None, None), size=(dp(196), dp(36)),
                         spacing=dp(6), pos_hint={"center_y": 0.5}, **kwargs)
        from .ui.metronome_bar import BeatDots
        self.metronome = metronome
        self.dots = BeatDots(dark=True, gap=19, size=5.0, size_hint=(None, 1), width=dp(84))
        self.button = _HeaderButton(size_hint=(None, 1), width=dp(106))
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

        header = BoxLayout(size_hint_y=None, height=dp(52), padding=(0, 0, dp(12), 0))
        name = Label(text="StringWise", font_name=theme.FONT_HEAD, font_size=sp(23),
                     color=rgba(theme.CREAM), halign="left", valign="middle", padding=(dp(18), 0))
        name.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        header.add_widget(name)
        self.header_metronome = HeaderMetronome(app.metronome)
        header.add_widget(self.header_metronome)
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
        for key, button in self.nav_buttons.items():
            button.set_active(key == tab)


class StringWiseApp(App):
    title = "StringWise"
    icon = theme.asset("images", "icon.png")

    def build(self):
        from .ui.screens.fingers import FingersScreen
        from .ui.screens.lessons import LessonsScreen
        from .ui.screens.metronome import MetronomeScreen
        from .ui.screens.take import TakeScreen
        from .ui.screens.playalong import PlayAlongScreen
        from .ui.screens.practice import PracticeScreen
        from .ui.screens.theory import TheoryScreen
        from .ui.screens.tuner import TunerScreen

        Window.clearcolor = rgba(theme.WOOD)
        self.store = ProgressStore(self.user_data_dir)
        self.listener = PitchListener()
        self.tones = TonePlayer(self.user_data_dir)
        self.metronome = Metronome(self.user_data_dir, output_delay=0.10 if platform.IS_ANDROID else 0.03)

        self.shell = Shell(self)
        for screen_class in (TunerScreen, MetronomeScreen, LessonsScreen, PlayAlongScreen,
                             TakeScreen, FingersScreen, TheoryScreen, PracticeScreen):
            self.shell.manager.add_widget(screen_class())
        self.go_to("tuner")

        Window.bind(on_keyboard=self._on_key, on_resize=lambda *_: self._apply_safe_area())
        Clock.schedule_once(lambda _dt: self._apply_safe_area(), 0.5)
        return self.shell

    # -- navigation ----------------------------------------------------------
    def go_to(self, name):
        if name != self.shell.manager.current:
            self.tones.stop()        # the metronome is left running on purpose
        self.shell.manager.current = name
        self.shell.highlight(name)

    def open_play_along(self, piece_id):
        self.shell.manager.get_screen("playalong").select(piece_id)
        self.go_to("playalong")

    def open_take(self, week):
        self.shell.manager.get_screen("take").select_week(week)
        self.go_to("take")

    def _on_key(self, _window, key, *_):
        if key == 27 and self.shell.manager.current in SUB_SCREENS:    # Android back button
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

    def on_stop(self):
        self._stop_audio()
