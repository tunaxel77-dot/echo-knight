# -*- coding: utf-8 -*-
"""Entidades: Player, Ghoul, Bat, Skeleton, Arrow, jefes (con fases y patrones de ataque) y enemigos nuevos."""
import array
import math
import random
import sys

import pygame
from .config import *
from .lighting import *
from .physics import *
from .level import *
from .nav import walk_toward, flee_from, air_steer, air_waypoint, los


class Player:
    is_player = True
    hw = 4.5
    h = 14.0

    def __init__(self, x, y):
        self.x, self.y = x, y            # y = pies
        self.vx = self.vy = 0.0
        self.face = 1
        self.on_ground = False
        self.hit_wall = False
        self.hp = MAX_HP
        self.inv = 0.0
        self.stun = 0.0
        self.attack_cd = 0.0
        self.attack_t = 0.0
        self.pulse_cd = 0.0
        self.shoot_cd = 0.0
        self.shoot_t = 0.0
        self.step_acc = 0.0
        self.walk = 0.0
        self.sneak = False
        self.shield = False
        self.coyote = 0.0
        self.jbuf = 0.0
        self.moved_total = 0.0
        self.boost = 1.0                 # impulso del salto diagonal
        self.look = 0.0                  # desplazamiento suavizado del haz frontal
        self.sf = 0.0                    # fraccion de velocidad (0..1)
        self.pogo = 0.0                  # evita cortar el rebote del tajo aereo
        self.air_atk = False
        self.in_vent = False
        self.dash_t = 0.0                # dash secreto (modo TUN)
        self.dash_cd = 0.0
        self.dash_dir = 1
        self.dash_hit = set()
        self.windup = 0.0                # anticipacion del tajo
        self.land_t = 0.0                # compresion al aterrizar
        self.land_pow = 0.0
        self.tilt = 0.0                  # inclinacion del sprite (grados, + = hacia delante)
        self.charging = False            # carga del arco (tecla de disparo mantenida)
        self.charge = 0.0
        self.mute_echo = 0.0             # ronda 3: segundos sin ecos (silenciador)
        self.clap_cd = 0.0               # luchador: enfriamiento del aplauso
        self.dive_t = 0.0                # luchador: tiempo con S pulsado en el aire (picada)
        self.clap_t = 0.0                # luchador: tiempo del aplauso en pantalla
        self.air_left = 0                # ronda 4: saltos en el aire que quedan (pícaro)


