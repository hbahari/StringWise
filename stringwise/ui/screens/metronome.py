from __future__ import annotations

from ... import theme
from ...content import metronome as text
from ..metronome_bar import MetronomeBar
from ..widgets import Txt, bullets, card, subtitle, title
from .base import PageScreen


class MetronomeScreen(PageScreen):
    def __init__(self, **kwargs):
        super().__init__(name="metronome", **kwargs)
        page = self.page
        page.add(title("Metronome"))
        page.add(Txt(text.INTRO, color=theme.INK_SOFT))
        panel = page.add(card())
        panel.add_widget(MetronomeBar(presets=(60, 72, 84, 96, 108, 120)))
        panel = page.add(card())
        panel.add_widget(subtitle(text.HOW_TITLE))
        panel.add_widget(bullets(text.HOW))
