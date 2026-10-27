# -*- coding: utf-8 -*-
"""Receta local de python-for-android para pygame-ce (SDL2).
ESTADO: SIN PROBAR. Escrita siguiendo la receta 'pygame' 2.x de python-for-android y la guia publica
https://gist.github.com/emersonmx/c5bba202506e3c3d2d828ad278a8d5fe (misma estructura: version 2.5.0,
dependencias sdl2/sdl2_image/sdl2_mixer/sdl2_ttf/setuptools/jpeg/png, plantilla buildconfig/Setup.Android.SDL2.in).
Si falla al compilar, sustituye este archivo por el de esa guia (boton 'Raw') y vuelve a lanzar la compilacion.
Aviso heredado: freetype, postmidi y libjpeg no forman parte del build; es usable pero incompleto."""
from os.path import join

from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.util import current_directory


class Pygame2Recipe(CompiledComponentsPythonRecipe):
    version = "2.5.0"
    url = "https://github.com/pygame-community/pygame-ce/archive/refs/tags/{version}.tar.gz"
    site_packages_name = "pygame"
    name = "pygame-ce"
    depends = ["sdl2", "sdl2_image", "sdl2_mixer", "sdl2_ttf", "setuptools", "jpeg", "png"]
    call_hostpython_via_targetpython = False      # por setuptools
    install_in_hostpython = False

    def get_recipe_env(self, arch=None, with_flags_in_cc=True):
        env = super().get_recipe_env(arch, with_flags_in_cc)
        env["USE_SDL2"] = "1"
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            with open(join("buildconfig", "Setup.Android.SDL2.in")) as f:
                setup_template = f.read()
            bd = self.ctx.bootstrap.build_dir
            ndk_lib_dir = join(self.ctx.ndk_platform, "usr", "lib")
            png = self.get_recipe("png", self.ctx)
            png_lib_dir = join(png.get_build_dir(arch.arch), ".libs")
            png_inc_dir = png.get_build_dir(arch)
            jpeg = self.get_recipe("jpeg", self.ctx)
            jpeg_inc_dir = jpeg_lib_dir = jpeg.get_build_dir(arch.arch)
            setup_file = setup_template.format(
                sdl_includes=(" -I" + join(bd, "jni", "SDL", "include") + " -L" + join(bd, "libs", arch.arch)
                              + " -L" + png_lib_dir + " -L" + jpeg_lib_dir + " -L" + ndk_lib_dir),
                sdl_ttf_includes="-I" + join(bd, "jni", "SDL2_ttf"),
                sdl_image_includes="-I" + join(bd, "jni", "SDL2_image"),
                sdl_mixer_includes="-I" + join(bd, "jni", "SDL2_mixer"),
                jpeg_includes="-I" + jpeg_inc_dir,
                png_includes="-I" + png_inc_dir,
                freetype_includes="",
            )
            with open("Setup", "w") as f:
                f.write(setup_file)


recipe = Pygame2Recipe()
