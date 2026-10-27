# -*- coding: utf-8 -*-
"""Polvo flotando en el haz de luz (ronda 1): unas pocas motas a la deriva alrededor del caballero.
Se dibujan en el mundo ANTES de aplicar la luz, asi que solo se ven donde llega el haz (o una antorcha): en la oscuridad no existen."""
import math
import random

import pygame
from .config import *


class MotesMixin:
    motes = None                # [x, y, vx, vy, fase, edad, vida]

    def _mote_new(self, p, first=False):
        bw, bu, bd = MOTE_BOX
        life = random.uniform(*MOTE_LIFE)
        return [p.x + random.uniform(-bw, bw), p.y - random.uniform(-bd, bu),
                random.uniform(-MOTE_SPEED, MOTE_SPEED), random.uniform(-MOTE_SPEED, MOTE_SPEED) * 0.6,
                random.uniform(0.0, 6.283), random.uniform(0.0, life) if first else 0.0, life]

    def update_motes(self, dt):
        p = getattr(self, "player", None)
        if p is None:
            return
        if self.motes is None:
            self.motes = [self._mote_new(p, True) for _ in range(MOTE_COUNT)]
        t = getattr(self, "time", 0.0)
        bw, bu, bd = MOTE_BOX
        for i, m in enumerate(self.motes):
            m[0] += (m[2] + math.sin(t * 0.9 + m[4]) * 3.0) * dt
            m[1] += (m[3] + math.cos(t * 0.7 + m[4]) * 2.5) * dt
            m[5] += dt
            if m[5] >= m[6] or abs(m[0] - p.x) > bw * 1.2 or not (p.y - bu * 1.2 < m[1] < p.y + bd * 1.2):
                self.motes[i] = self._mote_new(p)            # vuelve a nacer cerca del caballero (se apaga/enciende con fundido)

    def draw_motes(self, v):
        if not self.motes:
            return
        t = getattr(self, "time", 0.0)
        for m in self.motes:
            f = max(0.0, min(1.0, m[5] / 0.7, (m[6] - m[5]) / 0.7))
            c = int(255 * f * (0.55 + 0.45 * math.sin(t * 3.0 + m[4])))
            if c > 12:
                pygame.draw.rect(v, (c, int(c * 0.93), int(c * 0.78)), (int(m[0]), int(m[1]), 1, 1))
