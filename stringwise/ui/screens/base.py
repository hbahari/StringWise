"""Shared behaviour for screens, including the ones that listen to the microphone."""

from __future__ import annotations

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

from ...audio.mic import MicError
from ...audio.pitch import level_fraction
from .. import platform
from ..widgets import Page

MIC_DENIED = ("Microphone access is off. Allow it for StringWise in your phone's "
              "Settings, under Apps, then try again.")


class PageScreen(Screen):
    """A screen whose content is one scrolling page."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.page = Page()
        self.add_widget(self.page)

    @property
    def app(self):
        return App.get_running_app()


class ListeningScreen(PageScreen):
    """Adds a start/stop microphone button and a steady stream of pitch readings.

    Subclasses set ``self.mic_button`` and ``self.level_meter`` and implement
    ``listening_started``, ``listening_stopped``, ``handle_frame`` and ``show_status``.
    """

    mic_button = None
    level_meter = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._poll_event = None

    @property
    def listening(self) -> bool:
        return self._poll_event is not None

    def toggle_listening(self, *_):
        if self.listening:
            self.stop_listening()
        else:
            platform.request_microphone(self._permission_answered)

    def _permission_answered(self, granted: bool):
        if not granted:
            self.show_status(MIC_DENIED)
            return
        if self.manager is None or self.manager.current != self.name:
            return
        try:
            self.app.listener.start()
        except MicError as exc:
            self.show_status(str(exc))
            return
        self.app.tones.stop()
        platform.keep_screen_on(True)
        self.mic_button.set("Stop listening")
        self.listening_started()
        self._poll_event = Clock.schedule_interval(self._poll, 1 / 30)

    def stop_listening(self, *_):
        if not self.listening:
            return
        self._poll_event.cancel()
        self._poll_event = None
        self.app.listener.stop()
        platform.keep_screen_on(False)
        self.mic_button.set("Start listening")
        if self.level_meter is not None:
            self.level_meter.value = 0
        self.listening_stopped()

    def _poll(self, _dt):
        listener = self.app.listener
        frames = listener.poll()
        if listener.error:
            message = listener.error
            self.stop_listening()
            self.show_status(message)
            return
        if not frames:
            return
        for frame in frames:
            self.handle_frame(frame)
        if self.level_meter is not None:
            self.level_meter.value = level_fraction(frames[-1].rms)
        self.refresh()

    def on_leave(self, *_):
        self.stop_listening()

    # -- for subclasses ----------------------------------------------------
    def listening_started(self):
        pass

    def listening_stopped(self):
        pass

    def handle_frame(self, frame):
        pass

    def refresh(self):
        pass

    def show_status(self, text: str):
        pass
