# -*- coding: utf-8 -*-
"""Entrada: teclado y eventos por estado (menu, juego, pausa...)."""
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


class EventsMixin:
    """Entrada: teclado y eventos por estado (menu, juego, pausa...)."""

    # ------------------------------------------------------------ eventos
    def toggle_fullscreen(self):
        if self.touch_mode:                              # en movil siempre es pantalla completa
            return
        self.fullscreen = not self.fullscreen
        self.toast("Pantalla completa: %s  (F11)" % ("ACTIVADA" if self.fullscreen else "desactivada"), 2.0)
        try:
            pygame.display.toggle_fullscreen()
        except Exception:
            flags = pygame.FULLSCREEN if self.fullscreen else 0
            self.screen = pygame.display.set_mode((self.SW, self.SH), flags)

    def handle_events(self):
        for e in self.touch_translate(self.pad_translate(pygame.event.get())):     # el mando se convierte en teclas (gamepad.py)
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYUP:
                if self.key_is(e.key, "fire"):
                    self.release_fire()                  # soltar = disparar (normal o super)
                continue
            if e.type == pygame.MOUSEMOTION and self.state == "menu":
                self.menu_mouse_move(e.pos)
                continue
            if e.type == pygame.MOUSEBUTTONDOWN and self.state == "menu":
                if e.button == 1:
                    self.menu_mouse_click(e.pos)
                continue
            if e.type == pygame.MOUSEMOTION and self.state == "options":
                self.options_mouse_move(e.pos, bool(getattr(e, "buttons", (0,))[0]))
                continue
            if e.type == pygame.MOUSEBUTTONDOWN and self.state == "options":
                if e.button == 1:
                    self.options_mouse_click(e.pos)
                continue
            if e.type == pygame.MOUSEBUTTONUP and self.state == "options":
                self.options_mouse_up()
                continue
            if e.type == pygame.MOUSEMOTION and self.state == "paused":
                self.pause_mouse_move(e.pos)
                continue
            if e.type == pygame.MOUSEBUTTONDOWN and self.state == "paused":
                if e.button == 1:
                    self.pause_mouse_click(e.pos)
                continue
            if e.type == pygame.MOUSEBUTTONDOWN and self.state == "achievements":
                if e.button == 1:
                    self.ach_mouse_click(e.pos)
                continue
            if e.type == getattr(pygame, "MOUSEWHEEL", -1) and self.state == "achievements":
                self.ach_scroll_by(-e.y)
                continue
            if e.type == pygame.MOUSEMOTION and self.state == "select":
                self.select_mouse_move(e.pos)
                continue
            if e.type == pygame.MOUSEBUTTONDOWN and self.state == "select":
                if e.button == 1:
                    self.select_mouse_click(e.pos)
                continue
            if e.type == pygame.MOUSEMOTION and self.state == "cards":
                self.cards_mouse_move(e.pos)
                continue
            if e.type == pygame.MOUSEBUTTONDOWN and self.state == "cards":
                if e.button == 1:
                    self.cards_mouse_click(e.pos)
                continue
            if e.type != pygame.KEYDOWN:
                continue
            key = e.key
            if self.state == "options":                  # (F11 se atiende dentro de options_key)
                self.options_key(key)
                continue
            if key == pygame.K_F11:
                self.toggle_fullscreen()
                continue
            if key == pygame.K_m:
                if self.state == "play" and e.unicode:
                    self.feed_secret(e.unicode)          # "luchador" lleva una m (se silencia dos veces: queda igual)
                self.muted = not self.muted
                continue
            st = self.state
            if st == "menu":
                if self.menu_help:
                    if key in (pygame.K_h, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        self.menu_help = False
                elif key in (pygame.K_UP, pygame.K_w):
                    self.menu_sel = (self.menu_sel - 1) % self.menu_count()
                    self.sfx("step")
                elif key in (pygame.K_DOWN, pygame.K_s):
                    self.menu_sel = (self.menu_sel + 1) % self.menu_count()
                    self.sfx("step")
                elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.menu_activate(self.menu_sel)
                elif key == pygame.K_1:
                    self.menu_activate_id("levels")
                elif key == pygame.K_2:
                    self.menu_activate_id("endless")
                elif key == pygame.K_h:
                    self.menu_activate_id("help")
                elif key == pygame.K_o:
                    self.menu_activate_id("options")
                elif key == pygame.K_l:
                    self.menu_activate_id("achievements")
                elif key == pygame.K_n:
                    self.open_select("levels", False)
                elif key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            elif st == "play":
                if e.unicode:                            # comando secreto: se lee SIEMPRE, incluso con la ayuda abierta
                    skin0, tun0 = self.skin, self.tun_mode
                    self.feed_secret(e.unicode)
                    if (self.skin, self.tun_mode) != (skin0, tun0):
                        self.help = False                # la "h" de "darth" abre la ayuda: se cierra al completar
                        continue
                if key in (pygame.K_h, pygame.K_c) and e.unicode and self.secret_in_progress():
                    continue                             # H / C dentro de una palabra secreta (luchador, darth...): no abren ayuda ni disparan
                if self.help:
                    if key in (pygame.K_h, pygame.K_ESCAPE, pygame.K_RETURN):
                        self.help = False
                    continue
                if self.key_is(key, "attack"):
                    self.do_attack()
                elif self.key_is(key, "jump"):
                    self.player.jbuf = 0.12
                elif self.key_is(key, "pulse"):
                    self.do_pulse()
                elif self.key_is(key, "fire"):
                    self.start_charge()
                elif self.key_is(key, "dash"):
                    self.do_dash()
                elif self.key_is(key, "interact"):
                    self.try_open_chest()
                    self.try_buy()
                elif self.key_is(key, "shield"):
                    if not self.has_shield and self.level_idx >= 1 and not self.shield_warned:
                        self.shield_warned = True
                        self.toast("Todavía no tienes escudo. Busca el cofre de esta sala.", 3.0)
                elif key == pygame.K_h:
                    self.help = True
                elif key == pygame.K_p:
                    self.try_restart()
                elif key == pygame.K_ESCAPE:
                    self.open_pause()
            elif st == "cards":
                self.cards_key(key)
            elif st == "select":
                self.select_key(key)
            elif st == "achievements":
                self.ach_key(key)
            elif st == "paused":
                self.pause_key(key)
            elif st == "dead":
                if key in (pygame.K_p, pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.restart_current()
                elif key == pygame.K_ESCAPE:
                    self.state = "menu"
                    self.load_menu()
            elif st == "victory":
                if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                    self.state = "menu"
                    self.load_menu()
