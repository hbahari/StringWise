import sys
import types

import pytest


@pytest.fixture
def platform(monkeypatch):
    """The platform module with Kivy's Window replaced, so this runs without a display."""
    window = types.SimpleNamespace(allow_screensaver=True)
    core = types.ModuleType("kivy.core.window"); core.Window = window
    clock = types.ModuleType("kivy.clock"); clock.Clock = types.SimpleNamespace(schedule_once=lambda *a: None)
    utils = types.ModuleType("kivy.utils"); utils.platform = "linux"
    for name, module in (("kivy", types.ModuleType("kivy")), ("kivy.core", types.ModuleType("kivy.core")),
                         ("kivy.core.window", core), ("kivy.clock", clock), ("kivy.utils", utils)):
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.delitem(sys.modules, "stringwise.ui.platform", raising=False)
    import stringwise.ui.platform as module
    module._awake_reasons.clear()
    yield module, window
    module._awake_reasons.clear()
    sys.modules.pop("stringwise.ui.platform", None)     # later imports get the real module


def test_listening_does_not_undo_the_setting(platform):
    module, window = platform
    module.keep_screen_on(True, "setting")
    module.keep_screen_on(True)                 # tuner starts listening
    module.keep_screen_on(False)                # tuner stops
    assert module.screen_kept_on() and window.allow_screensaver is False
    module.keep_screen_on(False, "setting")     # user turns the option off
    assert not module.screen_kept_on() and window.allow_screensaver is True


def test_listening_alone_keeps_it_on_only_while_listening(platform):
    module, window = platform
    module.keep_screen_on(True)
    assert window.allow_screensaver is False
    module.keep_screen_on(False)
    assert window.allow_screensaver is True
