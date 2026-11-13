"""Small building blocks used by every screen."""

from __future__ import annotations

from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import escape_markup

from .. import theme
from ..theme import rgba


def rich(text: str) -> str:
    """Escape Kivy markup and switch font for the few symbols the body font lacks."""
    out = escape_markup(text)
    for symbol in theme.SYMBOLS:
        if symbol in out:
            out = out.replace(symbol, f"[font={theme.FONT_SYMBOL}]{symbol}[/font]")
    return out


def bold(text: str) -> str:
    return f"[b]{rich(text)}[/b]"


# -- text ------------------------------------------------------------------
class Txt(Label):
    """A label that wraps to its width and grows to fit its text."""

    def __init__(self, text="", size=theme.TEXT_BODY, color=theme.INK, font=None,
                 halign="left", is_markup=False, **kwargs):
        super().__init__(
            text=text if is_markup else rich(text), markup=True, font_size=sp(size),
            color=rgba(color), halign=halign, valign="top", size_hint_y=None,
            line_height=1.22, **kwargs)
        if font:
            self.font_name = font
        self.bind(width=self._wrap, texture_size=self._fit)

    def _wrap(self, *_):
        self.text_size = (self.width, None)

    def _fit(self, *_):
        self.height = self.texture_size[1]

    def set(self, text: str, color=None) -> None:
        self.text = rich(text)
        if color is not None:
            self.color = rgba(color)


def title(text, color=theme.INK):
    return Txt(text, size=theme.TEXT_TITLE, font=theme.FONT_HEAD, color=color)


def title_with_help(text, help_heading, help_items):
    """A page title with a Help button on the right that opens a pop-up."""
    line = BoxLayout(orientation="horizontal", size_hint_y=None, spacing=dp(10))
    heading = title(text)
    heading.bind(height=lambda _w, h: setattr(line, "height", max(h, dp(38))))
    button = Btn("Help", kind="outline", size_hint=(None, None), size=(dp(78), dp(36)),
                 pos_hint={"center_y": 0.5},
                 on_release=lambda _b: show_help(help_heading, help_items))
    line.add_widget(heading)
    line.add_widget(button)
    return line


def show_help(heading, items):
    """Open a pop-up with a heading, a list of points and a Close button."""
    from kivy.core.window import Window
    from kivy.uix.modalview import ModalView

    view = ModalView(size_hint=(0.9, None), background="", background_color=(0, 0, 0, 0),
                     overlay_color=(0, 0, 0, 0.55))
    panel = Box(bg=theme.PAPER, border=theme.PAPER_LINE, padding=dp(18), spacing=dp(12))
    panel.add_widget(subtitle(heading))
    scroller = ScrollView(do_scroll_x=False, size_hint_y=None, bar_width=dp(3))
    listing = bullets(items)
    scroller.add_widget(listing)
    panel.add_widget(scroller)
    panel.add_widget(Btn("Close", on_release=lambda _b: view.dismiss()))

    def fit(*_):
        scroller.height = min(listing.height, Window.height * 0.82 - dp(150))
        view.height = panel.height

    listing.bind(height=fit)
    panel.bind(height=fit)
    view.add_widget(panel)
    view.open()
    return view


def subtitle(text, color=theme.INK):
    return Txt(text, size=theme.TEXT_SUBTITLE, font=theme.FONT_HEAD, color=color)


def small(text, color=theme.INK_SOFT, **kwargs):
    return Txt(text, size=theme.TEXT_SMALL, color=color, **kwargs)


def bullets(items, color=theme.INK):
    box = Box(spacing=dp(6))
    for item in items:
        row = BoxLayout(orientation="horizontal", size_hint_y=None, spacing=dp(8))
        dot = Label(text="•", font_size=sp(theme.TEXT_BODY), color=rgba(theme.VARNISH),
                    size_hint=(None, None), size=(dp(10), dp(20)), pos_hint={"top": 1})
        label = Txt(item, color=color)
        label.bind(height=lambda _w, h, row=row: setattr(row, "height", h))
        row.add_widget(dot)
        row.add_widget(label)
        box.add_widget(row)
    return box


