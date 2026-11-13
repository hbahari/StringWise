[app]
title = StringWise
# Package id = package.domain + "." + package.name = golemapps.stringwise.app
# This must never change: it is the id of the existing Play Store listing.
package.name = app
package.domain = golemapps.stringwise

source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,txt
source.exclude_dirs = tests, bin, venv, .venv, .buildozer, .github, .git, __pycache__

# Shown to users in the Play Store.
version = 2.0.0
# Play's version code. Raise it by at least 1 for every upload, and keep it
# higher than any code you have already used for this app.
android.numeric_version = 7

# charset_normalizer is not used by the app. It is listed so the build tool
# treats it as an ordinary module; left to itself it picks an Android-only
# file for it that its own installer then refuses.
requirements = python3,kivy==2.3.1,numpy,pyjnius,android,charset_normalizer

orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/stringwise/assets/images/icon.png
presplash.filename = %(source.dir)s/stringwise/assets/images/presplash.png
android.presplash_color = #2b1810

# The microphone is the only permission. The app never uses the network.
android.permissions = android.permission.RECORD_AUDIO

# Google Play requires target API 36 and 16 KB page support; NDK r28 builds
# 16 KB-aligned libraries by default.
android.api = 36
android.minapi = 24
android.ndk = 28c
android.ndk_api = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

android.release_artifact = aab
android.debug_artifact = apk

p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 0
