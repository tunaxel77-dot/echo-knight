# -*- coding: utf-8 -*-
"""Rutas de datos de usuario. En Android se usa la carpeta privada de la app (ANDROID_PRIVATE);
en escritorio, la carpeta personal (~), igual que antes."""
import os
import sys


def is_android():
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ or sys.platform == "android"


def data_dir():
    base = os.environ.get("ANDROID_PRIVATE") if is_android() else None
    if not base:
        base = os.path.expanduser("~")
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        pass
    return base


def data_path(name):
    return os.path.join(data_dir(), name)
