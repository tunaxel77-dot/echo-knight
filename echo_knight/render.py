# -*- coding: utf-8 -*-
"""Dibujo del mundo: sprites, luz, siluetas, efectos."""
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


class RenderMixin:
    """Dibujo del mundo: sprites, luz, siluetas, efectos."""

    # ------------------------------------------------------------ dibujo
    def knight_frame(self, e):
        """Elige el fotograma del caballero: reposo, caminar (4 pasos), salto o caida."""
        T = self.tex
        base = {"vader": T.knight_anim_vd, "anakin": T.knight_anim_ak, "fighter": T.knight_anim_ft}.get(self.skin) or \
            T.char_anim.get(self.char, T.knight_anim)
        A = base["right" if e.face > 0 else "left"]
        if self.fighter_mode:                                     # LUCHADOR: punetazo recto / guardia de boxeador / vuelo
            if not e.on_ground and e.vy > 200:
                return A["punch"]                                 # PICADA: de cabeza con el puño por delante
            if e.on_ground and self.slam and e.land_t > 0:
                return A["slam"]                                  # IMPACTO: puño clavado en el suelo
            if e.shield:
                return A["guard"]
            if e.charging or e.clap_t > 0:
                return A["clap"]                                  # cargando / dando el aplauso
            if e.dash_t > 0 or e.shoot_t > 0 or e.attack_t > 0:
                return A["punch"]
            if not e.on_ground:
                return A["punch"] if abs(e.vx) > 25 else A["jump"]
        if self.anakin_mode and (e.charging or e.shoot_t > 0) and "force" in A:
            return A["force"]                                  # usando la FUERZA (brazo extendido)
        if not e.on_ground:
            return A["jump"] if e.vy < 0 else A["fall"]
        if abs(e.vx) > 6 and self.state in ("play", "paused", "clear"):
            return A["walk"][int(e.walk / 5) % 4]
        return A["idle"]

    def rim_sprite(self, spr, color, fill_k, rim_k, gain=1.0):
        """Silueta legible sobre la oscuridad: contorno de color de 1 px + relleno tenue.
        Se devuelve como superficie RGB sobre NEGRO y se dibuja con BLEND_RGB_MAX: el negro
        no cambia nada, asi que es imposible que aparezca un cuadro oscuro alrededor."""
        w, h = spr.get_size()
        tint = spr.copy()
        tint.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        tint.fill(tuple(color) + (0,), special_flags=pygame.BLEND_RGBA_ADD)
        out = pygame.Surface((w + 2, h + 2))
        out.fill((0, 0, 0))
        for ox, oy in ((0, 1), (2, 1), (1, 0), (1, 2)):
            out.blit(tint, (ox, oy))
        q = int(255 * max(0.0, min(1.0, rim_k)))
        out.fill((q, q, q), special_flags=pygame.BLEND_RGB_MULT)
        out.blit(self.faded(spr, 255 * max(0.0, min(1.0, fill_k))), (1, 1))
        g = int(255 * max(0.0, min(1.0, gain)))
        if g < 255:
            out.fill((g, g, g), special_flags=pygame.BLEND_RGB_MULT)
        return out

    def faded(self, spr, alpha):
        """Copia del sprite con el alfa multiplicado: los pixeles transparentes siguen
        siendo 100% transparentes (sin cuadro de fondo)."""
        s = spr.copy()
        s.fill((255, 255, 255, max(0, min(255, int(alpha)))), special_flags=pygame.BLEND_RGBA_MULT)
        return s

    def player_scale(self, e):
        """Estiramiento al elevarse / caer y compresion al aterrizar (sx, sy)."""
        if e.dash_t > 0:
            return 1.35, 0.86
        if e.land_t > 0:
            q = (e.land_t / LAND_T) * e.land_pow
            return 1.0 + 0.18 * q, 1.0 - 0.22 * q
        if not e.on_ground:
            if e.vy < 0:
                q = min(1.0, -e.vy / JUMP_V)
                return 1.0 - 0.10 * q, 1.0 + 0.14 * q
            q = min(1.0, e.vy / MAX_FALL)
            return 1.0 - 0.07 * q, 1.0 + 0.10 * q
        return 1.0, 1.0

    def player_sprite(self, e):
        """Devuelve (superficie, x, y) del caballero con estiramiento, inclinacion y
        retroceso de anticipacion aplicados. Los pies quedan siempre apoyados en e.y."""
        spr = self.knight_frame(e)
        idle = e.on_ground and abs(e.vx) <= 6
        bob = -1 if (idle and int(self.time * 1.6) % 2 == 1) else 0
        sx, sy = self.player_scale(e)
        sw0, sh0 = spr.get_size()
        w, h = max(1, int(round(sw0 * sx))), max(1, int(round(sh0 * sy)))
        if (w, h) != (sw0, sh0):
            spr = pygame.transform.scale(spr, (w, h))
        ox = 0
        if e.windup > 0:                                  # retroceso del cuerpo al armar el tajo
            ox = -int(round(e.face * 1.5 * (1.0 - e.windup / WINDUP_T)))
        bx, by = int(e.x) - w // 2 + ox, int(e.y) - h + bob
        if abs(e.tilt) > 0.8:
            spr = pygame.transform.rotate(spr, -e.tilt)
            r = spr.get_rect(midbottom=(bx + w // 2, by + h))
            bx, by = r.topleft
        return spr, bx, by

    def render_world(self):
        v, lv, p = self.view, self.level, self.player
        T = self.tex
        self._pdraw = None
        self._mdraw = []
        self._pblink = False
        v.blit(lv.static, (0, 0))
        if lv.door:
            v.blit(T.door_open if lv.door_open else T.door_closed, (lv.door[0] * TILE, lv.door[1] * TILE))
        for cell in lv.ghost_cells:                      # puentes fantasma (solo el contorno si duermen)
            if lv.ghost_t.get(cell, 0.0) <= 0.0:
                v.blit(T.ghost_off, (cell[0] * TILE, cell[1] * TILE))
        for t in lv.torches:
            tx, ty = t
            pygame.draw.rect(v, (74, 52, 34), (tx * TILE + 7, ty * TILE + 8, 2, 5))
            pygame.draw.rect(v, (110, 110, 124), (tx * TILE + 6, ty * TILE + 7, 4, 2))
            fl = int(self.time * 11 + tx * 3 + ty) % 3                    # llama que titila
            pygame.draw.rect(v, (255, 140, 40), (tx * TILE + 6, ty * TILE + 3 - fl % 2, 4, 4 + fl % 2))
            pygame.draw.rect(v, (255, 226, 120), (tx * TILE + 7, ty * TILE + 4 - fl // 2, 2, 3))
        if lv.chest:
            c = lv.chest
            v.blit(T.shadow, (c[0] - 6, c[1] - 3))
            v.blit(T.chest_open if self.chest_open else T.chest, (c[0] - 8, c[1] - 14))
        if lv.key and self.key_visible and not self.has_key:
            bob = int(math.sin(self.time * 3) * 1.5)
            v.blit(T.shadow, (lv.key[0] - 6, lv.key[1] + 4))
            v.blit(T.key, (lv.key[0] - 8, lv.key[1] - 8 + bob))
        self.draw_pickups(v)
        ents = [(m.y, 0, m) for m in self.monsters] + [(p.y + 0.5, 1, p)]
        ents.sort(key=lambda e: e[0])
        for _, kind, e in ents:
            if kind == 0:
                if getattr(e, "special", False) or getattr(e, "elite", False):     # jefes, enemigos nuevos y elites (rasgos propios)
                    self.draw_special_monster(v, e)
                elif e.kind == "ghoul":
                    v.blit(T.shadow, (int(e.x) - 6, int(e.y) - 2))
                    moving = e.on_ground and abs(e.vx) > 4
                    if moving:
                        spr = T.ghoul_anim["walk"][int(self.time * 8 + e.phase) % 4]
                        bob = 0
                    else:
                        spr = T.ghoul_anim["idle"]
                        bob = int(math.sin(self.time * 5 + e.phase) * 1.0) if e.on_ground else 0
                    v.blit(spr, (int(e.x) - 8, int(e.y) - 15 + bob))
                    self._mdraw.append((spr, int(e.x) - 8, int(e.y) - 15 + bob, self.rim_key(e, "ghoul"), getattr(e, "alert", 0.0)))
                elif e.kind == "skel":
                    v.blit(T.shadow, (int(e.x) - 6, int(e.y) - 2))
                    A = T.skel_anim["right" if e.face > 0 else "left"]
                    if e.on_ground and abs(e.vx) > 4:
                        spr = A["walk"][int(self.time * 7 + e.phase) % 4]
                    else:
                        spr = A["idle"]
                    v.blit(spr, (int(e.x) - 8, int(e.y) - 15))
                    self._mdraw.append((spr, int(e.x) - 8, int(e.y) - 15, self.rim_key(e, "skel"), getattr(e, "alert", 0.0)))
                else:
                    fr = int(self.time * (11 if e.chase_t > 0 else 6) + e.phase) % len(T.bat)
                    v.blit(T.bat[fr], (int(e.x) - 8, int(e.y - e.h / 2) - 8))
                    self._mdraw.append((T.bat[fr], int(e.x) - 8, int(e.y - e.h / 2) - 8, self.rim_key(e, "bat"), getattr(e, "alert", 0.0)))
            else:
                if self.state == "dead":
                    continue
                blink = e.inv > 0 and int(self.time * 18) % 2 == 0
                spr, bx, by = self.player_sprite(e)
                if not blink:
                    v.blit(T.shadow, (int(e.x) - 6, int(e.y) - 2))
                    if self.anakin_mode:
                        self.draw_cape(v, e)
                    v.blit(spr, (bx, by))
                self._pdraw = (spr, bx, by)
                self._pblink = blink
                if e.shield and not self.fighter_mode:
                    self.draw_shield(v, e)
                if e.shoot_t > 0 and not self.anakin_mode and not self.fighter_mode and char_of(self)["shot"] == "bow":   # (ANAKIN: FUERZA; mago: baston)
                    bx, by = int(e.x + e.face * 7), int(e.y) - 9
                    pygame.draw.lines(v, (176, 120, 60), False,
                                      [(bx, by - 5), (bx + e.face * 3, by), (bx, by + 5)], 2)
                    pygame.draw.line(v, (232, 220, 190), (bx, by - 5), (bx, by + 5))

        for a in self.arrows:
            if a.style:                                  # ronda 6: proyectiles de jefe (ondas, espiritus, sonicos, bombas)
                self.draw_foe_shot(v, a)
                continue
            if a.air:                                    # onda de aire blanca: medias lunas que se abren
                if a.big:
                    self.draw_super_wave(v, a)
                else:
                    self.draw_air_blast(v, a)
                continue
            if a.orb:                                    # bola magica del mago
                fl = 1 if int(self.time * 18 + a.t * 9) % 2 else 0
                pygame.draw.circle(v, (50, 100, 220), (int(a.x), int(a.y)), 3 + fl)
                pygame.draw.circle(v, (140, 215, 255), (int(a.x), int(a.y)), 2)
                pygame.draw.circle(v, (255, 255, 255), (int(a.x), int(a.y)), 1)
                continue
            if a.force:                                  # carga roja de la FUERZA (orbe)
                fl = 0.5 + 0.5 * math.sin(self.time * 30 + a.t * 9)
                rr = (5 if a.power else 2) + (1 if fl > 0.5 else 0)
                pygame.draw.circle(v, self.tc((150, 10, 12)), (int(a.x), int(a.y)), rr + 1)
                pygame.draw.circle(v, self.tc((255, 50, 36)), (int(a.x), int(a.y)), rr)
                pygame.draw.circle(v, self.tc((255, 225, 205)), (int(a.x), int(a.y)), max(1, rr - 2))
                continue
            ln = math.hypot(a.vx, a.vy) or 1.0
            seg = 16 if a.power else 6
            x2, y2 = a.x - a.vx / ln * seg, a.y - a.vy / ln * seg
            col = (240, 226, 190) if a.owner == "player" else (230, 110, 90)
            pygame.draw.line(v, col, (a.x, a.y), (x2, y2), 2 if a.power else 1)
            pygame.draw.circle(v, (255, 255, 255), (int(a.x), int(a.y)), 1)

        # ---- iluminacion
        L = self.light
        a = self.reveal
        L.fill((int(AMBIENT[0] + 110 * a), int(AMBIENT[1] + 100 * a), int(AMBIENT[2] + 120 * a)))
        if self.torch_fade > 0.01:               # antorchas: solo tras tomar la llave
            TL = self.tl
            TL.fill((0, 0, 0))
            for tl in lv.torch_lights:
                f = (math.sin(self.time * 9 + tl["phase"]) + math.sin(self.time * 13.7 + tl["phase"] * 2) + 2) / 4
                TL.blit(tl["surfs"][max(0, min(2, int(f * 3)))], (0, 0), special_flags=pygame.BLEND_RGB_MAX)
            if self.torch_fade < 0.99:
                q = int(255 * self.torch_fade)
                TL.fill((q, q, q), special_flags=pygame.BLEND_RGB_MULT)
            L.blit(TL, (0, 0), special_flags=pygame.BLEND_RGB_MAX)
        for w in self.waves:
            self.draw_wave(w)
        L.blit(self.glow_player, (int(p.x) - GLOW_R, int(p.y - 8) - GLOW_R), special_flags=pygame.BLEND_RGB_MAX)
        G = self.glow_fxset.get(self.skin) or self.glow_fxset["vader"]
        gd = self.glow_air if self.fighter_mode else (G["dash"] if self.anakin_mode else self.glow_dash)
        if p.dash_t > 0:                         # el dash y su estela iluminan en cian (rojo en modo ANAKIN)
            L.blit(gd, (int(p.x) - 14, int(p.y - 8) - 14), special_flags=pygame.BLEND_RGB_MAX)
        for tr in self.trail[-5:]:
            L.blit(gd, (int(tr[1]) + 8 - 14, int(tr[2]) + 8 - 14), special_flags=pygame.BLEND_RGB_MAX)
        if self.anakin_mode and self.state in ("play", "paused") and not (p.charging or p.shoot_t > 0):     # la espada ilumina sola
            fl = 0.8 + 0.2 * math.sin(self.time * 11.0) + 0.1 * math.sin(self.time * 23.0)
            gs = G["sword"].copy()
            q = int(255 * max(0.3, min(1.0, fl)))
            gs.fill((q, q, q), special_flags=pygame.BLEND_RGB_MULT)
            if self.ak_stab:
                bx0, by0 = self.ak_stab[0], self.ak_stab[1] - 5
                qs = max(0.0, min(1.0, self.ak_stab[3] / self.ak_stab[4]))
                gb = G["stab"].copy()
                qq = int(255 * qs)
                gb.fill((qq, qq, qq), special_flags=pygame.BLEND_RGB_MULT)
                L.blit(gb, (int(bx0) - 30, int(by0) - 30), special_flags=pygame.BLEND_RGB_MAX)
                L.blit(gs, (int(bx0) - 17, int(by0) - 17), special_flags=pygame.BLEND_RGB_MAX)
            else:
                shx, shy = self.sword_hand(p)
                L.blit(gs, (int(shx) - 17, int(shy - 5.5) - 17), special_flags=pygame.BLEND_RGB_MAX)
        for m in self.monsters:                  # halo de los monstruos que te estan atacando (alerta)
            al = getattr(m, "alert", 0.0)
            if al < 0.03 or (getattr(m, "invisible", False) and m.reveal <= 0.0):
                continue                                 # el fantasma invisible no tiene halo hasta que lo toca una onda
            gm = self.glow_boss if getattr(m, "boss", False) else self.glow_mon[m.kind]
            if al < 0.97:
                gm = gm.copy()
                q = int(255 * al)
                gm.fill((q, q, q), special_flags=pygame.BLEND_RGB_MULT)
            r = gm.get_width() // 2
            L.blit(gm, (int(m.x) - r, int(m.y - m.h / 2) - r), special_flags=pygame.BLEND_RGB_MAX)
        for m in self.monsters:                  # ronda 3: aura pulsante de los ELITES (siempre visible)
            if getattr(m, "elite", False):
                f = 0.5 + 0.5 * math.sin(self.time * 4.0 + m.elite_phase)
                ge = self.glow_elite[max(0, min(3, int(f * 4)))]
                r = ge.get_width() // 2
                L.blit(ge, (int(m.x) - r, int(m.y - m.h / 2) - r), special_flags=pygame.BLEND_RGB_MAX)
        if p.charging and (self.has_bow or self.anakin_mode or self.fighter_mode) and p.charge > 0.08:      # el arco / la FUERZA / el aplauso cargado brillan
            qq = min(1.0, p.charge / self.charge_t())
            if self.anakin_mode:
                gb = G["big"] if qq >= 1.0 else G["force"]
                rr = gb.get_width() // 2
                fhx, fhy = self.hand_pos(p)
                L.blit(gb, (int(fhx) - rr, int(fhy) - rr), special_flags=pygame.BLEND_RGB_MAX)
            else:
                gb = self.glow_super if qq >= 1.0 else self.glow_arrow
                rr = gb.get_width() // 2
                L.blit(gb, (int(p.x + p.face * 7) - rr, int(p.y) - 9 - rr), special_flags=pygame.BLEND_RGB_MAX)
        if self.state in ("play", "paused"):     # haz frontal: mas intenso y largo al correr
            bm = self.beam.copy()
            q = int(70 + 185 * p.sf)
            bm.fill((q, q, q), special_flags=pygame.BLEND_RGB_MULT)
            L.blit(bm, (int(p.x + p.look) - BEAM_W // 2, int(p.y - 9) - BEAM_H // 2),
                   special_flags=pygame.BLEND_RGB_MAX)
        if self.slam and self.slam["t"] > 0.55 * self.slam["tm"]:
            sx0, sy0 = int(self.slam["x"]), int(self.slam["y"])
            L.blit(self.glow_super, (sx0 - 30, sy0 - 34), special_flags=pygame.BLEND_RGB_MAX)      # el impacto ilumina todo
        for ar in self.arrows:
            if ar.style:                         # proyectil de jefe: brilla de su color para poder esquivarlo
                gfo = self.glow_foe[ar.style]
                rr = gfo.get_width() // 2
                L.blit(gfo, (int(ar.x) - rr, int(ar.y) - rr), special_flags=pygame.BLEND_RGB_MAX)
            elif ar.orb:                           # la bola del mago ilumina su camino
                L.blit(self.glow_orb, (int(ar.x) - 14, int(ar.y) - 14), special_flags=pygame.BLEND_RGB_MAX)
            elif ar.air:                         # la onda de aire ilumina de blanco
                L.blit(self.glow_air, (int(ar.x) - 14, int(ar.y) - 14), special_flags=pygame.BLEND_RGB_MAX)
                if ar.big:                       # la super onda es alta: ilumina tambien arriba y abajo
                    for oy in (-12, 12):
                        L.blit(self.glow_air, (int(ar.x) - 14, int(ar.y) - 14 + oy), special_flags=pygame.BLEND_RGB_MAX)
            elif ar.force:                       # la carga roja de la FUERZA ilumina su camino
                gf = G["big"] if ar.power else G["force"]
                rr = gf.get_width() // 2
                L.blit(gf, (int(ar.x) - rr, int(ar.y) - rr), special_flags=pygame.BLEND_RGB_MAX)
            elif ar.power:                       # el super disparo emite mucha mas luz
                L.blit(self.glow_super, (int(ar.x) - 30, int(ar.y) - 30), special_flags=pygame.BLEND_RGB_MAX)
            elif ar.owner == "player":
                L.blit(self.glow_arrow, (int(ar.x) - 9, int(ar.y) - 9), special_flags=pygame.BLEND_RGB_MAX)
            else:
                L.blit(self.glow_arrow_e, (int(ar.x) - 8, int(ar.y) - 8), special_flags=pygame.BLEND_RGB_MAX)
        if lv.key and self.key_visible and not self.has_key:
            dk = math.hypot(p.x - lv.key[0], p.y - lv.key[1])
            if dk < 70:
                idx = 2 if dk < 28 else (1 if dk < 48 else 0)
                L.blit(self.glow_key[idx], (lv.key[0] - 15, lv.key[1] - 15), special_flags=pygame.BLEND_RGB_MAX)
        if lv.chest and not self.chest_open:
            dk = math.hypot(p.x - lv.chest[0], p.y - lv.chest[1])
            if dk < 60:
                idx = 2 if dk < 24 else (1 if dk < 40 else 0)
                L.blit(self.glow_key[idx], (lv.chest[0] - 15, lv.chest[1] - 22), special_flags=pygame.BLEND_RGB_MAX)
        self.light_pickups(L)
        if lv.door and lv.door_open:
            dcx, dcy = lv.door[0] * TILE + 8, lv.door[1] * TILE + 8
            if math.hypot(p.x - dcx, p.y - dcy) < 90:
                L.blit(self.glow_door, (dcx - 20, dcy - 20), special_flags=pygame.BLEND_RGB_MAX)
        v.blit(L, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        # ---- siluetas de los monstruos: contorno de color propio (fantasma, murcielago, esqueleto)
        rim_col = {"ghoul": (170, 130, 255), "bat": (255, 140, 200), "skel": (235, 235, 210),
                   "elite": (255, 196, 80), "thief": (110, 255, 160), "silencer": (140, 175, 255),
                   "phantom": (215, 205, 255), "giant": (255, 120, 90), "bigbat": (255, 175, 90),
                   "swarm": (255, 150, 200), "bghost": (255, 110, 170)}
        for spr, mx, my, kd, al in self._mdraw:          # v9.5: SIN silueta fuera de tu luz; solo se ve si te atacan
            if al < 0.05:
                continue
            gain = al
            v.blit(self.rim_sprite(spr, rim_col[kd], 0.28, 0.5, gain), (mx - 1, my - 1),
                   special_flags=pygame.BLEND_RGB_MAX)

        # ---- silueta del caballero: nunca se pierde en la oscuridad
        if self._pdraw and self.state in ("play", "paused", "clear"):
            spr, sx, sy = self._pdraw
            v.blit(self.rim_sprite(spr, (255, 170, 160) if self.fighter_mode else self.tc((255, 110, 90)) if self.anakin_mode else (170, 215, 255),
                                   0.40 + 0.25 * self.danger, 0.55,
                                   0.45 if self._pblink else 1.0), (sx - 1, sy - 1),
                   special_flags=pygame.BLEND_RGB_MAX)

        # ---- efectos emisivos (encima de la oscuridad)
        self.draw_traps(v)                               # ronda 3: pinchos (solo un instante tras tocarlos una onda)
        for cell in lv.ghost_cells:                      # puentes fantasma activos
            t = lv.ghost_t.get(cell, 0.0)
            if t > 0 and (t > 1.5 or int(self.time * 10) % 2 == 0):
                v.blit(T.ghost_on, (cell[0] * TILE, cell[1] * TILE))
        for vi, (x0, y0, x1, y1) in enumerate(lv.vents):   # particulas de las corrientes de aire
            hh = y1 - y0
            ww = max(1, int(x1 - x0 - 4))
            for i in range(7):
                px = x0 + 2 + ((i * 37 + vi * 11) % ww)
                py = y1 - ((self.time * 40.0 + i * (hh / 7.0)) % hh)
                pygame.draw.rect(v, (110, 190, 220), (int(px), int(py), 1, 2))
        for t in (lv.torches if self.torch_fade > 0.25 else []):
            tx, ty = t
            ph = int(self.time * 8 + tx * 3 + ty) % 3
            fx, fy = tx * TILE + 8, ty * TILE + 6
            pygame.draw.ellipse(v, (255, 138, 40), (fx - 2, fy - 4 - (ph == 1), 4, 7))
            pygame.draw.ellipse(v, (255, 226, 120), (fx - 1, fy - 2, 2, 4))
        for w in self.winds:                             # estela de viento de las flechas
            f = w[4] / w[5]
            col = (int(w[6][0] * f), int(w[6][1] * f), int(w[6][2] * f))
            pygame.draw.line(v, col, (w[0], w[1]), (w[2], w[3]), w[7] if f > 0.5 else 1)
            if w[8]:                                     # el super disparo arrastra tres cintas
                dim = (int(col[0] * 0.55), int(col[1] * 0.55), int(col[2] * 0.55))
                pygame.draw.line(v, dim, (w[0], w[1] - 3), (w[2], w[3] - 3), 1)
                pygame.draw.line(v, dim, (w[0], w[1] + 3), (w[2], w[3] + 3), 1)
        if p.charging and self.anakin_mode and p.charge > 0.08 and self.state == "play":
            self.draw_force_charge(v, p)
        elif p.charging and self.fighter_mode and p.charge > 0.08 and self.state == "play":
            self.draw_clap_charge(v, p)
        elif p.charging and self.has_bow and p.charge > 0.08 and self.state == "play":
            qq = min(1.0, p.charge / SUPER_CHARGE_T)
            cbx, cby = int(p.x + p.face * 7), int(p.y) - 9
            full = qq >= 1.0
            rr = 2 + int(6 * qq) + (int(self.time * 16) % 2 if full else 0)
            ccol = (255, 255, 255) if (full and int(self.time * 12) % 2 == 0) else (255, 225, 150)
            pygame.draw.circle(v, ccol, (cbx, cby), rr, 1)
            if full:
                pygame.draw.circle(v, (255, 240, 190), (cbx, cby), rr + 3, 1)
        for tr in self.trail:                            # estela del dash (imagenes residuales)
            if tr[4] - tr[3] < 0.045:
                continue
            a = int(150 * (tr[3] / tr[4]) ** 1.2)
            if a > 4:
                v.blit(self.faded(tr[0], a), (tr[1], tr[2]))
        if p.dash_t > 0 and self.state == "play":        # lineas de velocidad
            d = p.dash_dir
            for i, (oy, ln) in enumerate(((-12, 24), (-8, 36), (-4, 30), (-1, 20))):
                ln *= 0.75 + 0.25 * math.sin(self.time * 55 + i * 1.7)
                x0, y0 = p.x - d * 7, p.y + oy
                xm = x0 - d * ln * 0.45
                c1, c2 = (((255, 255, 255), (190, 205, 240)) if self.fighter_mode
                          else (self.tc((255, 200, 170)), self.tc((230, 40, 30))) if self.anakin_mode
                          else ((225, 248, 255), (120, 200, 245)))
                pygame.draw.line(v, c1, (x0, y0), (xm, y0), 1)
                pygame.draw.line(v, c2, (xm, y0), (x0 - d * ln, y0), 1)
        for sp in self.sparks:                           # chispas
            f = sp[4] / sp[5]
            col = (int(sp[6][0] * f), int(sp[6][1] * f), int(sp[6][2] * f))
            sz = 2 if f > 0.5 else 1
            pygame.draw.rect(v, col, (int(sp[0]), int(sp[1]), sz, sz))
        if self.state in ("play", "paused"):
            drw = getattr(self, "draw_motes", None)
            if drw is not None:
                drw(v)                                   # polvo flotando: solo se ve donde llega la luz
        if p.windup > 0 and self.state == "play" and not self.fighter_mode:        # espada echada hacia atras (anticipacion)
            q = 1.0 - p.windup / WINDUP_T
            a0 = 0.0 if p.face > 0 else math.pi
            if p.air_atk:
                a0 += 0.75 * p.face
            ang = a0 - 1.2 - 0.6 * q
            ln = 10.0 + 5.0 * q
            cx0, cy0 = p.x - p.face * 1.5 * q, p.y - 8
            ex, ey = cx0 + math.cos(ang) * ln, cy0 + math.sin(ang) * ln
            pygame.draw.line(v, self.tc((255, 60, 44)) if self.anakin_mode else (236, 242, 255), (cx0, cy0), (ex, ey), 2)
            pygame.draw.line(v, self.tc((255, 170, 140)) if self.anakin_mode else (255, 214, 140), (cx0, cy0), (ex, ey), 1)
        if self.fighter_mode and p.attack_t > 0 and self.state in ("play", "dead"):
            self.draw_fighter_punch(v, p)                      # golpe: puñetazo con onda de aire (en vez de la espada)
        if self.slam:
            self.draw_slam(v)                                  # grietas, anillos y columna de luz del impacto
        if self.fighter_mode and p.clap_t > 0 and self.state in ("play", "dead"):
            self.draw_clap(v, p)                               # el aplauso: ondas blancas enormes
        elif p.attack_t > 0 and self.state in ("play", "dead"):
            a0 = 0.0 if p.face > 0 else math.pi
            if p.air_atk:                                # tajo aereo: arco diagonal hacia abajo
                a0 += 0.75 * p.face
            prog = 1 - p.attack_t / 0.16
            cy0 = p.y - 8
            pts = [(p.x + math.cos(a0 - 1.2 + 2.4 * prog * (i / 8)) * 16,
                    cy0 + math.sin(a0 - 1.2 + 2.4 * prog * (i / 8)) * 16) for i in range(9)]
            pygame.draw.lines(v, self.tc((255, 60, 44)) if self.anakin_mode else (236, 242, 255), False, pts, 2)
            pygame.draw.lines(v, self.tc((255, 170, 140)) if self.anakin_mode else (255, 214, 140), False,
                              [(x + 0.5 * math.cos(a0), y) for x, y in pts], 1)
        if (self.anakin_mode and self.state in ("play", "paused") and not self._pblink
                and not (p.charging or p.shoot_t > 0)):
            self.draw_ak_sword(v, p)                       # espada roja emisiva (encima de la oscuridad)
        if self.block_flash > 0:
            r = 9 + int((0.15 - self.block_flash) * 40)
            pygame.draw.circle(v, (150, 200, 255), (int(p.x + p.face * 8), int(p.y - 8)), r, 1)
