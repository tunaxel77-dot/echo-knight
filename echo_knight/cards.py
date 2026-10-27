# -*- coding: utf-8 -*-
"""RONDA 2: mejoras (cartas) del modo infinito y estadisticas por partida.

Las estadisticas que antes eran constantes globales (vida maxima, gravedad, velocidad...)
viven aqui como atributos de Game para poder cambiar durante una partida:
    self.max_hp  self.gravity  self.walk_speed  self.shield_mult  self.sword_dmg
    self.perk_echo  self.magnet  self.double_shot  self.dash_perk
Los valores de clase sirven de valor por defecto (modo niveles = igual que antes).
"""
import random

import pygame
from .config import *
from .characters import char_of

PERKS = [
    dict(id="maxhp", name="CORAZÓN EXTRA", desc="+1 vida máxima y te curas 1 corazón.", color=(226, 54, 70), max=99),
    dict(id="speed", name="BOTAS LIGERAS", desc="+25% de velocidad de movimiento.", color=(120, 220, 140), max=3),
    dict(id="sword", name="ESPADA AFILADA", desc="+1 de daño con la espada.", color=(230, 230, 240), max=2),
    dict(id="dash", name="DASH", desc="Desbloquea la embestida: pulsa R.", color=(150, 225, 255), max=1),
    dict(id="echo", name="ECO AMPLIO", desc="Tus ecos de pasos y de ataque llegan más lejos.", color=(115, 160, 255), max=3),
    dict(id="shield", name="ESCUDO LIGERO", desc="Te mueves más rápido con el escudo en alto.", color=(92, 108, 150), max=2),
    dict(id="magnet", name="IMÁN", desc="Recoges corazones y monedas desde el doble de lejos.", color=(255, 110, 160), max=1),
    dict(id="double", name="ARCO DOBLE", desc="Cada disparo lanza dos flechas.", color=(176, 120, 60), max=1),
]
PERK_BY_ID = {p["id"]: p for p in PERKS}


