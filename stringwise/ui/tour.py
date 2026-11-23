"""The first-launch tour: dims the app, lights up one part of it, and explains it in a bubble.

The overlay sits on top of the whole window and takes every touch, so the app can't be
changed by accident while the tour runs. The bubble has Skip and Next buttons.
"""

from __future__ import annotations

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from .. import theme
from ..content import tour as text
from ..theme import rgba
from .widgets import Box, Btn, Txt, subtitle

STORE_KEY = "tour"
DIM = 0.74
PAD = 6          # dp of space between the highlighted part and its outline
GAP = 14         # dp between the highlight and the bubble


def _find(root, class_name):
    return next((w for w in root.walk() if w.__class__.__name__ == class_name), None)


def target_widget(app, name):
    """The widget a step highlights, or None for a step with no highlight."""
    shell, get = app.shell, app.shell.manager.get_screen
    if name == "tuner_dial":
        return get("tuner").dial
    if name == "metronome":
        return _find(get("metronome"), "MetronomeBar")
    if name == "header_metronome":
        return shell.header_metronome
    if name == "week_chips":
        return get("lessons").chip_scroller
    if name == "fingerboard":
        return _find(get("fingers"), "Fingerboard")
    if name == "theory":
        return get("theory").sections[0]["header"]
    if name == "rhythm":
        return get("practice").rhythm_picker.parent
    if name == "gear":
        return shell.gear
    return None


