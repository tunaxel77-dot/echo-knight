# -*- coding: utf-8 -*-
"""Pulido visual (ronda 1): particulas, temblor de pantalla, camara lenta, fundidos y muerte.

Todo sale de config.py (bloque PULIDO). Para usar un efecto desde cualquier mixin:
    self.burst(x, y, colores, cantidad, velocidad)   # chispas / polvo
    self.add_shake(2.0)                              # temblor (px logicos)
    self.slowmo = 0.5                                # camara lenta (segundos reales)
    self.fade_in = FADE_T                            # fundido de negro a imagen
"""
import math
import random

import pygame
from .config import *
from .achievements import ach_notify

DUST = ((168, 156, 132), (122, 112, 96), (200, 190, 168))
HIT_SPARKS = {"ghoul": ((190, 150, 255), (235, 220, 255), (150, 110, 230)),
              "skel": ((240, 238, 215), (200, 200, 180), (255, 255, 240)),
              "bat": ((255, 150, 210), (255, 210, 235), (230, 100, 170))}
DEATH_COLORS = ((206, 214, 230), (132, 142, 170), (220, 70, 70), (246, 206, 72), (255, 255, 255))


class PolishMixin:
    """Efectos de pulido."""

    def init_polish(self):
        self.shake = 0.0
        self.slowmo = 0.0
        self.fade_in = 0.0
        self._fade_surf = None

    # ------------------------------------------------------------ utilidades
    def add_shake(self, mag):
        self.shake = max(self.shake, min(SHAKE_MAX, mag))

    def burst(self, x, y, colors, n, speed, up=0.0, life=(0.25, 0.55)):
        """Chispas en abanico. up > 0 las lanza hacia arriba (polvo, golpes)."""
        for _ in range(n):
            a = random.uniform(0.0, 6.283)
            sp = random.uniform(0.3, 1.0) * speed
            lf = random.uniform(*life)
            self.sparks.append([x + random.uniform(-2, 2), y + random.uniform(-2, 2),
                                math.cos(a) * sp, math.sin(a) * sp - up, lf, lf,
                                random.choice(colors)])
        if len(self.sparks) > 260:
            del self.sparks[:len(self.sparks) - 260]

    def landing_dust(self, x, y, fall):
        q = min(1.0, fall / 300.0)
        n = 3 + int(7 * q)
        for side in (-1, 1):
            for _ in range(n // 2 + 1):
                lf = random.uniform(0.2, 0.45)
                self.sparks.append([x + side * random.uniform(1, 4), y - 1,
                                    side * random.uniform(15, 60) * (0.5 + q), -random.uniform(10, 40),
                                    lf, lf, random.choice(DUST)])

    def hit_fx(self, m):
        """Chispas del color del monstruo al recibir un golpe."""
        self.burst(m.x, m.y - m.h / 2, HIT_SPARKS.get(m.kind, DUST), 9, 110, up=20)
        self.add_shake(SHAKE_HIT)

    def death_fx(self):
        """Muerte del caballero: la armadura salta en pedazos."""
        p = self.player
        ach_notify(self, "flush")
        self.burst(p.x, p.y - 8, DEATH_COLORS, 46, 170, up=70, life=(0.5, 1.1))
        self.add_wave(p.x, p.y - 8, "death", 1.6)
        self.add_shake(SHAKE_DEATH)

    # ------------------------------------------------------------ por fotograma
    def polish_dt(self, dt):
        """Llamar al inicio de update(): decae el temblor y aplica la camara lenta. Devuelve dt."""
        self.shake = max(0.0, self.shake - SHAKE_DECAY * dt)
        if self.fade_in > 0:
            self.fade_in = max(0.0, self.fade_in - dt)
        if self.slowmo > 0:
            self.slowmo -= dt
            return dt * SLOWMO_SCALE
        return dt

    def shake_offset(self):
        if self.shake < 0.3:
            return 0, 0
        m = int(round(self.shake))
        return random.randint(-m, m), random.randint(-m, m)

    def fade_alpha(self):
        """0..255: negro que sube al salir de la sala y baja al entrar."""
        a = 0.0
        if self.state == "clear" and self.clear_t < FADE_T:
            a = 1.0 - max(0.0, self.clear_t) / FADE_T
        if self.fade_in > 0:
            a = max(a, self.fade_in / FADE_T)
        return int(255 * max(0.0, min(1.0, a)))

    def draw_fade(self):
        a = self.fade_alpha()
        if a <= 0:
            return
        if self._fade_surf is None or self._fade_surf.get_size() != (self.SW, self.SH):
            self._fade_surf = pygame.Surface((self.SW, self.SH))
            self._fade_surf.fill((0, 0, 0))
        self._fade_surf.set_alpha(a)
        self.screen.blit(self._fade_surf, (0, 0))