# -- containers ------------------------------------------------------------
class Box(BoxLayout):
    """A vertical stack that is exactly as tall as its children.

    Give it ``bg`` for a filled, rounded panel and ``border`` for an outline.
    """

    def __init__(self, bg=None, border=None, radius=10, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", dp(10))
        super().__init__(size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter("height"))
        self._radius = dp(radius)
        self._bg_rect = self._border_line = None
        if bg or border:
            with self.canvas.before:
                if bg:
                    self._bg_color = Color(*rgba(bg))
                    self._bg_rect = RoundedRectangle(radius=[self._radius])
                if border:
                    Color(*rgba(border))
                    self._border_line = Line(width=1)
            self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        if self._bg_rect is not None:
            self._bg_rect.pos, self._bg_rect.size = self.pos, self.size
        if self._border_line is not None:
            self._border_line.rounded_rectangle = (*self.pos, *self.size, self._radius)


def card(**kwargs):
    kwargs.setdefault("padding", dp(16))
    return Box(bg=theme.PAPER, border=theme.PAPER_LINE, **kwargs)


def wood_card(**kwargs):
    kwargs.setdefault("padding", dp(16))
    return Box(bg=theme.WOOD, radius=14, **kwargs)


def row(*children, height=48, spacing=10):
    box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(height), spacing=dp(spacing))
    for child in children:
        box.add_widget(child)
    return box


class Page(ScrollView):
    """A vertically scrolling page with standard margins. Add widgets to ``.body``."""

    def __init__(self, **kwargs):
        super().__init__(do_scroll_x=False, bar_width=dp(3), scroll_type=["bars", "content"], **kwargs)
        self.body = Box(padding=(dp(16), dp(18), dp(16), dp(28)), spacing=dp(14))
        self.add_widget(self.body)

    def add(self, widget):
        self.body.add_widget(widget)
        return widget


def spacer(height=8):
    return Widget(size_hint_y=None, height=dp(height))


# -- controls --------------------------------------------------------------
class Btn(ButtonBehavior, Label):
    """A rounded button. kind: 'primary', 'outline' (on paper) or 'outline_dark' (on wood)."""

    kind = StringProperty("primary")

    def __init__(self, text="", kind="primary", **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(48))
        super().__init__(text=rich(text), markup=True, font_size=sp(15), bold=True,
                         halign="center", valign="middle", **kwargs)
        self.kind = kind
        with self.canvas.before:
            self._fill_color = Color(0, 0, 0, 0)
            self._fill = RoundedRectangle(radius=[dp(24)])
            self._line_color = Color(0, 0, 0, 0)
            self._line = Line(width=1.2)
        self.bind(pos=self._redraw, size=self._redraw, state=self._restyle,
                  disabled=self._restyle, kind=self._restyle)
        self._restyle()

    def set(self, text):
        self.text = rich(text)

    def _redraw(self, *_):
        self.text_size = (self.width - dp(16), None)
        self._fill.pos, self._fill.size = self.pos, self.size
        self._line.rounded_rectangle = (*self.pos, *self.size, dp(24))

    def _restyle(self, *_):
        down = self.state == "down"
        if self.kind == "primary":
            self._fill_color.rgba = rgba(theme.VARNISH_DARK if down else theme.VARNISH)
            self._line_color.rgba = (0, 0, 0, 0)
            self.color = rgba(theme.PAPER)
        elif self.kind == "outline_dark":
            self._fill_color.rgba = rgba(theme.CREAM, 0.14 if down else 0.0)
            self._line_color.rgba = rgba(theme.ON_WOOD_SOFT)
            self.color = rgba(theme.CREAM)
        else:
            self._fill_color.rgba = rgba(theme.VARNISH, 0.12 if down else 0.0)
            self._line_color.rgba = rgba(theme.VARNISH)
            self.color = rgba(theme.VARNISH_DARK)
        self.opacity = 0.4 if self.disabled else 1.0
        self.disabled_color = self.color


class Chip(ButtonBehavior, Label):
    """A small selectable pill. ``dark`` chips sit on wood, light ones on parchment."""

    selected = BooleanProperty(False)

    def __init__(self, text="", dark=False, done=False, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(40))
        super().__init__(text=text, markup=True, font_size=sp(14), bold=True,
                         halign="center", valign="middle", **kwargs)
        self.dark = dark
        self.done = done
        with self.canvas.before:
            self._fill_color = Color(0, 0, 0, 0)
            self._fill = RoundedRectangle(radius=[dp(10)])
            self._line_color = Color(0, 0, 0, 0)
            self._line = Line(width=1)
        self.bind(pos=self._redraw, size=self._redraw, selected=self._restyle)
        self._restyle()

    def _redraw(self, *_):
        self.text_size = self.size
        self._fill.pos, self._fill.size = self.pos, self.size
        self._line.rounded_rectangle = (*self.pos, *self.size, dp(10))

    def _restyle(self, *_):
        if self.selected:
            self._fill_color.rgba = rgba(theme.VARNISH)
            self._line_color.rgba = rgba(theme.VARNISH)
            self.color = rgba(theme.PAPER)
        elif self.dark:
            self._fill_color.rgba = rgba(theme.CREAM, 0.06)
            self._line_color.rgba = rgba(theme.WOOD_LINE)
            self.color = rgba(theme.CREAM)
        else:
            self._fill_color.rgba = rgba(theme.GOOD, 0.14) if self.done else rgba(theme.PAPER)
            self._line_color.rgba = rgba(theme.GOOD if self.done else theme.PAPER_LINE)
            self.color = rgba(theme.GOOD if self.done else theme.INK)


