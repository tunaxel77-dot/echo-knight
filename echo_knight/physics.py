# -*- coding: utf-8 -*-
"""Fisica de cajas: colisiones, movimiento con gravedad y vuelo."""
import array
import math
import random
import sys

import pygame
from .config import *


def solid_hit(lv, x, y, hw, h, is_player):
    x0, x1 = int((x - hw) // TILE), int((x + hw - 0.01) // TILE)
    y0, y1 = int((y - h) // TILE), int((y - 0.01) // TILE)
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            if lv.blocks(tx, ty, is_player):
                return True
    return False


def move_body(lv, b, dt):
    """Movimiento con gravedad: muros solidos y plataformas de un solo sentido
    (se atraviesan desde abajo y se pisan desde arriba)."""
    b.hit_wall = False
    nx = b.x + b.vx * dt
    if solid_hit(lv, nx, b.y, b.hw, b.h, b.is_player):
        b.hit_wall = True
        b.vx = 0.0
    else:
        b.x = nx
    ny = b.y + b.vy * dt
    b.on_ground = False
    if b.vy >= 0:
        row = int((ny - 0.01) // TILE)
        if solid_hit(lv, b.x, ny, b.hw, b.h, b.is_player):
            b.y = row * TILE
            b.vy = 0.0
            b.on_ground = True
        else:
            land = False
            if ny > row * TILE and b.y <= row * TILE + 0.01:
                for tx in range(int((b.x - b.hw) // TILE), int((b.x + b.hw - 0.01) // TILE) + 1):
                    if lv.is_plat(tx, row):
                        land = True
                        break
            if land:
                b.y = row * TILE
                b.vy = 0.0
                b.on_ground = True
            else:
                b.y = ny
    else:
        if solid_hit(lv, b.x, ny, b.hw, b.h, b.is_player):
            b.vy = 0.0
        else:
            b.y = ny


def move_fly(lv, b, dt):
    nx = b.x + b.vx * dt
    if solid_hit(lv, nx, b.y, b.hw, b.h, False):
        b.vx *= -0.3
    else:
        b.x = nx
    ny = b.y + b.vy * dt
    if solid_hit(lv, b.x, ny, b.hw, b.h, False):
        b.vy *= -0.3
    else:
        b.y = ny


def boxes_overlap(a, b):
    return (abs(a.x - b.x) < a.hw + b.hw and
            abs((a.y - a.h / 2) - (b.y - b.h / 2)) < (a.h + b.h) / 2)


# ----------------------------------------------------------------------------