class Ghoul:
    """Fantasma terrestre: patrulla, te oye, te persigue y SUBE, BAJA y cruza huecos entre plataformas (nav.py).
    Si te pierde de vista va al ultimo sitio donde te vio y busca un momento."""
    is_player = False
    kind = "ghoul"
    hw = 5.0
    h = 14.0
    spd_mult = 1.0                # multiplicador de velocidad de persecucion (elites, jefes)

    def __init__(self, x, y, seed):
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.hp = 2
        self.rnd = random.Random(seed)
        self.wdir = self.rnd.choice((-1, 1))
        self.wander_t = self.rnd.uniform(0.5, 2.0)
        self.chase_t = 0.0
        self.stun = 0.0
        self.jump_cd = 0.0
        self.on_ground = False
        self.hit_wall = False
        self.phase = self.rnd.random() * 6.28
        self.last_seen = None         # (x, y) donde vio u oyo al jugador por ultima vez
        self.air_tx = None            # x de aterrizaje durante un salto / caida (control aereo)

    def ground_ahead(self, lv, d):
        tx = int((self.x + d * (self.hw + 2)) // TILE)
        ty = int(self.y // TILE)
        return lv.blocks(tx, ty, False) or lv.is_plat(tx, ty)

    def sees(self, g):
        p = g.player
        return los(g.level, self.x, self.y - self.h * 0.6, p.x, p.y - 8)

    def legacy_chase(self, g, tx, ty, speed):
        """Persecucion antigua (sin grafo): solo se usa si no hay camino calculable."""
        lv = g.level
        dx = tx - self.x
        d = 1 if dx > 0 else -1
        tvx = d * speed if abs(dx) > 3 else 0.0
        above, below = self.y - ty > 14, ty - self.y > 14
        ahead = self.ground_ahead(lv, d)
        if self.jump_cd <= 0 and abs(dx) > 3:
            if above and abs(dx) < 44:
                self.vy, self.jump_cd = -GHOUL_JUMP, 0.9
            elif self.hit_wall:
                self.vy, self.jump_cd = -215.0, 0.9
            elif not ahead and not below and abs(dx) < 80:
                self.vy, self.jump_cd = -215.0, 0.9
                tvx = d * speed * 1.5
        if not ahead and not below and self.vy == 0:
            tvx = 0.0
        return tvx

    def chase_move(self, g, tx, ty, speed):
        """Velocidad horizontal para ir hacia (tx, ty) navegando por las plataformas."""
        if self.h <= 28.0:
            v = walk_toward(self, g, tx, ty, speed)
            if v is not None:
                return v
        return self.legacy_chase(g, tx, ty, speed)

    def lost_track(self, sees, tx, ty):
        """Llego al ultimo punto conocido y no te ve: busca un instante y se rinde."""
        if not sees and abs(self.x - tx) < 8 and abs(self.y - ty) < 20:
            self.chase_t = min(self.chase_t, 0.8)

    def update(self, dt, g):
        lv, p = g.level, g.player
        A = g.aggr
        self.jump_cd -= dt
        self.stun -= dt
        if self.on_ground:
            self.air_tx = None
        else:
            air_steer(self)
        dist = math.hypot(p.x - self.x, p.y - self.y)
        reach = 38 if p.sneak else 95
        sees = self.sees(g)
        if dist < reach and abs(p.y - self.y) < 70 and g.grace <= 0 and (sees or dist < 45):
            self.chase_t = max(self.chase_t, 2.5)
            self.last_seen = (p.x, p.y)
        if self.stun <= 0 and self.on_ground:
            tvx = 0.0
            if self.chase_t > 0:
                self.chase_t -= dt
                if sees or self.last_seen is None:
                    self.last_seen = (p.x, p.y)
                tx, ty = self.last_seen
                self.wdir = 1 if tx > self.x else -1
                tvx = self.chase_move(g, tx, ty, GHOUL_CHASE * A * self.spd_mult)
                self.lost_track(sees, tx, ty)
            else:
                self.last_seen = None
                self.wander_t -= dt
                if self.wander_t <= 0:
                    self.wander_t = self.rnd.uniform(1.0, 3.0)
                    self.wdir = self.rnd.choice((-1, 0, 1))
                if self.wdir:
                    if self.hit_wall or not self.ground_ahead(lv, self.wdir):
                        self.wdir = -self.wdir
                    tvx = self.wdir * GHOUL_WANDER
            self.vx = tvx
        elif self.stun > 0 and self.on_ground:
            self.vx *= 0.85 ** (dt * 60)
        self.vy = min(self.vy + g.gravity * dt, MAX_FALL)
        move_body(lv, self, dt)


class Bat:
    """Murcielago volador: ronda su guarida, rodea los muros para llegar a ti y se lanza en picado."""
    is_player = False
    kind = "bat"
    spd = 1.0                     # multiplicador de velocidad (jefes, elites)
    hw = 5.0
    h = 9.0

    def __init__(self, cx, cy, seed):
        self.x, self.y = cx, cy + self.h / 2          # y = "pies" (parte baja)
        self.home = (cx, cy)
        self.vx = self.vy = 0.0
        self.hp = 1
        self.rnd = random.Random(seed)
        self.phase = self.rnd.random() * 6.28
        self.t = self.rnd.random() * 6.28
        self.chase_t = 0.0
        self.retreat = 0.0
        self.stun = 0.0

    def update(self, dt, g):
        lv, p = g.level, g.player
        A = g.aggr
        self.t += dt
        cx, cy = self.x, self.y - self.h / 2
        pcx, pcy = p.x, p.y - 8
        dist = math.hypot(pcx - cx, pcy - cy)
        if dist < (30 if p.sneak else 78) and g.grace <= 0 and (dist < 40 or los(lv, cx, cy, pcx, pcy)):
            self.chase_t = max(self.chase_t, 3.5)
        if self.stun > 0:
            self.stun -= dt
            f = 0.88 ** (dt * 60)
            self.vx *= f
            self.vy *= f
        else:
            wob = 0.0
            if self.retreat > 0:
                self.retreat -= dt
                tx, ty = pcx + math.sin(self.t * 2) * 40, pcy - 48
                speed = BAT_CHASE * A * self.spd
            elif self.chase_t > 0:
                self.chase_t -= dt
                tx, ty = air_waypoint(lv, cx, cy, pcx, pcy)        # rodea los muros si no te ve
                speed = BAT_CHASE * A * self.spd
                if (tx, ty) == (pcx, pcy):
                    wob = math.sin(self.t * 7 + self.phase) * 20
            else:
                tx = self.home[0] + math.sin(self.t * 1.3 + self.phase) * 14
                ty = self.home[1] + math.sin(self.t * 2.1 + self.phase) * 8
                speed = BAT_IDLE
            vx, vy = tx - cx, ty - cy
            d = math.hypot(vx, vy) or 1.0
            ux, uy = vx / d, vy / d
            spd = speed if d > 3 else 0.0
            dvx = ux * spd + (-uy) * wob
            dvy = uy * spd + ux * wob
            k = min(1.0, dt * 6)
            self.vx += (dvx - self.vx) * k
            self.vy += (dvy - self.vy) * k
        move_fly(lv, self, dt)


class Skeleton(Ghoul):
    """Esqueleto arquero: te oye, mantiene la distancia y dispara flechas en linea recta (solo si te VE).
    Si estas en otro piso, sube o BAJA de plataforma hasta quedar a tu altura. Antes de disparar se
    queda quieto y emite un eco rojo de aviso."""
    kind = "skel"
    hw = 4.5

    def __init__(self, x, y, seed):
        Ghoul.__init__(self, x, y, seed)
        self.shoot_cd = self.rnd.uniform(2.5, 3.5)
        self.aim = 0.0
        self.face = -1
        self.strafe_dir = self.rnd.choice((-1, 1))
        self.strafe_t = self.rnd.uniform(0.5, 1.5)
        self.burst = 0.0              # elites: segunda flecha tras la primera

    def strafe(self, lv, dt):
        """Patrulla lateral: cambia de sentido cada cierto tiempo, ante un muro o un borde."""
        if not self.ground_ahead(lv, 1) and not self.ground_ahead(lv, -1):
            return 0
        self.strafe_t -= dt
        if self.strafe_t <= 0:
            self.strafe_dir = self.rnd.choice((-1, 1))
            self.strafe_t = self.rnd.uniform(0.9, 2.0)
        if self.hit_wall or not self.ground_ahead(lv, self.strafe_dir):
            self.strafe_dir = -self.strafe_dir
            self.strafe_t = self.rnd.uniform(0.9, 2.0)
        return self.strafe_dir

    def update(self, dt, g):
        lv, p = g.level, g.player
        self.stun -= dt
        self.jump_cd -= dt
        self.shoot_cd -= dt
        if self.on_ground:
            self.air_tx = None
        else:
            air_steer(self)
        if self.burst > 0:
            self.burst -= dt
            if self.burst <= 0 and self.stun <= 0:
                g.enemy_shoot(self)
        dx, dy = p.x - self.x, p.y - self.y
        dist = math.hypot(dx, dy)
        sees = self.sees(g)
        if dist < (40 if p.sneak else 130) and abs(dy) < 60 and g.grace <= 0 and (sees or dist < 45):
            self.chase_t = max(self.chase_t, 3.0)
            self.last_seen = (p.x, p.y)
        if self.stun <= 0 and self.on_ground:
            tvx = 0.0
            if self.chase_t > 0:
                self.chase_t -= dt
                if sees or self.last_seen is None:
                    self.last_seen = (p.x, p.y)
                d = 1 if dx > 0 else -1
                if self.aim > 0:
                    self.aim -= dt
                    self.face = d
                    tvx = self.strafe(lv, dt) * 9.0          # sigue desplazandose despacio al apuntar
                    if self.aim <= 0:
                        g.enemy_shoot(self)
                        if getattr(self, "elite", False):
                            self.burst = 0.22
                else:
                    adx = abs(dx)
                    if sees and abs(dy) < 26:                # a tiro: se mueve mientras combate
                        self.face = d
                        if adx > 95 and self.ground_ahead(lv, d):
                            tvx = d * 30.0                   # se acerca hasta tener distancia de tiro
                        elif adx < 45 and self.ground_ahead(lv, -d):
                            tvx = -d * 28.0                  # mantiene la distancia
                        else:
                            tvx = self.strafe(lv, dt) * 22.0     # patrulla / esquiva de lado
                        if self.shoot_cd <= 0 and adx < 170:
                            self.aim = 0.45
                            self.shoot_cd = 1.9
                            g.add_wave(self.x, self.y - 8, "aim")
                    else:                                    # otro piso o sin vision: navega hasta ti
                        tx, ty = self.last_seen
                        tvx = self.chase_move(g, tx, ty, 30.0)
                        if abs(tvx) > 1:
                            self.face = 1 if tvx > 0 else -1
                        self.lost_track(sees, tx, ty)
            else:
                self.aim = 0.0
                self.last_seen = None
                self.wander_t -= dt
                if self.wander_t <= 0:
                    self.wander_t = self.rnd.uniform(1.0, 3.0)
                    self.wdir = self.rnd.choice((-1, 0, 1))
                if self.wdir:
                    if self.hit_wall or not self.ground_ahead(lv, self.wdir):
                        self.wdir = -self.wdir
                    tvx = self.wdir * 20.0
                    self.face = self.wdir
            self.vx = tvx
        elif self.stun > 0 and self.on_ground:
            self.aim = 0.0
            self.vx *= 0.85 ** (dt * 60)
        self.vy = min(self.vy + g.gravity * dt, MAX_FALL)
        move_body(lv, self, dt)


class Arrow:
    """Flecha del jugador ("player") o del esqueleto (\"enemy\"). `style` = proyectil especial de jefe."""
    kind = "arrow"

    def __init__(self, x, y, vx, vy, owner, grav, power=False):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.owner, self.grav = owner, grav
        self.life = 2.5
        self.power = power               # super disparo: atraviesa y mata de un golpe
        self.force = False               # True = carga roja de la FUERZA (skin ANAKIN)
        self.hit = set()
        self.t = 0.0
        self.wt = 0.0                    # temporizador de las ondas de luz del super disparo
        self.orb = False                 # ronda 4: bola magica del mago
        self.air = False                 # skin luchador: onda de aire (atraviesa a los monstruos)
        self.bounces = 0                 # rebotes que le quedan en los muros
        self.dmg = None                  # luchador: dano propio de la onda (None = sword_dmg)
        self.push = None                 # luchador: empuje propio de la onda
        self.vr = 0.0                    # luchador: altura extra de golpe (onda alta)
        self.big = False                 # luchador: SUPER ONDA de choque (dibujo y luz propios)
        self.style = None                # ronda 6 (jefes): "shock", "spirit", "sonic", "bomb" o None


# ----------------------------------------------------------------------------
#  RONDA 3 + 6: jefes (con FASES y varios patrones de ataque) y enemigos nuevos.
#  Todos usan kind "ghoul" / "skel" / "bat" como base; `tag` los distingue; `special` = dibujo propio.
# ----------------------------------------------------------------------------
class BossAI:
    """Cerebro de los jefes: reposo -> elige ataque -> AVISO (parpadeo + onda) -> ejecucion -> pausa.
    Fases por vida: 1 (>66%), 2 (33-66%), 3 (<33%, furia). `power` = jefes ya derrotados (sube la dificultad).
    Los ataques programan eventos con at(t, "metodo_de_Game", args...) que se disparan t segundos despues."""
    boss = True
    special = True
    act = None
    act_t = 0.0
    act_len = 0.0
    think_t = 1.2
    last_act = None
    tele = 0.0                    # > 0: esta avisando de un ataque (el dibujo parpadea)
    power = 0
    hp_max = 1
    _ph = 1

    def bphase(self):
        f = self.hp / float(max(1, self.hp_max))
        return 1 if f > 0.66 else (2 if f > 0.33 else 3)

    def think_delay(self):
        k = max(0.5, 1.0 - BOSS_THINK_POWER * self.power)
        return BOSS_THINK[self.bphase() - 1] * k * self.rnd.uniform(0.85, 1.15)

    def pick(self, weights):
        names = [n for n in weights if n != self.last_act] or list(weights)
        r = self.rnd.uniform(0, sum(weights[n] for n in names))
        for n in names:
            r -= weights[n]
            if r <= 0:
                return n
        return names[-1]

    def start(self, name, length):
        self.act, self.act_t, self.act_len, self.last_act = name, 0.0, length, name
        self.pend = []

    def at(self, t, fn, *args):
        self.pend.append([t, fn, args])

    def end_act(self):
        self.act = None
        self.pend = []
        self.think_t = self.think_delay()

    def act_done(self):
        return self.act_t >= self.act_len and not self.pend

    def tick(self, dt, g):
        if self.tele > 0:
            self.tele -= dt
        ph = self.bphase()
        if ph != self._ph:
            self._ph = ph
            g.boss_phase_up(self)
        if self.act is not None:
            self.act_t += dt
            for ev in self.pend[:]:
                ev[0] -= dt
                if ev[0] <= 0:
                    self.pend.remove(ev)
                    getattr(g, ev[1])(self, *ev[2])

    def minions(self, g):
        return sum(1 for m in g.monsters if getattr(m, "minion", False))

    def physics(self, dt, g):
        self.vy = min(self.vy + g.gravity * dt, MAX_FALL)
        move_body(g.level, self, dt)


class GiantSkeleton(BossAI, Skeleton):
    """JEFE 1. Esqueleto gigante (sprite 2x). Ataques: ABANICO de flechas (3-9), SALTO con ondas rasantes,
    LLUVIA de flechas marcadas en el suelo, EMBESTIDA (si choca con un muro queda aturdido) e INVOCAR esqueletos."""
    tag = "giant"
    scale = 2.0
    hw = 8.0
    h = 28.0
    kb = 0.2                    # retroceso al ser golpeado (fraccion del normal)
    stun_mult = 0.25

    def __init__(self, x, y, seed, hp, power=0):
        Skeleton.__init__(self, x, y, seed)
        self.hp = self.hp_max = hp
        self.power = power
        self.think_t = 1.6
        self.pend = []
        self.stagger = 0.0
        self.leaping = False
        self.leap_air = 0.0
        self.charge_dir = 0

    def boss_value(self):
        return self.hp

    def weights(self, g, adx):
        ph = self.bphase()
        w = {"fan": 4.0, "rain": 2.5 + 0.5 * ph}
        if adx < 220:
            w["leap"] = 3.0
        if ph >= 2:
            w["charge"] = 2.0 + ph
            if self.minions(g) < BOSS_MINIONS_MAX - 1:
                w["summon"] = 1.3 + 0.4 * (ph - 2)
        return w

    def rain_targets(self, g, n):
        px = g.player.x
        xs = [px + self.rnd.uniform(-6, 6)]
        for _ in range(n - 1):
            xs.append(px + self.rnd.choice((-1, 1)) * self.rnd.uniform(18, 85))
        return [max(20.0, min(MAP_W - 20.0, x)) for x in xs]

    def begin(self, name, g):
        ph = self.bphase()
        if name == "fan":
            n = min(9, 3 + 2 * (ph - 1) + (2 if self.power >= 2 else 0))
            self.start("fan", 0.95 if ph < 3 else 1.5)
            self.tele = 0.65
            g.boss_tele(self, "aim", 1.5)
            self.at(0.65, "boss_fan_shoot", n)
            if ph >= 3:
                self.at(1.05, "boss_fan_shoot", n)
        elif name == "rain":
            n = 3 + ph + min(self.power, 3)
            self.start("rain", 0.85 + 0.2 * n + 0.55)
            self.tele = 0.85
            for i, x in enumerate(self.rain_targets(g, n)):
                self.at(0.0, "boss_rain_mark", x)
                self.at(0.85 + 0.2 * i, "boss_rain_drop", x)
        elif name == "leap":
            self.start("leap", 3.2)
            self.leaping = False
            self.tele = 0.45
        elif name == "charge":
            self.start("charge", 3.4)
            self.charge_dir = 0
            self.tele = 0.75
            g.boss_tele(self, "roar", 0.6)
        elif name == "summon":
            self.start("summon", 1.5)
            self.tele = 0.8
            g.boss_tele(self, "roar", 0.7)
            self.at(0.8, "boss_summon", "skel", 2 if ph == 2 else 3)

    def run_act(self, dt, g, d, adx):
        a, t, lv = self.act, self.act_t, g.level
        if a in ("fan", "rain", "summon"):
            self.face = d
            if self.act_done():
                self.end_act()
            return 0.0
        if a == "leap":
            if not self.leaping:
                self.face = d
                if t < 0.45:
                    return 0.0
                if self.on_ground:
                    self.vy = -BOSS_GIANT_JUMP
                    self.vx = d * min(115.0, adx * 1.1 + 20.0)
                    self.leaping, self.leap_air = True, 0.12
                    g.add_wave(self.x, self.y - 4, "roar", 0.5)
                return None
            self.leap_air -= dt
            if self.on_ground and self.leap_air <= 0:
                self.leaping = False
                g.boss_slam(self)
                if self.bphase() >= 2:
                    g.boss_shock(self)
                self.end_act()
            elif t > 3.2:
                self.leaping = False
                self.end_act()
            return None
        # embestida
        if t < 0.75:
            self.face = d
            return 0.0
        if self.charge_dir == 0:
            self.charge_dir = d
            g.add_wave(self.x, self.y - 6, "roar", 0.6)
        cd = self.charge_dir
        self.face = cd
        if self.hit_wall:                                  # choca con el muro: aturdido y vulnerable
            self.stagger = 1.25
            g.add_shake(5.0)
            g.add_wave(self.x + cd * 8, self.y - 12, "attack", 1.5)
            self.end_act()
            return 0.0
        if self.on_ground and not self.ground_ahead(lv, cd):
            self.stagger = 0.35
            self.end_act()
            return 0.0
        if t > 3.4:
            self.end_act()
            return 0.0
        return cd * (BOSS_GIANT_CHARGE + 10 * self.power)

    def update(self, dt, g):
        lv, p = g.level, g.player
        A = g.aggr
        self.stun -= dt
        self.jump_cd -= dt
        self.tick(dt, g)
        if self.stagger > 0:
            self.stagger -= dt
            self.vx *= 0.85 ** (dt * 60)
            self.physics(dt, g)
            return
        dx, dy = p.x - self.x, p.y - self.y
        d = 1 if dx > 0 else -1
        adx = abs(dx)
        tvx = None
        if self.act is None:
            self.face = d
            self.think_t -= dt
            if self.on_ground:
                tvx = 0.0
                speed = BOSS_GIANT_WALK * A * (1.0 + 0.12 * (self.bphase() - 1))
                if adx > 46 and self.ground_ahead(lv, d):
                    tvx = d * speed
                elif adx < 24 and self.ground_ahead(lv, -d):
                    tvx = -d * 20.0
                if self.jump_cd <= 0 and self.y - p.y > 20 and adx < 60:
                    self.vy, self.jump_cd = -GHOUL_JUMP * 1.05, 1.2
                elif self.jump_cd <= 0 and self.hit_wall:
                    self.vy, self.jump_cd = -GHOUL_JUMP, 1.2
                if self.think_t <= 0 and g.grace <= 0:
                    self.begin(self.pick(self.weights(g, adx)), g)
        else:
            tvx = self.run_act(dt, g, d, adx)
        if tvx is not None and self.on_ground:
            self.vx = tvx
        self.physics(dt, g)


class SwarmBat(Bat):
    """JEFE 2 (fase 1). Uno de los 8 murcielagos del enjambre: al dañar a cualquiera se funden en uno grande."""
    tag = "swarm"
    boss = True
    special = True
    spd = 1.12

    def __init__(self, cx, cy, seed, idx, value):
        Bat.__init__(self, cx, cy, seed)
        self.hp = 1
        self.delay = idx * 0.3
        self.value = value

    def boss_value(self):
        return self.value

    def on_hit(self, g):
        g.swarm_fuse(self)

    def update(self, dt, g):
        if g.grace <= 0 and g.t_level - GRACE_T > self.delay:
            self.chase_t = max(self.chase_t, 1.6)               # se lanzan escalonados, no todos a la vez
        Bat.update(self, dt, g)


class BigBat(BossAI, Bat):
    """JEFE 2 (fase 2). Murcielago grande nacido de la fusion. Ataques: PICADOS (1-4 seguidos), CHILLIDO
    (anillo de bolas sonicas), BARRIDO horizontal avisado, BOMBARDEO desde el techo e INVOCAR murcielagos."""
    tag = "bigbat"
    scale = 2.0
    hw = 9.0
    h = 16.0
    kb = 0.3
    stun_mult = 0.3

    def __init__(self, cx, cy, seed, hp, power=0):
        Bat.__init__(self, cx, cy, seed)
        self.hp = self.hp_max = hp
        self.power = power
        self.think_t = 1.3
        self.pend = []
        self.sub = 0
        self.sub_t = 0.0
        self.n_left = 0
        self.side = 1
        self.ty = 0.0

    def boss_value(self):
        return self.hp

    def weights(self, g):
        ph = self.bphase()
        w = {"dive": 4.0 if ph == 1 else 3.0, "screech": 3.0, "sweep": 2.0 if ph == 1 else 3.0}
        if ph >= 2:
            w["drop"] = 2.0 + (ph - 2)
            if self.minions(g) < BOSS_MINIONS_MAX - 1:
                w["summon"] = 1.4 + 0.6 * (ph - 2)
        return w

    def goto(self, g, tx, ty, speed, dt, k=6.0):
        cx, cy = self.x, self.y - self.h / 2
        vx, vy = tx - cx, ty - cy
        d = math.hypot(vx, vy) or 1.0
        s = speed if d > 3 else 0.0
        kk = min(1.0, dt * k)
        self.vx += (vx / d * s - self.vx) * kk
        self.vy += (vy / d * s - self.vy) * kk
        move_fly(g.level, self, dt)
        return d

    def begin(self, name, g):
        ph = self.bphase()
        self.sub, self.sub_t = 0, 0.0
        if name == "dive":
            self.n_left = min(4, ph + (1 if self.power >= 3 else 0))
            self.start("dive", 99.0)
        elif name == "screech":
            n = 8 + 2 * (ph - 1) + min(self.power, 2)
            self.start("screech", 1.3 if ph < 3 else 1.95)
            self.tele = 0.75
            g.boss_tele(self, "screech", 1.4)
            self.at(0.75, "boss_radial", n, BOSS_BAT_SCREECH_SPEED, "sonic", 0.0, 0.0, 3.2, 0)
            if ph >= 3:
                self.at(1.3, "boss_radial", n, BOSS_BAT_SCREECH_SPEED, "sonic", math.pi / n, 0.0, 3.2, 0)
        elif name == "sweep":
            self.n_left = 1 if ph < 3 else 2
            self.start("sweep", 99.0)
            self.side = -1 if g.player.x > MAP_W / 2 else 1
        elif name == "drop":
            self.start("drop", 99.0)
            self.side = -1 if g.player.x > MAP_W / 2 else 1
        elif name == "summon":
            self.start("summon", 1.4)
            self.tele = 0.7
            g.boss_tele(self, "roar", 0.8)
            self.at(0.7, "boss_summon", "bat", 3)

    def run_act(self, dt, g):
        a, p = self.act, g.player
        self.sub_t += dt
        if a == "dive":
            if self.sub == 0:                              # se eleva sobre ti
                self.retreat = max(self.retreat, 0.1)
                self.spd = 1.3
                self.tele = 0.15
                if self.sub_t >= 0.45:
                    self.sub, self.sub_t, self.retreat = 1, 0.0, 0.0
                    g.add_wave(self.x, self.y - 8, "roar", 0.5)
            else:                                          # picado
                self.retreat = 0.0
                self.spd = BOSS_BAT_DIVE_SPEED
                if self.sub_t >= 0.8:
                    self.n_left -= 1
                    if self.n_left <= 0:
                        self.spd = 0.8
                        self.end_act()
                        return
                    self.sub, self.sub_t = 0, 0.0
            Bat.update(self, dt, g)
        elif a in ("screech", "summon"):
            self.vx *= 0.9
            self.vy *= 0.9
            move_fly(g.level, self, dt)
            if self.act_done():
                self.end_act()
        elif a == "sweep":
            ex = 22.0 if self.side > 0 else MAP_W - 22.0       # lado de salida; cruza hacia el contrario
            if self.sub == 0:                                  # coloca en el borde, a tu altura
                self.ty = max(28.0, min(MAP_H - 30.0, p.y - 10))
                d = self.goto(g, ex, self.ty, 175.0, dt)
                if d < 9 or self.sub_t > 1.8:
                    self.sub, self.sub_t, self.tele = 1, 0.0, 0.55
                    g.boss_tele(self, "tele", 1.6)
            elif self.sub == 1:                                # aviso: queda quieto
                self.goto(g, self.x, self.ty - self.h / 2 + self.h / 2, 0.0, dt)
                self.vx *= 0.8
                if self.sub_t >= 0.55:
                    self.sub, self.sub_t = 2, 0.0
                    g.add_wave(self.x, self.y - 8, "roar", 0.6)
            else:                                              # barrido
                self.vx = -self.side * BOSS_BAT_SWEEP_SPEED
                self.vy = (self.ty - (self.y - self.h / 2)) * 6.0
                move_fly(g.level, self, dt)
                far = (self.x > MAP_W - 26) if self.vx > 0 else (self.x < 26)
                if far or abs(self.vx) < 40 or self.sub_t > 2.4:
                    self.n_left -= 1
                    if self.n_left <= 0:
                        self.end_act()
                        return
                    self.side = -self.side
                    self.sub, self.sub_t = 0, 0.0
        elif a == "drop":
            sx = 24.0 if self.side < 0 else MAP_W - 24.0
            if self.sub == 0:
                d = self.goto(g, sx, 2.6 * TILE, 170.0, dt)
                if d < 10 or self.sub_t > 2.0:
                    self.sub, self.sub_t, self.tele = 1, 0.0, 0.4
                    self.bomb_t = 0.0
            else:
                self.vx = -self.side * 135.0
                self.vy = (2.6 * TILE - (self.y - self.h / 2)) * 6.0
                move_fly(g.level, self, dt)
                self.bomb_t -= dt
                if self.bomb_t <= 0:
                    self.bomb_t = 0.27
                    g.boss_bomb(self)
                if self.sub_t > 3.3 or abs(self.vx) < 30 or self.x < 22 or self.x > MAP_W - 22:
                    self.end_act()

    def update(self, dt, g):
        if g.grace <= 0:
            self.chase_t = max(self.chase_t, 2.0)
        self.tick(dt, g)
        if self.act is None:
            self.spd = 0.8 + 0.1 * (self.bphase() - 1)
            self.think_t -= dt
            Bat.update(self, dt, g)
            if self.think_t <= 0 and g.grace <= 0:
                self.begin(self.pick(self.weights(g)), g)
        else:
            self.run_act(dt, g)


class BossGhost(BossAI, Ghoul):
    """JEFE 3. Fantasma que al morir se divide en 2 mas pequenos. El grande ataca con EMBESTIDA, LAMENTO
    (bolas espectrales apuntadas), ANILLO espectral rebotante y TELETRANSPORTE tras de ti (con embestida
    inmediata). Los pequeños (nivel 1) embisten sin parar. Mientras se teletransporta no se le puede dañar."""
    tag = "bghost"

    def __init__(self, x, y, seed, level, hp, power=0):
        Ghoul.__init__(self, x, y, seed)
        self.level = level
        self.hp = self.hp_max = hp
        self.power = power
        self.pend = []
        self.phased = False
        self.ghost_a = 1.0
        self.dash_dir = 0
        self.blink_to = None
        self.hopped = False
        if level >= 2:
            self.scale, self.hw, self.h = 1.8, 8.0, 24.0
            self.kb, self.stun_mult = 0.35, 0.4
            self.think_t = 1.6
        else:
            self.scale, self.hw, self.h = 1.2, 6.0, 17.0
            self.think_t = 1.0 + self.rnd.uniform(0.0, 0.8)

    def bphase(self):
        return BossAI.bphase(self) if self.level >= 2 else 1

    def boss_value(self):
        return self.hp + (2 * BOSS_GHOST_CHILD_HP if self.level >= 2 else 0)

    def on_death(self, g):
        if self.level >= 2:
            g.boss_split_ghost(self)

    def weights(self):
        ph = self.bphase()
        w = {"lunge": 4.0, "wail": 3.0, "blink": 2.0 + (ph - 1)}
        if ph >= 2:
            w["ring"] = 2.0 + (ph - 2)
        return w

    def begin(self, name, g, tele=0.55):
        ph = self.bphase()
        self.hopped = False
        if name == "lunge":
            self.start("lunge", tele + 0.6 + 0.4)
            self.lunge_tele = tele
            self.tele = tele
            g.boss_tele(self, "tele", 1.2)
        elif name == "wail":
            n = min(7, 3 + 2 * (ph - 1))
            self.start("wail", 1.5)
            self.tele = 0.8
            g.boss_tele(self, "wail", 1.4)
            self.at(0.8, "boss_aimed", n, 0.3, BOSS_GHOST_ORB_SPEED, "spirit", 1 if ph >= 2 else 0, 3.4)
            if ph >= 3:
                self.at(1.2, "boss_aimed", n, 0.3, BOSS_GHOST_ORB_SPEED, "spirit", 1, 3.4)
        elif name == "ring":
            n = 8 + 2 * (ph - 2) + min(self.power, 2)
            self.start("ring", 1.6)
            self.tele = 0.9
            g.boss_tele(self, "wail", 1.6)
            self.at(0.9, "boss_radial", n, BOSS_GHOST_ORB_SPEED * 0.8, "spirit", 0.0, 0.0, 3.6, 1)
        elif name == "blink":
            self.start("blink", 2.5)
            self.blink_to = None

    def run_act(self, dt, g):
        a, t, p = self.act, self.act_t, g.player
        d = 1 if p.x > self.x else -1
        if a == "lunge":
            lt = self.lunge_tele
            if t < lt:
                self.face = d
                self.dash_dir = d
                self.vx = 0.0 if self.on_ground else self.vx
            elif t < lt + 0.6:
                if not self.hopped:
                    self.hopped = True
                    self.vy = -110.0
                    g.add_wave(self.x, self.y - 8, "roar", 0.5)
                self.vx = self.dash_dir * (BOSS_GHOST_LUNGE + 10 * self.power) * (1.0 + 0.1 * (self.bphase() - 1))
            elif self.on_ground:
                self.vx *= 0.8
            if t >= lt + 1.0:
                self.end_act()
        elif a in ("wail", "ring"):
            self.face = d
            if self.on_ground:
                self.vx = 0.0
            if self.act_done():
                self.end_act()
        elif a == "blink":
            if self.on_ground:
                self.vx = 0.0
            if t >= 0.12:
                self.phased = True
            if t >= 0.3 and self.blink_to is None:
                dest = g.boss_blink_dest(self)
                self.blink_to = dest or False
                if dest:
                    g.add_wave(dest[0], dest[1] - 10, "tele", 1.6)
                else:
                    self.phased = False
                    self.end_act()
                    return
            if self.blink_to and t >= 0.95:
                self.x, self.y = self.blink_to
                self.vx = self.vy = 0.0
                self.phased = False
                g.boss_appear(self)
                self.begin("lunge", g, 0.3)                # reaparece detras de ti y embiste enseguida
        self.physics(dt, g)

    def update(self, dt, g):
        self.tick(dt, g)
        self.ghost_a += ((0.0 if self.phased else 1.0) - self.ghost_a) * min(1.0, dt * 9.0)
        if g.grace <= 0:
            self.chase_t = max(self.chase_t, 2.0)
            self.last_seen = (g.player.x, g.player.y)          # un jefe siempre sabe donde estas
        self.spd_mult = (1.0, 1.2, 1.4)[self.bphase() - 1] if self.level >= 2 else 1.4
        if self.act is None:
            self.think_t -= dt
            Ghoul.update(self, dt, g)
            if self.think_t <= 0 and g.grace <= 0 and self.on_ground:
                self.begin("lunge" if self.level < 2 else self.pick(self.weights()), g, 0.55 if self.level >= 2 else 0.4)
        else:
            self.stun -= dt
            self.run_act(dt, g)


class Phantom(Ghoul):
    """Fantasma invisible: solo se ve un instante cuando una onda de eco lo toca."""
    tag = "phantom"
    special = True
    invisible = True

    def __init__(self, x, y, seed):
        Ghoul.__init__(self, x, y, seed)
        self.reveal = 0.0

    def update(self, dt, g):
        self.reveal = max(0.0, self.reveal - dt)
        g.phantom_scan(self)
        Ghoul.update(self, dt, g)


class Silencer(Bat):
    """Murcielago silenciador: si te toca, tus ecos se apagan MUTE_T segundos."""
    tag = "silencer"
    special = True


class Thief(Ghoul):
    """Ladron: corre a por los corazones del suelo (por cualquier plataforma) y huye con ellos.
    Si lo matas, los suelta."""
    tag = "thief"
    special = True

    def __init__(self, x, y, seed):
        Ghoul.__init__(self, x, y, seed)
        self.loot = False
        self.flee_t = 0.0

    def on_death(self, g):
        if self.loot:
            g.thief_drop(self)                 # si lo matas, suelta el corazon

    def run(self, g, d, speed, target_y):
        """Metodo antiguo (sin grafo): correr en el sentido d saltando huecos, muros y plataformas."""
        lv = g.level
        tvx = d * speed
        if self.on_ground and self.jump_cd <= 0:
            if self.hit_wall:
                self.vy, self.jump_cd = -215.0, 0.8
            elif not self.ground_ahead(lv, d):
                self.vy, self.jump_cd = -215.0, 0.8
                tvx = d * speed * 1.4
            elif self.y - target_y > 14:
                self.vy, self.jump_cd = -GHOUL_JUMP, 0.8
        return tvx

    def update(self, dt, g):
        p, lv = g.player, g.level
        heart = None if self.loot else g.nearest_heart(self.x, self.y)
        if not self.loot and heart is None:
            Ghoul.update(self, dt, g)                      # sin corazones que robar: se comporta como un fantasma
            return
        self.stun -= dt
        self.jump_cd -= dt
        if self.on_ground:
            self.air_tx = None
        else:
            air_steer(self)
        if self.loot:
            self.flee_t -= dt
            if self.flee_t <= 0:
                g.thief_escape(self)
                return
        elif abs(self.x - heart.x) < 9 and abs(self.y - heart.y) < 12:
            g.thief_steal(self, heart)
        if self.stun <= 0 and self.on_ground:
            if self.loot:
                v = flee_from(self, g, p.x, p.y, THIEF_SPEED * 1.1)      # huye alejandose de ti por las plataformas
                if v is None:
                    v = self.run(g, 1 if self.x >= p.x else -1, THIEF_SPEED * 1.1, self.y)
                self.vx = v
            else:
                dx = heart.x - self.x
                v = walk_toward(self, g, heart.x, heart.y, THIEF_SPEED)
                if v is None:
                    v = self.run(g, 1 if dx > 0 else -1, THIEF_SPEED, heart.y) if abs(dx) > 3 else 0.0
                self.vx = v
            if self.vx:
                self.wdir = 1 if self.vx > 0 else -1
        elif self.stun > 0 and self.on_ground:
            self.vx *= 0.85 ** (dt * 60)
        self.vy = min(self.vy + g.gravity * dt, MAX_FALL)
        move_body(lv, self, dt)