class CardsMixin:
    # valores por defecto (los usa tambien el modo niveles)
    max_hp = MAX_HP
    gravity = GRAVITY
    walk_speed = WALK_SPEED
    shield_mult = SHIELD_MULT
    sword_dmg = 1
    perk_echo = 1.0
    magnet = 1.0
    double_shot = False
    dash_perk = False
    room_mod = ""
    mon_mult = 1.0
    perks = {}
    cards = ()
    cards_sel = 1
    cards_t = 0.0

    # ------------------------------------------------------------ estadisticas
    def init_run_stats(self):
        """Pone las estadisticas de la partida a su valor base (se llama al empezar partida/menu)."""
        self.perks = {}
        self.room_mod = ""
        self.mon_mult = 1.0
        self.max_hp = char_of(self)["hp"] + (FT_BONUS_HP if getattr(self, "fighter_mode", False) else 0)
        self.gravity = GRAVITY
        self.cards, self.cards_sel, self.cards_t = (), 1, 0.0
        self.recalc_stats()

    def recalc_stats(self):
        n = lambda k: self.perks.get(k, 0)
        self.walk_speed = WALK_SPEED * char_of(self)["speed"] * (1.0 + PERK_SPEED * n("speed"))
        self.shield_mult = min(1.0, SHIELD_MULT + PERK_SHIELD_ADD * n("shield"))
        self.sword_dmg = 1 + n("sword")
        self.perk_echo = PERK_ECHO ** n("echo")
        self.magnet = PERK_MAGNET if n("magnet") else 1.0
        self.double_shot = n("double") > 0
        self.dash_perk = n("dash") > 0

    def apply_perk(self, pid):
        self.perks[pid] = self.perks.get(pid, 0) + 1
        if pid == "maxhp":
            self.max_hp = min(MAX_HP_CAP, self.max_hp + 1)
            self.player.hp = min(self.max_hp, self.player.hp + 1)
        self.recalc_stats()

    def available_perks(self):
        out = []
        for p in PERKS:
            if self.perks.get(p["id"], 0) >= p["max"]:
                continue
            if p["id"] == "maxhp" and self.max_hp >= MAX_HP_CAP:
                continue
            if p["id"] == "shield" and char_of(self)["shield"] == "none":
                continue                 # el mago no usa escudo
            out.append(p["id"])
        return out

    # ------------------------------------------------------------ eleccion de cartas
    def start_cards(self):
        """Muestra 3 cartas al azar (si hay alguna disponible). Devuelve True si abrio la pantalla."""
        pool = self.available_perks()
        if not pool:
            return False
        self.cards = tuple(random.sample(pool, min(3, len(pool))))
        self.cards_sel = len(self.cards) // 2
        self.cards_t = 0.35
        self.state = "cards"
        return True

    def pick_card(self, i):
        if self.state != "cards" or not (0 <= i < len(self.cards)):
            return
        self.apply_perk(self.cards[i])
        self.cards = ()
        self.state = "play"
        self.sfx("key")
        self.add_wave(self.player.x, self.player.y - 8, "key", 0.9)

    def update_cards(self, dt):
        self.cards_t = max(0.0, self.cards_t - dt)
        self.update_waves(dt)
        self.update_fx(dt)

    def cards_ready(self):
        return self.state == "cards" and self.cards_t <= 0 and self.fade_in <= 0

    def cards_key(self, key):
        if not self.cards_ready():
            return
        n = len(self.cards)
        if key in (pygame.K_LEFT, pygame.K_a):
            self.cards_sel = (self.cards_sel - 1) % n
            self.sfx("step")
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.cards_sel = (self.cards_sel + 1) % n
            self.sfx("step")
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e):
            self.pick_card(self.cards_sel)
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3):
            self.pick_card(key - pygame.K_1)

    def cards_rects(self):
        SW, SH = self.SW, self.SH
        n = max(1, len(self.cards))
        w, h, gap = int(SW * 0.25), int(SH * 0.46), int(SW * 0.03)
        x0 = (SW - (n * w + (n - 1) * gap)) // 2
        y = int(SH * 0.26)
        return [pygame.Rect(x0 + i * (w + gap), y, w, h) for i in range(n)]

    def cards_mouse_move(self, pos):
        if not self.cards_ready():
            return
        pos = self.menu_mouse(pos)
        for i, r in enumerate(self.cards_rects()):
            if r.collidepoint(pos) and self.cards_sel != i:
                self.cards_sel = i
                self.sfx("step")

    def cards_mouse_click(self, pos):
        if not self.cards_ready():
            return
        pos = self.menu_mouse(pos)
        for i, r in enumerate(self.cards_rects()):
            if r.collidepoint(pos):
                self.pick_card(i)
                return

    # ------------------------------------------------------------ dibujo
    def draw_cards(self):
        if self.fade_in > 0:
            return
        k, SW, SH = self.k, self.SW, self.SH
        s = pygame.Surface((SW, SH), pygame.SRCALPHA)
        s.fill((6, 4, 12, 170))
        self.screen.blit(s, (0, 0))
        self.draw_text("ELIGE UNA MEJORA", SW // 2, int(SH * 0.12), 3.0, GOLD, anchor="c")
        self.draw_text("← / → + ENTER, o usa el ratón", SW // 2, int(SH * 0.2), 1.0, PARCH, anchor="c")
        for i, (pid, r) in enumerate(zip(self.cards, self.cards_rects())):
            P = PERK_BY_ID[pid]
            sel = i == self.cards_sel
            rr = r.move(0, -2 * k) if sel else r
            self.draw_panel(rr, 235 if sel else 190)
            if sel:
                pygame.draw.rect(self.screen, GOLD, rr, k)
            ic = int(rr.w * 0.34)
            ir = pygame.Rect(rr.centerx - ic // 2, rr.y + int(rr.h * 0.08), ic, ic)
            pygame.draw.rect(self.screen, (20, 16, 30), ir.inflate(4 * k, 4 * k))
            pygame.draw.rect(self.screen, P["color"], ir)
            pygame.draw.rect(self.screen, PARCH, ir, max(1, k // 2))
            self.draw_text(P["name"], rr.centerx, ir.bottom + 6 * k, 1.2, GOLD if sel else PARCH, anchor="c")
            lh = self.line_h()
            y = ir.bottom + 6 * k + int(self.line_h(1.2) * 1.6)
            for line in self.wrap(P["desc"], 1.0, rr.w - 10 * k):
                self.draw_text(line, rr.centerx, y, 1.0, PARCH, anchor="c")
                y += lh
            have = self.perks.get(pid, 0)
            if have:
                self.draw_text("Tienes: %d" % have, rr.centerx, rr.bottom - lh * 2, 1.0, CYAN, anchor="c")

    def draw_perk_icons(self, c):
        """Iconos pequenos de las mejoras (esquina superior izquierda del mapa)."""
        x = 3
        for P in PERKS:
            n = self.perks.get(P["id"], 0)
            if n <= 0:
                continue
            pygame.draw.rect(c, (12, 10, 18), (x - 1, 2, 9, 9))
            pygame.draw.rect(c, P["color"], (x, 3, 7, 7))
            for j in range(min(n, 4) - 1):          # puntitos = nivel de la mejora
                c.set_at((x + 1 + j * 2, 12), (255, 255, 255))
            x += 10
