# -*- coding: utf-8 -*-
"""Level (mapa, antorchas, capa estatica) y Wave (onda de eco)."""
import array
import math
import random
import sys

import pygame
from .config import *
from .lighting import *
from .physics import *


class Level:
    def __init__(self, spec, textures):
        self.name = spec["name"]
        self.tex = textures
        self.grid = [list(r) for r in spec["rows"]]
        feet = lambda c, r: (c * TILE + 8, (r + 1) * TILE)
        self.start = feet(*spec["start"])
        self.ghoul_spawns = [feet(c, r) for c, r in spec["ghouls"]]
        self.bat_spawns = [(c * TILE + 8, r * TILE + 8) for c, r in spec["bats"]]
        self.key = (spec["key"][0] * TILE + 8, (spec["key"][1] + 1) * TILE - 8) if spec["key"] else None
        self.chest = feet(*spec["chest"]) if spec["chest"] else None
        self.chest_item = spec.get("chest_item", "shield")
        self.skel_spawns = [feet(c, r) for c, r in spec.get("skels", [])]
        self.vents = list(spec.get("vents", []))
        self.door = (COLS - 1, ROWS - 2)
        self.door_open = False
        self.torches = [(x, y) for y, row in enumerate(self.grid) for x, ch in enumerate(row) if ch == "T"]
        self.ghost_cells = [(x, y) for y, row in enumerate(self.grid) for x, ch in enumerate(row) if ch == "~"]
        self.ghost_t = {}                      # casilla -> segundos que le quedan solida
        self.traps = [(x, y) for y, row in enumerate(self.grid) for x, ch in enumerate(row) if ch == "^"]
        self.trap_t = {}                       # casilla de pinchos -> segundos que se ve (la revela una onda)
        self.static = self.bake()
        self.torch_lights = []
        for (tx, ty) in self.torches:
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if not self.is_wall(tx + dx, ty + dy):
                    ox, oy = tx * TILE + 8 + dx * 10, ty * TILE + 8 + dy * 10
                    surfs = make_torch_surfs(self, ox, oy, 100, (255, 168, 84))
                    self.torch_lights.append(dict(tile=(tx, ty), surfs=surfs,
                                                  phase=random.random() * 6.28))
                    break

    # --- consultas
    def is_wall(self, tx, ty):
        if tx < 0 or ty < 0 or tx >= COLS or ty >= ROWS:
            return True
        return self.grid[ty][tx] in "#TE"

    def is_plat(self, tx, ty):
        if tx < 0 or ty < 0 or tx >= COLS or ty >= ROWS:
            return False
        ch = self.grid[ty][tx]
        if ch == "=":
            return True
        if ch == "~":                          # puente fantasma: solido solo si esta activo
            return self.ghost_t.get((tx, ty), 0.0) > 0.0
        return False

    def blocks(self, tx, ty, is_player):
        if tx < 0 or ty < 0 or tx >= COLS or ty >= ROWS:
            return True
        ch = self.grid[ty][tx]
        if ch == "E":
            return not (is_player and self.door_open)
        return ch in "#T"

    # --- capa estatica pre-renderizada
    def bake(self):
        T = self.tex
        surf = pygame.Surface((MAP_W, MAP_H))
        rnd = random.Random(42)
        for y in range(ROWS):
            for x in range(COLS):
                if self.grid[y][x] in "#TE":
                    surf.blit(T.walls[(x * 7 + y * 3) % len(T.walls)], (x * TILE, y * TILE))
                else:
                    surf.blit(T.floors[(x * 5 + y * 11 + rnd.randint(0, 3)) % len(T.floors)],
                              (x * TILE, y * TILE))
        for y in range(ROWS):
            for x in range(COLS):
                px, py = x * TILE, y * TILE
                if not self.is_wall(x, y):
                    if self.is_wall(x, y - 1):
                        surf.blit(T.shadow_top, (px, py))
                    if self.is_wall(x - 1, y):
                        surf.blit(T.shadow_left, (px, py))
                    if self.grid[y][x] == "=":
                        surf.blit(T.shadow_top, (px, py + 6))
                        surf.blit(T.plat, (px, py))
                    elif rnd.random() < 0.09:          # escombros y huesos
                        cx, cy = px + rnd.randint(4, 11), py + rnd.randint(4, 11)
                        if rnd.random() < 0.5:
                            for _ in range(4):
                                surf.set_at((cx + rnd.randint(-2, 2), cy + rnd.randint(-2, 2)), (66, 62, 76))
                            surf.set_at((cx, cy), (118, 114, 130))
                        else:
                            for i in range(-2, 3):
                                surf.set_at((cx + i, cy), (206, 198, 176))
                            surf.set_at((cx - 2, cy - 1), (206, 198, 176))
                            surf.set_at((cx + 2, cy + 1), (206, 198, 176))
                elif y > 0 and not self.is_wall(x, y - 1):
                    surf.blit(T.edge_light, (px, py))
        # rejillas de las corrientes de aire en el suelo
        for (x0, y0, x1, y1) in self.vents:
            for tx in range(x0 // TILE, x1 // TILE):
                gx, gy = tx * TILE, (ROWS - 2) * TILE
                pygame.draw.rect(surf, (30, 36, 50), (gx + 2, gy + 9, 12, 7))
                for i in range(3):
                    pygame.draw.line(surf, (96, 160, 190), (gx + 3 + i * 4, gy + 10), (gx + 3 + i * 4, gy + 14))
        surf.blit(T.edge_fade, (0, 0), special_flags=pygame.BLEND_RGB_MULT)   # bordes difuminados
        return surf.convert()


class Wave:
    __slots__ = ("x", "y", "r", "kind", "color", "max_r", "speed", "rays", "n",
                 "bw", "kk", "after", "bounces")

    def __init__(self, x, y, kind, rays, n, scale=1.0):
        cfg = WAVES[kind]
        self.x, self.y, self.kind = x, y, kind
        self.color = cfg["color"]
        self.max_r = cfg["max_r"] * scale
        self.speed = cfg["speed"]
        self.r = 2.0
        self.rays = rays
        self.n = n
        self.bw = cfg.get("bw", 5.0)         # grosor de cada anillo
        self.kk = cfg.get("k", 5)            # numero de anillos
        self.after = cfg.get("after", 0.0)   # luz que queda detras del frente
        self.bounces = []                    # rebotes pendientes (distancia, x, y)
