# -*- coding: utf-8 -*-
"""Ondas de eco: crear, ruido y dibujo."""
import array
import math
import random
import sys

import pygame
from .config import *
from .texts import *
from .sprites_data import *
from .sprites import *
from .lighting import *
from .physics import *
from .levels_data import *
from .level import *
from .entities import *


class EchoMixin:
    """Ondas de eco: crear, ruido y dibujo."""

    # ------------------------------------------------------------ ondas
    def add_wave(self, x, y, kind, scale=1.0):
        if kind in MUTE_KINDS and getattr(getattr(self, "player", None), "mute_echo", 0.0) > 0:
            return                                  # silenciador: tus ecos estan apagados
        if kind in ("step", "attack", "attack_air"):
            scale *= self.perk_echo                 # carta "eco amplio"
        mr = WAVES[kind]["max_r"] * scale
        n = 96 if mr > 200 else (72 if mr > 100 else (36 if kind == "bounce" else 56))
        rays = cast_rays(self.level, x, y, mr, n)
        w = Wave(x, y, kind, rays, n, scale)
        if kind == "pulse":                     # puntos donde el super eco REBOTA en los muros
            cs, sn = trig(n)
            for i in range(0, n, 8):
                dh = rays[i] - 7.0
                if 8 < dh < mr - 8:
                    w.bounces.append((dh, x + cs[i] * (dh - 5), y + sn[i] * (dh - 5)))
            w.bounces.sort()
        self.waves.append(w)
        if len(self.waves) > 40:
            self.waves.pop(0)

    def make_noise(self, x, y, radius):
        for m in self.monsters:
            if math.hypot(m.x - x, m.y - y) < radius:
                m.chase_t = max(m.chase_t, 4.0)
                if hasattr(m, "last_seen"):
                    m.last_seen = (x, y)                 # va al sitio de donde vino el ruido

    def draw_wave(self, w):
        BW, K = w.bw, w.kk
        fade = max(0.0, 1.0 - w.r / w.max_r) ** 0.75
        if fade <= 0.01:
            return
        n, rays = w.n, w.rays
        cs, sn = trig(n)
        x, y, r = w.x, w.y, w.r
        rect = pygame.Rect(int(x - r - 10), int(y - r - 10), int(2 * r + 20), int(2 * r + 20)).clip(self.tmp.get_rect())
        if rect.w <= 0 or rect.h <= 0:
            return
        self.tmp.fill((0, 0, 0), rect)
        cr, cg, cb = w.color
        poly = pygame.draw.polygon
        tmp = self.tmp
        for k in range(K - 1, -1, -1):
            ro = r - k * BW
            if ro <= 0:
                continue
            ri = max(0.0, ro - BW)
            inten = fade * (1 - k / K) ** 1.4
            col = (int(cr * inten), int(cg * inten), int(cb * inten))
            for i in range(n):
                j = i + 1 if i + 1 < n else 0
                d0, d1 = rays[i], rays[j]
                o0 = ro if ro < d0 else d0
                o1 = ro if ro < d1 else d1
                i0 = ri if ri < d0 else d0
                i1 = ri if ri < d1 else d1
                if o0 <= i0 and o1 <= i1:
                    continue
                poly(tmp, col, ((x + cs[i] * i0, y + sn[i] * i0), (x + cs[i] * o0, y + sn[i] * o0),
                                (x + cs[j] * o1, y + sn[j] * o1), (x + cs[j] * i1, y + sn[j] * i1)))
        if w.after > 0:                          # la sala sigue iluminada tras el frente
            ro = r - K * BW
            if ro > 0:
                inten = fade * w.after
                col = (int(cr * inten), int(cg * inten), int(cb * inten))
                for i in range(n):
                    j = i + 1 if i + 1 < n else 0
                    o0 = ro if ro < rays[i] else rays[i]
                    o1 = ro if ro < rays[j] else rays[j]
                    poly(tmp, col, ((x, y), (x + cs[i] * o0, y + sn[i] * o0),
                                    (x + cs[j] * o1, y + sn[j] * o1)))
        self.light.blit(tmp, rect.topleft, rect, special_flags=pygame.BLEND_RGB_MAX)
