# -*- coding: utf-8 -*-
"""Arranque de Game: ventana, superficies, luces, estado inicial y utilidades."""
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
from .textures import Textures
from .audio import build_sounds
from .options import read_settings
from .touch import want_touch


class GameCore:
    """Arranque de Game: ventana, superficies, luces, estado inicial y utilidades."""

    def __init__(self, sound=True, seed=None):
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
        except Exception:
            pass
        pygame.init()
        self.touch_mode = False
        if want_touch():                           # Android (o --tactil): ventana ancha con botones virtuales (touch.py)
            k = self.setup_touch_window()
        else:
            info = pygame.display.Info()
            h = info.current_h or 0
            k = 3
            if h > 0:                              # la arena es mas alta: escala segun la pantalla
                k = max(2, min(5, (h - 110) // LH))
            wk = read_settings().get("window_k")              # tamano guardado en OPCIONES (si existe)
            if isinstance(wk, int) and WINDOW_K_MIN <= wk <= WINDOW_K_MAX:
                k = wk
            self.k = k
            self.SW, self.SH = LW * k, LH * k
            self.screen = pygame.display.set_mode((self.SW, self.SH))
        pygame.display.set_caption("Echo Knight")
        self.clock = pygame.time.Clock()
        self.canvas = pygame.Surface((LW, LH)).convert()
        self.scaled = pygame.Surface((self.SW, self.SH)).convert()
        self.view = pygame.Surface((MAP_W, MAP_H)).convert()
        self.light = pygame.Surface((MAP_W, MAP_H)).convert()
        self.tmp = pygame.Surface((MAP_W, MAP_H)).convert()
        self.tl = pygame.Surface((MAP_W, MAP_H)).convert()      # luz de antorchas
        self.font = pygame.font.Font(None, 16)
        self.text_cache = {}
        self.tex = Textures()
        self.glow_player = make_radial(GLOW_R, (190, 195, 235), PLAYER_GLOW)
        self.beam = make_beam(BEAM_W, BEAM_H, (185, 212, 240), 0.42)
        self.glow_arrow = make_radial(9, (255, 225, 150), 0.6)
        self.glow_arrow_e = make_radial(8, (255, 110, 80), 0.55)
        self.glow_key = [make_radial(15, (255, 210, 90), s) for s in (0.25, 0.45, 0.7)]
        self.glow_door = make_radial(20, (110, 255, 170), 0.5)
        self.glow_orb = make_radial(14, (120, 190, 255), 0.7)       # bolas del mago
        self.glow_air = make_radial(14, (255, 255, 255), 0.6)       # punetazos de aire (luchador)
        self.glow_dash = make_radial(14, (120, 215, 255), 0.6)
        self.glow_fxset = {}                                         # luces del sable / FUERZA por skin
        for _nm, _sw in (("vader", False), ("anakin", True)):
            _cc = (lambda c: c[::-1]) if _sw else (lambda c: c)
            self.glow_fxset[_nm] = dict(
                dash=make_radial(14, _cc((255, 50, 36)), 0.7), sword=make_radial(17, _cc((255, 40, 28)), 0.55),
                stab=make_radial(30, _cc((255, 70, 40)), 0.9), force=make_radial(11, _cc((255, 60, 40)), 0.75),
                big=make_radial(30, _cc((255, 45, 32)), 0.95))
        self.glow_super = make_radial(30, (255, 235, 170), 0.95)
        # brillo propio de los monstruos (se suma a la luz: se distingue cada tipo en la oscuridad)
        self.glow_mon = {"ghoul": make_radial(13, (170, 125, 255), 0.34),
                         "skel": make_radial(13, (235, 235, 205), 0.34),
                         "bat": make_radial(11, (255, 130, 200), 0.34)}
        self.glow_elite = [make_radial(17, (255, 170, 60), s) for s in (0.28, 0.40, 0.52, 0.66)]   # aura pulsante de los elites
        self.glow_boss = make_radial(26, (255, 90, 70), 0.42)
        self.glow_foe = {"shock": make_radial(11, (255, 90, 60), 0.6), "spirit": make_radial(13, (170, 110, 255), 0.62),
                         "sonic": make_radial(11, (255, 140, 205), 0.58), "bomb": make_radial(11, (255, 130, 90), 0.58)}
        self.vign = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
        for i in range(9):                       # solo un MARCO rojo, nada de pantalla roja
            a = int(255 * (1 - i / 9) ** 1.4)
            pygame.draw.rect(self.vign, (235, 25, 25, a), (i, i, MAP_W - 2 * i, MAP_H - 2 * i), 1)
        self.flash = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
        self.sounds = {}
        self.muted = not sound
        if sound:
            try:
                self.sounds = build_sounds()
            except Exception:
                self.sounds = {}
        self.init_music(sound)                    # musica de fondo por capas (music.py)
        self.fullscreen = False
        self.time = 0.0
        self.state = "menu"
        self.help = False
        self.level_idx = 0
        self.total_time = 0.0
        self.kills = 0
        self.has_shield = False
        self.toast_text = ""
        self.toast_t = 0.0
        self.menu_t = 0.0
        self.shield_warned = False
        self.has_bow = False
        self.tutorial = False
        self.restart_arm = 0.0           # confirmacion de reinicio (pulsar P dos veces)
        self.ghost_hint = False
        self.tun_mode = False            # modo desarrollador (se activa escribiendo "tun")
        self.cheat_buf = ""
        self.anakin_mode = False         # True si hay una skin de FUERZA activa (anakin o darth vader)
        self.skin = None                 # None | "anakin" | "vader" | "fighter"
        self.fighter_mode = False           # True con la skin LUCHADOR (vuela, punetazos de aire, guardia de boxeador)
        self.ak_stab = None              # espada clavada tras el dash: [x, y_suelo, dir, t, t_max]
        self._pdraw = None
        self.cli_seed = seed             # --semilla N (None = aleatoria)
        self.init_characters()
        self.init_options()
        self.init_save()
        self.init_achievements()
        self.init_gamepad()
        self.init_run_stats()
        self.init_endless_state()
        self.init_threats_state()
        self.init_polish()
        self.in_demo = False
        self.demo = None
        self.menu_help = False
        self.menu_level = Level(MENU_ARENA, self.tex)
        self.load_menu()

    # ------------------------------------------------------------ utilidades
    def sfx(self, name):
        if not self.muted and not self.in_demo and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass

    def toast(self, text, t=3.0):
        self.toast_text, self.toast_t = text, t

    def get_input(self):
        if self.in_demo and self.demo is not None:       # demo del menu: teclas del bot
            return dict(self.demo["inp"])
        k = pygame.key.get_pressed()
        return dict(                                     # teclas segun KEYMAP (config.py / pantalla OPCIONES)
            left=int(self.held(k, "left")),
            right=int(self.held(k, "right")),
            jump=bool(self.held(k, "jump")),
            shield=bool(self.held(k, "shield")),
            sneak=bool(self.held(k, "sneak")),
        )

    def reset_runtime(self):
        self.waves = []
        self.has_key = False
        self.key_visible = False
        self.chest_open = False
        self.reveal = 0.0
        self.t_level = 0.0
        self.tut = 0
        self.attacks = 0
        self.pulses = 0
        self.jumps = 0
        self.sealed_cd = 0.0
        self.heart_t = 0.0
        self.hurt_flash = 0.0
        self.block_flash = 0.0
        self.danger = 0.0
        self.clear_t = 0.0
        self.arrows = []
        self.torch_fade = 0.0            # 0 = antorchas apagadas, 1 = encendidas
        self.tut_spawned = False
        self.sneak_dist = 0.0
        self.grace = 0.0                 # los monstruos aun no te detectan
        self.aggr = 1.0                  # factor de agresividad (sube tras aparecer)
        self.trail = []                  # estela del dash: [sprite, x, y, vida, vida_max]
        self.sparks = []                 # chispas del dash: [x, y, vx, vy, vida, vida_max, color]
        self.winds = []                  # estelas de viento de las flechas
        self.pickups = []                # corazones del suelo (modo infinito)
