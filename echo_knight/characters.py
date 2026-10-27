# -*- coding: utf-8 -*-
"""RONDA 4: personajes jugables y pantalla de seleccion (estado "select").

CHARACTERS: stats y habilidad de cada personaje (el balance esta en config.py).
  hp, speed (x velocidad), atk_cd (x enfriamiento del ataque), reach (x alcance), push (x empuje del golpe),
  shield: "chest" (hay que encontrar el escudo) | "none" (no puede usar escudo) | "always" (lo lleva desde el inicio),
  air_jumps: saltos extra en el aire, shot: "bow" (arco) | "orb" (bolas que rebotan), block_stun: segundos que
  atonta un bloqueo, bars: (vida, velocidad, ataque, defensa) de 1 a 5 para la pantalla de seleccion.
Para anadir un personaje: entrada aqui + sprite en sprites_data.py (CHAR_SPRITES).
"""
import json
import os

import pygame
from .config import *

CHAR_ORDER = ["knight", "mage", "rogue", "tank"]
CHAR_FILE = os.path.join(os.path.expanduser("~"), ".echo_knight_char.json")

CHARACTERS = {
    "knight": dict(name="CABALLERO", hp=MAX_HP, speed=1.0, atk_cd=1.0, reach=1.0, push=1.0, shield="chest",
                   air_jumps=0, shot="bow", block_stun=0.45, bars=(3, 3, 3, 3),
                   skill="Equilibrado. Arco con super disparo y escudo para bloquear."),
    "mage": dict(name="MAGO", hp=MAGE_HP, speed=1.0, atk_cd=1.0, reach=1.0, push=1.0, shield="none",
                 air_jumps=0, shot="orb", block_stun=0.45, bars=(2, 3, 4, 1),
                 skill="Bolas mágicas lentas que REBOTAN 2 veces en los muros (F / C). No usa escudo."),
    "rogue": dict(name="PÍCARO", hp=ROGUE_HP, speed=ROGUE_SPEED, atk_cd=ROGUE_ATK_CD, reach=ROGUE_REACH, push=1.0,
                  shield="chest", air_jumps=1, shot="bow", block_stun=0.45, bars=(2, 5, 4, 1),
                  skill="DOBLE SALTO, +30% de velocidad y daga muy rápida de corto alcance."),
    "tank": dict(name="TANQUE", hp=TANK_HP, speed=TANK_SPEED, atk_cd=TANK_ATK_CD, reach=1.0, push=TANK_PUSH,
                 shield="always", air_jumps=0, shot="bow", block_stun=TANK_BLOCK_STUN, bars=(5, 1, 2, 5),
                 skill="Escudo siempre listo: bloquear atonta 1 s al enemigo. Golpe lento que empuja."),
}


def char_of(g):
    """Definicion del personaje activo de la partida (el caballero si aun no hay ninguno)."""
    return CHARACTERS.get(getattr(g, "char", "knight"), CHARACTERS["knight"])