class CheckMark(Widget):
    checked = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(26), dp(26)), pos_hint={"center_y": 0.5}, **kwargs)
        self.bind(pos=self._draw, checked=self._draw)
        self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        x, y, s = self.x, self.y, self.width
        with self.canvas:
            if self.checked:
                Color(*rgba(theme.GOOD))
                RoundedRectangle(pos=(x, y), size=(s, s), radius=[dp(6)])
                Color(*rgba(theme.PAPER))
                Line(points=[x + s * .24, y + s * .52, x + s * .43, y + s * .32, x + s * .77, y + s * .70],
                     width=dp(1.6), cap="round", joint="round")
            else:
                Color(*rgba(theme.INK_SOFT))
                Line(rounded_rectangle=(x + 1, y + 1, s - 2, s - 2, dp(6)), width=1.2)


class CheckRow(ButtonBehavior, BoxLayout):
    """A tappable checklist line: tick box, bold title, description, minutes."""

    checked = BooleanProperty(False)

    def __init__(self, heading, text, minutes=None, checked=False, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, spacing=dp(12),
                         padding=(dp(12), dp(12), dp(12), dp(12)), **kwargs)
        with self.canvas.before:
            self._bg_color = Color(0, 0, 0, 0)
            self._bg = RoundedRectangle(radius=[dp(8)])
        self._mark = CheckMark()
        self._heading = Txt(bold(heading), is_markup=True)
        self._text = small(text)
        column = Box(spacing=dp(3))
        column.add_widget(self._heading)
        column.add_widget(self._text)
        column.bind(height=self._fit)
        self.add_widget(self._mark)
        self.add_widget(column)
        if minutes is not None:
            self.add_widget(Label(text=f"{minutes} min", font_size=sp(13), color=rgba(theme.INK_SOFT),
                                  size_hint=(None, None), size=(dp(48), dp(26)), halign="right",
                                  pos_hint={"center_y": 0.5}))
        self.bind(pos=self._redraw, size=self._redraw, checked=self._restyle)
        self.checked = checked
        self._restyle()

    def _fit(self, _column, height):
        self.height = height + dp(24)

    def _redraw(self, *_):
        self._bg.pos, self._bg.size = self.pos, self.size

    def _restyle(self, *_):
        self._mark.checked = self.checked
        self._bg_color.rgba = rgba(theme.GOOD, 0.10) if self.checked else rgba(theme.INK, 0.04)
        self._heading.color = rgba(theme.INK_SOFT if self.checked else theme.INK)


class Meter(Widget):
    """A thin horizontal bar, 0..1. Used for the microphone level and for progress."""

    value = NumericProperty(0.0)

    def __init__(self, track=theme.WOOD_LINE, fill=theme.GOOD_LIGHT, height=6, **kwargs):
        super().__init__(size_hint_y=None, height=dp(height), **kwargs)
        self._track, self._fill = track, fill
        self.bind(pos=self._draw, size=self._draw, value=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        radius = [self.height / 2]
        with self.canvas:
            Color(*rgba(self._track))
            RoundedRectangle(pos=self.pos, size=self.size, radius=radius)
            width = self.width * max(0.0, min(1.0, self.value))
            if width >= self.height:
                Color(*rgba(theme.BAD_LIGHT if self.value > 0.92 and self._fill == theme.GOOD_LIGHT
                            else self._fill))
                RoundedRectangle(pos=self.pos, size=(width, self.height), radius=radius)


# -- drawing text on a canvas -----------------------------------------------
_textures: dict = {}


def text_texture(text, size_px, font=None, is_bold=False):
    key = (text, round(size_px, 1), font, is_bold)
    texture = _textures.get(key)
    if texture is None:
        label = CoreLabel(text=text, font_size=size_px, font_name=font or theme.FONT_BODY, bold=is_bold)
        label.refresh()
        texture = _textures[key] = label.texture
    return texture


def draw_text(text, cx, cy, size_px, color, font=None, is_bold=False):
    """Draw ``text`` centred on (cx, cy). Call inside a ``with canvas:`` block."""
    texture = text_texture(text, size_px, font, is_bold)
    Color(*rgba(color))
    Rectangle(texture=texture, size=texture.size,
              pos=(round(cx - texture.width / 2), round(cy - texture.height / 2)))
