"""Settings: tuning pitch, feedback, progress reset and about. Opened from the gear."""

from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.modalview import ModalView

from ... import __version__, theme
from ...content import settings as text
from ...music import notes
from .. import platform
from ..widgets import Box, Btn, Chip, Txt, card, row, small, subtitle, title
from .base import PageScreen


class SettingsScreen(PageScreen):
    def __init__(self, **kwargs):
        super().__init__(name="settings", **kwargs)
        page = self.page
        page.add(Btn("Back", kind="outline", height=dp(40), size_hint_x=None, width=dp(110),
                     on_release=lambda _b: self.app.close_settings()))
        page.add(title("Settings"))

        panel = page.add(card(spacing=dp(10)))
        panel.add_widget(subtitle(text.PITCH_TITLE))
        panel.add_widget(small(text.PITCH_TEXT))
        self.pitch_chips = {}
        chips = row(height=44, spacing=8)
        for hz in notes.REFERENCE_CHOICES:
            chip = Chip(f"A = {hz}", height=dp(44))
            chip.bind(on_release=lambda _c, hz=hz: self._set_pitch(hz))
            self.pitch_chips[hz] = chip
            chips.add_widget(chip)
        panel.add_widget(chips)

        panel = page.add(card(spacing=dp(10)))
        panel.add_widget(subtitle(text.FEEDBACK_TITLE))
        panel.add_widget(small(text.FEEDBACK_TEXT))
        panel.add_widget(Btn("Send feedback", on_release=self._feedback))
        panel.add_widget(Btn("Rate StringWise on Google Play", kind="outline", on_release=self._rate))
        panel.add_widget(Btn("Share StringWise", kind="outline", on_release=self._share))
        self.notice = small("", color=theme.VARNISH_DARK)
        panel.add_widget(self.notice)

        panel = page.add(card(spacing=dp(10)))
        panel.add_widget(subtitle(text.PROGRESS_TITLE))
        panel.add_widget(small(text.PROGRESS_TEXT))
        panel.add_widget(Btn("Reset progress", kind="outline", on_release=self._confirm_reset))
        self.reset_notice = small("", color=theme.GOOD)
        panel.add_widget(self.reset_notice)

        panel = page.add(card(spacing=dp(8)))
        panel.add_widget(subtitle(text.ABOUT_TITLE))
        panel.add_widget(Txt(f"StringWise {__version__}"))
        panel.add_widget(small(text.ABOUT_TEXT))
        panel.add_widget(small(f"Contact: {text.SUPPORT_EMAIL}"))
        panel.add_widget(Btn(text.TOUR_BUTTON, kind="outline", height=dp(44),
                             on_release=lambda _b: self.app.start_tour()))
        panel.add_widget(Btn("Privacy policy", kind="outline", height=dp(44), on_release=self._privacy))
        self._show_pitch()

    def on_pre_enter(self, *_):
        self.notice.set("")
        self.reset_notice.set("")
        self.page.scroll_y = 1

    # -- tuning pitch -----------------------------------------------------------
    def _set_pitch(self, hz):
        self.app.set_reference(hz)
        self._show_pitch()

    def _show_pitch(self):
        for hz, chip in self.pitch_chips.items():
            chip.selected = hz == int(notes.A4_HZ)

    # -- links -------------------------------------------------------------------
    def _feedback(self, *_):
        body = text.FEEDBACK_BODY.format(version=__version__, device=platform.device_summary())
        if not platform.send_email(text.SUPPORT_EMAIL, f"{text.FEEDBACK_SUBJECT} ({__version__})", body):
            self.notice.set(text.NO_EMAIL_APP)

    def _rate(self, *_):
        if not platform.open_link(text.STORE_APP_LINK, fallback=text.STORE_WEB_LINK):
            self.notice.set(text.NO_BROWSER)

    def _share(self, *_):
        result = platform.share_text(text.SHARE_SUBJECT, text.SHARE_MESSAGE)
        if result == "copied":
            self.notice.set(text.SHARE_COPIED)
        elif result == "failed":
            self.notice.set(text.SHARE_FAILED)

    def _privacy(self, *_):
        platform.open_link(text.PRIVACY_LINK)

    # -- reset -------------------------------------------------------------------
    def _confirm_reset(self, *_):
        view = ModalView(size_hint=(0.88, None), background="", background_color=(0, 0, 0, 0),
                         overlay_color=(0, 0, 0, 0.55))
        panel = Box(bg=theme.PAPER, border=theme.PAPER_LINE, padding=dp(18), spacing=dp(12))
        panel.add_widget(subtitle(text.RESET_CONFIRM_TITLE))
        panel.add_widget(Txt(text.RESET_CONFIRM))

        def reset(_b):
            view.dismiss()
            self.app.reset_progress()
            self.reset_notice.set(text.RESET_DONE)

        panel.add_widget(row(Btn("Cancel", kind="outline", on_release=lambda _b: view.dismiss()),
                             Btn("Reset", on_release=reset)))
        panel.bind(height=lambda _p, h: setattr(view, "height", h))
        view.add_widget(panel)
        view.open()