class Tour(FloatLayout):
    def __init__(self, app, on_finish=None, **kwargs):
        super().__init__(size=Window.size, pos=(0, 0), size_hint=(None, None), **kwargs)
        self.app = app
        self.on_finish = on_finish
        self.index = -1
        self._hole = None          # (x, y, w, h) of the lit-up part, in window pixels
        self._tab = None           # outline drawn round the bottom tab
        self._previewing = False
        self.bubble = Box(bg=theme.PAPER, border=theme.PAPER_LINE, radius=14, padding=dp(16),
                          spacing=dp(8), size_hint=(None, None))
        self.add_widget(self.bubble)
        self.bind(size=lambda *_: self._layout())
        Window.bind(size=self._resize)
        self.opacity = 0

    # -- control ---------------------------------------------------------------
    def start(self):
        Window.add_widget(self)
        Animation(opacity=1, duration=0.25).start(self)
        self.next()

    def next(self, *_):
        self._end_preview()
        self.index += 1
        if self.index >= len(text.STEPS):
            self.finish(completed=True)
            return
        step = text.STEPS[self.index]
        if step.screen:
            self.app.go_to(step.screen)
        widget = target_widget(self.app, step.target) if step.target else None
        if widget is not None and step.target == "header_metronome" and not self.app.metronome.used:
            self._previewing = True            # show the control, which is hidden until first use
            widget.opacity = 1
        if widget is not None:
            if step.target == "week_chips":
                widget.scroll_x = 0            # show week 1 at the start of the row
            page = self._page_of(widget)
            if page is not None:
                page.scroll_to(widget, padding=dp(24), animate=False)
        self._build_bubble(step)
        self.bubble.opacity = 0
        # Wait a frame so scrolled and newly shown widgets have their final positions.
        Clock.schedule_once(lambda _dt: self._show(widget, step), 0.08)

    def finish(self, completed=False, *_):
        self._end_preview()
        store = self.app.store
        store.set(STORE_KEY, {"done": True})
        Window.unbind(size=self._resize)

        def remove(*_):
            if self.parent is not None:
                self.parent.remove_widget(self)

        anim = Animation(opacity=0, duration=0.2)
        anim.bind(on_complete=remove)
        anim.start(self)
        if self.on_finish:
            self.on_finish(completed)

    # -- drawing -------------------------------------------------------------------
    def _show(self, widget, step):
        self._hole = self._rect_of(widget, PAD) if widget is not None else None
        if self._hole and self._page_of(widget) is not None:
            self._hole = self._clip_to_page(self._hole)
        tab = self.app.shell.nav_buttons.get(step.tab) if step.tab else None
        self._tab = self._rect_of(tab, -2) if tab is not None else None
        self._draw()
        self._layout()
        Animation(opacity=1, duration=0.18).start(self.bubble)

    @staticmethod
    def _rect_of(widget, pad):
        x, y = widget.to_window(widget.x, widget.y)
        return (x - dp(pad), y - dp(pad), widget.width + dp(pad) * 2, widget.height + dp(pad) * 2)

    def _clip_to_page(self, rect):
        """Keep a highlight on a scrolling page inside the page, clear of the title and tab bars."""
        manager = self.app.shell.manager
        mx, my = manager.to_window(manager.x, manager.y)
        x, y, w, h = rect
        bottom, top = max(y, my + dp(4)), min(y + h, my + manager.height - dp(4))
        return (x, bottom, w, max(dp(20), top - bottom))

    @staticmethod
    def _page_of(widget):
        node, seen = widget.parent, set()
        while node is not None and id(node) not in seen:     # the window is its own parent
            if node.__class__.__name__ == "Page":
                return node
            seen.add(id(node))
            node = node.parent
        return None

    def _draw(self):
        """Dim everything except the hole, then outline the hole and the tab."""
        self.canvas.before.clear()
        width, height = self.size
        holes = [self._hole] if self._hole else []
        xs = sorted({0, width, *[v for h in holes for v in (h[0], h[0] + h[2])]})
        ys = sorted({0, height, *[v for h in holes for v in (h[1], h[1] + h[3])]})
        with self.canvas.before:
            Color(*rgba(theme.WOOD_DEEP, DIM))
            for x0, x1 in zip(xs, xs[1:]):
                for y0, y1 in zip(ys, ys[1:]):
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    if not any(h[0] <= cx <= h[0] + h[2] and h[1] <= cy <= h[1] + h[3] for h in holes):
                        Rectangle(pos=(x0, y0), size=(x1 - x0, y1 - y0))
            if self._hole:
                Color(*rgba(theme.CREAM))
                Line(rounded_rectangle=(*self._hole, dp(12)), width=dp(2))
            if self._tab:
                Color(*rgba(theme.WARN_LIGHT))
                Line(rounded_rectangle=(*self._tab, dp(10)), width=dp(1.8))

    def _build_bubble(self, step):
        bubble = self.bubble
        bubble.clear_widgets()
        bubble.add_widget(subtitle(step.title))
        bubble.add_widget(Txt(step.text))
        first, last = self.index == 0, self.index == len(text.STEPS) - 1
        footer = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        if last:
            footer.add_widget(Widget())
        else:
            footer.add_widget(Btn(text.SKIP, kind="outline", size_hint_x=None, width=dp(108),
                                  on_release=lambda _b: self.finish(False)))
        counter = Label(text="" if first or last else f"{self.index} of {len(text.STEPS) - 2}",
                        color=rgba(theme.INK_SOFT), font_size=dp(13))
        footer.add_widget(counter)
        label = text.FIRST if first else text.LAST if last else text.NEXT
        footer.add_widget(Btn(label, size_hint_x=None, width=dp(150 if first or last else 96),
                              on_release=self._advance))
        bubble.add_widget(footer)
        bubble.width = min(self.width - dp(32), dp(460))

    def _advance(self, *_):
        if self.index == len(text.STEPS) - 1:
            self.app.go_to("lessons")
            self.app.shell.manager.get_screen("lessons").show_week(1)
        self.next()

    def _layout(self):
        """Put the bubble where there is room: below the highlight, above it, or centred."""
        bubble = self.bubble
        bubble.width = min(self.width - dp(32), dp(460))
        x = (self.width - bubble.width) / 2
        if not self._hole:
            bubble.pos = (x, (self.height - bubble.height) / 2)
            return
        hx, hy, hw, hh = self._hole
        top_limit, bottom_limit = self.height - dp(12), dp(66)      # keep clear of the tab bar
        below = hy - dp(GAP) - bottom_limit
        above = top_limit - (hy + hh + dp(GAP))
        if below >= bubble.height:
            y = hy - dp(GAP) - bubble.height
        elif above >= bubble.height:
            y = hy + hh + dp(GAP)
        else:
            y = bottom_limit          # no room either side: sit low, over the highlight
        bubble.pos = (x, max(bottom_limit, min(y, top_limit - bubble.height)))

    def _resize(self, _window, size):
        self.size = size
        if 0 <= self.index < len(text.STEPS):
            step = text.STEPS[self.index]
            widget = target_widget(self.app, step.target) if step.target else None
            Clock.schedule_once(lambda _dt: self._show(widget, step), 0.05)

    def _end_preview(self):
        if self._previewing:
            self._previewing = False
            self.app.shell.header_metronome.sync()

    # -- touches -------------------------------------------------------------------
    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        return True              # nothing behind the tour reacts while it is showing

    def on_touch_move(self, touch):
        super().on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        return True
