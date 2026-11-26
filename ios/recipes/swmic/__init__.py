"""kivy-ios recipe for StringWise's microphone module.

Build it with:  toolchain build swmic --add-custom-recipe ios/recipes/swmic
"""

from kivy_ios.toolchain import CythonRecipe


class SwmicRecipe(CythonRecipe):
    version = "1.0"
    url = "src"
    library = "libswmic.a"
    depends = ["python"]
    pbx_frameworks = ["AVFoundation", "AudioToolbox"]
    hostpython_prerequisites = ["Cython==0.29.37"]

    def install(self):
        self.install_python_package(name=self.so_filename("swmic"), is_dir=False)


recipe = SwmicRecipe()
