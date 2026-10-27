# -*- coding: utf-8 -*-
"""Texto, paneles y teclas."""
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


class TextUIMixin:
    """Texto, paneles y teclas."""

    # ------------------------------------------------------------ texto
    def text_surf(self, s, size, color):
        key = (s, size, color, self.k)
        if key not in self.text_cache:
            base = self.font.render(s, False, color)
            f = self.k / 2.0 * size
            w, h = base.get_size()
            self.text_cache[key] = pygame.transform.scale(base, (max(1, int(w * f)), max(1, int(h * f))))
        return self.text_cache[key]

    def draw_text(self, s, x, y, size=1.0, color=PARCH, anchor="l", shadow=True, surf=None):
        surf = surf or self.screen
        t = self.text_surf(s, size, color)
        if anchor == "c":
            x -= t.get_width() // 2
        elif anchor == "r":
            x -= t.get_width()
        if shadow:
            surf.blit(self.text_surf(s, size, (10, 8, 14)), (x + self.k // 2 + 1, y + self.k // 2 + 1))
        surf.blit(t, (x, y))
        return t.get_height()

    def line_h(self, size=1.0):
        return int(self.font.get_height() * self.k / 2.0 * size)

    def wrap(self, s, size, max_w):
        f = self.k / 2.0 * size
        lines, cur = [], ""
        for w in s.split(" "):
            t = (cur + " " + w).strip()
            if self.font.size(t)[0] * f <= max_w:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    def draw_panel(self, rect, alpha=205):
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        s.fill((14, 12, 22, alpha))
        self.screen.blit(s, rect.topleft)
        pygame.draw.rect(self.screen, (176, 132, 56), rect, self.k // 2 + 1)
        pygame.draw.rect(self.screen, (84, 60, 30), rect.inflate(-self.k * 3, -self.k * 3), 1)

    def draw_key(self, label, x, y):
        f = self.k / 2.0
        t = self.text_surf(label, 1.0, (240, 232, 210))
        w, h = t.get_width() + int(10 * f), t.get_height() + int(6 * f)
        r = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (24, 20, 34), r.move(0, int(2 * f)))
        pygame.draw.rect(self.screen, (66, 58, 84), r)
        pygame.draw.rect(self.screen, (176, 150, 96), r, max(1, int(f // 2)))
        self.screen.blit(t, (x + int(5 * f), y + int(3 * f)))
        return w, h

    def draw_controls(self, x, y, w):
        f = self.k / 2.0
        lh = self.line_h()
        self.draw_text("CONTROLES", x + w // 2, y, 1.3, GOLD, anchor="c")
        y += int(lh * 1.7)
        keycol = int(w * 0.36)
        for keys, desc in (CONTROLS_TOUCH if self.touch_mode else CONTROLS):
            lines = desc.split("\n")
            kx, kh = x, 0
            for kk in keys:
                if kk == "|":
                    self.draw_text("o", kx, y + int(3 * f), 1.0, PARCH)
                    kx += int(12 * f)
                    continue
                kw, kh = self.draw_key(kk, kx, y)
                kx += kw + int(5 * f)
            for i, l in enumerate(lines):
                self.draw_text(l, x + keycol, y + i * lh + (0 if len(lines) > 1 else int(3 * f)), 1.0, PARCH)
            y += max(lh * len(lines), kh) + int(3 * f)
        y += int(3 * f)
        obj = "OBJETIVO: derrota a TODOS los monstruos, toma la LLAVE dorada y cruza la PUERTA de salida."
        for l in self.wrap(obj, 1.0, w):
            self.draw_text(l, x, y, 1.0, GOLD)
            y += lh
