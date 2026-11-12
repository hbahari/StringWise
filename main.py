"""Entry point. Buildozer looks for this file."""

import os

from kivy.utils import platform

if platform not in ("android", "ios"):
    # A phone-shaped window for working on a desktop.
    from kivy.config import Config
    Config.set("graphics", "width", os.environ.get("STRINGWISE_WIDTH", "400"))
    Config.set("graphics", "height", os.environ.get("STRINGWISE_HEIGHT", "820"))
    Config.set("input", "mouse", "mouse,multitouch_on_demand")

from stringwise.app import StringWiseApp

if __name__ == "__main__":
    StringWiseApp().run()
