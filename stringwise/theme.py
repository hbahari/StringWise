"""Colours, fonts and sizes shared by every screen."""

from __future__ import annotations

import os

from kivy.utils import get_color_from_hex

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def asset(*parts: str) -> str:
    return os.path.join(ASSETS, *parts)


def rgba(value, alpha: float | None = None):
    """Accept '#rrggbb' or an existing colour tuple."""
    color = list(get_color_from_hex(value)) if isinstance(value, str) else list(value)
    if alpha is not None:
        color[3] = alpha
    return color


# Palette: varnished wood, old sheet music.
WOOD = "#2b1810"
WOOD_DEEP = "#1f130c"
WOOD_LINE = "#4a2c1a"
PARCHMENT = "#efe4cd"
PAPER = "#f8f1e0"
PAPER_LINE = "#d9c9a6"
INK = "#2b2016"
INK_SOFT = "#6b5c45"
VARNISH = "#a8542e"
VARNISH_DARK = "#8a4322"
CREAM = "#e8dcc0"
ON_WOOD_SOFT = "#c9b89a"

GOOD = "#4a7c4e"          # on paper
GOOD_LIGHT = "#8fbf8a"    # on wood
WARN = "#c98a4e"
WARN_LIGHT = "#e8c98a"
BAD = "#a8422e"
BAD_LIGHT = "#c96a52"

# Finger colours are the same everywhere a finger is shown. Index 0 is the open string.
FINGER_COLORS = ("#efe4cd", "#a8542e", "#3a6ea8", "#8b5a9e", "#b8912f")
STRING_COLORS = {"G": "#b98a4a", "D": "#9a8a68", "A": "#7f9aa6", "E": "#b5ba95"}

FONT_HEAD = asset("fonts", "CrimsonText-SemiBold.ttf")
FONT_BODY = "Roboto"
FONT_SYMBOL = "data/fonts/DejaVuSans.ttf"   # ships with Kivy; has the music symbols

# Characters the body font lacks, drawn with the symbol font instead.
SYMBOLS = "♯♭♮♩✓"

TEXT_BODY = 15
TEXT_SMALL = 13
TEXT_TITLE = 26
TEXT_SUBTITLE = 19
