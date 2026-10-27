# -*- coding: utf-8 -*-
"""RONDA 3: elites, jefes, enemigos nuevos (invisible, ladron, silenciador) y pinchos.

Las clases de los enemigos estan en entities.py (GiantSkeleton, SwarmBat, BigBat, BossGhost,
Phantom, Thief, Silencer). Este mixin pone la logica que necesita el juego entero:
  * jefes: aparicion, barra de vida, abanico de flechas, fusion del enjambre, division del fantasma
  * elites: apply_elite()
  * ladron: nearest_heart / thief_steal / thief_escape / thief_drop
  * fantasma invisible y pinchos: una onda de eco "toca" algo si su frente pasa por encima (wave_touches)
  * dibujo de los enemigos especiales (escalados / teñidos / invisibles), de los pinchos y de la barra del jefe
Todo el balance esta en config.py (bloque RONDA 3).
"""
import math
import random

import pygame
from .config import *
from .achievements import ach_notify
from .entities import GiantSkeleton, SwarmBat, BigBat, BossGhost, Arrow, Ghoul, Skeleton, Bat
from .nav import node_at, graph
from .physics import solid_hit
from .rooms import boss_index, BOSS_INFO, spawn_points
from .endless import Coin, Heart

REVEAL_SKIP = ("spawn",)                                              # ondas que NO revelan al fantasma invisible
BOSS_BAR_COL = (220, 70, 70)


