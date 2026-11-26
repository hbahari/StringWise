"""The iOS port, tested without an iPhone.

Kivy, pyobjus, kivy-ios's ``ios`` module and our ``swmic`` are replaced with small
fakes, so this checks our side of each call. Whether iOS itself behaves as
expected can only be seen on a device or in the Simulator (see docs/IOS.md).
"""

import importlib
import json
import plistlib
import shutil
import subprocess
import sys
import sysconfig
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


# -- fakes ---------------------------------------------------------------------
class FakeSwmic:
    def __init__(self, permission="granted", start_code=0, chunks=()):
        self.state = permission
        self.start_code = start_code
        self.chunks = list(chunks)
        self.requested = False
        self.started_at = None
        self.stopped = False

    def permission(self):
        return self.state

    def request_permission(self):
        self.requested = True

    def start(self, rate):
        self.started_at = rate
        return self.start_code

    def read(self, count):
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)[:count]
        return np.asarray(chunk, dtype=np.float32).tobytes()

    def stop(self):
        self.stopped = True


class FakeObjc:
    """Records what is called on it; attributes return more FakeObjc objects."""

    def __init__(self, name, log, **values):
        self._name, self._log, self._values = name, log, values

    def __getattr__(self, attr):
        if attr in self._values:
            return self._values[attr]

        def call(*args):
            self._log.append((self._name, attr, args))
            return FakeObjc(f"{self._name}.{attr}", self._log)
        return call

    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            object.__setattr__(self, attr, value)
        else:
            self._log.append((self._name, f"set {attr}", (value,)))


@pytest.fixture
def ios(monkeypatch):
    """stringwise.ui.platform imported as if on an iPhone."""
    log, intervals = [], []
    window = types.SimpleNamespace(allow_screensaver=True)
    core = types.ModuleType("kivy.core.window"); core.Window = window
    clock = types.ModuleType("kivy.clock")
    clock.Clock = types.SimpleNamespace(schedule_once=lambda f, *a: f(0),
                                        schedule_interval=lambda f, t: intervals.append(f))
    utils = types.ModuleType("kivy.utils"); utils.platform = "ios"

    ios_module = types.ModuleType("ios")
    ios_module.open_url = lambda url: log.append(("ios", "open_url", (url,)))
    ios_module.get_safe_area = lambda: {"top": 59.0, "bottom": 34.0, "left": 0.0, "right": 0.0}
    ios_module.get_scale = lambda: 3.0

    controller = FakeObjc("controller", log, presentedViewController=None, view="the-view")
    key_window = FakeObjc("window", log, rootViewController=controller)
    application = FakeObjc("app", log, keyWindow=key_window)
    sheet = FakeObjc("sheet", log, popoverPresentationController=FakeObjc("popover", log))

    def autoclass(name):
        if name == "UIApplication":
            return types.SimpleNamespace(sharedApplication=lambda: application)
        if name == "UIActivityViewController":
            alloc = types.SimpleNamespace(
                initWithActivityItems_applicationActivities_=lambda items, extra: sheet)
            return types.SimpleNamespace(alloc=lambda: alloc)
        if name == "NSArray":
            return types.SimpleNamespace(arrayWithObject_=lambda item: [item])
        if name == "UIDevice":
            text = lambda value: types.SimpleNamespace(UTF8String=lambda: value)
            device = types.SimpleNamespace(systemName=lambda: text("iOS"), systemVersion=lambda: text("26.1"))
            return types.SimpleNamespace(currentDevice=lambda: device)
        raise AssertionError(name)

    pyobjus = types.ModuleType("pyobjus")
    pyobjus.autoclass = autoclass
    pyobjus.objc_str = lambda value: value
    swmic = FakeSwmic()

    for name, module in (("kivy", types.ModuleType("kivy")), ("kivy.core", types.ModuleType("kivy.core")),
                         ("kivy.core.window", core), ("kivy.clock", clock), ("kivy.utils", utils),
                         ("ios", ios_module), ("pyobjus", pyobjus), ("swmic", swmic)):
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.delitem(sys.modules, "stringwise.ui.platform", raising=False)
    import stringwise.ui.platform as module
    module._awake_reasons.clear()
    yield types.SimpleNamespace(module=module, log=log, intervals=intervals, swmic=swmic,
                                window=window, sheet=sheet)
    module._awake_reasons.clear()
    sys.modules.pop("stringwise.ui.platform", None)


