"""Turn the Xcode project that kivy-ios generates into the StringWise app.

Run after ``toolchain create``:

    python ios/configure_xcode.py stringwise-ios --build 7

It edits Info.plist (name, bundle id, version, microphone wording, portrait
only), limits the app to iPhone, puts in the app icon and colours the launch
screen. It only uses the standard library, so it is tested on Linux too.
"""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

APP_NAME = "StringWise"
BUNDLE_ID = "golemapps.stringwise.app"      # change before registering it with Apple if you prefer another
MIC_REASON = ("StringWise listens to your violin to show whether each note is in tune "
              "and to check your recordings. Nothing is saved or sent anywhere.")
LAUNCH_RGB = (0x2B, 0x18, 0x10)             # the same dark wood as the Android splash


def app_version() -> str:
    text = (ROOT / "stringwise" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'__version__\s*=\s*"([^"]+)"', text).group(1)


def find_plist(project: Path) -> Path:
    found = sorted(project.glob("*-Info.plist"))
    if not found:
        raise SystemExit(f"No *-Info.plist in {project}")
    return found[0]


def find_pbxproj(project: Path) -> Path:
    found = sorted(project.glob("*.xcodeproj/project.pbxproj"))
    if not found:
        raise SystemExit(f"No .xcodeproj in {project}")
    return found[0]


def update_plist(path: Path, version: str, build: str, bundle_id: str) -> dict:
    with path.open("rb") as handle:
        info = plistlib.load(handle)
    info.update({
        "CFBundleDisplayName": APP_NAME,
        "CFBundleName": APP_NAME,
        "CFBundleIdentifier": bundle_id,
        "CFBundleShortVersionString": version,
        "CFBundleVersion": str(build),
        "NSMicrophoneUsageDescription": MIC_REASON,
        "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait"],
        "UIRequiresFullScreen": True,
        "UIStatusBarHidden": True,
        # The app uses no encryption beyond what iOS itself provides, so App Store
        # Connect does not need to ask about export compliance on every upload.
        "ITSAppUsesNonExemptEncryption": False,
    })
    info.pop("UISupportedInterfaceOrientations~ipad", None)
    with path.open("wb") as handle:
        plistlib.dump(info, handle)
    return info


def update_pbxproj(path: Path, bundle_id: str) -> str:
    text = path.read_text(encoding="utf-8")
    # iPhone only for now. iPads still run it, in an iPhone-sized window, and the
    # store listing then needs no iPad screenshots.
    text = re.sub(r'TARGETED_DEVICE_FAMILY = "?[0-9,]+"?;', 'TARGETED_DEVICE_FAMILY = 1;', text)
    if "PRODUCT_BUNDLE_IDENTIFIER" in text:
        text = re.sub(r"PRODUCT_BUNDLE_IDENTIFIER = [^;]+;", f"PRODUCT_BUNDLE_IDENTIFIER = {bundle_id};", text)
    else:
        text = text.replace("INFOPLIST_FILE =", f"PRODUCT_BUNDLE_IDENTIFIER = {bundle_id};\n\t\t\t\tINFOPLIST_FILE =")
    path.write_text(text, encoding="utf-8")
    return text


def install_icon(project: Path, icon: Path) -> Path:
    """Xcode 14 and later build every size from one 1024 px picture."""
    sets = sorted(project.glob("*/Images.xcassets"))
    if not sets:
        raise SystemExit(f"No Images.xcassets in {project}")
    target = sets[0] / "AppIcon.appiconset"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copy(icon, target / "icon-1024.png")
    contents = {
        "images": [{"filename": "icon-1024.png", "idiom": "universal",
                    "platform": "ios", "size": "1024x1024"}],
        "info": {"author": "xcode", "version": 1},
    }
    (target / "Contents.json").write_text(json.dumps(contents, indent=2), encoding="utf-8")
    return target


def style_launch_screen(project: Path, splash_icon: Path) -> None:
    """Dark wood background with the app icon, instead of kivy-ios's black screen."""
    if splash_icon.exists() and (project / "icon.png").exists():
        shutil.copy(splash_icon, project / "icon.png")
    for board in project.glob("Storyboards/*.storyboard"):
        text = board.read_text(encoding="utf-8")
        r, g, b = (round(c / 255, 3) for c in LAUNCH_RGB)
        colour = (f'<color key="backgroundColor" red="{r}" green="{g}" blue="{b}" alpha="1" '
                  f'colorSpace="custom" customColorSpace="sRGB"/>')
        text = re.sub(r'<color key="backgroundColor"[^>]*/>', colour, text)
        board.write_text(text, encoding="utf-8")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project", type=Path, help="folder made by toolchain create, e.g. stringwise-ios")
    parser.add_argument("--build", default="1", help="build number; must go up with every upload")
    parser.add_argument("--version", default=None, help="defaults to stringwise/__init__.py")
    parser.add_argument("--bundle-id", default=BUNDLE_ID)
    parser.add_argument("--icon", type=Path, default=HERE / "assets" / "icon-1024.png")
    args = parser.parse_args(argv)

    version = args.version or app_version()
    update_plist(find_plist(args.project), version, args.build, args.bundle_id)
    update_pbxproj(find_pbxproj(args.project), args.bundle_id)
    install_icon(args.project, args.icon)
    style_launch_screen(args.project, ROOT / "stringwise" / "assets" / "images" / "icon.png")
    print(f"{APP_NAME} {version} ({args.build}), {args.bundle_id}, configured in {args.project}")


if __name__ == "__main__":
    main()
