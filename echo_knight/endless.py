# -*- coding: utf-8 -*-
"""MODO INFINITO (hard core): salas aleatorias que cambian sin fin, monstruos que no paran
de aparecer y corazones que a veces sueltan al morir (no hay otra forma de curarse).

Reglas:
  * Cada sala se genera al azar (rooms.py).
  * Los monstruos aparecen sin parar mientras estes en la sala.
  * Cuando acumulas las bajas de la sala (cuota), la puerta se abre. Cruzarla => sala nueva.
  * La vida pasa de una sala a otra: sin corazones no hay curacion.
Toda la dificultad se ajusta en config.py (bloque MODO INFINITO).
"""
import json
import math
import os

from .paths import data_path
import random

import pygame
from . import save
from .config import *
from .achievements import ach_notify
from .lighting import make_radial
from .physics import move_body
from .level import Level
from .entities import Player, Ghoul, Bat, Skeleton, Phantom, Thief, Silencer
from .rooms import (generate_room, generate_shop, spawn_points, is_shop_room, is_boss_room, pick_modifier,
                    MOD_INFO, BOSS_INFO)

BEST_FILE = data_path(".echo_knight_best.json")


def parse_seed(argv):
    """Lee `--semilla N` o `--semilla=N` de los argumentos. Devuelve int o None."""
    for i, a in enumerate(argv):
        try:
            if a == "--semilla" and i + 1 < len(argv):
                return int(argv[i + 1])
            if a.startswith("--semilla="):
                return int(a.split("=", 1)[1])
        except ValueError:
            return None
    return None


class Coin:
    """Moneda dorada que sueltan los monstruos (se gasta en la tienda)."""
    is_player = False
    kind = "coin"
    hw = 3.0
    h = 5.0

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx, self.vy = random.uniform(-35, 35), -110.0
        self.on_ground = False
        self.hit_wall = False
        self.t = COIN_LIFETIME
        self.phase = random.random() * 6.28


class Heart:
    """Corazon que sueltan los monstruos: cae al suelo y se recoge al tocarlo."""
    is_player = False
    kind = "heart"
    hw = 4.0
    h = 7.0

    def __init__(self, x, y):
        self.x, self.y = x, y            # y = parte baja
        self.vx, self.vy = random.uniform(-25, 25), -90.0
        self.on_ground = False
        self.hit_wall = False
        self.t = HEART_LIFETIME
        self.phase = random.random() * 6.28