class ThreatsMixin:
    # valores por defecto (Game.__new__ en las pruebas y modo niveles)
    e_boss = None
    boss_name = ""
    boss_max = 1.0
    boss_banner_t = 0.0
    swarm_total = BOSS_SWARM_BIG_HP

    def init_threats_state(self):
        self.e_boss = None
        self.boss_name = ""
        self.boss_max = 1.0
        self.boss_banner_t = 0.0
        self.swarm_total = BOSS_SWARM_BIG_HP
        self._sprite_cache = {}
        self._thief_warned = False

    # ------------------------------------------------------------ elites
    def apply_elite(self, m):
        """Elite: x2 vida, aura pulsante, mas botin (ver endless_on_kill)."""
        m.elite = True
        m.hp = m.hp * ELITE_HP_MULT
        m.elite_phase = random.random() * 6.28
        if isinstance(m, Bat):
            m.spd = 1.3                                  # elite murcielago: mas rapido
        elif isinstance(m, Ghoul):
            m.spd_mult = 1.25                            # elite fantasma: mas rapido
            # (elite esqueleto: dispara dos flechas seguidas, ver Skeleton.update)

    # ------------------------------------------------------------ jefes
    def boss_monsters(self):
        return [m for m in self.monsters if getattr(m, "boss", False)]

    def boss_fraction(self):
        """Vida restante del jefe (0..1) para la barra; suma todas sus partes."""
        tot = sum(m.boss_value() for m in self.boss_monsters())
        return max(0.0, min(1.0, tot / max(1.0, self.boss_max)))

    def spawn_boss(self):
        """Crea el jefe de la sala actual (rota entre los 3 segun el numero de sala)."""
        lv, p = self.level, self.player
        idx = boss_index(self.e_room)
        bf = 1.0 + BOSS_HP_STEP * (self.e_room // BOSS_EVERY)         # cada jefe es algo mas duro
        rnd = random.Random(self.e_base_seed + self.e_room * 31 + 5)
        ground, air = spawn_points(lv)
        floor = [q for q in ground if q[1] == ROWS - 2 and q[0] >= COLS - 9] or ground
        c, r = rnd.choice(floor)
        fx, fy = c * TILE + 8, (r + 1) * TILE
        seed = self.e_base_seed + 900 + self.e_room
        pw = self.e_room // BOSS_EVERY                                  # jefes ya derrotados: sube los ataques
        self.boss_power = pw
        self.e_boss = idx
        self.boss_name = BOSS_INFO[idx][0]
        if idx == 0:
            hp = int(round(BOSS_GIANT_HP * bf))
            self.monsters.append(GiantSkeleton(fx, fy, seed, hp, pw))
            self.boss_max = float(hp)
        elif idx == 1:
            total = int(math.ceil(BOSS_SWARM_BIG_HP * bf))
            self.swarm_total = total
            self.boss_max = float(total)
            cands = [q for q in air if q[0] >= 12] or air
            cx, cy = rnd.choice(cands)
            for i in range(BOSS_SWARM_BATS):
                ang = i * 6.283 / BOSS_SWARM_BATS
                bx, by = cx * TILE + 8 + math.cos(ang) * 22, cy * TILE + 8 + math.sin(ang) * 12
                if lv.is_wall(int(bx // TILE), int(by // TILE)):
                    bx, by = cx * TILE + 8, cy * TILE + 8
                self.monsters.append(SwarmBat(bx, by, seed + i, i, total / float(BOSS_SWARM_BATS)))
        else:
            hp = int(round(BOSS_GHOST_HP * bf))
            m = BossGhost(fx, fy, seed, 2, hp, pw)
            self.monsters.append(m)
            self.boss_max = float(m.boss_value())
        self.boss_banner_t = MOD_BANNER_T + 0.8
        self.add_wave(fx, fy - 12, "roar", 1.2)
        self.sfx("pulse")
        self.toast("¡JEFE: %s! Derrótalo para abrir la puerta. %s" % (self.boss_name, BOSS_INFO[idx][1]), 5.0)

    def boss_slam(self, m):
        """Aterrizaje del esqueleto gigante: onda y polvo (el dano lo hace el contacto)."""
        self.add_wave(m.x, m.y - 3, "attack", 1.6)
        self.add_shake(4.0)
        self.landing_dust(m.x, m.y, 300.0)
        self.sfx("step")

    def boss_fan_shoot(self, m, n=3):
        """n flechas en abanico apuntando al jugador (3, 5, 7 o 9 segun la fase)."""
        p = self.player
        ox, oy = m.x + m.face * 10, m.y - m.h * 0.65
        ang = math.atan2((p.y - 8) - oy, p.x - ox)
        for k in range(n):
            a = ang + (k - (n - 1) / 2.0) * BOSS_GIANT_FAN
            self.arrows.append(Arrow(ox, oy, math.cos(a) * BOSS_GIANT_ARROW, math.sin(a) * BOSS_GIANT_ARROW,
                                     "enemy", 0.0))
        self.sfx("bow")

    # ---------------- ronda 6: piezas de los ataques de los jefes (las llaman BossAI.at(...) y las clases de jefe)
    def boss_tele(self, m, kind="tele", scale=1.0):
        """Aviso de ataque: una onda de eco sale del jefe."""
        self.add_wave(m.x, m.y - m.h * 0.6, kind, scale)

    def boss_phase_up(self, m):
        """El jefe cruza el 66% / 33% de vida: ruge, tiembla la sala y ataca antes."""
        self.add_wave(m.x, m.y - m.h * 0.5, "roar", 1.7)
        self.add_shake(3.5)
        self.sfx("pulse")
        m.think_t = min(m.think_t, 0.5)
        self.burst(m.x, m.y - m.h * 0.5, ((255, 120, 90), (255, 200, 150), (220, 70, 60)), 18, 120, up=10)
        if m._ph >= 3:
            self.toast("¡%s SE ENFURECE!" % self.boss_name, 2.5)

    def boss_shot(self, x, y, ang, speed, style=None, grav=0.0, life=3.0, bounces=0):
        a = Arrow(x, y, math.cos(ang) * speed, math.sin(ang) * speed, "enemy", grav)
        a.style, a.life, a.bounces = style, life, bounces
        self.arrows.append(a)
        return a

    def boss_radial(self, m, n, speed, style, offset=0.0, grav=0.0, life=3.0, bounces=0):
        """Anillo de n proyectiles repartidos alrededor del jefe."""
        ox, oy = m.x, m.y - m.h * 0.5
        for i in range(n):
            self.boss_shot(ox, oy, offset + i * 6.2832 / n, speed, style, grav, life, bounces)
        self.add_wave(ox, oy, "attack", 1.2)
        self.sfx("bow")

    def boss_aimed(self, m, n, spread, speed, style, bounces=0, life=3.0):
        """n proyectiles apuntados al jugador con `spread` radianes entre ellos."""
        p = self.player
        ox, oy = m.x, m.y - m.h * 0.5
        ang = math.atan2((p.y - 8) - oy, p.x - ox)
        for k in range(n):
            self.boss_shot(ox, oy, ang + (k - (n - 1) / 2.0) * spread, speed, style, 0.0, life, bounces)
        self.add_wave(ox, oy, "attack", 1.2)
        self.sfx("bow")

    def boss_shock(self, m):
        """Dos ondas rasantes (izquierda y derecha) al aterrizar el esqueleto: hay que saltarlas."""
        for s_ in (-1, 1):
            a = self.boss_shot(m.x + s_ * 10, m.y - 3, 0.0 if s_ > 0 else math.pi, BOSS_SHOCK_SPEED, "shock", 0.0, 2.8)
        self.add_wave(m.x, m.y - 4, "attack", 1.3)

    def _floor_y(self, x, y):
        n = node_at(self.level, x, y)
        return (n[1] + 1) * TILE if n else y

    def boss_rain_mark(self, m, x):
        """Marca en el suelo (eco rojo) donde va a caer una flecha de la lluvia."""
        self.add_wave(x, self._floor_y(x, self.player.y) - 3, "tele", 1.0)

    def boss_rain_drop(self, m, x):
        self.arrows.append(Arrow(x, TILE * 1.4, 0.0, BOSS_GIANT_RAIN_ARROW, "enemy", 0.0))
        self.sfx("bow")

    def boss_bomb(self, m):
        """Bola que cae desde el techo (bombardeo del murcielago grande)."""
        a = Arrow(m.x, m.y, 0.0, 30.0, "enemy", 240.0)
        a.style, a.life = "bomb", 3.2
        self.arrows.append(a)

    def boss_summon(self, m, kind, n):
        """El jefe invoca esbirros (de 1 de vida) a sus lados; mueren con el jefe."""
        lv = self.level
        made = 0
        for i in range(n):
            if self.boss_minions() >= BOSS_MINIONS_MAX:
                break
            side = -1 if i % 2 == 0 else 1
            x = max(14.0, min(MAP_W - 14.0, m.x + side * (24 + 14 * (i // 2))))
            seed = self.e_base_seed + 700 + self.e_room * 7 + i + int(self.time * 10) % 50
            if kind == "skel":
                if solid_hit(lv, x, m.y, 5.0, 14.0, False):
                    x = m.x
                mon = Skeleton(x, m.y, seed)
            else:
                mon = Bat(x, m.y - m.h * 0.5 - 8, seed)
            mon.hp = 1
            mon.chase_t = 4.0
            mon.minion = True
            self.monsters.append(mon)
            made += 1
            self.burst(x, m.y - 6, ((255, 230, 200), (230, 190, 150), (200, 150, 110)), 8, 70, up=20)
        if made:
            self.add_wave(m.x, m.y - m.h * 0.5, "fuse", 1.2)
            self.sfx("pulse")

    def boss_minions(self):
        return sum(1 for q in self.monsters if getattr(q, "minion", False))

    def boss_blink_dest(self, m):
        """Sitio donde reaparece el fantasma: en tu misma plataforma, a 2-5 casillas, mejor a tu espalda."""
        lv, p = self.level, self.player
        pn = node_at(lv, p.x, p.y)
        if pn is None:
            return None
        nodes = graph(lv).nodes
        cands = [pn[0] + o for o in (3, -3, 4, -4, 2, -2, 5, -5) if (pn[0] + o, pn[1]) in nodes]
        cands.sort(key=lambda c: 0 if (c - pn[0]) * p.face < 0 else 1)
        for c in cands:
            x, y = c * TILE + 8, (pn[1] + 1) * TILE
            if not solid_hit(lv, x, y, m.hw, m.h, False):
                return (x, y)
        return None

    def boss_appear(self, m):
        self.add_wave(m.x, m.y - 10, "roar", 0.9)
        self.burst(m.x, m.y - 10, ((190, 150, 255), (235, 220, 255), (150, 110, 230)), 16, 110, up=15)
        self.add_shake(1.5)
        self.sfx("pulse")

    def swarm_fuse(self, hit):
        """Al daniar a un murcielago del enjambre, los demas se funden en uno grande."""
        swarm = [b for b in self.monsters if getattr(b, "tag", "") == "swarm" and b is not hit]
        if not swarm:
            return
        cx = sum(b.x for b in swarm) / len(swarm)
        cy = sum(b.y - b.h / 2 for b in swarm) / len(swarm)
        for b in swarm:
            self.monsters.remove(b)
        hp = max(1, int(math.ceil(self.swarm_total * len(swarm) / float(BOSS_SWARM_BATS))))
        big = BigBat(cx, cy, self.e_base_seed + 950 + self.e_room, hp, getattr(self, "boss_power", 0))
        big.chase_t = 4.0
        self.monsters.append(big)
        self.add_wave(cx, cy, "fuse", 1.2)
        self.burst(cx, cy, ((255, 150, 210), (255, 210, 235), (230, 100, 170)), 24, 130, up=10)
        self.add_shake(3.0)
        self.sfx("pulse")

    def boss_split_ghost(self, m):
        """El fantasma grande se divide en 2 pequenos (nivel 1)."""
        for s in (-1, 1):
            c = BossGhost(m.x + s * 6, m.y, self.e_base_seed + 960 + s, 1, BOSS_GHOST_CHILD_HP, m.power)
            c.vx, c.vy, c.chase_t = s * 110.0, -130.0, 4.0
            self.monsters.append(c)
        self.add_wave(m.x, m.y - 10, "fuse", 1.0)
        self.burst(m.x, m.y - 10, ((190, 150, 255), (235, 220, 255), (150, 110, 230)), 22, 130, up=20)
        self.add_shake(2.5)

    def boss_defeated(self, m):
        """Ultima parte del jefe muerta: botin, puntos y puerta abierta."""
        self.boss_banner_t = 0.0
        ach_notify(self, "boss")
        self.score += BOSS_SCORE
        for _ in range(BOSS_COINS):
            self.pickups.append(Coin(m.x + random.uniform(-6, 6), m.y - 6))
        self.pickups.append(Heart(m.x, m.y - 4))
        self.add_wave(m.x, m.y - 8, "heart", 1.2)
        self.arrows = [a for a in self.arrows if a.owner != "enemy"]
        for q in [q for q in self.monsters if getattr(q, "minion", False)]:        # los esbirros caen con el jefe
            self.burst(q.x, q.y - 6, ((255, 230, 200), (230, 190, 150)), 8, 70, up=20)
        self.monsters[:] = [q for q in self.monsters if not getattr(q, "minion", False)]
        self.slowmo = SLOWMO_LAST_KILL * 1.6
        self.add_shake(SHAKE_DEATH)
        self.endless_open_door("¡JEFE DERROTADO! (+%d puntos). La puerta está abierta." % BOSS_SCORE)

    # ------------------------------------------------------------ ladron
    def nearest_heart(self, x, y):
        best, bd = None, 1e9
        for q in self.pickups:
            if q.kind == "heart":
                d = math.hypot(q.x - x, q.y - y)
                if d < bd:
                    best, bd = q, d
        return best

    def thief_steal(self, m, heart):
        if heart in self.pickups:
            self.pickups.remove(heart)
        m.loot, m.flee_t = True, THIEF_FLEE_T
        self.add_wave(m.x, m.y - 8, "thief", 1.2)
        self.sfx("locked")
        if not self._thief_warned:
            self._thief_warned = True
            self.toast("¡Un ladrón te ha robado un corazón! Mátalo antes de que escape.", 3.5)

    def thief_escape(self, m):
        if m in self.monsters:
            self.monsters.remove(m)
        self.add_wave(m.x, m.y - 8, "thief", 0.8)
        self.toast("El ladrón escapó con el corazón.", 2.5)

    def thief_drop(self, m):
        self.pickups.append(Heart(m.x, m.y - 4))
        self.add_wave(m.x, m.y - 6, "heart")

    # ------------------------------------------------------------ ondas: ¿tocan algo?
    def wave_touches(self, w, x, y, band=7.0):
        """True si el frente de la onda w pasa por el punto (x, y) y hay linea de vision."""
        d = math.hypot(x - w.x, y - w.y)
        if d > w.max_r or abs(d - w.r) > band:
            return False
        n = w.n
        i = int((math.atan2(y - w.y, x - w.x) % 6.283185307179586) / 6.283185307179586 * n + 0.5) % n
        return w.rays[i] >= d - 2.0

    def phantom_scan(self, m):
        """El fantasma invisible se deja ver un instante cuando el frente de una onda lo toca."""
        cy = m.y - m.h / 2
        for w in self.waves:
            if w.kind not in REVEAL_SKIP and self.wave_touches(w, m.x, cy, 8.0):
                m.reveal = PHANTOM_REVEAL_T
                return

    # ------------------------------------------------------------ pinchos
    def update_traps(self, dt):
        lv, p = self.level, self.player
        traps = getattr(lv, "traps", None)
        if not traps:
            return
        tt = lv.trap_t
        for k in list(tt):
            tt[k] -= dt
            if tt[k] <= 0:
                del tt[k]
        for (tx, ty) in traps:
            cx, cy = tx * TILE + 8, ty * TILE + 11
            for w in self.waves:
                if self.wave_touches(w, cx, cy, 8.0):
                    tt[(tx, ty)] = TRAP_REVEAL_T
                    break
        if p.inv > 0 or p.dash_t > 0:
            return
        for (tx, ty) in traps:
            if (p.x + p.hw > tx * TILE + 2 and p.x - p.hw < (tx + 1) * TILE - 2
                    and p.y > ty * TILE + 9 and p.y - p.h < (ty + 1) * TILE):
                self.trap_damage((tx, ty))
                return

    def trap_damage(self, cell):
        """Pincharse: 1 de dano (el escudo no vale), TRAP_INV s de invulnerabilidad y rebote."""
        p = self.player
        p.hp -= 1
        ach_notify(self, "hurt")
        p.inv = TRAP_INV
        p.stun = 0.2
        p.vy = -170.0
        p.vx *= 0.3
        p.on_ground = False
        self.level.trap_t[cell] = 1.5
        self.hurt_flash = 0.5
        self.add_shake(SHAKE_HURT)
        self.add_wave(p.x, p.y - 4, "hurt")
        self.sfx("hurt")
        if p.hp <= 0:
            self.state = "dead"
            self.death_fx()
            if self.mode == "endless":
                self.endless_game_over()

    # ------------------------------------------------------------ dibujo
    def scaled_sprite(self, spr, scale):
        key = (id(spr), "s", scale)
        s = self._sprite_cache.get(key)
        if s is None:
            w, h = spr.get_size()
            s = pygame.transform.scale(spr, (int(round(w * scale)), int(round(h * scale))))
            self._sprite_cache[key] = s
        return s

    def tinted_sprite(self, spr, color):
        key = (id(spr), "t", color)
        s = self._sprite_cache.get(key)
        if s is None:
            s = spr.copy()
            s.fill(tuple(color) + (255,), special_flags=pygame.BLEND_RGBA_MULT)
            self._sprite_cache[key] = s
        return s

    def rim_key(self, e, base):
        """Clave del color del contorno: dorado para elites, propio para jefes y enemigos especiales."""
        if getattr(e, "elite", False):
            return "elite"
        tag = getattr(e, "tag", "")
        return tag if tag in ("thief", "silencer", "phantom", "giant", "bigbat", "swarm", "bghost") else base

    def variant_name(self, e):
        """Nombre de las variantes de variants.py que le tocan a este monstruo (None = piel base)."""
        tag, elite = getattr(e, "tag", ""), getattr(e, "elite", False)
        if tag == "bghost":
            return "bghost" if e.level >= 2 else "bghost_kid"
        if tag in ("giant", "bigbat", "swarm"):
            return tag
        if tag in ("thief", "phantom", "silencer"):
            return ("elite_" + tag) if elite else tag
        return ("elite_" + e.kind) if elite else None

    def flashed_sprite(self, spr):
        """Version brillante (rojiza) del sprite: el jefe parpadea mientras AVISA de un ataque."""
        key = (id(spr), "f")
        s = self._sprite_cache.get(key)
        if s is None:
            s = spr.copy()
            s.fill((110, 40, 30, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self._sprite_cache[key] = s
        return s

    def draw_special_monster(self, v, e):
        """Monstruos con dibujo propio: jefes, enemigos nuevos y elites (rasgos de variants.py, escalados, invisibles)."""
        T = self.tex
        base = e.kind
        q = 1.0
        if getattr(e, "invisible", False):
            q = min(1.0, e.reveal / PHANTOM_REVEAL_T)
        q = min(q, getattr(e, "ghost_a", 1.0))                 # el fantasma jefe se desvanece al teletransportarse
        if q <= 0.02:
            return                                       # invisible: no se dibuja nada (ni silueta ni halo)
        name = self.variant_name(e)
        fr = T.var.get(name) if name else None
        if base == "ghoul":
            A = fr or T.ghoul_anim
            moving = e.on_ground and abs(e.vx) > 4
            spr = A["walk"][int(self.time * 8 + e.phase) % 4] if moving else A["idle"]
        elif base == "skel":
            A = (fr or T.skel_anim)["right" if e.face > 0 else "left"]
            spr = A["walk"][int(self.time * 7 + e.phase) % 4] if (e.on_ground and abs(e.vx) > 4) else A["idle"]
        else:
            F = fr or T.bat
            spr = F[int(self.time * (11 if e.chase_t > 0 else 6) + e.phase) % len(F)]
        sc = getattr(e, "scale", 1.0)
        if sc != 1.0:
            spr = self.scaled_sprite(spr, sc)
        if getattr(e, "tele", 0.0) > 0 and int(self.time * 16) % 2 == 0:
            spr = self.flashed_sprite(spr)                # aviso de ataque: parpadea
        if q < 1.0:
            spr = self.faded(spr, 255 * q)
        w, h = spr.get_size()
        x = int(e.x - w / 2)
        if base == "bat":
            y = int(e.y - e.h / 2 - h / 2)
        else:
            y = int(e.y - h) + 1
            sh = self.scaled_sprite(T.shadow, sc) if sc != 1.0 else T.shadow
            v.blit(sh, (int(e.x) - sh.get_width() // 2, int(e.y) - 2))
        v.blit(spr, (x, y))
        if getattr(e, "loot", False):
            v.blit(T.heart_full, (int(e.x) - 4, y - 9))   # el ladron lleva el corazon robado
        al = getattr(e, "alert", 0.0)
        self._mdraw.append((spr, x, y, self.rim_key(e, base), q if getattr(e, "invisible", False) else al))

    def draw_foe_shot(self, v, a):
        """Proyectiles de jefe: ondas rasantes (shock), espiritus, sonicos del murcielago y bombas."""
        x, y = int(a.x), int(a.y)
        fl = 1 if int(self.time * 18 + a.t * 9) % 2 else 0
        if a.style == "shock":
            sg = 1 if a.vx >= 0 else -1
            pygame.draw.polygon(v, (200, 40, 40), ((x + sg * 6, y), (x - sg * 4, y - 5), (x - sg * 1, y), (x - sg * 4, y + 4)))
            pygame.draw.polygon(v, (255, 190, 150), ((x + sg * 5, y), (x - sg * 2, y - 3), (x, y), (x - sg * 2, y + 2)))
        elif a.style == "spirit":
            pygame.draw.circle(v, (70, 36, 150), (x, y), 4 + fl)
            pygame.draw.circle(v, (185, 145, 255), (x, y), 3)
            pygame.draw.circle(v, (245, 235, 255), (x, y), 1)
        elif a.style == "sonic":
            pygame.draw.circle(v, (255, 120, 190), (x, y), 3 + fl, 1)
            pygame.draw.circle(v, (255, 215, 235), (x, y), 1)
        else:                                            # bomb
            pygame.draw.circle(v, (70, 24, 52), (x, y), 3 + fl)
            pygame.draw.circle(v, (255, 140, 70), (x, y), 2)
            pygame.draw.circle(v, (255, 235, 170), (x, y), 1)

    def draw_traps(self, v):
        """Pinchos: solo se ven mientras dura el aviso de una onda (o si te han pinchado)."""
        for (tx, ty), t in getattr(self.level, "trap_t", {}).items():
            f = min(1.0, t / (TRAP_REVEAL_T * 0.6))
            if f < 0.12:
                continue
            x0, y1 = tx * TILE, (ty + 1) * TILE
            col = (int(225 * f), int(232 * f), int(246 * f))
            for i in range(3):
                bx = x0 + 1 + i * 5
                pygame.draw.polygon(v, col, ((bx, y1), (bx + 4, y1), (bx + 2, y1 - 8)))
            pygame.draw.line(v, (int(170 * f), int(40 * f), int(40 * f)), (x0, y1 - 1), (x0 + TILE - 1, y1 - 1))

    def draw_boss_bar(self):
        """Barra de vida del jefe (arriba, en pantalla)."""
        if self.mode != "endless" or self.e_boss is None or self.state not in ("play", "paused"):
            return
        if not self.boss_monsters():
            return
        k, SW = self.k, self.SW
        bw, bh = int(200 * k), max(4, int(5 * k))
        x0, y0 = (SW - bw) // 2, int(3 * k) + self.line_h()
        self.draw_text(self.boss_name, SW // 2, int(3 * k), 1.0, (255, 150, 120), anchor="c")
        pygame.draw.rect(self.screen, (14, 10, 20), (x0 - 2, y0 - 2, bw + 4, bh + 4))
        pygame.draw.rect(self.screen, (70, 24, 28), (x0, y0, bw, bh))
        pygame.draw.rect(self.screen, BOSS_BAR_COL, (x0, y0, int(bw * self.boss_fraction()), bh))
        pygame.draw.rect(self.screen, (232, 220, 190), (x0 - 2, y0 - 2, bw + 4, bh + 4), 1)
        for fr in (0.66, 0.33):                                  # marcas de fase (66% y 33%)
            tx = x0 + int(bw * fr)
            pygame.draw.line(self.screen, (232, 220, 190), (tx, y0 - 2), (tx, y0 + bh + 1))
