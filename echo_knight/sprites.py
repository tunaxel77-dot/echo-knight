# -*- coding: utf-8 -*-
"""Constructores de sprites y texturas a partir de los mapas de pixeles."""
import array
import math
import random
import sys

import pygame
from .config import *
from .sprites_data import *


def make_sprite(rows):
    surf = pygame.Surface((16, 16), pygame.SRCALPHA)
    for y, row in enumerate(rows[:16]):
        row = row.ljust(16, ".")[:16]
        for x, ch in enumerate(row):
            c = PAL.get(ch)
            if c:
                surf.set_at((x, y), c)
    return surf


def variant(rows, cut, tail, bob=False):
    """Fotograma derivado: sustituye las filas de las piernas (desde `cut`) y,
    opcionalmente, sube el torso 1 px (rebote al caminar)."""
    head = rows[:cut] if not bob else rows[1:cut] + [rows[cut - 1]]
    return make_sprite(list(head) + list(tail))


def make_heart(color, outline):
    surf = pygame.Surface((9, 7), pygame.SRCALPHA)
    for y, row in enumerate(HEART):
        for x, ch in enumerate(row):
            if ch == "#":
                surf.set_at((x, y), color)
    return surf


def make_floor(v):
    rnd = random.Random(77 + v * 13)
    s = pygame.Surface((TILE, TILE))
    base = (88, 84, 100)
    for y in range(TILE):
        for x in range(TILE):
            n = rnd.randint(-7, 7)
            s.set_at((x, y), (base[0] + n, base[1] + n, base[2] + n + 2))
    mortar = (68, 64, 80)          # junta mas suave: se nota menos la cuadricula
    hl = (100, 96, 114)
    pygame.draw.line(s, mortar, (0, 0), (15, 0))
    pygame.draw.line(s, mortar, (0, 0), (0, 15))
    pygame.draw.line(s, hl, (1, 1), (15, 1))
    pygame.draw.line(s, hl, (1, 1), (1, 15))
    if v == 1:      # grieta
        x, y = rnd.randint(4, 10), 3
        for _ in range(9):
            s.set_at((x, y), (46, 42, 56))
            y += 1
            x += rnd.choice((-1, 0, 1))
            x = max(2, min(14, x))
    elif v == 2:    # musgo
        for _ in range(10):
            s.set_at((rnd.randint(2, 14), rnd.randint(2, 14)), (70, 104, 66))
    elif v == 3:    # mancha oscura
        pygame.draw.ellipse(s, (66, 62, 78), (4, 5, 8, 6))
    return s


def make_wall(v):
    rnd = random.Random(500 + v * 7)
    s = pygame.Surface((TILE, TILE))
    mortar = (58, 50, 62)          # mortero mas claro = menos contraste de cuadricula
    s.fill(mortar)
    for r, y0 in enumerate((0, 5, 10)):
        off = 0 if r % 2 == 0 else 4
        for bx in range(-8 + off, TILE, 8):
            x0, x1 = max(bx, 0), min(bx + 7, TILE - 1)
            if x1 < x0:
                continue
            base = rnd.randint(-10, 10)
            col = (128 + base, 100 + base, 94 + base)
            for yy in range(y0, y0 + 4):
                for xx in range(x0, x1 + 1):
                    n = rnd.randint(-5, 5)
                    c = [col[0] + n, col[1] + n, col[2] + n]
                    if yy == y0:
                        c = [c[0] + 9, c[1] + 8, c[2] + 8]
                    elif yy == y0 + 3:
                        c = [c[0] - 13, c[1] - 12, c[2] - 12]
                    s.set_at((xx, yy), tuple(max(0, min(255, q)) for q in c))
    if v == 2:
        for _ in range(8):
            s.set_at((rnd.randint(0, 15), rnd.randint(0, 15)), (74, 100, 70))
    return s


def make_door(opened):
    s = make_wall(0).copy()
    pygame.draw.rect(s, (28, 24, 34), (2, 1, 12, 15))
    pygame.draw.rect(s, (92, 86, 108), (2, 1, 12, 15), 1)
    if not opened:
        pygame.draw.rect(s, (118, 76, 44), (3, 3, 10, 13))
        for x in (5, 8, 10):
            pygame.draw.line(s, (84, 52, 30), (x, 3), (x, 15))
        pygame.draw.line(s, (156, 104, 62), (3, 3), (3, 15))
        pygame.draw.rect(s, (62, 64, 78), (3, 6, 10, 2))
        pygame.draw.rect(s, (62, 64, 78), (3, 12, 10, 2))
        pygame.draw.rect(s, GOLD, (7, 9, 3, 3))
        s.set_at((8, 10), (30, 20, 10))
    else:
        pygame.draw.rect(s, (10, 12, 22), (3, 3, 10, 13))
        pygame.draw.rect(s, (90, 230, 150), (5, 5, 6, 11))
        pygame.draw.rect(s, (200, 255, 220), (7, 7, 2, 9))
        pygame.draw.rect(s, (118, 76, 44), (3, 3, 2, 13))
    return s