class EndlessMixin:
    """Logica del modo infinito."""

    # ------------------------------------------------------------ estado / record
    def init_endless_state(self):
        self.mode = "levels"            # "levels" | "endless"
        self.menu_sel = 0               # 0 = niveles, 1 = infinito
        self.e_room = 0                 # indice de la sala actual (0 = primera)
        self.e_room_kills = 0
        self.e_quota = ENDLESS_QUOTA_BASE
        self.e_spawn_t = 0.0
        self.e_seed = 0
        self.e_base_seed = 0
        self.e_pity = 0
        self.e_new_best = False
        self.glow_heart = None
        self.glow_coin = None
        self.best_score = 0
        self.best = self.load_best()
        self.score = 0
        self.combo = 0
        self.combo_t = 0.0
        self.coins = 0
        self.e_new_score = False
        self.e_shop = False
        self.shop_items = []
        self.mod_banner_t = 0.0
        self._shop_txt = {}

    def load_best(self):
        """Record del infinito: viene del guardado unico (save.py); si aun no esta, se migra del archivo antiguo."""
        d = save.read_save_file().get("best")
        if not isinstance(d, dict):
            try:
                with open(BEST_FILE, "r", encoding="utf-8") as f:       # archivo antiguo (rondas 1-4)
                    d = json.load(f)
            except Exception:
                d = {}
        try:
            self.best_score = int(d.get("score", 0))
            return (int(d.get("rooms", 0)), int(d.get("kills", 0)))
        except Exception:
            self.best_score = 0
            return (0, 0)

    def save_best(self):
        save.write_save_file({"best": {"rooms": self.best[0], "kills": self.best[1], "score": self.best_score}})

    def endless_game_over(self):
        """Al morir: guarda el record si lo superas."""
        cur = (self.e_room, self.kills)
        self.e_new_best = cur > self.best
        if self.e_new_best:
            self.best = cur
        self.e_new_score = self.score > self.best_score
        if self.e_new_score:
            self.best_score = self.score
        if self.e_new_best or self.e_new_score:
            self.save_best()

    # ------------------------------------------------------------ arranque / salas
    def start_endless(self):
        self.mode = "endless"
        self.e_room = 0
        self.e_seed = 0
        cli = getattr(self, "cli_seed", None)
        self.e_base_seed = cli if cli is not None else random.randrange(1, 10 ** 8)
        self.char = self.sel_char                # ronda 4: personaje elegido
        self.init_run_stats()                    # vida maxima, mejoras y gravedad vuelven a su valor base
        self.score = self.combo = self.coins = 0
        self.combo_t = 0.0
        self.e_new_score = False
        self.e_pity = 0
        self.e_new_best = False
        self.total_time = 0.0
        self.kills = 0
        self.has_shield = ENDLESS_START_SHIELD
        self.has_bow = ENDLESS_START_BOW
        self.shield_warned = True
        self.apply_char_loadout()
        self.load_endless_room(None)

    def endless_next_room(self):
        hp = self.player.hp
        self.score += ROOM_SCORE
        self.e_room += 1
        ach_notify(self, "room", self.e_room)
        self.load_endless_room(hp)
        if CARD_EVERY and not self.e_shop and self.e_room % CARD_EVERY == 0:
            self.start_cards()                   # tras el fundido: eleccion de 3 cartas

    def endless_cap(self):
        return min(ENDLESS_ALIVE_MAX, ENDLESS_ALIVE_BASE + self.e_room // ENDLESS_ALIVE_EVERY)

    def load_endless_room(self, carry_hp):
        seed = self.e_base_seed + self.e_room * 7919
        self.e_shop = is_shop_room(self.e_room)
        self.room_mod = "" if self.e_shop else (pick_modifier(self.e_base_seed, self.e_room) or "")
        self.gravity = GRAVITY * (MOD_LOWGRAV if self.room_mod == "lowgrav" else 1.0)
        self.mon_mult = MOD_FAST if self.room_mod == "fast" else 1.0
        self.mod_banner_t = MOD_BANNER_T if self.room_mod else 0.0
        spec = generate_shop(seed, self.e_room) if self.e_shop else generate_room(seed, self.e_room, self.room_mod)
        self.tutorial = False
        self.level_idx = self.e_room
        self.level = Level(spec, self.tex)
        sx, sy = self.level.start
        self.player = Player(sx, sy)
        self.player.hp = carry_hp if carry_hp is not None else self.max_hp
        self.monsters = []
        self.reset_runtime()
        self.ak_stab = None
        self.restart_arm = 0.0
        self.chest_open = True
        self.state = "play"
        self.help = False
        self.fade_in = FADE_T
        self.e_room_kills = 0
        self.e_quota = min(ENDLESS_QUOTA_MAX, ENDLESS_QUOTA_BASE + ENDLESS_QUOTA_STEP * self.e_room)
        self.e_spawn_t = 2.0
        self.add_wave(sx, sy - 8, "attack", 0.75)
        self.shop_items = []
        self.e_boss, self.boss_name, self.boss_banner_t = None, "", 0.0
        if self.e_shop:                          # sala tienda: sin monstruos, puerta abierta
            self.build_shop()
            self.has_key = True
            self.level.door_open = True
            self.toast("TIENDA DEL ECO. Camina hasta un objeto y pulsa E para comprarlo. "
                       "La puerta está abierta cuando quieras seguir.", 6.0)
            return
        if is_boss_room(self.e_room):            # sala de JEFE: sin cuota; la puerta se abre al matarlo
            self.e_quota = 10 ** 9
            self.spawn_boss()
            return
        for _ in range(min(2, self.endless_cap())):
            self.endless_spawn(hunt=False)
        self.toast("SALA %d · %s. Mata %d monstruos para abrir la puerta. No dejarán de aparecer; "
                   "a veces sueltan corazones." % (self.e_room + 1, self.level.name, self.e_quota), 5.0)

    # ------------------------------------------------------------ apariciones
    def endless_pick_kind(self):
        w = [("ghoul", 3.0)]
        if self.e_room >= ENDLESS_BAT_FROM:
            w.append(("bat", 2.0))
        if self.e_room >= ENDLESS_SKEL_FROM:
            w.append(("skel", 1.0 + 0.15 * (self.e_room - ENDLESS_SKEL_FROM)))
        if self.e_room >= PHANTOM_FROM:
            w.append(("phantom", 0.8 + 0.1 * (self.e_room - PHANTOM_FROM)))
        if self.e_room >= THIEF_FROM:                 # el ladron sale mas si hay corazones en el suelo
            w.append(("thief", 2.5 if any(q.kind == "heart" for q in self.pickups) else 0.5))
        if self.e_room >= SILENCER_FROM:
            w.append(("silencer", 0.8 + 0.1 * (self.e_room - SILENCER_FROM)))
        tot = sum(x for _, x in w)
        r = random.uniform(0, tot)
        for kind, x in w:
            r -= x
            if r <= 0:
                return kind
        return w[0][0]

    def endless_spawn(self, hunt=True):
        if self.e_shop:
            return
        lv, p = self.level, self.player
        ground, air = spawn_points(lv)
        kind = self.endless_pick_kind()
        pool = air if kind in ("bat", "silencer") else ground
        random.shuffle(pool)
        pick = None
        for (c, r) in pool[:40]:
            x, y = c * TILE + 8, (r + 1) * TILE
            if math.hypot(x - p.x, y - p.y) >= ENDLESS_SPAWN_SAFE:
                pick = (c, r)
                break
        if pick is None:
            return
        c, r = pick
        self.e_seed += 1
        seed = self.e_base_seed + self.e_seed
        if kind == "bat":
            m = Bat(c * TILE + 8, r * TILE + 8, seed)
        elif kind == "skel":
            m = Skeleton(c * TILE + 8, (r + 1) * TILE, seed)
        elif kind == "silencer":
            m = Silencer(c * TILE + 8, r * TILE + 8, seed)
        elif kind == "phantom":
            m = Phantom(c * TILE + 8, (r + 1) * TILE, seed)
        elif kind == "thief":
            m = Thief(c * TILE + 8, (r + 1) * TILE, seed)
        else:
            m = Ghoul(c * TILE + 8, (r + 1) * TILE, seed)
        if kind in ("ghoul", "bat", "skel") and self.e_room >= ELITE_FROM and random.random() < ELITE_CHANCE:
            self.apply_elite(m)                 # ELITE: x2 vida, aura pulsante, mas botin
        if hunt:
            m.chase_t = 3.0                     # tras el periodo de gracia salen ya cazando
            if hasattr(m, "last_seen"):
                m.last_seen = (p.x, p.y)
        self.monsters.append(m)
        self.add_wave(m.x, m.y - m.h / 2, "spawn", 1.6 if getattr(m, "elite", False) else 1.0)

    def endless_update(self, dt):
        """Aparicion continua de monstruos y corazones del suelo."""
        self.e_spawn_t -= dt
        if self.mod_banner_t > 0:
            self.mod_banner_t -= dt
        if self.boss_banner_t > 0:
            self.boss_banner_t -= dt
        if self.combo_t > 0:
            self.combo_t -= dt
            if self.combo_t <= 0:
                self.combo = 0
        if self.grace <= 0 and self.e_spawn_t <= 0 and not self.e_shop and self.e_boss is None:
            if len(self.monsters) < self.endless_cap():
                self.endless_spawn()
            interval = max(ENDLESS_SPAWN_MIN, ENDLESS_SPAWN_T0 - ENDLESS_SPAWN_DECAY * self.e_room)
            self.e_spawn_t = interval * random.uniform(0.8, 1.2)
        p, lv = self.player, self.level
        for h in self.pickups[:]:
            h.t -= dt
            h.vy = min(h.vy + self.gravity * dt, MAX_FALL)
            move_body(lv, h, dt)
            if h.on_ground:
                h.vx *= 0.8 ** (dt * 60)
            if h.t <= 0:
                self.pickups.remove(h)
                continue
            if abs(p.x - h.x) < 9 * self.magnet and abs((p.y - 7) - (h.y - 4)) < 12 * self.magnet:
                self.pickups.remove(h)
                if h.kind == "coin":
                    self.coins += 1
                    self.score += COIN_SCORE
                    self.add_wave(p.x, p.y - 8, "coin", 0.8)
                    self.sfx("step")
                    continue
                if p.hp < self.max_hp:
                    p.hp += 1
                    self.add_wave(p.x, p.y - 8, "heart", 1.2)
                    self.sfx("key")
                    self.toast("¡Corazón recogido! +1 vida.", 2.0)

    # ------------------------------------------------------------ bajas / puerta
    def endless_on_kill(self, m):
        if getattr(m, "minion", False):
            return                               # esbirros invocados por un jefe: sin puntos ni botin (evita farmearlos)
        self.e_room_kills += 1
        p = self.player
        # --- combo y puntuacion
        self.combo = self.combo + 1 if self.combo_t > 0 else 1
        self.combo_t = COMBO_WINDOW
        ach_notify(self, "combo", self.combo)
        elite = getattr(m, "elite", False)
        pts = KILL_SCORE.get(getattr(m, "tag", None) or m.kind, 10) * (ELITE_SCORE_MULT if elite else 1)
        self.score += pts * self.combo_mult()
        # --- monedas (los elites sueltan el doble)
        for _ in range(ELITE_COINS if elite else 1):
            if random.random() < COIN_DROP + (COIN_DROP_SKEL if m.kind == "skel" else 0.0):
                self.pickups.append(Coin(m.x + random.uniform(-3, 3), m.y - 4))
        missing = self.max_hp - p.hp
        if missing > 0 and sum(1 for q in self.pickups if q.kind == "heart") < 2:
            self.e_pity += 1
            chance = (HEART_DROP_BASE + HEART_DROP_PER_HP * (missing - 1)
                      + HEART_DROP_PITY * self.e_pity + (0.08 if m.kind == "skel" else 0.0)
                      + (ELITE_HEART_BONUS if elite else 0.0))
            if random.random() < chance:
                self.e_pity = 0
                self.pickups.append(Heart(m.x, m.y - 4))
                self.add_wave(m.x, m.y - 6, "heart")
        if getattr(m, "boss", False) and not self.boss_monsters():
            self.boss_defeated(m)                # ultima parte del jefe: botin y puerta
        if self.e_boss is None and self.e_room_kills >= self.e_quota:
            self.endless_open_door("¡PUERTA ABIERTA! (esquina inferior derecha). Los monstruos siguen llegando: corre.")

    def endless_open_door(self, msg):
        """Abre la puerta de salida (reutiliza la llave: puerta abierta + antorchas)."""
        if self.has_key:
            return
        lv = self.level
        self.has_key = True
        lv.door_open = True
        dcx, dcy = lv.door[0] * TILE + 8, lv.door[1] * TILE + 8
        self.add_wave(dcx, dcy, "key", 1.3)
        self.sfx("key")
        self.toast(msg, 4.0)

    # ------------------------------------------------------------ combo / tienda
    def combo_mult(self):
        return max(1, min(COMBO_MAX, self.combo)) if self.combo_t > 0 else 1

    def build_shop(self):
        feet = (ROWS - 1) * TILE
        names = (("heart", SHOP_HEART, "un corazón"), ("card", SHOP_CARD, "una carta de mejora"),
                 ("maxhp", SHOP_MAXHP, "+1 vida máxima"))
        self.shop_items = [dict(id=i, price=pr, label=lb, x=c * TILE + 8, y=feet, sold=False)
                           for (i, pr, lb), c in zip(names, SHOP_COLS)]

    def shop_item_near(self):
        if not self.e_shop:
            return None
        p = self.player
        for it in self.shop_items:
            if not it["sold"] and abs(p.x - it["x"]) < 14 and abs(p.y - it["y"]) < 20:
                return it
        return None

    def shop_hint(self):
        it = self.shop_item_near()
        if it is None:
            return ""
        return "E: comprar %s por %d monedas (tienes %d)" % (it["label"], it["price"], self.coins)

    def try_buy(self):
        """Compra el objeto de la tienda que tengas al lado (tecla E)."""
        if self.state != "play" or self.mode != "endless":
            return False
        it = self.shop_item_near()
        if it is None:
            return False
        p = self.player
        if self.coins < it["price"]:
            self.toast("Te faltan %d monedas." % (it["price"] - self.coins), 2.0)
            self.sfx("locked")
            return False
        if it["id"] == "heart" and p.hp >= self.max_hp:
            self.toast("Ya tienes la vida llena.", 2.0)
            return False
        if it["id"] == "maxhp" and self.max_hp >= MAX_HP_CAP:
            self.toast("Ya tienes la vida máxima posible.", 2.0)
            return False
        if it["id"] == "card" and not self.available_perks():
            self.toast("Ya tienes todas las mejoras.", 2.0)
            return False
        self.coins -= it["price"]
        it["sold"] = True
        ach_notify(self, "buy")
        self.add_wave(it["x"], it["y"] - 8, "buy", 1.0)
        self.sfx("key")
        if it["id"] == "heart":
            p.hp = min(self.max_hp, p.hp + 1)
        elif it["id"] == "maxhp":
            self.apply_perk("maxhp")
        else:
            self.start_cards()
        return True

    def draw_endless_stats(self):
        """Puntos, combo, monedas y modificador (esquina superior derecha)."""
        k, SW = self.k, self.SW
        lh = self.line_h()
        x, y = SW - 4 * k, 3 * k
        self.draw_text("PUNTOS %d" % self.score, x, y, 1.0, GOLD, anchor="r")
        y += lh
        self.draw_text("MONEDAS %d" % self.coins, x, y, 1.0, (255, 215, 90), anchor="r")
        y += lh
        if self.combo_t > 0 and self.combo >= 2:
            self.draw_text("COMBO x%d" % self.combo_mult(), x, y, 1.0, (255, 150, 90), anchor="r")
            y += lh
        if self.room_mod:
            self.draw_text(MOD_INFO[self.room_mod][0], x, y, 1.0, CYAN, anchor="r")
            y += lh
        if self.player.mute_echo > 0:
            self.draw_text("SIN ECOS %.1f" % self.player.mute_echo, x, y, 1.0, (140, 170, 210), anchor="r")

    def draw_mod_banner(self):
        if self.e_boss is not None and self.boss_banner_t > 0 and self.fade_in <= 0:
            self.draw_center_title("JEFE: " + self.boss_name, RED, BOSS_INFO[self.e_boss][1])
            return
        if self.room_mod and self.mod_banner_t > 0 and self.fade_in <= 0:
            nm, ds = MOD_INFO[self.room_mod]
            self.draw_center_title(nm, CYAN, ds)

    # ------------------------------------------------------------ dibujo
    def shop_text(self, s):
        t = self._shop_txt.get(s)
        if t is None:
            t = self.font.render(s, False, (255, 215, 90))
            self._shop_txt[s] = t
        return t

    def draw_pickups(self, v):
        T = self.tex
        for it in self.shop_items:
            if it["sold"]:
                continue
            x, y = int(it["x"]), int(it["y"])
            pygame.draw.rect(v, (60, 52, 70), (x - 6, y - 8, 12, 8))
            pygame.draw.rect(v, (130, 112, 150), (x - 6, y - 8, 12, 2))
            bob = int(math.sin(self.time * 3 + x) * 1.2)
            if it["id"] == "card":
                pygame.draw.rect(v, (232, 220, 190), (x - 4, y - 21 + bob, 8, 11))
                pygame.draw.rect(v, GOLD, (x - 4, y - 21 + bob, 8, 11), 1)
                pygame.draw.rect(v, (150, 225, 255), (x - 1, y - 17 + bob, 2, 3))
            else:
                v.blit(T.heart_full, (x - 4, y - 19 + bob))
                if it["id"] == "maxhp":
                    pygame.draw.rect(v, GOLD, (x + 3, y - 22 + bob, 1, 5))
                    pygame.draw.rect(v, GOLD, (x + 1, y - 20 + bob, 5, 1))
            tx = self.shop_text(str(it["price"]))
            v.blit(tx, (x - tx.get_width() // 2, y - 33))
        for h in self.pickups:
            if h.t < 3.0 and int(self.time * 8) % 2 == 0:
                continue                           # parpadea antes de desaparecer
            bob = int(math.sin(self.time * 5 + h.phase) * 1.2) if h.on_ground else 0
            if h.kind == "coin":
                v.blit(T.shadow, (int(h.x) - 6, int(h.y) - 2))
                w = 1 + int(abs(math.sin(self.time * 6 + h.phase)) * 4)       # giro de la moneda
                pygame.draw.rect(v, (150, 100, 20), (int(h.x) - w // 2 - 1, int(h.y) - 6 + bob, w + 2, 6))
                pygame.draw.rect(v, (255, 215, 90), (int(h.x) - w // 2, int(h.y) - 6 + bob, w, 5))
                continue
            v.blit(T.shadow, (int(h.x) - 6, int(h.y) - 2))
            v.blit(T.heart_full, (int(h.x) - 4, int(h.y) - 9 + bob))

    def light_pickups(self, L):
        if self.glow_heart is None:
            self.glow_heart = make_radial(14, (255, 110, 160), 0.8)
            self.glow_coin = make_radial(12, (255, 215, 90), 0.8)
        for it in self.shop_items:
            if not it["sold"]:
                L.blit(self.glow_coin, (int(it["x"]) - 12, int(it["y"]) - 22), special_flags=pygame.BLEND_RGB_MAX)
        for h in self.pickups:
            if h.t < 3.0 and int(self.time * 8) % 2 == 0:
                continue
            if h.kind == "coin":
                L.blit(self.glow_coin, (int(h.x) - 12, int(h.y) - 16), special_flags=pygame.BLEND_RGB_MAX)
            else:
                L.blit(self.glow_heart, (int(h.x) - 14, int(h.y) - 18), special_flags=pygame.BLEND_RGB_MAX)
