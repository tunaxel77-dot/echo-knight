# -*- coding: utf-8 -*-
"""Pantallas: draw(), menu, pausa, victoria."""
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


class ScreensMixin:
    """Pantallas: draw(), menu, pausa, victoria."""

    # ------------------------------------------------------------ pantalla
    def draw(self):
        k, st = self.k, self.state
        if st == "menu":
            self.state = "play"              # el fondo del menu es una demo real: se dibuja como en partida
            try:
                self.render_world()
            finally:
                self.state = "menu"
        elif st == "select":
            self.state = "play"              # (como el menu: la demo del caballero de fondo)
            try:
                self.render_world()
            finally:
                self.state = "select"
        elif st == "options":
            self.state = "paused" if self.opt_return == "paused" else "play"     # mundo (o demo) detras de las opciones
            try:
                self.render_world()
            finally:
                self.state = "options"
        elif st == "achievements":
            self.state = "play"              # (como el menu: la demo del caballero de fondo)
            try:
                self.render_world()
            finally:
                self.state = "achievements"
        elif st == "cards":
            self.state = "paused"            # el mundo se ve congelado detras de las cartas
            try:
                self.render_world()
            finally:
                self.state = "cards"
        else:
            self.render_world()
        if st in ("play", "dead", "clear") and self.shake >= 0.3:
            ox, oy = self.shake_offset()                 # temblor de pantalla
            self.canvas.fill((0, 0, 0))
            self.canvas.blit(self.view, (ox, oy))
        else:
            self.canvas.blit(self.view, (0, 0))
        if st in ("play", "paused", "dead", "clear"):
            # v9.5: marco rojo de peligro ELIMINADO (causaba un cuadro negro sobre monstruo y jugador)
            pass
        self.draw_hud()
        pygame.transform.scale(self.canvas, (self.SW, self.SH), self.scaled)
        self.screen.blit(self.scaled, (0, 0))
        self.draw_fade()
        SW, SH = self.SW, self.SH
        lh = self.line_h()

        if st in ("play", "paused", "dead", "clear", "cards"):
            hy = MAP_H * k + (HUD_H * k - lh) // 2
            self.draw_text("ECO", 90 * k, hy, 1.0, CYAN)
            if self.mode == "endless" and self.e_shop:
                self.draw_text("TIENDA", 152 * k, hy, 1.0, (255, 215, 90))
            elif self.mode == "endless":
                done = self.e_room_kills >= self.e_quota
                if self.e_boss is not None:
                    self.draw_text("JEFE", 152 * k, hy, 1.0, (255, 150, 120) if self.boss_monsters() else (120, 230, 150))
                else:
                    self.draw_text("BAJAS: %d/%d" % (min(self.e_room_kills, self.e_quota), self.e_quota), 152 * k, hy, 1.0,
                                   (120, 230, 150) if done else GOLD)
            else:
                self.draw_text("MONSTRUOS: %d" % len(self.monsters), 152 * k, hy, 1.0,
                               GOLD if self.monsters else (120, 230, 150))
            self.draw_text("[H]", 198 * k, hy, 1.0, (170, 160, 140))
            self.draw_text("[F11] PANTALLA", 214 * k, hy, 1.0, (170, 160, 140))
            if self.anakin_mode:                         # indicador del modo ANAKIN (y recarga del dash)
                ready = self.player.dash_cd <= 0
                lab_sk = "DARTH VADER" if self.skin == "vader" else "SKIN ANAKIN"
                self.draw_text(lab_sk + " · R: DASH", 6 * k, (MAP_H - 13) * k, 1.0,
                               self.tc((255, 80, 60)) if ready else self.tc((140, 60, 56)))
            elif self.fighter_mode:                         # indicador del modo LUCHADOR
                ready = self.player.dash_cd <= 0
                self.draw_text("LUCHADOR · W/S: VOLAR · R: DASH", 6 * k, (MAP_H - 13) * k, 1.0,
                               (255, 255, 255) if ready else (150, 160, 190))
            elif self.tun_mode or self.dash_perk:        # indicador del dash (modo TUN o carta DASH)
                ready = self.player.dash_cd <= 0
                self.draw_text("MODO TUN · R: DASH" if self.tun_mode else "R: DASH", 6 * k, (MAP_H - 13) * k, 1.0,
                               CYAN if ready else (90, 120, 150))
            if self.mode == "endless":
                lab = "INFINITO · SALA %d" % (self.e_room + 1)
            else:
                lab = "TUTORIAL" if self.tutorial else "NIVEL %d · %s" % (self.level_idx + 1, self.level.name)
            self.draw_text(lab, SW - 4 * k, hy, 1.0, GOLD, anchor="r")
            if self.mode == "endless" and st in ("play", "paused", "clear"):
                self.draw_endless_stats()
            if st == "play" and self.mode == "endless":
                self.draw_mod_banner()
            self.draw_boss_bar()
            if st == "play" and self.near_chest():
                self.draw_hint("Pulsa E para abrir el cofre")
            elif st == "play" and self.mode == "endless" and self.shop_item_near() is not None:
                self.draw_hint(self.shop_hint())
            elif self.tutorial and st == "play":
                msgs = TUT_MSGS_TOUCH if self.touch_mode else TUT_MSGS
                self.draw_hint(msgs[min(self.tut, len(msgs) - 1)])
            elif self.toast_t > 0:
                self.draw_hint(self.toast_text)
        if st == "menu":
            self.draw_menu()
        elif st == "select":
            self.draw_select()
        elif st == "options":
            self.draw_options()
        elif st == "achievements":
            self.draw_achievements()
        elif st == "paused":
            self.draw_pause()
        elif st == "dead":
            if self.mode == "endless":
                tag = "  ¡NUEVO RÉCORD!" if self.e_new_best else "  MEJOR: %d salas" % self.best[0]
                self.draw_center_title("HAS CAÍDO", RED, "SALAS: %d   BAJAS: %d%s     ENTER: reintentar   ESC: menú"
                                       % (self.e_room, self.kills, tag))
                stag = "  ¡NUEVA PUNTUACIÓN MÁXIMA!" if self.e_new_score else "  MEJOR: %d" % self.best_score
                r = pygame.Rect(int(self.SW * 0.25), self.SH // 2 + 11 * k, int(self.SW * 0.5), self.line_h() * 2 + 8 * k)
                self.draw_panel(r, 200)
                self.draw_text("PUNTOS: %d%s" % (self.score, stag), r.centerx, r.y + 3 * k, 1.0, GOLD, anchor="c")
                self.draw_text("SEMILLA: %d  (repítela con --semilla %d)" % (self.e_base_seed, self.e_base_seed),
                               r.centerx, r.y + 4 * k + self.line_h(), 1.0, PARCH, anchor="c")
            else:
                self.draw_center_title("HAS CAÍDO", RED, "ENTER / P: reintentar nivel    ESC: menú")
        elif st == "cards":
            self.draw_cards()
        elif st == "clear":
            self.draw_center_title("¡NIVEL SUPERADO!", GOLD, "")
        elif st == "victory":
            self.draw_victory()
        if self.help and st == "play":
            w = int(SW * 0.66)
            r = pygame.Rect((SW - w) // 2, int(SH * 0.03), w, int(SH * 0.94))
            self.draw_panel(r, 232)
            self.draw_controls(r.x + 4 * k, r.y + 4 * k, r.w - 8 * k)
            self.draw_text("[H] cerrar", r.centerx, r.bottom - lh * 1.5, 1.0, GOLD, anchor="c")
        self.draw_ach_banner()                   # cartel de LOGRO DESBLOQUEADO (3 s, arriba)

    def draw_hint(self, text):
        k = self.k
        lh = self.line_h()
        maxw = int(self.SW * 0.86)
        lines = self.wrap(text, 1.0, maxw - 12 * k)
        w = max(self.text_surf(l, 1.0, PARCH).get_width() for l in lines) + 12 * k
        h = lh * len(lines) + 8 * k
        r = pygame.Rect((self.SW - w) // 2, 3 * k, w, h)
        self.draw_panel(r, 190)
        for i, l in enumerate(lines):
            self.draw_text(l, r.centerx, r.y + 4 * k + i * lh, 1.0, PARCH, anchor="c")

    def draw_center_title(self, title, color, sub):
        k = self.k
        s = pygame.Surface((self.SW, int(34 * k)), pygame.SRCALPHA)
        s.fill((8, 6, 14, 190))
        y = self.SH // 2 - int(26 * k)
        self.screen.blit(s, (0, y))
        self.draw_text(title, self.SW // 2, y + 4 * k, 3.0, color, anchor="c")
        if sub:
            self.draw_text(sub, self.SW // 2, y + 25 * k, 1.0, PARCH, anchor="c")

    def draw_fs_badge(self, cx, y):
        """Indicador del menu: icono de esquinas + tecla F11 + 'Pantalla completa'."""
        f = self.k / 2.0
        label = "Pantalla completa"
        tw = self.text_surf(label, 1.0, PARCH).get_width()
        kw = self.text_surf("F11", 1.0, PARCH).get_width() + int(10 * f)
        ic, gap = int(12 * f), int(6 * f)
        x = cx - (ic + gap + kw + gap + tw) // 2
        col = GOLD if int(self.time * 2) % 2 == 0 else PARCH
        s, lw = max(2, int(3.5 * f)), max(1, int(f))
        x0, y0 = x, y + int(3 * f)
        x1, y1 = x0 + ic, y0 + ic
        for px, py, ax, ay in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            pygame.draw.line(self.screen, col, (px, py), (px + ax * s, py), lw)
            pygame.draw.line(self.screen, col, (px, py), (px, py + ay * s), lw)
        w, _ = self.draw_key("F11", x + ic + gap, y)
        self.draw_text(label, x + ic + gap + w + gap, y + int(3 * f), 1.0, PARCH)

    def draw_victory(self):
        k, SW, SH = self.k, self.SW, self.SH
        r = pygame.Rect(int(SW * 0.2), int(SH * 0.2), int(SW * 0.6), int(SH * 0.55))
        self.draw_panel(r, 220)
        self.draw_text("¡VICTORIA!", SW // 2, r.y + 6 * k, 3.5, GOLD, anchor="c")
        m, s = divmod(int(self.total_time), 60)
        lines = ["Has escapado de las catacumbas.", "",
                 "Tiempo total: %02d:%02d" % (m, s), "Monstruos derrotados: %d" % self.kills, "",
                 "ENTER: volver al menú"]
        y = r.y + 40 * k
        for l in lines:
            self.draw_text(l, SW // 2, y, 1.2, PARCH, anchor="c")
            y += int(self.line_h(1.2) * 1.2)
