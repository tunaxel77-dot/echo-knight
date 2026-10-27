# -*- coding: utf-8 -*-
"""Combate: ataque, super eco, arco, flechas, cofres, dano al jugador."""
import array
import math
import random
import sys

import pygame
from .config import *
from .achievements import ach_notify
from .texts import *
from .sprites_data import *
from .sprites import *
from .lighting import *
from .physics import *
from .levels_data import *
from .level import *
from .entities import *
from .polish import HIT_SPARKS
from .characters import char_of


class CombatMixin:
    """Combate: ataque, super eco, arco, flechas, cofres, dano al jugador."""
    fighter_mode = False                # skin LUCHADOR (valor por defecto; lo fija SkinsMixin)
    slam = None                         # luchador: efecto del impacto en curso (ver fighter_slam)

    def charge_t(self):
        """Carga necesaria para el disparo cargado (la super onda del luchador carga mas rapido)."""
        return FT_SUPER_CHARGE_T if self.fighter_mode else SUPER_CHARGE_T

    # ------------------------------------------------------------ acciones
    def check_cleared(self):
        """La llave solo aparece cuando no queda ningun monstruo."""
        lv = self.level
        if self.mode == "endless":
            return                       # en el modo infinito no hay llave: manda la cuota de bajas
        if self.monsters or self.key_visible or not lv.key:
            return
        if self.tutorial and not self.tut_spawned:
            return
        self.key_visible = True
        self.add_wave(lv.key[0], lv.key[1], "key", 1.2)
        self.sfx("key")
        self.toast("¡Todos los monstruos han caído! Ha aparecido la llave dorada.", 3.5)

    def do_attack(self):
        """Inicia el ataque: primero la espada retrocede (anticipacion) y el tajo
        se ejecuta en perform_attack cuando termina WINDUP_T."""
        p = self.player
        if (p.attack_cd > 0 or p.shield or p.stun > 0 or p.dash_t > 0 or p.windup > 0
                or self.state != "play"):
            return
        p.attack_cd = ATTACK_COOLDOWN * char_of(self)["atk_cd"] * (FT_PUNCH_CD if self.fighter_mode else 1.0)   # daga rapida / maza lenta
        p.windup = WINDUP_T
        p.air_atk = not p.on_ground

    def perform_attack(self):
        p = self.player
        p.attack_t = 0.16
        self.attacks += 1
        air = not p.on_ground
        p.air_atk = air                          # tajo aereo: diagonal hacia abajo
        self.add_wave(p.x, p.y - 8, "attack_air" if self.fighter_mode else "attack")      # luchador: eco blanco
        self.sfx("slash")
        self.make_noise(p.x, p.y, 100)
        C = char_of(self)
        reach = ATTACK_RANGE * C["reach"] * (FT_PUNCH_REACH if self.fighter_mode else 1.0)
        dmg = self.sword_dmg + (FT_PUNCH_DMG if self.fighter_mode else 0)
        push = C["push"] * (FT_PUNCH_PUSH if self.fighter_mode else 1.0)
        if p.face > 0:
            x0, x1 = p.x - 4, p.x + reach
        else:
            x0, x1 = p.x - reach, p.x + 4
        y0, y1 = (p.y - 14, p.y + 14) if air else (p.y - 22, p.y + 2)
        hits = 0
        for m in self.monsters[:]:
            if m.x + m.hw < x0 or m.x - m.hw > x1 or m.y < y0 or m.y - m.h > y1:
                continue
            self.damage_monster(m, p.face, dmg=dmg, push=push)
            hits += 1
        if air and hits:                         # rebote al golpear desde el aire
            p.vy = -190.0
            p.pogo = 0.2
            p.on_ground = False
        self.check_cleared()

    def do_pulse(self):
        p = self.player
        if p.pulse_cd > 0 or self.state != "play":
            return
        p.pulse_cd = PULSE_COOLDOWN
        self.pulses += 1
        ach_notify(self, "pulse")
        self.add_wave(p.x, p.y - 8, "pulse")
        self.add_shake(SHAKE_PULSE)
        self.sfx(getattr(self, "pulse_sfx_name", lambda: "pulse")())     # mas grave en salas grandes (music.py)
        self.make_noise(p.x, p.y, 260)
        woke = False                             # el super eco solidifica los puentes fantasma
        for cell in self.level.ghost_cells:
            cx, cy = cell[0] * TILE + 8, cell[1] * TILE + 3
            if math.hypot(p.x - cx, (p.y - 8) - cy) < 300:
                self.level.ghost_t[cell] = 7.0
                woke = True
        if woke and not self.ghost_hint:
            self.ghost_hint = True
            self.toast("¡Los puentes fantasma se solidifican unos segundos!", 3.0)

    def damage_monster(self, m, dirn, kill=False, dmg=1, push=1.0):
        if getattr(m, "phased", False):
            return                                       # el fantasma jefe es intangible mientras se teletransporta
        if kill and getattr(m, "boss", False):          # el super disparo no mata de un golpe a un jefe
            kill, dmg = False, BOSS_SUPER_DMG
        m.hp = 0 if kill else m.hp - dmg
        kb = getattr(m, "kb", 1.0)                      # los jefes casi no retroceden
        m.vx = dirn * 130 * kb * push                   # el tanque empuja mucho mas
        m.vy = (-30 if m.kind == "bat" else -80) * kb
        m.stun = 0.35 * getattr(m, "stun_mult", 1.0) * (1.0 if push <= 1.0 else 1.4)
        m.chase_t = 4.0
        if hasattr(m, "last_seen"):
            m.last_seen = (self.player.x, self.player.y)     # si le pegas, sabe donde estas
        self.sfx("hit")
        self.add_wave(m.x, m.y - m.h / 2, "hurt")
        self.hit_fx(m)
        if hasattr(m, "on_hit"):
            m.on_hit(self)                              # p. ej. el enjambre se funde
        if m.hp <= 0:
            if m in self.monsters:
                self.monsters.remove(m)
            if hasattr(m, "on_death"):
                m.on_death(self)                        # p. ej. el fantasma se divide, el ladron suelta el corazon
            if not self.tutorial:
                self.kills += 1
                ach_notify(self, "kill", m)
            self.add_wave(m.x, m.y - m.h / 2, "death")
            self.burst(m.x, m.y - m.h / 2, HIT_SPARKS.get(m.kind, ((255, 255, 255),)), 16, 140, up=30, life=(0.3, 0.7))
            if not self.monsters and self.mode == "levels" and not self.tutorial:
                self.slowmo = SLOWMO_LAST_KILL          # camara lenta al matar al ultimo
            if self.mode == "endless":
                self.endless_on_kill(m)
            self.check_cleared()

    def start_charge(self):
        """Pulsar el disparo empieza a cargar el arco; al soltar se dispara (ver release_fire)."""
        p = self.player
        if char_of(self)["shot"] == "orb" and not self.anakin_mode:      # mago: sin carga, dispara al pulsar
            if self.state == "play" and not self.help:
                self.do_shoot(0.0)
            return
        if (self.has_bow or self.anakin_mode or self.fighter_mode) and self.state == "play" and not p.charging:
            p.charging = True
            p.charge = 0.0

    def release_fire(self):
        p = self.player
        was, c = p.charging, p.charge
        p.charging, p.charge = False, 0.0
        if was and self.state == "play" and not self.help:
            self.do_shoot(c)

    def do_shoot(self, charge=0.0):
        p = self.player
        if (self.fighter_mode and charge >= self.charge_t() and self.state == "play" and p.clap_cd <= 0
                and p.stun <= 0):
            self.shoot_super_wave()                       # carga llena: SUPER ONDA (no depende del enfriamiento del puño ni de la guardia)
            return
        if (not (self.has_bow or self.anakin_mode or self.fighter_mode) or self.state != "play" or p.shoot_cd > 0
                or p.shield or p.stun > 0):
            return
        if self.fighter_mode:
            self.shoot_air()                              # carga a medias: puñetazo de aire normal
            return
        if char_of(self)["shot"] == "orb" and not self.anakin_mode:
            self.shoot_orb()
            return
        force = self.anakin_mode                          # skin ANAKIN: la FUERZA reemplaza al arco
        if force:
            bx, by = self.hand_pos(p)                     # mano extendida
        else:
            bx, by = p.x + p.face * 6, p.y - 9
        if charge >= SUPER_CHARGE_T:                      # SUPER DISPARO cargado
            p.shoot_cd, p.shoot_t = BOW_COOLDOWN * 1.8, 0.3
            a = Arrow(bx, by, p.face * SUPER_SPEED, 0.0, "player", 0.0, power=True)
            a.life = 1.6
            a.force = force
            self.arrows.append(a)
            self.add_wave(bx, by, self.fxk("fsuperhit") if force else "superhit", 0.8)
            self.sfx("super")
            self.make_noise(p.x, p.y, 140)
            for _ in range(20):
                ang = random.uniform(-0.7, 0.7)
                sp = random.uniform(60.0, 190.0)
                life = random.uniform(0.2, 0.45)
                self.sparks.append([bx, by + random.uniform(-3, 3), p.face * sp * math.cos(ang),
                                    sp * math.sin(ang), life, life,
                                    self.tc(random.choice(((255, 90, 60), (255, 40, 30), (255, 210, 190))))
                                    if force else (255, 236, 170)])
            return
        p.shoot_cd, p.shoot_t = BOW_COOLDOWN, 0.18
        a = Arrow(bx, by, p.face * ARROW_SPEED, -14.0, "player", ARROW_GRAV)
        a.force = force
        self.arrows.append(a)
        if self.double_shot:                              # carta ARCO DOBLE: segunda flecha en otro angulo
            b = Arrow(bx, by + 2, p.face * ARROW_SPEED, -14.0 - DOUBLE_SHOT_DV, "player", ARROW_GRAV)
            b.force = force
            self.arrows.append(b)
        self.add_wave(bx, by, self.fxk("fshot") if force else "shot")
        self.sfx("bow")
        self.make_noise(p.x, p.y, 50)

    def shoot_air(self):
        """LUCHADOR: puñetazo recto de la mano adelantada que lanza una onda de aire blanca (atraviesa monstruos)."""
        p = self.player
        p.shoot_cd, p.shoot_t = FT_SHOT_CD, 0.22
        bx, by = p.x + p.face * 11, p.y - 8
        a = Arrow(bx, by, p.face * FT_AIR_SPEED, 0.0, "player", 0.0)
        a.air = True
        a.life = FT_AIR_LIFE
        self.arrows.append(a)
        self.add_wave(bx, by, "airpunch")
        self.add_shake(1.5)
        self.sfx("dash")
        self.make_noise(p.x, p.y, 80)
        for _ in range(10):                                  # rafaga de aire alrededor del puño
            ang = random.uniform(-0.8, 0.8)
            sp = random.uniform(50.0, 160.0)
            life = random.uniform(0.15, 0.35)
            self.sparks.append([bx, by + random.uniform(-3, 3), p.face * sp * math.cos(ang), sp * math.sin(ang),
                                life, life, random.choice(((255, 255, 255), (225, 235, 255)))])

    def shoot_super_wave(self):
        """LUCHADOR, super disparo (v2): al soltar con la carga llena lanza una ONDA DE CHOQUE gigante hacia delante.
        Viaja ~275 px, atraviesa a todos los monstruos (1 golpe a cada uno), los empuja lejos y borra las flechas enemigas
        que toque. Nace en el centro del cuerpo: lo que esta pegado al luchador tambien se lleva el golpe."""
        p = self.player
        d = p.face
        p.clap_cd, p.shoot_cd, p.shoot_t, p.clap_t = FT_SUPER_CD, 0.35, 0.4, 0.45
        bx, by = p.x + d * 4, p.y - 8
        a = Arrow(bx, by, d * FT_SUPER_SPEED, 0.0, "player", 0.0)
        a.air, a.big = True, True
        a.life, a.dmg, a.push, a.vr = FT_SUPER_LIFE, FT_SUPER_DMG, FT_SUPER_PUSH, FT_SUPER_VREACH
        self.arrows.append(a)
        self.add_wave(bx + d * 8, by, "clap")
        self.add_shake(SHAKE_PULSE * 2)
        self.sfx("super")
        self.make_noise(p.x, p.y, 220)
        for _ in range(34):
            ang = random.uniform(-0.9, 0.9)
            sp = random.uniform(90.0, 300.0)
            life = random.uniform(0.25, 0.55)
            self.sparks.append([bx, by + random.uniform(-4, 4), d * sp * math.cos(ang), sp * math.sin(ang),
                                life, life, random.choice(((255, 255, 255), (225, 235, 255), (180, 200, 245)))])

    def fighter_slam(self, fall=FT_SLAM_MIN_FALL):
        """LUCHADOR: aterrizaje en picada = IMPACTO. Cuanto mas rapido caes, mas grande: grietas en el suelo, anillos
        de choque, escombros y polvo, temblor y camara lenta; los monstruos cercanos salen volando."""
        p = self.player
        power = max(0.0, min(1.0, (fall - FT_SLAM_MIN_FALL) / max(1.0, FT_DIVE_SPEED - FT_SLAM_MIN_FALL)))
        radius = FT_SLAM_RADIUS * (1.0 + 0.9 * power)
        cracks = []
        for side in (-1, 1):                                # grietas dentadas que se abren por el suelo
            for _ in range(4):
                x, y = p.x, p.y + 1.0
                pts = [(x, y)]
                for _ in range(random.randint(3, 5)):
                    x += side * random.uniform(6.0, 14.0) * (1.0 + power)
                    y += random.choice((-1.0, 0.0, 1.0))
                    pts.append((x, y))
                cracks.append(pts)
        self.slam = dict(x=p.x, y=p.y, t=1.0, tm=1.0, r=radius, power=power, cracks=cracks)
        self.add_wave(p.x, p.y - 3, "slam", 1.0 + power)
        self.add_shake(SHAKE_DEATH * (0.6 + 0.6 * power))
        self.slowmo = max(self.slowmo, 0.12 + 0.14 * power)
        self.sfx("super")
        self.make_noise(p.x, p.y, 200)
        dmg = 2 + (1 if power > 0.6 else 0)
        for m in self.monsters[:]:
            if abs(m.x - p.x) < radius and abs(m.y - p.y) < 30:
                self.damage_monster(m, 1 if m.x >= p.x else -1, dmg=dmg, push=2.6 + power)
                m.vy = -170.0 - 90.0 * power               # sale volando
        for _ in range(int(26 + 26 * power)):               # escombros que saltan
            life = random.uniform(0.35, 0.8)
            self.sparks.append([p.x + random.uniform(-10, 10), p.y - 1, random.uniform(-150, 150) * (0.6 + power),
                                random.uniform(-230, -70) * (0.7 + 0.5 * power), life, life,
                                random.choice(((150, 138, 128), (104, 94, 90), (196, 184, 168), (70, 62, 66)))])
        for _ in range(18):                                 # destellos blancos del impacto
            life = random.uniform(0.2, 0.5)
            ang = random.uniform(-3.0, -0.14)
            sp = random.uniform(80.0, 260.0)
            self.sparks.append([p.x, p.y - 2, math.cos(ang) * sp, math.sin(ang) * sp, life, life, (245, 248, 255)])

    def fighter_dive_fx(self, p):
        """Estela de la PICADA: imagenes residuales blancas y rayas de aire hacia arriba."""
        spr, bx, by = self.player_sprite(p)
        t = spr.copy()
        t.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        t.fill((235, 242, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self.trail.append([t, bx, by, 0.28, 0.28])
        if len(self.trail) > 24:
            self.trail.pop(0)
        for _ in range(2):
            life = random.uniform(0.2, 0.4)
            self.sparks.append([p.x + random.uniform(-5, 5), p.y - random.uniform(2.0, 16.0), random.uniform(-12, 12),
                                -random.uniform(60, 140), life, life, (240, 246, 255)])

    def shoot_orb(self):
        """MAGO: bola magica lenta que rebota MAGE_ORB_BOUNCES veces en los muros."""
        p = self.player
        p.shoot_cd, p.shoot_t = MAGE_ORB_CD, 0.18
        bx, by = p.x + p.face * 7, p.y - 9
        vys = (-MAGE_ORB_DV / 2, MAGE_ORB_DV / 2) if self.double_shot else (0.0,)     # carta ARCO DOBLE: 2 bolas
        for vy in vys:
            a = Arrow(bx, by, p.face * MAGE_ORB_SPEED, vy, "player", 0.0)
            a.orb = True
            a.bounces = MAGE_ORB_BOUNCES
            a.life = MAGE_ORB_LIFE
            self.arrows.append(a)
        self.add_wave(bx, by, "orb")
        self.sfx("bow")
        self.make_noise(p.x, p.y, 50)

    def arrow_fx(self, a, px, py, dt):
        """Estela de viento de las flechas: cinta que se desvanece + remolinos de particulas."""
        if a.air:                                         # la onda de aire deja rayas blancas
            for _ in range(2):
                l2 = random.uniform(0.1, 0.25)
                self.sparks.append([a.x - (1 if a.vx > 0 else -1) * random.uniform(2, 8), a.y + random.uniform(-7, 7),
                                    -a.vx * 0.15, random.uniform(-8, 8), l2, l2, (240, 246, 255)])
            return
        if a.orb:                                         # la bola deja chispas azules
            if random.random() < 0.6:
                l2 = random.uniform(0.15, 0.35)
                self.sparks.append([a.x + random.uniform(-2, 2), a.y + random.uniform(-2, 2), random.uniform(-14, 14),
                                    random.uniform(-14, 14), l2, l2, random.choice(((120, 190, 255), (210, 240, 255)))])
            return
        sup = a.power
        life = 0.55 if sup else 0.24
        if a.force:
            col = self.tc((255, 60, 44) if sup else (255, 110, 80))
        elif sup:
            col = (255, 236, 170)
        else:
            col = (235, 245, 255) if a.owner == "player" else (255, 130, 100)
        self.winds.append([px, py, a.x, a.y, life, life, col, 3 if sup else 1, sup])
        if len(self.winds) > 160:
            del self.winds[:len(self.winds) - 160]
        ln = math.hypot(a.vx, a.vy) or 1.0
        nx, ny = -a.vy / ln, a.vx / ln
        for _ in range(3 if sup else 1):
            off = random.uniform(-3.0, 3.0) * (2.0 if sup else 1.0)
            l2 = random.uniform(0.18, 0.4)
            self.sparks.append([a.x + nx * off, a.y + ny * off,
                                -a.vx * 0.08 + nx * off * 4, -a.vy * 0.08 + ny * off * 4 - 6,
                                l2, l2, col])
        if sup:                                           # el super disparo ilumina todo su recorrido
            a.wt -= dt
            if a.wt <= 0:
                a.wt = 0.07
                self.add_wave(a.x, a.y, self.fxk("fsuperlight") if a.force else "superlight")

    def enemy_shoot(self, m):
        self.arrows.append(Arrow(m.x + m.face * 7, m.y - 9, m.face * 150.0, 0.0, "enemy", 0.0))
        self.sfx("bow")

    def update_arrows(self, dt):
        lv, p = self.level, self.player
        for a in self.arrows[:]:
            px, py = a.x, a.y
            a.life -= dt
            a.t += dt
            steps = max(1, int(math.ceil(math.hypot(a.vx, a.vy) * dt / 6.0)))   # subpasos: no atraviesa muros
            sdt = dt / steps
            wall = False
            for _ in range(steps):
                if a.bounces > 0:                         # bola del mago: rebota en vez de chocar
                    nx, ny = a.x + a.vx * sdt, a.y + a.vy * sdt
                    bounced = False
                    if lv.is_wall(int(nx // TILE), int(a.y // TILE)):
                        a.vx, nx, bounced = -a.vx, a.x, True
                    if lv.is_wall(int(nx // TILE), int(ny // TILE)):
                        a.vy, ny, bounced = -a.vy, a.y, True
                    a.x, a.y = nx, ny
                    if bounced:
                        a.bounces -= 1
                        self.add_wave(a.x, a.y, "bounce", 0.6)
                        self.sfx("step")
                    continue
                a.x += a.vx * sdt
                a.y += a.vy * sdt
                a.vy += a.grav * sdt
                if lv.is_wall(int(a.x // TILE), int(a.y // TILE)):
                    wall = True
                    break
            self.arrow_fx(a, px, py, dt)
            if a.life <= 0 or wall:
                self.arrows.remove(a)
                if a.power and wall:
                    self.add_wave(px, py, self.fxk("fsuperhit") if a.force else "superhit")
                elif a.life > 0:
                    self.add_wave(px, py, self.fxk("farrowhit") if a.force else "arrowhit")
                continue
            if a.owner == "player":
                lo, hi = min(px, a.x), max(px, a.x)
                for m in self.monsters[:]:
                    if lo - m.hw - 2 < m.x < hi + m.hw + 2 and m.y - m.h - 2 - a.vr < a.y < m.y + 2 + a.vr:
                        dirn = 1 if a.vx > 0 else -1
                        if a.air:                         # onda de aire: atraviesa y empuja fuerte (1 golpe por monstruo)
                            if id(m) in a.hit:
                                continue
                            a.hit.add(id(m))
                            self.add_wave(m.x, m.y - m.h / 2, "airpunch", 0.6)
                            self.damage_monster(m, dirn, dmg=a.dmg or self.sword_dmg, push=a.push or FT_AIR_PUSH)
                        elif a.power:                     # atraviesa y mata de un solo golpe
                            if id(m) in a.hit:
                                continue
                            a.hit.add(id(m))
                            self.add_wave(m.x, m.y - m.h / 2, self.fxk("fsuperhit") if a.force else "superhit", 0.6)
                            self.damage_monster(m, dirn, kill=True)
                        else:
                            self.arrows.remove(a)
                            self.damage_monster(m, dirn)
                            break
            elif p.inv <= 0 and p.dash_t <= 0 and abs(a.x - p.x) < p.hw + 2 and p.y - p.h - 1 < a.y < p.y + 1:
                self.arrows.remove(a)
                self.hurt_player(a)
                if self.state != "play":
                    return

    def tut_advance(self):
        self.tut += 1
        self.attacks = self.pulses = self.jumps = 0
        self.sneak_dist = 0.0
        if self.tut == 5 and not self.tut_spawned:       # aparece el fantasma de practica
            self.tut_spawned = True
            gx, gy = (14 + DX) * TILE + 8, (ROWS - 1) * TILE
            self.monsters.append(Ghoul(gx, gy, 999))
            self.add_wave(gx, gy - 8, "death")

    def near_chest(self):
        c = self.level.chest
        p = self.player
        return bool(c) and not self.chest_open and abs(p.x - c[0]) < 16 and abs(p.y - c[1]) < 20

    def try_open_chest(self):
        if self.state != "play" or not self.near_chest():
            return
        c = self.level.chest
        self.chest_open = True
        self.add_wave(c[0], c[1] - 8, "key", 1.1)
        self.sfx("key")
        if self.level.chest_item == "bow":
            self.has_bow = True
            self.toast("¡Cofre abierto! Obtienes el ARCO: toca F o C para disparar; mantén pulsado "
                       "y suelta para un SÚPER DISPARO que cruza el mapa y mata de un golpe.", 6.0)
        elif not self.shield_allowed():
            self.toast("¡Cofre abierto! Dentro hay un ESCUDO, pero el mago no puede usarlo.", 4.0)
        else:
            self.has_shield = True
            self.toast("¡Cofre abierto! Obtienes el ESCUDO: mantén S o FLECHA abajo para bloquear "
                       "(un bloqueo perfecto lanza un eco azul).", 5.0)

    def try_restart(self):
        """Reiniciar el nivel exige pulsar P dos veces (evita pulsaciones accidentales)."""
        if self.restart_arm > 0:
            self.restart_arm = 0.0
            self.restart_current()
        else:
            self.restart_arm = 2.0
            self.toast("¿Reiniciar el nivel? Pulsa P otra vez para confirmar.", 2.0)

    def hurt_player(self, m):
        p = self.player
        front = (m.x - p.x) * p.face >= -2
        if m.kind == "bat":
            m.retreat = 1.0
        d = 1 if m.x >= p.x else -1
        if p.shield and front:                                  # BLOQUEO
            p.inv = 0.4
            m.stun = char_of(self)["block_stun"]           # tanque: el bloqueo atonta 1 s
            m.vx = d * (140 if m.stun < 0.9 else 190)
            if self.fighter_mode and hasattr(m, "hp"):     # guardia de boxeador: contragolpe al que ataca (las flechas no tienen vida)
                self.damage_monster(m, d, dmg=1, push=2.0)
                m.stun = FT_BLOCK_STUN
            m.vy = -40 if m.kind == "bat" else -60
            p.vx -= d * 50
            self.block_flash = 0.15
            self.add_shake(SHAKE_BLOCK)
            self.add_wave(p.x, p.y - 8, "block")
            self.sfx("block")
            return
        if getattr(m, "tag", "") == "silencer":          # el silenciador apaga tus ecos
            p.mute_echo = MUTE_T
            self.add_wave(p.x, p.y - 8, "silence")
            self.toast("¡Silenciado! No puedes emitir ecos durante %d s." % MUTE_T, 2.5)
        p.hp -= 1
        ach_notify(self, "hurt")
        if self.fighter_mode:                              # SUPER ARMADURA: no te empujan ni te aturden, y contraatacas
            p.inv = 1.0
            if hasattr(m, "hp"):                           # contraataca a monstruos (una flecha no tiene vida)
                self.damage_monster(m, d, dmg=1, push=2.5)
        else:
            p.inv = 1.3
            p.stun = 0.25
            p.vx = -d * 120
            p.vy = -150
            p.on_ground = False
        self.hurt_flash = 0.5
        self.add_shake(SHAKE_HURT)
        self.add_wave(p.x, p.y - 8, "hurt")
        self.sfx("hurt")
        if p.hp <= 0:
            self.state = "dead"
            self.death_fx()
            if self.mode == "endless":
                self.endless_game_over()
