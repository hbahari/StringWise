from __future__ import annotations

from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from ... import theme
from ...content.theory import SECTIONS, THEORY_INTRO
from ...music.fingering import STRINGS
from ...theme import rgba
from ..staff import Staff
from ..widgets import Box, Btn, Txt, bold, bullets, card, row, small, subtitle, title
from .base import PageScreen


class Chevron(Widget):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(20), dp(20)), **kwargs)
        self.open = False
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        cx, cy, r = self.x + self.width / 2, self.y + self.height / 2, dp(5)
        with self.canvas:
            Color(*rgba(theme.VARNISH))
            points = ([cx - r, cy + r / 2, cx, cy - r / 2, cx + r, cy + r / 2] if self.open
                      else [cx - r / 2, cy + r, cx + r / 2, cy, cx - r / 2, cy - r])
            Line(points=points, width=dp(1.4), cap="round", joint="round")


class SectionHeader(ButtonBehavior, BoxLayout):
    def __init__(self, section, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, spacing=dp(10), **kwargs)
        column = Box(spacing=dp(2))
        column.add_widget(subtitle(section.title))
        column.add_widget(small(section.summary))
        column.bind(height=self.setter("height"))
        self.chevron = Chevron(pos_hint={"center_y": 0.5})
        self.add_widget(column)
        self.add_widget(self.chevron)


class TheoryScreen(PageScreen):
    def __init__(self, **kwargs):
        super().__init__(name="theory", **kwargs)
        page = self.page
        page.add(title("Theory"))
        page.add(Txt(THEORY_INTRO, color=theme.INK_SOFT))
        page.add(row(Btn("Open all", kind="outline", height=dp(40), on_release=lambda _b: self._set_all(True)),
                     Btn("Close all", kind="outline", height=dp(40), on_release=lambda _b: self._set_all(False)),
                     height=40))
        self.sections = []
        for index, section in enumerate(SECTIONS):
            panel = page.add(card())
            header = SectionHeader(section)
            body = self._build_body(section)
            entry = {"panel": panel, "header": header, "body": body, "open": False}
            header.bind(on_release=lambda _h, e=entry: self._set(e, not e["open"]))
            panel.add_widget(header)
            self.sections.append(entry)
            if index == 0:
                self._set(entry, True)

    def _set(self, entry, is_open):
        if entry["open"] == is_open:
            return
        entry["open"] = is_open
        if is_open:
            entry["panel"].add_widget(entry["body"])
        else:
            entry["panel"].remove_widget(entry["body"])
        entry["header"].chevron.open = is_open
        entry["header"].chevron.draw()

    def _set_all(self, is_open):
        for entry in self.sections:
            self._set(entry, is_open)

    def _build_body(self, section):
        body = Box(spacing=dp(10))
        for block in section.blocks:
            kind = block[0]
            if kind == "p":
                body.add_widget(Txt(block[1]))
            elif kind == "h":
                body.add_widget(Txt(bold(block[1]), is_markup=True, color=theme.VARNISH_DARK))
            elif kind == "list":
                body.add_widget(bullets(block[1]))
            elif kind == "terms":
                body.add_widget(self._terms(block[1]))
            elif kind == "open_strings":
                body.add_widget(self._open_strings())
        return body

    def _terms(self, pairs):
        box = Box(spacing=dp(8))
        for term, meaning in pairs:
            line = BoxLayout(orientation="horizontal", size_hint_y=None, spacing=dp(10))
            left = Txt(bold(term), is_markup=True, size_hint_x=0.38)
            right = Txt(meaning, size_hint_x=0.62)
            sync = lambda *_a, line=line, left=left, right=right: setattr(line, "height", max(left.height, right.height))
            left.bind(height=sync)
            right.bind(height=sync)
            line.add_widget(left)
            line.add_widget(right)
            box.add_widget(line)
        return box

    def _open_strings(self):
        box = Box(spacing=dp(2))
        staff = Staff([string.open_note for string in STRINGS], scale=1.0, show_fingers=False)
        holder = BoxLayout(size_hint_y=None, height=staff.height)
        holder.add_widget(Widget())
        holder.add_widget(staff)
        holder.add_widget(Widget())
        box.add_widget(holder)
        box.add_widget(small("The open strings, low to high: G, D, A, E", halign="center"))
        return box
