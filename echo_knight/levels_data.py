# -*- coding: utf-8 -*-
"""Disenos de arenas del MODO NIVELES (funcion arena() y lista LEVELS)."""
import array
import math
import random
import sys

import pygame
from .config import *


DEFAULT_TORCHES = ((6, 0), (12, 0), (18, 0), (0, 7), (COLS - 1, 6), (9, ROWS - 1), (15, ROWS - 1))
LEDGES = ((2, 6, 9), (2, 14, 17))       # repisas altas en coordenadas NUEVAS (usan el espacio extra)


def arena(name, plats, ghouls, bats, key, start, chest=None, torches=None,
          skels=(), chest_item="shield", ghosts=(), vents=(), ledges=True, traps=()):
    if torches is None:
        torches = DEFAULT_TORCHES
    g = [["."] * COLS for _ in range(ROWS)]
    for x in range(COLS):
        g[0][x] = "#"
        g[ROWS - 1][x] = "#"
    for y in range(ROWS):
        g[y][0] = "#"
        g[y][COLS - 1] = "#"
    for (r, c0, c1) in plats:
        for c in range(c0 + DX, c1 + DX + 1):
            g[r + DY][c] = "="
    if ledges:
        for (r, c0, c1) in LEDGES:
            for c in range(c0, c1 + 1):
                if g[r][c] == ".":
                    g[r][c] = "="
    for (r, c0, c1) in ghosts:
        for c in range(c0 + DX, c1 + DX + 1):
            if g[r + DY][c] == ".":
                g[r + DY][c] = "~"
    for (r, c0, c1) in traps:                    # pinchos '^' sobre la plataforma de la fila r (10 = suelo)
        for c in range(c0 + DX, c1 + DX + 1):
            if 0 < c < COLS - 1 and g[r + DY - 1][c] == ".":
                g[r + DY - 1][c] = "^"
    for (tx, ty) in torches:
        g[ty][tx] = "T"
    g[ROWS - 2][COLS - 1] = "E"                  # puerta de salida (a ras de suelo)
    sh = lambda q: (q[0] + DX, q[1] + DY)
    vrects = []
    for (c, hgt) in vents:
        x0 = (c + DX) * TILE
        vrects.append((x0, (ROWS - 1 - hgt) * TILE, x0 + 2 * TILE, (ROWS - 1) * TILE))
    return dict(name=name, rows=["".join(r) for r in g],
                ghouls=[sh(q) for q in ghouls], bats=[sh(q) for q in bats],
                key=sh(key) if key else None, start=sh(start),
                chest=sh(chest) if chest else None, skels=[sh(q) for q in skels],
                chest_item=chest_item, vents=vrects)


