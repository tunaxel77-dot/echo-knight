# -*- coding: utf-8 -*-
"""Clase Textures: todas las superficies pre-renderizadas."""
import array
import math
import random
import sys

import pygame
from .config import *
from .sprites_data import *
from .sprites import *
from .lighting import *
from .variants import build_surfaces


class Textures:
    def __init__(self):
        self.floors = [make_floor(i).convert() for i in range(4)]
        self.walls = [make_wall(i).convert() for i in range(3)]
        self.plat = make_platform().convert()
        self.door_closed = make_door(False).convert()
        self.door_open = make_door(True).convert()
        kr = make_sprite(KNIGHT_RIGHT)
        self.knight = {
            "down": make_sprite(KNIGHT_DOWN).convert_alpha(),
            "right": kr.convert_alpha(),
            "left": pygame.transform.flip(kr, True, False).convert_alpha(),
        }
        # --- caballero: ciclo de 4 pasos + salto + caida
        kn = KNIGHT_RIGHT
        walk = [variant(kn, 14, KN_LEGS_A), variant(kn, 14, KN_LEGS_T, True),
                variant(kn, 14, KN_LEGS_A2), variant(kn, 14, KN_LEGS_T, True)]
        jump = variant(kn, 14, KN_LEGS_UP)
        fall = variant(kn, 14, KN_LEGS_A)
        right = anim_set(kr, walk, jump, fall)
        flip = lambda s: pygame.transform.flip(s, True, False).convert_alpha()
        self.knight_anim = {
            "right": {k: ([x.convert_alpha() for x in v] if isinstance(v, list) else v.convert_alpha())
                      for k, v in right.items()},
            "left": {k: ([flip(x) for x in v] if isinstance(v, list) else flip(v))
                     for k, v in right.items()},
        }
        self.knight_anim_ak = build_knight_anim(AK_PAL, AK_RIGHT, AK_FORCE_ROWS)   # skin ANAKIN
        self.knight_anim_ft = build_knight_anim(FT_PAL, FT_IDLE, extra={"punch": (FT_PUNCH, KN_LEGS_A),
                                                                         "clap": (FT_CLAP, KN_LEGS_T),
                                                                         "slam": (FT_SLAM, KN_LEGS_T),
                                                                         "guard": (FT_GUARD, KN_LEGS_T)})   # skin LUCHADOR
        _sc = lambda s: pygame.transform.smoothscale(s, FT_SIZE).convert_alpha()      # grande, como DARTH VADER
        self.knight_anim_ft = {side: {k: ([_sc(x) for x in v] if isinstance(v, list) else _sc(v))
                                      for k, v in d.items()} for side, d in self.knight_anim_ft.items()}
        self.char_anim = {"knight": self.knight_anim}                              # ronda 4: personajes
        for _cid, (_pal, _rows) in CHAR_SPRITES.items():
            self.char_anim[_cid] = build_knight_anim(_pal, _rows)
        self.knight_anim_vd = build_vader_anim()                                    # skin DARTH VADER
        # --- fantasma: ciclo de caminar
        self.ghoul = make_sprite(GHOUL).convert_alpha()
        self.ghoul_anim = dict(
            idle=self.ghoul,
            walk=[variant(GHOUL, 13, GH_LEGS_A).convert_alpha(),
                  variant(GHOUL, 13, GH_LEGS_T, True).convert_alpha(),
                  self.ghoul,
                  variant(GHOUL, 13, GH_LEGS_T, True).convert_alpha()])
        # --- esqueleto: ciclo de caminar (derecha / izquierda)
        sk = make_sprite(SKEL)
        swalk = [sk, variant(SKEL, 13, SK_LEGS_A), variant(SKEL, 13, SK_LEGS_T, True),
                 variant(SKEL, 13, SK_LEGS_A)]
        self.skel = {"right": sk.convert_alpha(),
                     "left": pygame.transform.flip(sk, True, False).convert_alpha()}
        self.skel_anim = {
            "right": dict(idle=self.skel["right"], walk=[x.convert_alpha() for x in swalk]),
            "left": dict(idle=self.skel["left"], walk=[flip(x) for x in swalk]),
        }
        # --- murcielago: 4 fotogramas (alas arriba, medio, abajo, medio)
        self.bat = [make_sprite(BAT_A).convert_alpha(), make_sprite(BAT_C).convert_alpha(),
                    make_sprite(BAT_B).convert_alpha(), make_sprite(BAT_C).convert_alpha()]
        self.var = build_surfaces(pygame)                      # ronda 6: variantes con rasgos propios (variants.py)
        self.chest = make_sprite(CHEST).convert_alpha()
        self.chest_open = make_sprite(CHEST_OPEN).convert_alpha()
        self.key = make_sprite(KEY).convert_alpha()
        self.key_dim = self.key.copy()
        self.key_dim.fill((70, 70, 80, 255), special_flags=pygame.BLEND_RGBA_MULT)
        self.shadow = pygame.Surface((12, 5), pygame.SRCALPHA)
        pygame.draw.ellipse(self.shadow, (0, 0, 0, 120), (0, 0, 12, 5))
        self.heart_full = make_heart((226, 54, 70), None).convert_alpha()
        self.heart_empty = make_heart((60, 44, 60), None).convert_alpha()
        self.shadow_top = pygame.Surface((TILE, 5), pygame.SRCALPHA)
        for y in range(5):
            self.shadow_top.fill((0, 0, 0, int(120 * (1 - y / 5) ** 1.3)), (0, y, TILE, 1))
        self.shadow_left = pygame.Surface((3, TILE), pygame.SRCALPHA)
        for x in range(3):
            self.shadow_left.fill((0, 0, 0, int(90 * (1 - x / 3))), (x, 0, 1, TILE))
        self.edge_light = pygame.Surface((TILE, 1), pygame.SRCALPHA)
        self.edge_light.fill((210, 190, 170, 70))
        # --- puentes fantasma (activo / dormido)
        self.ghost_on = pygame.Surface((TILE, 6), pygame.SRCALPHA)
        self.ghost_on.fill((110, 215, 245, 170))
        pygame.draw.line(self.ghost_on, (220, 250, 255, 235), (0, 0), (TILE - 1, 0))
        pygame.draw.line(self.ghost_on, (60, 140, 190, 210), (0, 5), (TILE - 1, 5))
        self.ghost_on = self.ghost_on.convert_alpha()
        self.ghost_off = pygame.Surface((TILE, 6), pygame.SRCALPHA)
        self.ghost_off.fill((110, 215, 245, 34))
        pygame.draw.line(self.ghost_off, (150, 220, 240, 95), (0, 0), (TILE - 1, 0))
        self.ghost_off = self.ghost_off.convert_alpha()
        # --- difuminado de los bordes del mapa (suaviza el limite estricto)
        ef = pygame.Surface((MAP_W, MAP_H))
        ef.fill((255, 255, 255))
        FADE = 34
        for i in range(FADE):
            v = int(255 * (0.58 + 0.42 * (i / FADE) ** 1.3))
            pygame.draw.rect(ef, (v, v, v), (i, i, MAP_W - 2 * i, MAP_H - 2 * i), 1)
        self.edge_fade = ef.convert()
