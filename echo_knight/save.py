# -*- coding: utf-8 -*-
"""Ronda 5.2 - Guardado unico en ~/.echo_knight_save.json: progreso del modo niveles (CONTINUAR) + record del infinito.
Los logros (ronda 5.3) iran en la misma clave raiz \"achievements\". Los ajustes (teclas, volumen) viven aparte: options.py."""
import json
import os

from .paths import data_path

from .config import *
from .levels_data import LEVELS
from .characters import CHARACTERS

SAVE_FILE = data_path(".echo_knight_save.json")
SAVE_VERSION = 1


def read_save_file():
    """Contenido del archivo de guardado (dict vacio si no existe o esta roto)."""
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def write_save_file(updates):
    """Mezcla `updates` (claves raiz) con lo que ya hay y lo guarda (escritura atomica). True si se pudo."""
    d = read_save_file()
    d.update(updates)
    d["version"] = SAVE_VERSION
    tmp = SAVE_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, SAVE_FILE)
        return True
    except Exception:
        return False


def clean_progress(raw, char_ids):
    """Valida el progreso guardado; devuelve un dict limpio o None si no sirve."""
    if not isinstance(raw, dict):
        return None
    try:
        lvl = int(raw.get("level"))
    except Exception:
        return None
    if not 1 <= lvl < len(LEVELS):
        return None
    cid = raw.get("char")
    try:
        kills = max(0, int(raw.get("kills", 0)))
        total = max(0.0, float(raw.get("total_time", 0.0)))
    except Exception:
        kills, total = 0, 0.0
    return dict(level=lvl, char=cid if cid in char_ids else "knight", has_shield=bool(raw.get("has_shield")),
                has_bow=bool(raw.get("has_bow")), kills=kills, total_time=total)


class SaveMixin:
    """CONTINUAR del modo niveles. `self.progress` = dict valido o None (se mantiene en memoria)."""

    progress = None

    def init_save(self):
        self.progress = clean_progress(read_save_file().get("progress"), CHARACTERS)

    def has_save(self):
        return self.progress is not None

    def save_progress(self, idx):
        """Guarda que vas a jugar el nivel idx (0-based). Solo desde el nivel 2 (idx >= 1): el 1 es trivial de reempezar."""
        if idx < 1 or idx >= len(LEVELS):
            return
        self.progress = dict(level=idx, char=self.char, has_shield=bool(self.has_shield), has_bow=bool(self.has_bow),
                             kills=int(self.kills), total_time=round(float(self.total_time), 2))
        write_save_file({"progress": self.progress})

    def clear_progress(self):
        self.progress = None
        write_save_file({"progress": None})

    def continue_game(self):
        """Retoma el modo niveles donde se guardo (personaje, escudo/arco, bajas y tiempo incluidos)."""
        pr = self.progress
        if pr is None:
            return False
        self.char = pr["char"]
        self.init_run_stats()
        self.mode = "levels"
        self.total_time = pr["total_time"]
        self.kills = pr["kills"]
        self.has_shield = pr["has_shield"]
        self.has_bow = pr["has_bow"]
        self.shield_warned = True
        self.apply_char_loadout()
        self.load_level(pr["level"])
        return True
