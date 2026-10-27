# -*- coding: utf-8 -*-
"""HUD inferior (corazones, llave, escudo, arco, eco)."""
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
from .characters import char_of


class HudMixin:
    """HUD inferior (corazones, llave, escudo, arco, eco)."""

    def draw_hud(self):
        c, T = self.canvas, self.tex
        pygame.draw.rect(c, (30, 26, 40), (0, MAP_H, LW, HUD_H))
        pygame.draw.line(c, (160, 120, 52), (0, MAP_H), (LW, MAP_H))
        pygame.draw.line(c, (82, 60, 34), (0, MAP_H + 1), (LW, MAP_H + 1))
        if self.state in ("menu", "select") or (self.state == "options" and self.opt_return == "menu"):
            return
        p = self.player
        step = 11 if self.max_hp <= 3 else max(4, 36 // self.max_hp)      # con muchos corazones se solapan
        for i in range(self.max_hp):
            c.blit(T.heart_full if i < p.hp else T.heart_empty, (5 + i * step, MAP_H + 5))
        if self.mode == "endless":
            self.draw_perk_icons(c)
        c.blit(T.key if self.has_key else T.key_dim, (44, MAP_H + 1))
        if self.has_shield and not self.fighter_mode:      # icono del escudo (solo si lo tienes; luchador usa guardia)
            pygame.draw.rect(c, (20, 18, 30), (63, MAP_H + 3, 8, 11))
            pygame.draw.rect(c, (92, 108, 150), (64, MAP_H + 4, 6, 9))
            pygame.draw.rect(c, (206, 214, 230), (64, MAP_H + 4, 6, 9), 1)
            pygame.draw.rect(c, GOLD, (66, MAP_H + 7, 2, 3))
        ranged = self.has_bow or self.anakin_mode or self.fighter_mode
        if self.anakin_mode:                     # icono de la FUERZA (orbe rojo)
            pygame.draw.circle(c, self.tc((110, 8, 10)), (80, MAP_H + 8), 5)
            pygame.draw.circle(c, self.tc((255, 60, 44)), (80, MAP_H + 8), 4)
            pygame.draw.circle(c, self.tc((255, 225, 205)), (80, MAP_H + 8), 2)
        elif self.fighter_mode:                     # icono del puño de aire (luchador)
            pygame.draw.circle(c, (140, 150, 190), (80, MAP_H + 8), 5)
            pygame.draw.circle(c, (255, 255, 255), (80, MAP_H + 8), 4)
            pygame.draw.rect(c, (214, 52, 56), (77, MAP_H + 6, 6, 3))
        elif self.has_bow and char_of(self)["shot"] == "orb":   # icono de la bola magica (mago)
            pygame.draw.circle(c, (50, 100, 220), (80, MAP_H + 8), 5)
            pygame.draw.circle(c, (140, 215, 255), (80, MAP_H + 8), 3)
            pygame.draw.circle(c, (255, 255, 255), (80, MAP_H + 8), 1)
        elif self.has_bow:                       # icono del arco
            pygame.draw.lines(c, (176, 120, 60), False, [(78, MAP_H + 3), (82, MAP_H + 5), (83, MAP_H + 8),
                                                         (82, MAP_H + 11), (78, MAP_H + 13)], 2)
            pygame.draw.line(c, (232, 220, 190), (78, MAP_H + 3), (78, MAP_H + 13))
        if self.fighter_mode and p.clap_cd > 0:                 # luchador: el aplauso se esta recargando (barra gris)
            pygame.draw.rect(c, (12, 10, 18), (87, MAP_H + 5, 20, 6))
            pygame.draw.rect(c, (110, 120, 160), (88, MAP_H + 6, int(18 * max(0.0, 1.0 - p.clap_cd / FT_SUPER_CD)), 4))
        elif ranged and p.charging and p.charge > 0.05:         # barra de carga del super disparo
            qq = min(1.0, p.charge / self.charge_t())
            pygame.draw.rect(c, (12, 10, 18), (87, MAP_H + 5, 20, 6))
            pygame.draw.rect(c, (255, 255, 255) if (qq >= 1 and int(self.time * 10) % 2 == 0)
                             else (self.tc((255, 70, 50)) if self.anakin_mode else ((235, 242, 255) if self.fighter_mode else (255, 225, 150))),
                             (88, MAP_H + 6, int(18 * qq), 4))
        bx, by, bw = 112, MAP_H + 5, 36
        pygame.draw.rect(c, (12, 10, 18), (bx - 1, by - 1, bw + 2, 8))
        ready = 1.0 - p.pulse_cd / PULSE_COOLDOWN
        col = CYAN if ready >= 1 else (70, 110, 150)
        pygame.draw.rect(c, col, (bx, by, int(bw * ready), 6))
        if ready >= 1 and int(self.time * 3) % 2 == 0:
            pygame.draw.rect(c, (230, 250, 255), (bx, by, bw, 1))
