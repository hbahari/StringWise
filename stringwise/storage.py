"""Saved progress: one small JSON file in the app's private data folder."""

from __future__ import annotations

import json
import os


class ProgressStore:
    def __init__(self, folder: str) -> None:
        self._path = os.path.join(folder, "progress.json")
        self._data: dict = {}
        try:
            with open(self._path, encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                self._data = loaded
        except (OSError, ValueError):
            pass     # first run, or a damaged file: start fresh

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        temporary = self._path + ".tmp"
        try:
            with open(temporary, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle)
            os.replace(temporary, self._path)
        except OSError:
            pass     # progress simply isn't saved this time