class CharactersMixin:
    char = "knight"                  # personaje de la partida en curso (el menu y su demo usan el caballero)
    sel_char = "knight"              # ultimo personaje elegido (se guarda en disco)
    select_idx = 0
    select_pending = ("endless", False)

    # ------------------------------------------------------------ estado / guardado
    def init_characters(self):
        self.sel_char = self.load_char()
        self.char = "knight"

    def char_def(self):
        return char_of(self)

    def load_char(self):
        try:
            with open(CHAR_FILE, "r", encoding="utf-8") as f:
                cid = json.load(f).get("char", "knight")
            return cid if cid in CHARACTERS else "knight"
        except Exception:
            return "knight"

    def save_char(self):
        try:
            with open(CHAR_FILE, "w", encoding="utf-8") as f:
                json.dump({"char": self.sel_char}, f)
        except Exception:
            pass

    def shield_allowed(self):
        return char_of(self)["shield"] != "none"

    def apply_char_loadout(self):
        """Tras fijar escudo/arco de una partida nueva: el mago lleva su baston, el tanque su escudo."""
        c = char_of(self)
        if c["shot"] == "orb":
            self.has_bow = True
        if c["shield"] == "always":
            self.has_shield = True
        elif c["shield"] == "none":
            self.has_shield = False

    # ------------------------------------------------------------ seleccion
    def open_select(self, mode, tutorial=False):
        """Pantalla ELEGIR PERSONAJE tras elegir modo (mode = "levels" | "endless")."""
        self.select_pending = (mode, tutorial)
        self.select_idx = CHAR_ORDER.index(self.sel_char) if self.sel_char in CHAR_ORDER else 0
        self.state = "select"
        self.sfx("step")

    def select_confirm(self, i=None):
        if i is not None:
            self.select_idx = i
        self.sel_char = CHAR_ORDER[self.select_idx % len(CHAR_ORDER)]
        self.save_char()
        mode, tut = self.select_pending
        self.sfx("key")
        if mode == "endless":
            self.start_endless()
        else:
            self.start_game(tut)

    def select_back(self):
        self.state = "menu"

    def select_key(self, key):
        n = len(CHAR_ORDER)
        if key in (pygame.K_LEFT, pygame.K_a):
            self.select_idx = (self.select_idx - 1) % n
            self.sfx("step")
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.select_idx = (self.select_idx + 1) % n
            self.sfx("step")
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.select_confirm()
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            self.select_confirm(key - pygame.K_1)
        elif key == pygame.K_ESCAPE:
            self.select_back()

    def select_rects(self):
        SW, SH = self.SW, self.SH
        n = len(CHAR_ORDER)
        w, h, gap = int(SW * 0.215), int(SH * 0.56), int(SW * 0.02)
        x0 = (SW - (n * w + (n - 1) * gap)) // 2
        y = int(SH * 0.2)
        return [pygame.Rect(x0 + i * (w + gap), y, w, h) for i in range(n)]

    def select_mouse_move(self, pos):
        pos = self.menu_mouse(pos)
        for i, r in enumerate(self.select_rects()):
            if r.collidepoint(pos) and self.select_idx != i:
                self.select_idx = i
                self.sfx("step")

    def select_mouse_click(self, pos):
        pos = self.menu_mouse(pos)
        for i, r in enumerate(self.select_rects()):
            if r.collidepoint(pos):
                self.select_confirm(i)
                return

    def update_select(self, dt):
        """El fondo sigue siendo la demo del menu (con el caballero)."""
        self.update_demo(dt)
        self.state = "select"            # update_demo deja el estado en "menu"

    # ------------------------------------------------------------ dibujo
    def draw_select(self):
        k, SW, SH = self.k, self.SW, self.SH
        s = pygame.Surface((SW, SH), pygame.SRCALPHA)
        s.fill((6, 4, 12, 185))
        self.screen.blit(s, (0, 0))
        self.draw_text("ELEGIR PERSONAJE", SW // 2, int(SH * 0.07), 3.0, GOLD, anchor="c")
        self.draw_text("← / →  +  ENTER, o usa el ratón   ·   ESC: volver", SW // 2, int(SH * 0.15), 1.0, PARCH, anchor="c")
        labels = ("VIDA", "VELOC.", "ATAQUE", "DEFENSA")
        lh = self.line_h()
        for i, (cid, r) in enumerate(zip(CHAR_ORDER, self.select_rects())):
            C = CHARACTERS[cid]
            sel = i == self.select_idx
            rr = r.move(0, -2 * k) if sel else r
            self.draw_panel(rr, 238 if sel else 190)
            if sel:
                pygame.draw.rect(self.screen, GOLD, rr, k)
            anim = self.tex.char_anim[cid]["right"]
            if sel:                                   # el elegido camina; el resto respira en reposo
                spr = anim["walk"][int(self.time * 6) % 4]
                bob = 0
            else:
                spr = anim["idle"]
                bob = -1 if int(self.time * 1.6) % 2 else 0
            size = int(rr.w * 0.42) // 16 * 16 or 16
            big = pygame.transform.scale(spr, (size, size))
            self.screen.blit(big, (rr.centerx - size // 2, rr.y + int(rr.h * 0.05) + bob * k))
            y = rr.y + int(rr.h * 0.05) + size + 3 * k
            self.draw_text(C["name"], rr.centerx, y, 1.5, GOLD if sel else PARCH, anchor="c")
            y += self.line_h(1.5) + 3 * k
            for lab, val in zip(labels, C["bars"]):
                self.draw_text(lab, rr.x + 5 * k, y, 1.0, (190, 178, 150))
                bx = rr.x + int(rr.w * 0.42)
                seg = int(rr.w * 0.085)
                for j in range(5):
                    col = (120, 220, 140) if j < val else (46, 42, 58)
                    pygame.draw.rect(self.screen, col, (bx + j * (seg + k), y + k, seg, lh - 3 * k))
                y += lh + k
            y += 2 * k
            for line in self.wrap(C["skill"], 1.0, rr.w - 10 * k):
                self.draw_text(line, rr.centerx, y, 1.0, PARCH, anchor="c")
                y += lh
        self.draw_text("Hay que elegir con cuidado: el personaje cambia cómo se juega.", SW // 2, int(SH * 0.84), 1.0,
                       (190, 178, 150), anchor="c")
