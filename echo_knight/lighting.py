# -*- coding: utf-8 -*-
"""Utilidades de luz: raycasting, resplandores radiales, haces."""
import array
import math
import random
import sys

import pygame
from .config import *


_TRIG = {}


def trig(n):
    if n not in _TRIG:
        _TRIG[n] = ([math.cos(2 * math.pi * i / n) for i in range(n)],
                    [math.sin(2 * math.pi * i / n) for i in range(n)])
    return _TRIG[n]


def cast_rays(level, ox, oy, maxr, n):
    """Lanza n rayos desde (ox,oy). Devuelve la distancia a la que cada rayo
    toca un muro (+7 px para que la cara del muro tambien se ilumine)."""
    cs, sn = trig(n)
    out = []
    for i in range(n):
        cx, cy = cs[i], sn[i]
        d = 0.0
        hit = maxr
        while d < maxr:
            d += 2.0
            if level.is_wall(int((ox + cx * d) // TILE), int((oy + cy * d) // TILE)):
                hit = d
                break
        out.append(min(hit + 7.0, maxr + 7.0))
    return out


def make_radial(radius, color, strength):
    d = radius * 2
    s = pygame.Surface((d, d))
    s.fill((0, 0, 0))
    for y in range(d):
        for x in range(d):
            dist = math.hypot(x - radius + 0.5, y - radius + 0.5)
            if dist < radius:
                v = (1 - dist / radius) ** 1.6 * strength
                s.set_at((x, y), (int(color[0] * v), int(color[1] * v), int(color[2] * v)))
    return s.convert()


def make_beam(w, h, color, strength):
    """Haz de luz elipsoidal (se coloca delante del caballero)."""
    s = pygame.Surface((w, h))
    s.fill((0, 0, 0))
    for y in range(h):
        for x in range(w):
            nx = (x + 0.5 - w / 2) / (w / 2)
            ny = (y + 0.5 - h / 2) / (h / 2)
            d = math.hypot(nx, ny)
            if d < 1:
                v = (1 - d) ** 1.3 * strength
                s.set_at((x, y), (int(color[0] * v), int(color[1] * v), int(color[2] * v)))
    return s.convert()


def make_torch_surfs(level, ox, oy, radius, tint):
    """Luz estatica de antorcha con sombras (3 niveles de parpadeo)."""
    n, K = 96, 12
    rays = cast_rays(level, ox, oy, radius, n)
    cs, sn = trig(n)
    base = pygame.Surface((MAP_W, MAP_H))
    base.fill((0, 0, 0))
    for k in range(K - 1, -1, -1):
        ro = radius * (k + 1) / K
        ri = radius * k / K
        inten = (1 - (k + 0.5) / K) ** 1.5
        col = (int(tint[0] * inten), int(tint[1] * inten), int(tint[2] * inten))
        for i in range(n):
            j = (i + 1) % n
            d0, d1 = rays[i], rays[j]
            o0, o1 = min(ro, d0), min(ro, d1)
            i0, i1 = min(ri, d0), min(ri, d1)
            if o0 <= i0 and o1 <= i1:
                continue
            pts = [(ox + cs[i] * i0, oy + sn[i] * i0), (ox + cs[i] * o0, oy + sn[i] * o0),
                   (ox + cs[j] * o1, oy + sn[j] * o1), (ox + cs[j] * i1, oy + sn[j] * i1)]
            pygame.draw.polygon(base, col, pts)
    base = base.convert()
    out = []
    for f in (0.74, 0.88, 1.0):
        s = base.copy()
        v = int(255 * f)
        s.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
        out.append(s)
    return out
