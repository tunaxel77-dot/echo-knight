# -*- coding: utf-8 -*-
"""Dibujo de capa, sable y FUERZA (skins)."""
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


class FxDrawMixin:
    """Dibujo de capa, sable y FUERZA (skins)."""

    # ------------------------------------------------------------ modo ANAKIN
    def draw_cape(self, v, p):
        """Capa animada: cuelga de los hombros, ondea sola, se estira al correr / dash
        y se levanta con furia mientras cargas la FUERZA. (Negra en Vader, parda en Anakin.)"""
        f = p.face
        vd = self.skin == "vader"
        ch = min(1.0, p.charge / SUPER_CHARGE_T) if p.charging else 0.0
        sp = 1.0 if p.dash_t > 0 else min(1.0, p.sf)
        sp = max(sp, 0.55 * ch)
        ax, ay = (p.x - f * 4.5, p.y - 12.5) if vd else (p.x - f * 3.5, p.y - 8.5)     # hombros
        cl = 13.0 if vd else 10.0
        c_body, c_edge, c_hem = (((14, 14, 20), (74, 74, 90), (40, 40, 52)) if vd
                                 else ((38, 26, 22), (112, 84, 62), (70, 50, 40)))
        if not p.on_ground:
            lift = max(-1.0, min(1.0, -p.vy / 140.0))        # al caer, la capa sube; al saltar, cae
        else:
            lift = 0.0
        lift = max(lift, 0.7 * ch)
        n = 9
        pts = []
        for i in range(n + 1):
            t = i / n
            wave = math.sin(self.time * (7 + 7 * sp + 6 * ch) - t * 5.2) * (0.5 + 2.8 * sp + 0.9 * abs(lift)) * t
            idle = math.sin(self.time * 2.0 - t * 2.2) * 0.6 * t
            back = -f * t * (2.2 + 14.0 * sp)
            cx = ax + back - idle * f
            cy = ay + t * (cl - 6.0 * sp) + wave - lift * 5.5 * t
            pts.append((cx, cy))
        left, right = [], []
        for i, (cx, cy) in enumerate(pts):
            t = i / n
            if i < n:
                dx, dy = pts[i + 1][0] - cx, pts[i + 1][1] - cy
            else:
                dx, dy = cx - pts[i - 1][0], cy - pts[i - 1][1]
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            w = (1.6 + 3.4 * t) if vd else (1.4 + 3.0 * t)
            left.append((cx + nx * w, cy + ny * w))
            right.append((cx - nx * w, cy - ny * w))
        poly = left + right[::-1]
        pygame.draw.polygon(v, c_body, poly)
        pygame.draw.lines(v, c_edge, False, right, 1)                 # brillo del borde
        pygame.draw.line(v, c_hem, left[-1], right[-1], 1)
        if ch > 0.2:                                                  # destellos al cargar (rojos / azules)
            q = int(150 * ch)
            pygame.draw.lines(v, self.tc((q + 60, 14, 14)), False, left, 1)

    def draw_force_charge(self, v, p):
        """Carga de la FUERZA: orbe que crece en la mano; al llenarse parpadea con halo y rayos."""
        tc = self.tc
        qq = min(1.0, p.charge / SUPER_CHARGE_T)
        full = qq >= 1.0
        hx, hy = self.hand_pos(p)
        cx, cy = int(hx), int(hy)
        rr = 1 + int(5 * qq) + (int(self.time * 16) % 2 if full else 0)
        flick = int(self.time * 12) % 2 == 0
        pygame.draw.circle(v, tc((130, 8, 10)), (cx, cy), rr + 1)
        pygame.draw.circle(v, tc((255, 50, 36)), (cx, cy), rr)
        pygame.draw.circle(v, tc((255, 235, 220)) if (full and flick) else tc((255, 170, 140)), (cx, cy), max(1, rr - 2))
        if qq > 0.35:                                                 # rayos que crepitan hacia la mano
            for i in range(2 + int(3 * qq)):
                a0 = self.time * 9 + i * 2.1
                r0 = rr + 3 + 4 * qq
                x0, y0 = cx + math.cos(a0) * r0, cy + math.sin(a0) * r0
                x1, y1 = cx + math.cos(a0 + 0.4) * (r0 + 3), cy + math.sin(a0 + 0.4) * (r0 + 3)
                pygame.draw.line(v, tc((255, 90, 60)), (x0, y0), (x1, y1), 1)
        if full:                                                      # SUPER CARGA: anillos
            pygame.draw.circle(v, tc((255, 120, 90)), (cx, cy), rr + 3, 1)
            pygame.draw.circle(v, tc((255, 60, 44)), (cx, cy), rr + 6 + int(self.time * 14) % 3, 1)

    def ak_blade(self, v, x0, y0, ang, ln, k=1.0):
        """Sable (rojo en Vader, azul fosforescente en Anakin): empunadura gris, nucleo casi blanco,
        cuerpo de color y halo exterior."""
        tc = self.tc
        ca, sa = math.cos(ang), math.sin(ang)
        hx, hy = x0 + ca * 3.0, y0 + sa * 3.0                      # fin de la empunadura
        pygame.draw.line(v, (30, 30, 36), (x0, y0), (hx, hy), 3)
        pygame.draw.line(v, (128, 128, 140), (x0, y0), (hx, hy), 1)
        ex, ey = x0 + ca * (ln + 3.0), y0 + sa * (ln + 3.0)
        pulse = 0.85 + 0.15 * math.sin(self.time * 14.0)
        pygame.draw.line(v, tc((int(120 * k * pulse), int(8 * k), int(8 * k))), (hx, hy), (ex, ey), 3)
        pygame.draw.line(v, tc((int(255 * k * pulse), int(46 * k), int(34 * k))), (hx, hy), (ex, ey), 2)
        pygame.draw.line(v, tc((255, int(225 * k), int(205 * k))), (hx, hy), (ex, ey), 1)
        return ex, ey

    def draw_ak_sword(self, v, p):
        """Sable emisivo (se dibuja sobre la oscuridad: brilla por si solo)."""
        tc = self.tc
        f = p.face
        hx, hy = self.sword_hand(p)                          # mano
        a_fwd = 0.0 if f > 0 else math.pi
        if self.ak_stab:                                     # espada CLAVADA en el suelo
            sx, gy, d, t, tm = self.ak_stab
            q = max(0.0, min(1.0, t / tm))
            tip = (sx, gy + 1.0)
            dx, dy = (hx - tip[0]), (hy - tip[1])
            dist = math.hypot(dx, dy) or 1.0
            vis = min(12.0, dist) * (0.35 + 0.65 * min(1.0, q * 2.0))   # se va hundiendo al final
            ux, uy = dx / dist, dy / dist
            ex, ey = tip[0] + ux * vis, tip[1] + uy * vis
            pygame.draw.line(v, tc((120, 8, 8)), tip, (ex, ey), 3)
            pygame.draw.line(v, tc((255, 46, 34)), tip, (ex, ey), 2)
            pygame.draw.line(v, tc((255, 215, 190)), tip, (ex, ey), 1)
            pygame.draw.line(v, (60, 56, 66), (ex - uy * 2, ey + ux * 2), (ex + uy * 2, ey - ux * 2), 1)  # guarda
            r = int(2 + (1.0 - q) * 9)                           # onda de choque en el suelo
            pygame.draw.ellipse(v, tc((255, 90, 50)), (int(sx) - r, int(gy) - 1, 2 * r, 3), 1)
            return
        if p.dash_t > 0:                                     # EMBESTIDA: espada al frente como lanza
            bob = math.sin(self.time * 60) * 0.6
            self.ak_blade(v, hx, hy + bob, a_fwd, 19.0)
            return
        if p.windup > 0 or p.attack_t > 0:                   # durante el tajo la hoja sigue el arco
            a0 = 0.0 if p.face > 0 else math.pi
            if p.air_atk:
                a0 += 0.75 * p.face
            if p.windup > 0:
                q = 1.0 - p.windup / WINDUP_T
                ang = a0 - 1.2 - 0.6 * q
            else:
                prog = 1 - p.attack_t / 0.16
                ang = a0 - 1.2 + 2.4 * prog
            self.ak_blade(v, p.x, p.y - 8, ang, 15.0)
            return
        sway = math.sin(self.time * 2.4) * 0.07
        # reposo: hoja hacia arriba y un poco al frente
        ang = (-1.2 + sway) if f > 0 else (-math.pi + 1.2 - sway)
        self.ak_blade(v, hx, hy, ang, 10.0)

    def draw_shield(self, v, p):
        sx = int(p.x + p.face * 6) - 2
        sy = int(p.y) - 13
        flash = self.block_flash > 0
        body = (150, 195, 255) if flash else (92, 108, 150)
        pygame.draw.rect(v, (20, 18, 30), (sx - 1, sy - 1, 6, 13))
        pygame.draw.rect(v, body, (sx, sy, 4, 11))
        pygame.draw.rect(v, (206, 214, 230), (sx, sy, 4, 11), 1)
        pygame.draw.rect(v, GOLD, (sx + 1, sy + 4, 2, 3))

    # ------------------------------------------------------------ LUCHADOR: puñetazos de aire
    def air_crescents(self, v, x, y, d, grow, n=3):
        """Medias lunas blancas que se abren hacia delante (la onda de aire de un puñetazo)."""
        cols = ((255, 255, 255), (222, 232, 255), (168, 188, 232))
        for i in range(n):
            ry = 4.0 + 9.0 * grow + 2.5 * i
            rx = 2.5 + 1.5 * i
            cx = x - d * i * 5.0
            pts = [(cx + d * math.cos(t) * rx, y + math.sin(t) * ry) for t in
                   (-1.25 + 2.5 * j / 8 for j in range(9))]
            pygame.draw.lines(v, cols[i % 3], False, pts, 2 if i == 0 else 1)

    def draw_air_blast(self, v, a):
        """Disparo de LUCHADOR: puño blanco con medias lunas de aire y rayas de velocidad."""
        d = 1 if a.vx > 0 else -1
        grow = min(1.0, a.t / 0.3)
        self.air_crescents(v, a.x, a.y, d, grow)
        for i, oy in enumerate((-5, -1, 3, 6)):                       # rayas de velocidad
            ln = (10 + 5 * i) * (0.7 + 0.3 * math.sin(self.time * 40 + i * 2.1))
            x0 = a.x - d * (7 + 3 * i)
            pygame.draw.line(v, (255, 255, 255) if i % 2 == 0 else (190, 205, 240), (x0, a.y + oy), (x0 - d * ln, a.y + oy), 1)
        pygame.draw.circle(v, (255, 255, 255), (int(a.x), int(a.y)), 2)

    def draw_fighter_punch(self, v, p):
        """Golpe cuerpo a cuerpo de LUCHADOR (en vez del tajo de la espada): puño recto y onda de aire."""
        prog = 1.0 - p.attack_t / 0.16
        d = p.face
        y = p.y - 8 + (4 if p.air_atk else 0)
        x = p.x + d * (11 + 12 * prog)
        self.air_crescents(v, x, y, d, prog, 2)
        pygame.draw.line(v, (255, 255, 255), (p.x + d * 8, y), (x - d * 2, y), 2)

    def draw_clap_charge(self, v, p):
        """Carga de la super onda: una esfera de energia blanca crece frente a los puños; al llenarse parpadea y espera."""
        qq = min(1.0, p.charge / self.charge_t())
        full = qq >= 1.0
        d = p.face
        cx, cy = int(p.x + d * 12), int(p.y - 8)
        rr = 2 + int(8 * qq)
        blink = full and int(self.time * 14) % 2 == 0
        pygame.draw.circle(v, (110, 140, 225), (cx, cy), rr + 3, 1)
        pygame.draw.circle(v, (255, 255, 255) if blink else (200, 218, 255), (cx, cy), rr)
        pygame.draw.circle(v, (255, 255, 255), (cx, cy), max(1, rr // 2))
        if full:
            pygame.draw.circle(v, (255, 255, 255), (cx, cy), rr + 6 + int(self.time * 14) % 3, 1)

    def draw_super_wave(self, v, a):
        """La super onda en vuelo: tres medias lunas altas y brillantes, una detras de otra, con estela."""
        d = 1 if a.vx > 0 else -1
        x, y = int(a.x), int(a.y)
        for i, col in enumerate(((255, 255, 255), (205, 222, 255), (140, 165, 230))):
            back = i * 7
            pts = [(x - d * back + d * abs(dy) // 2, y + dy) for dy in range(-FT_SUPER_VREACH.__int__() + 4, FT_SUPER_VREACH.__int__() - 3, 3)]
            if len(pts) > 1:
                pygame.draw.lines(v, col, False, pts, 2 if i == 0 else 1)
        pygame.draw.line(v, (230, 238, 255), (x - d * 30, y), (x - d * 8, y))

    def draw_clap(self, v, p):
        """El aplauso: medias lunas blancas gigantes que se abren hacia delante y rayas de velocidad."""
        prog = 1.0 - p.clap_t / 0.45
        d = p.face
        x = p.x + d * (12 + 70 * prog)
        y = p.y - 8
        for i in range(4):
            q = max(0.0, prog - 0.12 * i)
            if q <= 0:
                continue
            cx = p.x + d * (12 + 110 * q)
            ry = 6.0 + 30.0 * q
            rx = 4.0 + 5.0 * q
            pts = [(cx + d * math.cos(t) * rx, y + math.sin(t) * ry) for t in (-1.3 + 2.6 * j / 10 for j in range(11))]
            pygame.draw.lines(v, (255, 255, 255) if i == 0 else (200, 215, 250), False, pts, 3 if i == 0 else 1)
        for oy in (-14, -7, 0, 7, 14):
            x0 = p.x + d * (14 + 60 * prog)
            pygame.draw.line(v, (235, 242, 255), (x0, y + oy), (x0 + d * 28 * (1 - 0.5 * prog), y + oy), 1)

    def draw_slam(self, v):
        """IMPACTO del luchador: columna de luz, anillos de choque planos que se expanden y grietas que quedan en el suelo."""
        s = self.slam
        prog = 1.0 - s["t"] / s["tm"]
        x, y, R = s["x"], s["y"], s["r"]
        fade = max(0.0, 1.0 - max(0.0, prog - 0.45) / 0.55)                 # las grietas se desvanecen al final
        for pts in s["cracks"]:
            if fade <= 0.05:
                break
            k = max(0.0, min(1.0, prog * 4.0))
            n = max(2, int(len(pts) * k) + 1)
            seg = pts[:n]
            if len(seg) >= 2:
                pygame.draw.lines(v, (18, 14, 22), False, seg, 2)
                pygame.draw.lines(v, (int(120 + 120 * fade), int(120 + 125 * fade), int(130 + 125 * fade)), False,
                                  [(a, b - 1) for a, b in seg], 1)
        for i in range(3):                                                   # anillos de choque
            q = prog * 1.35 - 0.18 * i
            if 0.0 < q < 1.0:
                rx, ry = 6 + R * 1.6 * q, 2 + 7 * q
                c = int(255 * (1.0 - q))
                pygame.draw.ellipse(v, (c, c, 255 if c > 80 else c), (int(x - rx), int(y - ry), int(2 * rx), int(2 * ry)), 2 if i == 0 else 1)
        if prog < 0.3:                                                       # columna de luz del impacto
            h = int(46 * (1.0 - prog / 0.3) * (0.7 + 0.5 * s["power"]))
            w = max(1, int(5 * (1.0 - prog / 0.3)))
            pygame.draw.rect(v, (255, 255, 255), (int(x - w), int(y - h), 2 * w, h))
            pygame.draw.rect(v, (205, 222, 255), (int(x - w - 2), int(y - h * 0.7), 2 * w + 4, int(h * 0.7)), 1)
