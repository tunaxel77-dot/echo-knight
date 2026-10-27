# -*- coding: utf-8 -*-
"""Demo del menu: el fondo es el juego REAL jugando solo.

Un caballero automatico (bot) pelea contra fantasmas y murcielagos con las mismas reglas
del juego: camina, salta a las plataformas, ataca, se cubre con el escudo, dispara el arco
y lanza el super eco. Abajo se muestra la tecla que "pulsa" para ensenar como se juega.
Retoca el comportamiento en demo_think().
"""
import math
import random

from .config import *
from .entities import Ghoul, Bat

DEMO_MAX_X = 322.0               # el bot no se acerca a la puerta de salida
DEMO_MIN_X = 28.0


class DemoMixin:
    """Caballero automatico para el fondo del menu."""

    def demo_reset(self):
        self.in_demo = False
        self.has_key = True               # antorchas encendidas: la arena se ve de fondo
        self.torch_fade = 1.0
        self.has_shield = True
        self.has_bow = True
        self.t_level = 10.0               # sin periodo de gracia
        self.player.hp = MAX_HP
        self.demo = dict(t=0.0, spawn=0.8, patrol=80.0, pulse=7.0, shot=1.0, jump=2.0,
                         jhold=0.0, hold=0.0, seed=0, shield=0.0,
                         cap=("", [], 0.0), inp=dict(left=0, right=0, jump=False, shield=False, sneak=False))
        self.add_wave(self.player.x, self.player.y - 8, "attack", 0.75)

    def demo_cap(self, text, keys):
        self.demo["cap"] = (text, keys, 1.5)

    def demo_spawn(self):
        d, p = self.demo, self.player
        d["seed"] += 1
        right = p.x < MAP_W / 2
        if random.random() < 0.65:
            x = (COLS - 4 if right else 3) * TILE + 8
            m = Ghoul(x, (ROWS - 1) * TILE, 500 + d["seed"])
        else:
            x = (COLS - 4 if right else 3) * TILE + 8
            m = Bat(x, random.randint(48, 110), 500 + d["seed"])
        m.chase_t = 4.0
        m.alert = 1.0
        self.monsters.append(m)
        self.add_wave(m.x, m.y - m.h / 2, "spawn")

    def update_demo(self, dt):
        """Un paso del juego real con las teclas pulsadas por el bot."""
        if self.demo is None:
            return
        self.in_demo = True               # sin sonidos y get_input() lee al bot
        self.state = "play"               # update_play() solo corre en estado "play"
        try:
            self.demo_think(dt)
            self.update_play(dt)
        finally:
            self.state = "menu"
            self.in_demo = False

    def demo_think(self, dt):
        d, p = self.demo, self.player
        d["t"] += dt
        p.hp = MAX_HP                     # el bot no muere
        txt, keys, ct = d["cap"]
        d["cap"] = (txt, keys, max(0.0, ct - dt))
        inp = dict(left=0, right=0, jump=False, shield=False, sneak=False)
        for k in ("spawn", "pulse", "shot", "jump", "jhold", "hold", "shield"):
            d[k] -= dt

        if d["spawn"] <= 0:
            if len(self.monsters) < 2:
                self.demo_spawn()
            d["spawn"] = random.uniform(2.5, 4.5)
        if p.charging and d["hold"] <= 0:
            self.release_fire()
        if d["pulse"] <= 0 and self.monsters:
            d["pulse"] = random.uniform(10.0, 14.0)
            self.do_pulse()
            self.demo_cap("Súper eco", ["Q"])

        def jump():
            if p.on_ground and p.jbuf <= 0:
                p.jbuf = 0.12
                d["jhold"] = 0.32
                self.demo_cap("Saltar", ["W"])

        tgt = min(self.monsters, key=lambda m: math.hypot(m.x - p.x, m.y - p.y), default=None)
        if tgt is not None:
            dx = tgt.x - p.x
            dy = (tgt.y - tgt.h / 2) - (p.y - 7)
            adx, sgn = abs(dx), (1 if dx > 0 else -1)
            reach = 26.0 if tgt.kind == "bat" else 28.0
            if adx > 75 and abs(dy) < 16 and d["shot"] <= 0 and p.shoot_cd <= 0 and not p.charging:
                p.face = sgn                                  # dispara el arco
                self.start_charge()
                d["hold"] = 0.08
                d["shot"] = random.uniform(1.6, 2.8)
                self.demo_cap("Arco", ["F"])
            elif adx > reach - 4:                             # acercarse
                if sgn > 0:
                    inp["right"] = 1
                else:
                    inp["left"] = 1
                if dy < -24 and adx < 52:
                    jump()
                elif p.hit_wall:
                    jump()
            else:                                             # a rango: atacar o cubrirse
                p.face = sgn
                if dy < -12 and p.on_ground:
                    jump()
                if tgt.kind == "ghoul" and adx < 18 and 0.12 < p.attack_cd and p.windup <= 0:
                    inp["shield"] = True
                    if d["shield"] <= 0:
                        d["shield"] = 1.5
                        self.demo_cap("Escudo", ["S"])
                else:
                    before = p.attack_cd
                    self.do_attack()
                    if p.attack_cd > before:
                        self.demo_cap("Atacar", ["ESPACIO"])
        else:                                                 # sin enemigos: patrulla y salta
            px = d["patrol"]
            if abs(p.x - px) < 6:
                d["patrol"] = random.uniform(50.0, 300.0)
            else:
                if px > p.x:
                    inp["right"] = 1
                else:
                    inp["left"] = 1
                if d["cap"][2] <= 0.0 and p.on_ground:
                    self.demo_cap("Moverse", ["A", "D"])
            if d["jump"] <= 0:
                d["jump"] = random.uniform(2.5, 4.5)
                jump()

        if d["jhold"] > 0:
            inp["jump"] = True                                # mantener = salto mas alto
        if p.x > DEMO_MAX_X and inp["right"]:
            inp["right"] = 0
        if p.x < DEMO_MIN_X and inp["left"]:
            inp["left"] = 0
        d["inp"] = inp
