# -*- coding: utf-8 -*-
"""Skins secretas (Anakin / Vader), modo TUN y dash."""
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


class SkinsMixin:
    """Skins secretas (Anakin / Vader / Luchador), modo TUN y dash."""
    fighter_mode = False

    # --- skins secretas: ANAKIN (azul) y DARTH VADER (rojo)
    def tc(self, c):
        """Color de un efecto segun la skin: rojo (DARTH VADER) o azul (ANAKIN, canales R y B cambiados)."""
        return (c[2], c[1], c[0]) if self.skin == "anakin" else c

    def fxk(self, name):
        """Nombre de la onda segun la skin (las de ANAKIN terminan en _b)."""
        return name + "_b" if self.skin == "anakin" else name

    def hand_pos(self, p):
        """Mano con la que se usa la FUERZA (de aqui sale la carga)."""
        if self.skin == "vader":
            return p.x + p.face * 11.0, p.y - 12.0
        return p.x + p.face * 9.0, p.y - 5.5

    def sword_hand(self, p):
        """Mano que empuna el sable."""
        if self.skin == "vader":
            return p.x + p.face * 6.0, p.y - 7.0
        return p.x + p.face * 5.0, p.y - 5.5

    def set_skin(self, skin):
        p = self.player
        p.charging, p.charge = False, 0.0
        self.ak_stab = None
        self.trail = []
        was_fighter = self.fighter_mode
        self.skin = None if self.skin == skin else skin
        self.anakin_mode = self.skin in ("anakin", "vader")
        self.fighter_mode = self.skin == "fighter"
        if self.fighter_mode and not was_fighter:                   # luchador: corazones extra
            self.max_hp = min(MAX_HP_CAP + FT_BONUS_HP, self.max_hp + FT_BONUS_HP)
            p.hp = min(self.max_hp, p.hp + FT_BONUS_HP)
        elif was_fighter and not self.fighter_mode:
            self.max_hp = max(1, self.max_hp - FT_BONUS_HP)
            p.hp = min(p.hp, self.max_hp)
        self.add_wave(p.x, p.y - 8, "dash_air" if self.fighter_mode else (self.fxk("dash_red") if self.anakin_mode else "dash"), 1.4)
        self.sfx("key")
        if self.skin == "fighter":
            self.toast("LUCHADOR: ¡vuelas! Mantén W / ↑ para subir y S / ↓ para bajar. F / C = puñetazo de aire, R = dash con el puño, "
                       "S = guardia de boxeador. Escribe luchador otra vez para quitarlo.", 5.0)
        elif self.skin == "anakin":
            self.toast("SKIN ANAKIN: sable azul, capa y DASH con R. Escribe anakin otra vez para quitarla "
                       "(o darth vader para el otro personaje).", 3.8)
        elif self.skin == "vader":
            self.toast("DARTH VADER: sable rojo, capa y DASH con R. Escribe darth vader otra vez para quitarlo.", 3.8)
        else:
            self.toast("Skin desactivada.", 2.5)

    # --- modo TUN: palabra secreta + dash con estela
    SECRET_WORDS = ("anakin", "darthvader", "luchador", "tun")

    def secret_in_progress(self):
        """True si lo ultimo escrito es el comienzo (2+ letras) de una palabra secreta: asi las teclas H (ayuda) y
        C (disparo) que lleva la palabra no hacen su accion normal a mitad de comando."""
        buf = self.cheat_buf
        return any(len(buf) >= k and buf.endswith(w[:k]) for w in self.SECRET_WORDS for k in range(2, len(w)))

    def feed_secret(self, ch):
        """Detecta la palabra secreta "tun" escrita durante la partida."""
        ch = ch.lower()
        if len(ch) != 1 or not ch.isalpha():
            return
        self.cheat_buf = (self.cheat_buf + ch)[-12:]
        for word, skin in (("anakin", "anakin"), ("darthvader", "vader"), ("luchador", "fighter")):   # (ver SECRET_WORDS)
            if self.cheat_buf.endswith(word):
                self.cheat_buf = ""
                self.set_skin(skin)
                return
        if self.cheat_buf[-3:] == "tun":
            self.cheat_buf = ""
            self.tun_mode = not self.tun_mode
            p = self.player
            self.add_wave(p.x, p.y - 8, "dash", 1.4)
            self.sfx("key")
            self.toast("MODO TUN activado: pulsa R para hacer el DASH." if self.tun_mode
                       else "Modo TUN desactivado.", 3.0)

    def do_dash(self):
        p = self.player
        if (not (self.tun_mode or self.anakin_mode or self.fighter_mode or self.dash_perk) or self.state != "play" or p.dash_cd > 0
                or p.dash_t > 0 or p.stun > 0 or p.windup > 0):
            return
        inp = self.get_input()
        d = inp["right"] - inp["left"]
        p.dash_dir = d if d else p.face
        p.face = p.dash_dir
        p.dash_t = DASH_TIME
        p.dash_cd = DASH_COOLDOWN
        p.dash_hit = set()
        p.vy = 0.0
        p.boost = 1.0
        self.ak_stab = None
        self.add_wave(p.x, p.y - 8, "dash_air" if self.fighter_mode else (self.fxk("dash_red") if self.anakin_mode else "dash"))
        self.sfx("dash")
        self.make_noise(p.x, p.y, 70)
        for _ in range(14):                      # rafaga de chispas al arrancar
            a = random.uniform(-0.9, 0.9)
            sp = random.uniform(40.0, 130.0)
            life = random.uniform(0.25, 0.5)
            self.sparks.append([p.x - p.dash_dir * 4, p.y - random.uniform(2.0, 13.0),
                                -p.dash_dir * sp * math.cos(a), -sp * math.sin(a) * 0.8,
                                life, life, random.choice(((255, 255, 255), (225, 235, 255), (190, 205, 240)))
                                if self.fighter_mode else self.tc(random.choice(((255, 200, 150), (255, 90, 50), (255, 255, 255))))
                                if self.anakin_mode else
                                random.choice(((190, 240, 255), (130, 215, 255), (255, 255, 255)))])

    def dash_trail(self, p):
        """Deja una imagen residual (silueta cian) del caballero en cada fotograma del dash."""
        spr, bx, by = self.player_sprite(p)
        t = spr.copy()
        t.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)      # conserva solo el alfa
        t.fill((255, 255, 255, 0) if self.fighter_mode else
               self.tc((255, 50, 36)) + (0,) if self.anakin_mode else (140, 225, 255, 0),
               special_flags=pygame.BLEND_RGBA_ADD)                        # tinte cian (rojo / azul segun la skin)
        self.trail.append([t, bx, by, 0.30, 0.30])
        if len(self.trail) > 24:
            self.trail.pop(0)
        for _ in range(2):
            life = random.uniform(0.2, 0.4)
            self.sparks.append([p.x - p.dash_dir * random.uniform(3, 8), p.y - random.uniform(1.0, 14.0),
                                -p.dash_dir * random.uniform(10, 40), random.uniform(-25, 10),
                                life, life, (240, 246, 255) if self.fighter_mode else
                                self.tc((255, 110, 70)) if self.anakin_mode else (170, 235, 255)])

    def ak_stab_start(self, p):
        """Fin del dash en modo ANAKIN: clava la espada en el suelo con una explosion de brasas."""
        d = p.dash_dir
        sx = p.x + d * 13
        gy = p.y                                 # el dash no tiene gravedad: sigue a ras de suelo
        self.ak_stab = [sx, gy, d, 0.55, 0.55]
        self.add_wave(sx, gy - 3, self.fxk("stab"), 1.0)
        self.make_noise(p.x, p.y, 60)
        for _ in range(26):
            a = random.uniform(-2.9, -0.25)
            sp = random.uniform(35.0, 120.0)
            life = random.uniform(0.3, 0.7)
            self.sparks.append([sx, gy - 1, math.cos(a) * sp, math.sin(a) * sp, life, life,
                                self.tc(random.choice(((255, 220, 160), (255, 90, 50), (255, 40, 30), (255, 150, 60))))])

    def update_fx(self, dt):
        if self.slam:
            self.slam["t"] -= dt
            if self.slam["t"] <= 0:
                self.slam = None
        if self.ak_stab:
            self.ak_stab[3] -= dt
            if self.ak_stab[3] <= 0:
                self.ak_stab = None
        for tr in self.trail:
            tr[3] -= dt
        self.trail = [tr for tr in self.trail if tr[3] > 0]
        for w in self.winds:
            w[4] -= dt
        self.winds = [w for w in self.winds if w[4] > 0]
        for s in self.sparks:
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            s[3] += 120.0 * dt
            s[4] -= dt
        self.sparks = [s for s in self.sparks if s[4] > 0]
        upd = getattr(self, "update_motes", None)
        if upd is not None and self.state in ("play", "paused", "menu"):
            upd(dt)                                      # polvo flotando en el haz (motes.py)
