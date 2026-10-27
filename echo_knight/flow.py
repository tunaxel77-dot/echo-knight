# -*- coding: utf-8 -*-
"""Carga de menu / niveles del modo NIVELES."""
import array
import math
import random
import sys

import pygame
from .config import *
from .achievements import ach_notify
from .texts import *
from .sprites_data import *
from .sprites import *
from .lighting import *
from .physics import *
from .levels_data import *
from .level import *
from .entities import *


class LevelFlowMixin:
    """Carga de menu / niveles del modo NIVELES."""

    # ------------------------------------------------------------ niveles
    def load_menu(self):
        ach_notify(self, "flush")
        self.char = "knight"                      # la demo del menu usa siempre al caballero
        self.init_run_stats()
        self.mode = "levels"
        self.level = self.menu_level
        sx, sy = self.level.start
        self.player = Player(sx, sy)
        self.player.on_ground = True
        self.monsters = []
        self.reset_runtime()
        self.menu_t = 0.0
        self.menu_help = False
        self.demo_reset()

    def start_game(self, tutorial=True):
        self.char = self.sel_char                 # ronda 4: personaje elegido
        self.init_run_stats()
        self.mode = "levels"
        self.level_idx = 0
        self.total_time = 0.0
        self.kills = 0
        self.has_shield = False          # escudo y arco se pierden al empezar partida nueva
        self.has_bow = False
        self.shield_warned = False
        self.apply_char_loadout()
        self.load_level(-1 if tutorial else 0)

    def load_level(self, idx):
        spec = TUTORIAL_ARENA if idx < 0 else LEVELS[idx]
        self.tutorial = idx < 0
        self.level_idx = idx
        self.level = Level(spec, self.tex)
        sx, sy = self.level.start
        self.player = Player(sx, sy)
        self.player.hp = self.max_hp
        self.monsters = [Ghoul(x, y, idx * 100 + i) for i, (x, y) in enumerate(self.level.ghoul_spawns)]
        self.monsters += [Bat(x, y, idx * 100 + 50 + i) for i, (x, y) in enumerate(self.level.bat_spawns)]
        self.monsters += [Skeleton(x, y, idx * 100 + 80 + i) for i, (x, y) in enumerate(self.level.skel_spawns)]
        self.reset_runtime()
        self.ak_stab = None
        self.restart_arm = 0.0
        self.chest_open = bool(self.level.chest) and (
            self.has_bow if self.level.chest_item == "bow" else self.has_shield)
        self.state = "play"
        self.help = False
        self.fade_in = FADE_T
        self.add_wave(sx, sy - 8, "attack", 0.75)
        if idx >= 0:
            msg = "Nivel %d: %s. Derrota a TODOS los monstruos para que aparezca la llave." % (idx + 1, self.level.name)
            if self.level.chest and not self.chest_open:
                msg += " Hay un cofre en la sala: pulsa E junto a él."
            if idx == 1:
                msg += " Las CORRIENTES DE AIRE (partículas cian) te elevan sin saltar."
            if idx == 2:
                msg += " Pulsa Q para solidificar los PUENTES FANTASMA durante unos segundos."
            if idx == 5:
                msg += " ¡Cuidado! Los ESQUELETOS ARQUEROS disparan flechas: esquívalas o bloquéalas."
            if idx == 8:
                msg += " Sube en zigzag por la escalera de plataformas."
            if idx == 10:
                msg += " ¡Hay muchos esqueletos! Ahora patrullan y esquivan mientras disparan."
            if idx == 13:
                msg += " ¡La última arena! Usa todo lo aprendido."
            self.toast(msg, 5.0)
            self.save_progress(idx)                  # ronda 5.2: CONTINUAR (solo niveles >= 2)

    def restart_current(self):
        """Reinicia lo que se esta jugando: la sala/nivel actual o la partida infinita."""
        if self.mode == "endless":
            self.start_endless()
        else:
            self.load_level(self.level_idx)