def make_platform():
    """Plataforma flotante: el mismo ladrillo de make_wall, en version delgada."""
    w = make_wall(1)
    s = pygame.Surface((TILE, 6))
    s.blit(w, (0, 0), (0, 0, TILE, 6))
    pygame.draw.line(s, (190, 170, 150), (0, 0), (TILE - 1, 0))
    pygame.draw.line(s, (30, 24, 38), (0, 5), (TILE - 1, 5))
    return s


def anim_set(idle, walk, jump, fall):
    return dict(idle=idle, walk=walk, jump=jump, fall=fall)

def _vd_lift(g, left, right):
    """Paso: levanta una pierna una fila."""
    h, w = len(g), len(g[0])
    n = [r[:] for r in g]
    for use, (c0, c1) in ((left, (0, 14)), (right, (14, w))):
        if not use:
            continue
        for y in range(VD_LEG0, h):
            for x in range(c0, c1):
                ch = g[y][x]
                if ch != ".":
                    n[y - 1][x] = ch
                elif y - 1 >= VD_LEG0:
                    n[y - 1][x] = "."
        for x in range(c0, c1):
            n[h - 1][x] = "."
    return n


def _vd_bob(g):
    """Rebote: el torso sube una fila (las piernas se quedan)."""
    n = [r[:] for r in g]
    for y in range(0, VD_LEG0 - 1):
        n[y] = g[y + 1][:]
    return n


def _vd_surf(g):
    h, w = len(g), len(g[0])
    sf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            c = VD_PAL.get(g[y][x])
            if c:
                sf.set_at((x, y), c)
    return pygame.transform.smoothscale(sf, (VD_W, VD_H))


def build_vader_anim():
    idle = [list(r) for r in VD_IDLE]
    one = lambda g: _vd_surf(g).convert_alpha()
    left = dict(idle=one(idle),
                walk=[one(_vd_lift(idle, True, False)), one(_vd_bob(idle)),
                      one(_vd_lift(idle, False, True)), one(_vd_bob(idle))],
                jump=one(_vd_lift(idle, True, True)), fall=one(idle),
                force=one([list(r) for r in VD_FORCE]))
    flip = lambda sf: pygame.transform.flip(sf, True, False).convert_alpha()
    right = {k: ([flip(x) for x in v] if isinstance(v, list) else flip(v)) for k, v in left.items()}
    return {"left": left, "right": right}   # la imagen original mira a la izquierda




def build_knight_anim(pal_over=None, rows=None, force_rows=None, extra=None):
    """Genera el set de animaciones del caballero (opcionalmente con otra paleta y sprite)."""
    saved = dict(PAL)
    if pal_over:
        PAL.update(pal_over)
    try:
        kn = rows or KNIGHT_RIGHT
        kr = make_sprite(kn)
        walk = [variant(kn, 14, KN_LEGS_A), variant(kn, 14, KN_LEGS_T, True),
                variant(kn, 14, KN_LEGS_A2), variant(kn, 14, KN_LEGS_T, True)]
        jump = variant(kn, 14, KN_LEGS_UP)
        fall = variant(kn, 14, KN_LEGS_A)
        right = anim_set(kr, walk, jump, fall)
        if force_rows:
            right["force"] = variant(force_rows, 14, KN_LEGS_A)
        for name, (xrows, xlegs) in (extra or {}).items():       # poses extra (luchador: punch, guard)
            right[name] = variant(xrows, 14, xlegs)
    finally:
        PAL.clear()
        PAL.update(saved)
    flip = lambda sp: pygame.transform.flip(sp, True, False).convert_alpha()
    return {
        "right": {k: ([x.convert_alpha() for x in v] if isinstance(v, list) else v.convert_alpha())
                  for k, v in right.items()},
        "left": {k: ([flip(x) for x in v] if isinstance(v, list) else flip(v))
                 for k, v in right.items()},
    }
