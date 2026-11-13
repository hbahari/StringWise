from __future__ import annotations

from ...content import metronome as text
from ..metronome_bar import MetronomeBar
from ..widgets import card, title_with_help
from .base import PageScreen


class MetronomeScreen(PageScreen):
    def __init__(self, **kwargs):
        super().__init__(name="metronome", **kwargs)
        page = self.page
        page.add(title_with_help("Metronome", text.HOW_TITLE, text.HOW))
        panel = page.add(card())
        panel.add_widget(MetronomeBar(presets=(60, 72, 84, 96, 108, 120)))
