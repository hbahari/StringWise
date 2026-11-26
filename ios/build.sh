#!/bin/bash
# Build the StringWise iOS app. Runs on a Mac (or the GitHub macOS runner).
#
#   ios/build.sh                 compile everything, create and configure the Xcode project
#   ios/build.sh simulator       ...then build for the iOS Simulator
#   ios/build.sh device          ...then build an unsigned iPhone app (checks it compiles)
#
# Needs: Xcode, Python 3.11+, Homebrew packages autoconf automake libtool pkg-config.
# The first run takes a long time (Python, Kivy and NumPy are compiled for iOS);
# later runs reuse ios/build/kivy-ios.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
WORK="$HERE/build"
BUILD_NUMBER="${IOS_BUILD_NUMBER:-1}"
# Pinned so a change upstream can't break a build we know works.
KIVY_IOS="git+https://github.com/kivy/kivy-ios@fd363d49eddb5ac06766348738bd89c7d46007f8"
RECIPES="python3 kivy numpy pyobjus swmic"

mkdir -p "$WORK/kivy-ios"
cd "$WORK"

if [ ! -d venv ]; then
    python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet "$KIVY_IOS" "Cython==0.29.37"

# 1. Compile the libraries for iPhone and the Simulator.
cd "$WORK/kivy-ios"
# shellcheck disable=SC2086
toolchain build $RECIPES --add-custom-recipe "$HERE/recipes/swmic"

# 2. Copy only the app itself (no tests, docs or Android files) for Xcode to bundle.
rm -rf "$WORK/app"
mkdir -p "$WORK/app"
cp "$ROOT/main.py" "$WORK/app/"
rsync -a --exclude '__pycache__' --exclude '*.pyc' "$ROOT/stringwise" "$WORK/app/"

# 3. Make the Xcode project once, then configure it every time.
if [ -d stringwise-ios ]; then
    toolchain update stringwise-ios        # picks up newly built libraries
else
    toolchain create StringWise "$WORK/app"
fi
python "$HERE/configure_xcode.py" stringwise-ios --build "$BUILD_NUMBER"

PROJECT="stringwise-ios/stringwise.xcodeproj"
case "${1:-}" in
    simulator)
        if [ "$(uname -m)" = "arm64" ]; then SIM_ARCH=arm64; else SIM_ARCH=x86_64; fi
        xcodebuild -project "$PROJECT" -scheme stringwise -configuration Release \
            -destination 'generic/platform=iOS Simulator' -derivedDataPath "$WORK/derived" \
            build CODE_SIGNING_ALLOWED=NO ARCHS="$SIM_ARCH"
        echo "Simulator app: $WORK/derived/Build/Products/Release-iphonesimulator/stringwise.app"
        ;;
    device)
        xcodebuild -project "$PROJECT" -scheme stringwise -configuration Release \
            -destination 'generic/platform=iOS' -derivedDataPath "$WORK/derived" \
            build CODE_SIGNING_ALLOWED=NO
        ;;
    "")
        echo "Xcode project ready: $WORK/kivy-ios/$PROJECT"
        ;;
    *)
        echo "Unknown option: $1 (use simulator or device)" >&2
        exit 2
        ;;
esac