# -- platform.py ---------------------------------------------------------------
def test_detects_ios(ios):
    assert ios.module.IS_IOS and not ios.module.IS_ANDROID


def test_links_and_email_open_through_ios(ios):
    assert ios.module.open_link("https://example.com/privacy")
    assert ios.module.send_email("golemapps1@gmail.com", "StringWise feedback (2.6.0)", "Hi\nthere")
    urls = [args[0] for name, call, args in ios.log if call == "open_url"]
    assert urls[0] == "https://example.com/privacy"
    assert urls[1] == ("mailto:golemapps1@gmail.com?subject=StringWise%20feedback%20%282.6.0%29"
                       "&body=Hi%0Athere")


def test_keep_screen_on_uses_the_idle_timer(ios):
    ios.module.keep_screen_on(True, "setting")
    ios.module.keep_screen_on(False, "setting")
    calls = [args for name, call, args in ios.log if call == "setIdleTimerDisabled_"]
    assert calls == [(True,), (False,)]


def test_safe_area_is_in_pixels(ios):
    assert ios.module.safe_area() == (177.0, 102.0)


def test_share_sheet_is_presented_and_anchored(ios):
    assert ios.module.share_text("StringWise", "Try this") == "shared"
    assert ("popover", "set sourceView", ("the-view",)) in ios.log
    presented = [args for name, call, args in ios.log if call == "presentViewController_animated_completion_"]
    assert presented == [(ios.sheet, True, None)]


def test_device_summary_names_the_system(ios):
    summary = ios.module.device_summary()
    assert summary.endswith("iOS 26.1")


@pytest.mark.parametrize("state, expected", [("granted", True), ("denied", False)])
def test_microphone_answer_known(ios, state, expected):
    ios.swmic.state = state
    answers = []
    ios.module.request_microphone(answers.append)
    assert answers == [expected] and not ios.swmic.requested


def test_microphone_asks_then_waits_for_the_answer(ios):
    ios.swmic.state = "unknown"
    answers = []
    ios.module.request_microphone(answers.append)
    assert ios.swmic.requested and answers == []
    check = ios.intervals[0]
    assert check(0.25) is True              # still waiting: keep checking
    ios.swmic.state = "granted"
    assert check(0.25) is False and answers == [True]


# -- the microphone backend ----------------------------------------------------
def test_ios_mic_reads_float_samples():
    from stringwise.audio.mic import IosMic, SAMPLE_RATE
    fake = FakeSwmic(chunks=[[0.1, -0.2, 0.3]])
    mic = IosMic(fake)
    mic.open()
    assert fake.started_at == SAMPLE_RATE
    assert np.allclose(mic.read(1024), [0.1, -0.2, 0.3])
    mic.close()
    assert fake.stopped


def test_ios_mic_reports_problems():
    from stringwise.audio.mic import IosMic, MicError
    with pytest.raises(MicError, match="Settings"):
        IosMic(FakeSwmic(permission="denied")).open()
    with pytest.raises(MicError, match="code -3"):
        IosMic(FakeSwmic(start_code=-3)).open()
    mic = IosMic(FakeSwmic())
    mic.timeout = 0.02
    mic.open()
    with pytest.raises(MicError, match="stopped responding"):
        mic.read(1024)


