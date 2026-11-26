from distutils.core import setup, Extension

setup(name="swmic",
      version="1.0",
      ext_modules=[Extension("swmic", ["swmic.c", "swmic_ios.m"])])
