# -*- coding: utf-8 -*-
"""Menu principal: centrado, con botones (teclado y raton) sobre la demo de pelea."""
import math

import pygame
from .config import *
from .texts import *


class MenuMixin:
    """Dibujo y control del menu. Para anadir un boton: sube MENU_ITEMS (config.py),
    agrega su texto en menu_labels() y su accion en menu_activate()."""

    # ------------------------------------------------------------ botones
    def menu_entries(self):
        """Lista (id, texto) de los botones. CONTINUAR solo aparece si hay partida guardada (save.py)."""
        ents = []
        if self.has_save():
            ents.append(("continue", "CONTINUAR (NIVEL %d)" % (self.progress["level"] + 1)))
        ents += [("levels", "MODO NIVELES"), ("endless", "MODO INFINITO"),
                 ("achievements", "LOGROS (%d/%d)" % (self.ach_count(), len(ACH_LIST))), ("options", "OPCIONES"),
                 ("fullscreen", "PANTALLA COMPLETA: %s" % ("SÍ" if self.fullscreen else "NO")), ("help", "CONTROLES")]
        return ents

    def menu_count(self):
        return len(self.menu_entries())

    def menu_labels(self):
        return [lab for _, lab in self.menu_entries()]

    def menu_index(self, ident):
        for i, (eid, _) in enumerate(self.menu_entries()):
            if eid == ident:
                return i
        return None

    def menu_rects(self):
        SW, SH = self.SW, self.SH
        n = self.menu_count()
        w, h, gap = int(SW * 0.34), int(SH * (0.06 if n <= 5 else 0.054 if n == 6 else 0.049)), int(SH * (0.013 if n <= 5 else 0.011 if n == 6 else 0.009))
        x, y0 = (SW - w) // 2, int(SH * 0.31)
        return [pygame.Rect(x, y0 + i * (h + gap), w, h) for i in range(n)]

    def menu_activate_id(self, ident):
        i = self.menu_index(ident)
        if i is not None:
            self.menu_sel = i
            self.menu_activate(i)

    def menu_activate(self, i):
        ents = self.menu_entries()
        if not 0 <= i < len(ents):
            return
        ident = ents[i][0]
        if ident == "continue":
            self.continue_game()
        elif ident == "levels":
            self.open_select("levels", True)
        elif ident == "endless":
            self.open_select("endless", False)
        elif ident == "achievements":
            self.open_achievements()
        elif ident == "options":
            self.open_options("menu")
        elif ident == "fullscreen":
            self.toggle_fullscreen()
        elif ident == "help":
            self.menu_help = not self.menu_help

    # ------------------------------------------------------------ raton
    def menu_mouse(self, pos):
        """Coordenadas del raton en la superficie del juego (por si la ventana se escala)."""
        if self.touch_mode:                              # ventana ancha: el juego esta centrado (margen ox)
            try:
                if self.touch_scaled:                    # SCALED ya entrega coordenadas logicas
                    x, y = pos
                else:
                    ww, wh = pygame.display.get_window_size()
                    x, y = pos[0] * self.WS // max(1, ww), pos[1] * self.HS // max(1, wh)
                return (x - self.ox, y)
            except Exception:
                return pos
        try:
            ww, wh = pygame.display.get_window_size()
            if ww > 0 and wh > 0 and (ww != self.SW or wh != self.SH):
                return (pos[0] * self.SW // ww, pos[1] * self.SH // wh)
        except Exception:
            pass
        return pos

    def menu_mouse_move(self, pos):
        if self.menu_help:
            return
        pos = self.menu_mouse(pos)
        for i, r in enumerate(self.menu_rects()):
            if r.collidepoint(pos):
                if self.menu_sel != i:
                    self.menu_sel = i
                    self.sfx("step")
                return

    def menu_mouse_click(self, pos):
        if self.menu_help:
            self.menu_help = False
            return
        pos = self.menu_mouse(pos)
        for i, r in enumerate(self.menu_rects()):
            if r.collidepoint(pos):
                self.menu_sel = i
                self.menu_activate(i)
                return

    # ------------------------------------------------------------ dibujo
    def menu_gradient(self):
        key = (self.SW, self.SH)
        if getattr(self, "_menu_grad_key", None) != key:
            h = int(self.SH * 0.33)
            g = pygame.Surface((self.SW, h), pygame.SRCALPHA)
            for y in range(h):
                a = int(215 * (1 - y / h) ** 1.2)
                pygame.draw.line(g, (6, 4, 12, a), (0, y), (self.SW, y))
            self._menu_grad, self._menu_grad_key = g, key
        return self._menu_grad

    def draw_menu(self):
        k, SW, SH = self.k, self.SW, self.SH
        cx = SW // 2
        self.screen.blit(self.menu_gradient(), (0, 0))
        # --- titulo (3 tonos fijos: la cache de texto no crece)
        tone = (GOLD, (255, 226, 120), (255, 240, 170), (255, 226, 120))[int(self.time * 3) % 4]
        ty = int(SH * 0.045)
        self.draw_text("ECHO KNIGHT", cx, ty, 6.0, tone, anchor="c")
        sy = ty + self.line_h(6.0) + 2 * k
        self.draw_text("Caballero del Eco", cx, sy, 1.5, CYAN, anchor="c")
        self.draw_text("Arenas medievales a oscuras", cx, sy + self.line_h(1.5) + k, 1.0,
                       (190, 178, 150), anchor="c")

        if self.menu_help:                      # panel de controles
            w = int(SW * 0.66)
            r = pygame.Rect((SW - w) // 2, int(SH * 0.03), w, int(SH * 0.94))
            self.draw_panel(r, 238)
            self.draw_controls(r.x + 4 * k, r.y + 4 * k, r.w - 8 * k)
            self.draw_text("[clic / H / ESC] cerrar", r.centerx, r.bottom - self.line_h() * 1.5, 1.0,
                           GOLD, anchor="c")
        else:
            lh = self.line_h(1.3)
            for i, (lab, r) in enumerate(zip(self.menu_labels(), self.menu_rects())):
                sel = i == self.menu_sel
                s = pygame.Surface(r.size, pygame.SRCALPHA)
                s.fill((16, 12, 28, 215 if sel else 150))
                self.screen.blit(s, r.topleft)
                pygame.draw.rect(self.screen, GOLD if sel else (104, 88, 60), r, (k // 2 + 2) if sel else max(1, k // 2))
                if sel:                          # esquinas que parpadean
                    c = (255, 240, 170) if int(self.time * 4) % 2 == 0 else GOLD
                    for px, py in ((r.left, r.top), (r.right - 1, r.top), (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1)):
                        pygame.draw.rect(self.screen, c, (px - k, py - k, 2 * k, 2 * k))
                self.draw_text(lab, r.centerx, r.centery - lh // 2, 1.3, GOLD if sel else PARCH, anchor="c")
            if self.best[0] > 0:
                rr = self.menu_rects()[self.menu_index("endless")]
                self.draw_text("Récord: %d salas" % self.best[0], rr.right - 3 * k, rr.top + 2 * k, 1.0,
                               CYAN, anchor="r")
            self.draw_text("ARRIBA / ABAJO + ENTER, o usa el ratón   ·   N: niveles sin tutorial   ·   ESC: salir",
                           cx, int(SH * 0.705), 1.0, (190, 178, 150), anchor="c")
            if self.best_score > 0:
                self.draw_text("PUNTUACIÓN MÁXIMA (infinito): %d" % self.best_score, cx,
                               int(SH * 0.705) + self.line_h() + 2 * k, 1.0, CYAN, anchor="c")

        # --- barra inferior: la tecla que "pulsa" el caballero de la demo
        txt, keys, ct = self.demo["cap"] if self.demo else ("", [], 0.0)
        by = MAP_H * k + (HUD_H * k - self.line_h()) // 2
        if ct > 0 and keys:
            f = k / 2.0
            kws = [self.text_surf(kk, 1.0, PARCH).get_width() + int(10 * f) for kk in keys]
            tw = self.text_surf(txt, 1.0, GOLD).get_width()
            total = sum(kws) + int(4 * f) * (len(keys) - 1) + int(10 * f) + tw
            x = cx - total // 2
            for kk in keys:
                w, _ = self.draw_key(kk, x, by - int(2 * f))
                x += w + int(4 * f)
            self.draw_text(txt, x + int(6 * f), by, 1.0, GOLD)
        else:
            self.draw_text("Así se juega: mira a tu caballero", cx, by, 1.0, (170, 160, 140), anchor="c")