def test_ios_mic_feeds_the_pitch_listener():
    from stringwise.audio.listener import PitchListener
    from stringwise.audio.mic import IosMic, SAMPLE_RATE
    t = np.arange(SAMPLE_RATE) / SAMPLE_RATE
    tone = (0.05 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    fake = FakeSwmic(chunks=[tone[i:i + 470] for i in range(0, len(tone), 470)])   # odd sizes, like iOS
    listener = PitchListener(mic_factory=lambda: IosMic(fake))
    listener.start()
    import time
    deadline = time.time() + 5
    frames = []
    while time.time() < deadline and len(frames) < 20:
        frames += [f for f in listener.poll() if f.freq]
        time.sleep(0.01)
    listener.stop()
    assert len(frames) >= 20
    assert abs(np.median([f.freq for f in frames]) - 440) < 2


def test_default_mic_on_ios(monkeypatch):
    utils = types.ModuleType("kivy.utils"); utils.platform = "ios"
    monkeypatch.setitem(sys.modules, "kivy", types.ModuleType("kivy"))
    monkeypatch.setitem(sys.modules, "kivy.utils", utils)
    monkeypatch.delenv("STRINGWISE_FAKE_MIC", raising=False)
    from stringwise.audio import mic
    assert isinstance(mic.open_default_mic(), mic.IosMic)


# -- store links ---------------------------------------------------------------
def test_store_links(monkeypatch):
    from stringwise.content import settings
    android = settings.store_for(ios=False)
    assert android["rate"].startswith("market://") and "Google Play" in android["rate_label"]
    assert settings.share_message(android) == settings.SHARE_MESSAGE

    monkeypatch.setattr(settings, "APP_STORE_ID", "")
    assert settings.store_for(ios=True) is None          # nothing to point at yet: buttons hidden

    monkeypatch.setattr(settings, "APP_STORE_ID", "1234567890")
    apple = settings.store_for(ios=True)
    assert apple["web"] == "https://apps.apple.com/app/id1234567890"
    assert apple["rate"].startswith("itms-apps://") and "App Store" in apple["rate_label"]
    assert "play.google" not in settings.share_message(apple)


# -- Xcode project settings ----------------------------------------------------
def test_configure_xcode(tmp_path):
    project = tmp_path / "stringwise-ios"
    (project / "stringwise.xcodeproj").mkdir(parents=True)
    (project / "stringwise" / "Images.xcassets" / "AppIcon.appiconset").mkdir(parents=True)
    (project / "Storyboards").mkdir()
    with (project / "stringwise-Info.plist").open("wb") as handle:
        plistlib.dump({"CFBundleIdentifier": "org.kivy.stringwise",
                       "UISupportedInterfaceOrientations": ["UIInterfaceOrientationLandscapeLeft"],
                       "UISupportedInterfaceOrientations~ipad": ["UIInterfaceOrientationLandscapeLeft"]},
                      handle)
    (project / "stringwise.xcodeproj" / "project.pbxproj").write_text(
        'INFOPLIST_FILE = "x-Info.plist";\nTARGETED_DEVICE_FAMILY = "1,2";\n')
    (project / "Storyboards" / "Launch Screen.storyboard").write_text(
        '<color key="backgroundColor" white="0.0" alpha="1"/>')
    (project / "icon.png").write_bytes(b"old")

    spec = importlib.util.spec_from_file_location("configure_xcode", ROOT / "ios" / "configure_xcode.py")
    configure = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(configure)
    configure.main([str(project), "--build", "12"])

    with (project / "stringwise-Info.plist").open("rb") as handle:
        info = plistlib.load(handle)
    from stringwise import __version__
    assert info["CFBundleShortVersionString"] == __version__ and info["CFBundleVersion"] == "12"
    assert info["CFBundleIdentifier"] == configure.BUNDLE_ID
    assert info["UISupportedInterfaceOrientations"] == ["UIInterfaceOrientationPortrait"]
    assert "UISupportedInterfaceOrientations~ipad" not in info
    assert "violin" in info["NSMicrophoneUsageDescription"]
    assert info["ITSAppUsesNonExemptEncryption"] is False
    pbx = (project / "stringwise.xcodeproj" / "project.pbxproj").read_text()
    assert "TARGETED_DEVICE_FAMILY = 1;" in pbx and f"PRODUCT_BUNDLE_IDENTIFIER = {configure.BUNDLE_ID};" in pbx
    icons = json.loads((project / "stringwise" / "Images.xcassets" / "AppIcon.appiconset" /
                        "Contents.json").read_text())
    assert icons["images"][0]["size"] == "1024x1024"
    assert 'red="0.169"' in (project / "Storyboards" / "Launch Screen.storyboard").read_text()


def test_app_icon_is_opaque_and_full_size():
    header = (ROOT / "ios" / "assets" / "icon-1024.png").read_bytes()[:26]
    width, height = int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")
    colour_type = header[25]            # 2 = RGB, no transparency: Apple rejects icons with alpha
    assert (width, height, colour_type) == (1024, 1024, 2)


def test_android_build_leaves_out_the_ios_folder():
    spec = (ROOT / "buildozer.spec").read_text()
    line = next(l for l in spec.splitlines() if l.startswith("source.exclude_dirs"))
    assert "ios" in [part.strip() for part in line.split("=", 1)[1].split(",")]


# -- the native ring buffer, compiled against a stand-in for iOS ----------------
@pytest.fixture(scope="module")
def swmic_stub(tmp_path_factory):
    cython = shutil.which("cython")
    compiler = shutil.which("cc") or shutil.which("gcc")
    if not cython or not compiler:
        pytest.skip("needs Cython and a C compiler")
    out = tmp_path_factory.mktemp("swmic")
    src = ROOT / "ios" / "recipes" / "swmic" / "src"
    subprocess.run([cython, "-3", str(src / "swmic.pyx"), "-o", str(out / "swmic.c")], check=True)
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    result = subprocess.run(
        [compiler, "-shared", "-fPIC", "-O1", "-w", f"-I{sysconfig.get_paths()['include']}", f"-I{src}",
         str(out / "swmic.c"), str(ROOT / "tests" / "ios_stub" / "swmic_stub.c"),
         "-o", str(out / f"swmic{suffix}")], capture_output=True, text=True)
    if result.returncode:
        pytest.skip("could not compile the stub: " + result.stderr[-300:])
    sys.path.insert(0, str(out))
    try:
        sys.modules.pop("swmic", None)
        module = importlib.import_module("swmic")
    finally:
        sys.path.remove(str(out))
        sys.modules.pop("swmic", None)
    return module


def _drain(module, chunk=1000):
    parts = []
    while True:
        data = module.read(chunk)
        if not data:
            return np.concatenate(parts) if parts else np.zeros(0, np.float32)
        parts.append(np.frombuffer(data, dtype=np.float32))


def test_ring_keeps_order_across_the_wrap(swmic_stub):
    swmic_stub.stop()
    swmic_stub.start(100_000)
    assert np.array_equal(_drain(swmic_stub), np.arange(100_000))
    swmic_stub.start(100_000)            # this one wraps past the end of the buffer
    assert np.array_equal(_drain(swmic_stub, 777), np.arange(100_000, 200_000))
    assert swmic_stub.dropped() == 0


def test_ring_drops_newest_when_python_falls_behind(swmic_stub):
    swmic_stub.stop()
    swmic_stub.start(140_000)            # about 3.2 s with nobody reading; the buffer holds 2^17
    got = _drain(swmic_stub)
    assert np.array_equal(got, np.arange(2 ** 17))
    assert swmic_stub.dropped() == 140_000 - 2 ** 17


def test_permission_states_from_the_wrapper(swmic_stub):
    assert swmic_stub.permission() in ("unknown", "granted")
    swmic_stub.request_permission()
    assert swmic_stub.permission() == "granted"
