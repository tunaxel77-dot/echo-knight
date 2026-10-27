[app]
title = Echo Knight Movil
package.name = echoknightmovil
package.domain = org.tunaxel
source.dir = .
source.include_exts = py,json
source.exclude_dirs = venv,bin,.github,__pycache__,.buildozer
version = 0.1.0

# pygame-ce NO viene en python-for-android: la receta local esta en ./p4a-recipes/pygame-ce
requirements = python3,pygame-ce
# Si la compilacion falla por Cython, prueba:  requirements = python3,pygame-ce,cython==0.29.36

orientation = landscape
fullscreen = 1

android.api = 34
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

p4a.local_recipes = ./p4a-recipes

[buildozer]
log_level = 2
warn_on_root = 1