LEVELS = [
    arena("La Cripta Antigua",
          plats=[(8, 2, 5), (8, 14, 17), (6, 7, 12), (4, 2, 6), (4, 13, 17)],
          ghouls=[(11, 9), (9, 5)], bats=[(4, 2)], key=(15, 3), start=(2, 9), ledges=False),
    arena("Pasadizos Olvidados",
          plats=[(8, 3, 6), (8, 12, 16), (6, 8, 11), (4, 1, 6), (4, 13, 18), (2, 7, 12)],
          ghouls=[(10, 9), (14, 7), (9, 5)], bats=[(3, 3), (16, 2)],
          key=(10, 1), start=(2, 9), chest=(16, 3), vents=[(9, 6)]),
    arena("Catacumbas Susurrantes",
          plats=[(8, 1, 4), (8, 8, 11), (8, 15, 18), (6, 4, 7), (6, 12, 15),
                 (4, 1, 3), (4, 8, 11), (4, 16, 18), (2, 5, 14)],
          ghouls=[(6, 9), (14, 9), (9, 7), (13, 5)], bats=[(3, 2), (17, 2), (10, 3)],
          key=(9, 1), start=(2, 9), ghosts=[(4, 4, 7), (4, 12, 15)], vents=[(13, 6)]),
    arena("El Corazón del Abismo",
          plats=[(8, 1, 3), (8, 8, 11), (8, 16, 18), (6, 4, 7), (6, 12, 15),
                 (4, 1, 3), (4, 8, 11), (4, 16, 18), (2, 5, 7), (2, 12, 14)],
          ghouls=[(6, 9), (10, 9), (14, 9), (9, 7), (13, 5)],
          bats=[(3, 3), (17, 3), (6, 1), (10, 2)], key=(13, 1), start=(2, 9),
          ghosts=[(2, 8, 11), (4, 4, 7), (4, 12, 15)], vents=[(5, 7)]),
    # ---- niveles nuevos -------------------------------------------------
    arena("El Arsenal Maldito",                       # nivel 5: cofre con el ARCO
          plats=[(8, 1, 4), (8, 15, 18), (6, 5, 8), (6, 11, 14), (4, 2, 6), (4, 13, 17), (2, 7, 12)],
          ghouls=[(7, 5), (12, 9), (3, 3)], bats=[(10, 4), (16, 6)],
          key=(9, 1), start=(2, 9), chest=(15, 3), chest_item="bow",
          ghosts=[(6, 9, 10)], vents=[(9, 7)]),
    arena("La Torre del Arquero",                     # nivel 6: aparecen los esqueletos
          plats=[(8, 1, 4), (8, 8, 11), (8, 15, 18), (6, 4, 7), (6, 12, 15),
                 (4, 1, 3), (4, 8, 11), (4, 16, 18), (2, 5, 14)],
          ghouls=[(6, 9), (9, 7)], bats=[(3, 2), (10, 3)], skels=[(17, 3), (2, 3)],
          key=(9, 1), start=(2, 9), ghosts=[(4, 4, 7), (4, 12, 15)], vents=[(16, 7)]),
    arena("Salón de Huesos",                          # nivel 7
          plats=[(8, 2, 5), (8, 8, 11), (8, 14, 17), (6, 5, 8), (6, 11, 14),
                 (4, 2, 5), (4, 8, 11), (4, 14, 17), (2, 5, 8), (2, 11, 14)],
          ghouls=[(8, 9), (12, 9), (6, 5)], bats=[(10, 6), (16, 4)], skels=[(15, 3), (3, 3)],
          key=(7, 1), start=(2, 9), ghosts=[(4, 6, 7), (4, 12, 13)], vents=[(6, 7), (12, 7)]),
    arena("El Trono del Eco",                         # nivel 8
          plats=[(8, 1, 3), (8, 8, 11), (8, 16, 18), (6, 4, 7), (6, 12, 15),
                 (4, 1, 3), (4, 8, 11), (4, 16, 18), (2, 5, 7), (2, 12, 14)],
          ghouls=[(6, 9), (14, 9), (5, 5)], bats=[(3, 6), (17, 6), (10, 1)],
          skels=[(9, 3), (17, 3), (2, 3)], key=(13, 1), start=(2, 9),
          ghosts=[(2, 8, 11), (4, 4, 7), (4, 12, 15)], vents=[(5, 7), (13, 7)]),
    # ---- ampliacion: niveles 9 a 14 -----------------------------------------
    arena("La Escalera Rota",                         # nivel 9: escalera en zigzag
          plats=[(8, 1, 3), (8, 16, 18), (6, 4, 7), (6, 12, 15), (4, 8, 11), (2, 2, 5), (2, 14, 17)],
          ghouls=[(8, 9), (14, 9), (5, 5)], bats=[(10, 3), (3, 3)], skels=[(17, 7)],
          key=(3, 1), start=(2, 9), vents=[(9, 7)]),
    arena("Puentes Etéreos",                          # nivel 10: casi todo son puentes fantasma
          plats=[(8, 1, 3), (8, 16, 18), (4, 8, 11), (2, 5, 14)],
          ghouls=[(6, 9), (14, 9), (9, 3)], bats=[(3, 4), (16, 4), (10, 6)], skels=[(2, 7)],
          key=(9, 1), start=(2, 9), ghosts=[(6, 4, 6), (6, 13, 15), (8, 8, 11)]),
    arena("Foso de Flechas",                          # nivel 11: muchos esqueletos
          plats=[(8, 2, 5), (8, 14, 17), (6, 8, 11), (4, 3, 6), (4, 13, 16), (2, 8, 11)],
          ghouls=[(9, 9), (9, 5)], bats=[(10, 4), (6, 6)], skels=[(3, 7), (16, 7), (15, 3)],
          key=(9, 1), start=(2, 9)),
    arena("Torres Gemelas",                           # nivel 12: dos torres unidas por un puente fantasma
          plats=[(8, 2, 4), (6, 2, 4), (4, 2, 4), (2, 2, 4),
                 (8, 15, 17), (6, 15, 17), (4, 15, 17), (2, 15, 17), (6, 8, 11)],
          ghouls=[(10, 5), (5, 9), (14, 9)], bats=[(9, 3), (6, 2), (13, 2)], skels=[(3, 1), (16, 1)],
          key=(9, 1), start=(2, 9), ghosts=[(2, 5, 14)], vents=[(9, 7)]),
    arena("Corrientes Cruzadas",                      # nivel 13: se sube a golpe de corrientes de aire
          plats=[(8, 8, 11), (4, 3, 6), (4, 13, 16), (2, 8, 11)],
          ghouls=[(5, 9), (14, 9), (9, 7)], bats=[(6, 4), (13, 4), (9, 3), (3, 2)], skels=[(16, 3)],
          key=(9, 1), start=(2, 9), vents=[(3, 7), (9, 7), (15, 7)]),
    arena("La Cámara del Eco Final",                  # nivel 14: final
          plats=[(8, 1, 4), (8, 8, 11), (8, 15, 18), (6, 3, 6), (6, 13, 16), (4, 8, 11),
                 (4, 1, 2), (4, 17, 18), (2, 4, 7), (2, 12, 15)],
          ghouls=[(6, 9), (10, 7), (14, 9), (8, 3)], bats=[(2, 2), (17, 2), (10, 5)],
          skels=[(2, 3), (18, 3), (16, 5)], key=(5, 1), start=(2, 9),
          ghosts=[(2, 8, 11)], vents=[(9, 7)]),
]

MENU_ARENA = arena("Menu", plats=[(8, 2, 5), (8, 14, 17), (6, 8, 11)], ghouls=[], bats=[],
                   key=None, start=(3, 9), ledges=False)

# Sala de practica del mini tutorial (el fantasma aparece mas adelante, ver tut_advance)
TUTORIAL_ARENA = arena("Sala de Práctica", plats=[(8, 7, 11)], ghouls=[], bats=[],
                       key=(16, 9), start=(2, 9), ledges=False)
