from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

from ... import theme
from ...content.lessons import LESSON_BY_WEEK, LESSONS, LESSONS_INTRO
from ...music.pieces import PIECES
from ..staff import StaffScroller
from ..widgets import (Box, Btn, CheckRow, Chip, Txt, bold, bullets, card, small,
                       subtitle, title)
from .base import PageScreen

STORE_KEY = "lessons"


class LessonsScreen(PageScreen):
    def __init__(self, **kwargs):
        super().__init__(name="lessons", **kwargs)
        saved = self.app.store.get(STORE_KEY, {})
        self.current_week = int(saved.get("current_week", 1))
        self.completed = set(saved.get("completed", []))
        self.checks = {int(week): list(values) for week, values in saved.get("checks", {}).items()}
        if self.current_week not in LESSON_BY_WEEK:
            self.current_week = 1

        page = self.page
        page.add(title("Lessons"))
        page.add(Txt(LESSONS_INTRO, color=theme.INK_SOFT))

        self.week_chips = {}
        chips = BoxLayout(orientation="horizontal", size_hint=(None, None), height=dp(40), spacing=dp(8))
        chips.bind(minimum_width=chips.setter("width"))
        for lesson in LESSONS:
            chip = Chip(f"Week {lesson.week}", size_hint_x=None, width=dp(84))
            chip.bind(on_release=lambda _c, week=lesson.week: self.show_week(week))
            self.week_chips[lesson.week] = chip
            chips.add_widget(chip)
        self.chip_scroller = ScrollView(do_scroll_y=False, size_hint_y=None, height=dp(40), bar_width=0)
        self.chip_scroller.add_widget(chips)
        page.add(self.chip_scroller)

        self.lesson_box = page.add(Box(spacing=dp(14)))
        self.show_week(self.current_week, save=False)

    # -- state ---------------------------------------------------------------
    def _save(self):
        self.app.store.set(STORE_KEY, {
            "current_week": self.current_week,
            "completed": sorted(self.completed),
            "checks": {str(week): values for week, values in self.checks.items()},
        })

    def _checks_for(self, lesson):
        values = self.checks.get(lesson.week)
        if values is None or len(values) != len(lesson.plan):
            values = self.checks[lesson.week] = [False] * len(lesson.plan)
        return values

    # -- building ------------------------------------------------------------
    def show_week(self, week, save=True):
        self.current_week = week
        if save:
            self._save()
        for number, chip in self.week_chips.items():
            chip.selected = number == week
            chip.done = number in self.completed
            chip._restyle()
        chip = self.week_chips[week]
        self.chip_scroller.scroll_to(chip, padding=dp(40), animate=False)
        self._build_lesson(LESSON_BY_WEEK[week])
        self.page.scroll_y = 1

    def _build_lesson(self, lesson):
        box = self.lesson_box
        box.clear_widgets()

        head = card()
        head.add_widget(small(f"Week {lesson.week} of {len(LESSONS)}, about an hour a day", color=theme.VARNISH_DARK))
        head.add_widget(subtitle(lesson.title))
        head.add_widget(Txt(bold("This week you will"), is_markup=True))
        head.add_widget(bullets(lesson.goals))
        for paragraph in lesson.body:
            head.add_widget(Txt(paragraph))
        box.add_widget(head)

        for number, piece_id in enumerate(lesson.pieces, start=1):
            piece = PIECES[piece_id]
            panel = card(spacing=dp(8))
            panel.add_widget(small(f"Practice piece {number} of {len(lesson.pieces)}", color=theme.VARNISH_DARK))
            panel.add_widget(subtitle(piece.title))
            panel.add_widget(small(piece.info))
            panel.add_widget(StaffScroller(piece.notes))
            panel.add_widget(Btn("Play along with this piece", kind="outline",
                                 on_release=lambda _b, pid=piece_id: self.app.open_play_along(pid)))
            box.add_widget(panel)

        plan = card(spacing=dp(8))
        plan.add_widget(subtitle("Daily practice plan"))
        plan.add_widget(small("Tick each part off as you finish it."))
        checks = self._checks_for(lesson)
        self._rows = []
        for index, item in enumerate(lesson.plan):
            check_row = CheckRow(item.title, item.text, minutes=item.minutes, checked=checks[index])
            check_row.bind(on_release=lambda _r, i=index: self._toggle(lesson, i))
            self._rows.append(check_row)
            plan.add_widget(check_row)
        self._tally = small("")
        plan.add_widget(self._tally)
        box.add_widget(plan)

        actions = Box(spacing=dp(10))
        self._complete_button = Btn("", on_release=lambda _b: self._complete(lesson))
        actions.add_widget(self._complete_button)
        self._skip_button = None
        if lesson.week < len(LESSONS):
            self._skip_button = Btn(f"Skip to week {lesson.week + 1}", kind="outline",
                                    on_release=lambda _b: self._skip(lesson))
            actions.add_widget(self._skip_button)
        self._nudge = small("", halign="center")
        actions.add_widget(self._nudge)
        actions.add_widget(Btn("Clear this week's ticks", kind="outline", height=dp(40),
                               on_release=lambda _b: self._clear(lesson)))
        box.add_widget(actions)
        self._update_actions(lesson)

    def _update_actions(self, lesson):
        checks = self._checks_for(lesson)
        done = sum(checks)
        all_done = done == len(checks)
        complete = lesson.week in self.completed
        self._tally.set(f"{done} of {len(checks)} done. {lesson.total_minutes} minutes in all.")
        self._complete_button.set("Week complete ✓" if complete else f"Mark week {lesson.week} complete")
        if self._skip_button is not None:
            self._skip_button.disabled = not all_done
        if all_done:
            self._nudge.set("Everything is ticked. You're ready to move on.")
        elif self._skip_button is not None:
            self._nudge.set("Tick every part of the plan to unlock the next week early.")
        else:
            self._nudge.set("")

    # -- actions -------------------------------------------------------------
    def _toggle(self, lesson, index):
        checks = self._checks_for(lesson)
        checks[index] = not checks[index]
        self._rows[index].checked = checks[index]
        self._save()
        self._update_actions(lesson)

    def _clear(self, lesson):
        self.checks[lesson.week] = [False] * len(lesson.plan)
        for check_row in self._rows:
            check_row.checked = False
        self._save()
        self._update_actions(lesson)

    def _complete(self, lesson):
        self.completed.add(lesson.week)
        self.show_week(min(lesson.week + 1, len(LESSONS)))

    def _skip(self, lesson):
        if all(self._checks_for(lesson)):
            self._complete(lesson)
