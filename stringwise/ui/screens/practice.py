from __future__ import annotations

import datetime

from kivy.metrics import dp

from ... import theme
from ...content.practice import PRACTICE_INTRO, ROUTINE
from ..widgets import Btn, CheckRow, Meter, Txt, card, small, title
from .base import PageScreen

STORE_KEY = "practice"


class PracticeScreen(PageScreen):
    def __init__(self, **kwargs):
        super().__init__(name="practice", **kwargs)
        self.done = set()
        page = self.page
        page.add(title("Practice"))
        page.add(Txt(PRACTICE_INTRO, color=theme.INK_SOFT))

        summary = page.add(card(spacing=dp(8)))
        self.tally = Txt("")
        self.meter = Meter(track=theme.PAPER_LINE, fill=theme.GOOD, height=8)
        summary.add_widget(self.tally)
        summary.add_widget(self.meter)

        self.rows = {}
        listing = page.add(card(spacing=dp(8)))
        for item in ROUTINE:
            check_row = CheckRow(item.title, item.text, minutes=item.minutes)
            check_row.bind(on_release=lambda _r, item_id=item.id: self._toggle(item_id))
            self.rows[item.id] = check_row
            listing.add_widget(check_row)
        total = sum(item.minutes for item in ROUTINE)
        listing.add_widget(small(f"{total} minutes in all."))
        page.add(Btn("Clear today's list", kind="outline", on_release=self._reset))
        self._load()

    def on_pre_enter(self, *_):
        self._load()          # a new day clears yesterday's ticks

    def _load(self):
        saved = self.app.store.get(STORE_KEY, {})
        today = datetime.date.today().isoformat()
        self.done = set(saved.get("done", [])) if saved.get("date") == today else set()
        self._refresh()

    def _save(self):
        self.app.store.set(STORE_KEY, {"date": datetime.date.today().isoformat(), "done": sorted(self.done)})

    def _toggle(self, item_id):
        self.done.symmetric_difference_update({item_id})
        self._save()
        self._refresh()

    def _reset(self, *_):
        self.done = set()
        self._save()
        self._refresh()

    def _refresh(self):
        for item_id, check_row in self.rows.items():
            check_row.checked = item_id in self.done
        count = len(self.done & set(self.rows))
        self.tally.set(f"{count} of {len(ROUTINE)} done today")
        self.meter.value = count / len(ROUTINE)
