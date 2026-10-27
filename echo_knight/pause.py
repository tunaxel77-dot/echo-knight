# -*- coding: utf-8 -*-
"""Menu de pausa (ESC / Start): CONTINUAR, REINICIAR, OPCIONES, AYUDA y MENU PRINCIPAL. Teclado, raton y mando.
Reiniciar y salir al menu piden confirmacion (pulsar otra vez en menos de PAUSE_CONFIRM_T segundos)."""
import pygame
from .config import *

PAUSE_ITEMS = ("resume", "restart", "options", "help", "menu")


class PauseMixin:
    pause_sel = 0
    pause_arm_id = None
    pause_arm_until = 0.0

    # ------------------------------------------------------------ datos
    def open_pause(self):
        self.state = "paused"
        self.pause_sel, self.pause_arm_id = 0, None
        self.sfx("step")

    def pause_armed(self, ident):
        return self.pause_arm_id == ident and self.time < self.pause_arm_until

    def pause_label(self, ident):
        if self.pause_armed(ident):
            return "¿SEGURO? PULSA OTRA VEZ"
        return {"resume": "CONTINUAR", "restart": "REINICIAR " + ("PARTIDA" if self.mode == "endless" else "NIVEL"),
                "options": "OPCIONES", "help": "AYUDA", "menu": "MENÚ PRINCIPAL"}[ident]

    def pause_rects(self):
        SW, SH = self.SW, self.SH
        n = len(PAUSE_ITEMS)
        w, h, gap = int(SW * 0.34), int(SH * 0.07), int(SH * 0.014)
        x, y0 = (SW - w) // 2, int(SH * 0.30)
        return [pygame.Rect(x, y0 + i * (h + gap), w, h) for i in range(n)]

    # ------------------------------------------------------------ acciones
    def pause_resume(self):
        self.pause_arm_id = None
        self.state = "play"

    def pause_go_menu(self):
        """Vuelve al menu principal. En el modo infinito guarda antes el record de la partida abandonada."""
        self.pause_arm_id = None
        if self.mode == "endless":
            self.endless_game_over()
        self.state = "menu"
        self.load_menu()

    def pause_activate(self, i):
        ident = PAUSE_ITEMS[i]
        if ident == "resume":
            self.pause_resume()
        elif ident == "options":
            self.pause_arm_id = None
            self.open_options("paused")
        elif ident == "help":
            self.pause_arm_id = None
            self.state = "play"
            self.help = True
        elif self.pause_armed(ident):                      # segunda pulsacion: confirmado
            self.pause_arm_id = None
            if ident == "restart":
                self.state = "play"
                self.restart_current()
            else:
                self.pause_go_menu()
        else:                                              # primera pulsacion: pide confirmar
            self.pause_arm_id, self.pause_arm_until = ident, self.time + PAUSE_CONFIRM_T
            self.sfx("step")

    def pause_move(self, d):
        self.pause_sel = (self.pause_sel + d) % len(PAUSE_ITEMS)
        self.pause_arm_id = None
        self.sfx("step")

    # ------------------------------------------------------------ entrada
    def pause_key(self, key):
        if key == pygame.K_ESCAPE:
            self.pause_resume()
        elif key in (pygame.K_UP, pygame.K_w):
            self.pause_move(-1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.pause_move(1)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.pause_activate(self.pause_sel)
        elif key == pygame.K_p:
            self.try_restart()
        elif key == pygame.K_o:
            self.pause_activate(PAUSE_ITEMS.index("options"))
        elif key == pygame.K_h:
            self.pause_activate(PAUSE_ITEMS.index("help"))

    def pause_mouse_move(self, pos):
        pos = self.menu_mouse(pos)
        for i, r in enumerate(self.pause_rects()):
            if r.collidepoint(pos):
                if self.pause_sel != i:
                    self.pause_sel = i
                    self.sfx("step")
                return

    def pause_mouse_click(self, pos):
        pos = self.menu_mouse(pos)
        for i, r in enumerate(self.pause_rects()):
            if r.collidepoint(pos):
                self.pause_sel = i
                self.pause_activate(i)
                return

    # ------------------------------------------------------------ dibujo
    def draw_pause(self):
        k, SW, SH = self.k, self.SW, self.SH
        dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
        dim.fill((6, 4, 12, 150))
        self.screen.blit(dim, (0, 0))
        rects = self.pause_rects()
        self.draw_text("PAUSA", SW // 2, rects[0].y - int(self.line_h() * 3.4), 3.0, GOLD, anchor="c")
        for i, (r, ident) in enumerate(zip(rects, PAUSE_ITEMS)):
            sel = i == self.pause_sel
            armed = self.pause_armed(ident)
            s = pygame.Surface(r.size, pygame.SRCALPHA)
            s.fill((90, 40, 36, 220) if armed else (60, 46, 20, 220) if sel else (20, 16, 30, 200))
            self.screen.blit(s, r.topleft)
            pygame.draw.rect(self.screen, RED if armed else GOLD if sel else (84, 76, 98), r, max(1, k // 2) if sel else 1)
            self.draw_text(self.pause_label(ident), r.centerx, r.centery - self.line_h() // 2, 1.0,
                           RED if armed else GOLD if sel else PARCH, anchor="c")
        if not self.touch_mode:
            self.draw_text("↑/↓ elegir   ENTER aceptar   ESC continuar   P reiniciar   O opciones   H ayuda", SW // 2,
                           rects[-1].bottom + int(self.line_h() * 0.9), 1.0, (150, 142, 160), anchor="c")
