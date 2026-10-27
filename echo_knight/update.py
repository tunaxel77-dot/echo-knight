# -*- coding: utf-8 -*-
"""Actualizacion por fotograma: estados y logica de juego."""
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
from .characters import char_of


class UpdateMixin:
    """Actualizacion por fotograma: estados y logica de juego."""

    # ------------------------------------------------------------ actualizacion
    def update(self, dt):
        dt = self.polish_dt(dt)
        self.time += dt
        tick = getattr(self, "music_tick", None)
        if tick is not None:
            tick(dt)                                  # musica por capas (fundidos)
        if getattr(self, "ach_queue", None):
            self.ach_tick(dt)                         # cartel de logro (3 s)
        tgt = 1.0 if (self.has_key and self.room_mod != "dark") else 0.0        # las antorchas se encienden con la llave
        self.torch_fade += max(-2.0 * dt, min(0.7 * dt, tgt - self.torch_fade))
        if self.toast_t > 0:
            self.toast_t -= dt
        if self.restart_arm > 0:
            self.restart_arm -= dt
        st = self.state
        if st == "menu":
            self.update_demo(dt)             # el fondo del menu es el juego real jugando solo
        elif st == "play":
            if not self.help:
                self.update_play(dt)
        elif st == "cards":
            self.update_cards(dt)
        elif st == "select":
            self.update_select(dt)
        elif st == "achievements":
            self.update_demo(dt)                     # la demo del menu sigue de fondo
            self.state = "achievements"               # update_demo deja el estado en "menu"
        elif st == "options":
            if self.opt_return == "menu":
                self.update_demo(dt)                 # la demo del menu sigue de fondo
                self.state = "options"               # update_demo deja el estado en "menu"
        elif st == "dead":
            self.reveal = min(1.0, self.reveal + dt * 0.7)
            self.update_waves(dt)
            self.update_fx(dt)
            self.hurt_flash = max(0.0, self.hurt_flash - dt)
        elif st == "clear":
            self.reveal = min(0.8, self.reveal + dt * 0.7)
            self.clear_t -= dt
            self.update_waves(dt)
            self.update_fx(dt)
            if self.clear_t <= 0:
                self.fade_in = FADE_T
                if self.mode == "endless":
                    self.endless_next_room()
                elif self.level_idx + 1 < len(LEVELS):
                    if self.tutorial:
                        self.total_time = 0.0
                    self.load_level(self.level_idx + 1)
                else:
                    self.state = "victory"
                    ach_notify(self, "victory")
                    self.clear_progress()            # partida terminada: ya no hay nada que continuar
        elif st == "victory":
            self.reveal = min(1.0, self.reveal + dt * 0.5)

    def update_waves(self, dt):
        for w in self.waves[:]:
            w.r += w.speed * dt
            while w.bounces and w.r >= w.bounces[0][0]:      # el eco rebota en el muro
                _, bx, by = w.bounces.pop(0)
                self.add_wave(bx, by, "bounce")
            if w.r >= w.max_r and w in self.waves:
                self.waves.remove(w)

    def update_play(self, dt):
        inp = self.get_input()
        p, lv = self.player, self.level
        self.t_level += dt
        self.total_time += dt
        # los monstruos tardan en despertar y luego ganan agresividad poco a poco
        if self.tutorial:
            self.grace, self.aggr = 0.0, 1.0
        else:
            self.grace = max(0.0, GRACE_T - self.t_level)
            self.aggr = 0.7 + 0.3 * min(1.0, max(0.0, self.t_level - GRACE_T) / 3.0)
        if self.mode == "endless":                       # cada sala los monstruos son algo mas agresivos
            self.aggr = min(ENDLESS_AGGR_MAX, self.aggr * (1.0 + ENDLESS_AGGR_STEP * self.e_room))
            self.aggr *= self.mon_mult                   # sala "monstruos frenéticos" (+30%)
        p.inv = max(0.0, p.inv - dt)
        p.stun = max(0.0, p.stun - dt)
        p.attack_cd = max(0.0, p.attack_cd - dt)
        p.attack_t = max(0.0, p.attack_t - dt)
        p.pulse_cd = max(0.0, p.pulse_cd - dt)
        p.shoot_cd = max(0.0, p.shoot_cd - dt)
        p.shoot_t = max(0.0, p.shoot_t - dt)
        p.jbuf = max(0.0, p.jbuf - dt)
        p.pogo = max(0.0, p.pogo - dt)
        p.land_t = max(0.0, p.land_t - dt)
        p.dash_cd = max(0.0, p.dash_cd - dt)
        p.mute_echo = max(0.0, p.mute_echo - dt)
        dashing = p.dash_t > 0
        p.dash_t = max(0.0, p.dash_t - dt)
        if dashing and p.dash_t <= 0:                    # fin del dash: salida suave
            p.vx = max(-self.walk_speed * 1.5, min(self.walk_speed * 1.5, p.vx))
            if self.anakin_mode:
                self.ak_stab_start(p)                    # clava la espada en el suelo
        p.clap_t = max(0.0, p.clap_t - dt)
        p.clap_cd = max(0.0, p.clap_cd - dt)
        if p.charging and (self.has_bow or self.anakin_mode or self.fighter_mode):     # carga del arco / FUERZA / aplauso
            need = self.charge_t()
            was_full = p.charge >= need
            # luchador: la super onda se recarga; la carga NO avanza mientras dura su enfriamiento
            gain = 0.0 if (self.fighter_mode and p.clap_cd > 0) else dt
            p.charge = min(need + 0.8, p.charge + gain)
            q = min(1.0, p.charge / need)
            if p.charge >= need and not was_full:      # carga llena (el luchador espera a que sueltes: ya no sale sola)
                self.sfx("key")
                self.add_wave(p.x, p.y - 8, "key", 0.7)
            if q > 0.25 and random.random() < 0.4 + 0.5 * q:      # energia que converge en el arco
                ang = random.uniform(0.0, 6.283)
                cxb, cyb = p.x + p.face * 7, p.y - 9
                if self.anakin_mode:
                    cxb, cyb = self.hand_pos(p)
                l2 = 0.22
                self.sparks.append([cxb + math.cos(ang) * 16, cyb + math.sin(ang) * 16,
                                    -math.cos(ang) * 16 / l2, -math.sin(ang) * 16 / l2,
                                    l2, l2, self.tc((255, 70, 50) if random.random() < 0.7 else (255, 200, 170))
                                    if self.anakin_mode else ((255, 255, 255) if self.fighter_mode else (255, 232, 165))])
        if p.windup > 0:                                 # anticipacion -> tajo
            if p.stun > 0:
                p.windup = 0.0
            else:
                p.windup -= dt
                if p.windup <= 0:
                    p.windup = 0.0
                    self.perform_attack()
        self.sealed_cd = max(0.0, self.sealed_cd - dt)
        self.hurt_flash = max(0.0, self.hurt_flash - dt)
        self.block_flash = max(0.0, self.block_flash - dt)
        if lv.ghost_t:                                   # puentes fantasma: cuenta atras
            lv.ghost_t = {c: t - dt for c, t in lv.ghost_t.items() if t - dt > 0}

        # --- control horizontal
        p.sneak = inp["sneak"]
        p.shield = bool((self.fighter_mode or (self.has_shield and self.shield_allowed()))      # luchador: guardia de boxeador, sin escudo
                        and inp["shield"] and p.stun <= 0 and p.dash_t <= 0)
        dx = inp["right"] - inp["left"]
        if p.dash_t > 0:                                 # dash: velocidad fija y sin gravedad
            p.vx = p.dash_dir * DASH_SPEED
        elif p.stun <= 0:
            sp = SNEAK_SPEED if p.sneak else self.walk_speed
            if p.shield:
                sp *= self.shield_mult
            sp *= p.boost                                # impulso del salto diagonal
            flying = self.fighter_mode and not p.on_ground and not self.in_demo
            if flying:
                sp *= FT_FLY_HSPEED                      # luchador: en vuelo es mucho mas rapido
            target = dx * sp
            acc = (1100.0 if dx == 0 else 900.0) if p.on_ground else (FT_FLY_AIR_ACC if flying else 520.0)
            step = acc * dt
            p.vx += max(-step, min(step, target - p.vx))
            if dx:
                p.face = 1 if dx > 0 else -1
        else:
            p.vx *= 0.9 ** (dt * 60)

        # --- corrientes de aire
        p.in_vent = any(x0 < p.x < x1 and y0 - 4 < p.y <= y1 + 1 for (x0, y0, x1, y1) in lv.vents)

        # --- salto (coyote time + buffer + altura variable + impulso diagonal)
        if p.on_ground:
            p.coyote = 0.1
            p.air_left = char_of(self)["air_jumps"]          # pícaro: recupera su doble salto
        else:
            p.coyote = max(0.0, p.coyote - dt)
        if p.jbuf > 0 and p.coyote > 0 and p.stun <= 0:
            p.vy = -JUMP_V
            if dx:                                       # SALTO DIAGONAL: impulso horizontal extra
                p.boost = DIAG_BOOST
                p.vx = dx * (SNEAK_SPEED if p.sneak else self.walk_speed) * DIAG_BOOST
            p.coyote = p.jbuf = 0.0
            p.dash_t = 0.0                               # saltar cancela el dash
            p.on_ground = False
            self.jumps += 1
            self.sfx("jump")
        elif p.jbuf > 0 and not p.on_ground and p.air_left > 0 and p.stun <= 0:      # DOBLE SALTO (pícaro)
            p.air_left -= 1
            p.vy = -JUMP_V * AIR_JUMP_MULT
            p.jbuf = 0.0
            p.pogo = 0.0
            p.dash_t = 0.0
            self.jumps += 1
            self.add_wave(p.x, p.y - 3, "airjump")
            self.sfx("jump")
            for _ in range(8):
                life = random.uniform(0.2, 0.4)
                self.sparks.append([p.x + random.uniform(-4, 4), p.y - 1, random.uniform(-30, 30),
                                    random.uniform(10, 50), life, life, (150, 240, 180)])
        if not inp["jump"] and p.vy < -110 and p.pogo <= 0 and not p.in_vent:
            p.vy = -110.0

        # --- fisica
        was_ground = p.on_ground
        if self.fighter_mode and not p.on_ground and not self.in_demo:     # LUCHADOR VUELA: W sube, S baja, sin tecla flota
            p.dive_t = p.dive_t + dt if (inp["shield"] and not inp["jump"]) else 0.0
            if p.dive_t > FT_DIVE_AFTER:                 # mantener S: PICADA a toda velocidad
                tgt = FT_DIVE_SPEED
            else:
                tgt = -FT_FLY_SPEED if inp["jump"] else (FT_FLY_SPEED if inp["shield"] else 0.0)
            p.vy += (tgt - p.vy) * min(1.0, dt * (FT_FLY_ACCEL * (1.6 if p.dive_t > FT_DIVE_AFTER else 1.0)))
        else:
            p.vy = min(p.vy + self.gravity * dt, MAX_FALL)
        if p.in_vent and p.vy > -135.0:
            p.vy = max(-135.0, p.vy - 1500.0 * dt)       # la corriente te eleva
        if p.dash_t > 0:
            p.vy = 0.0                                   # el dash flota en linea recta
        fall = p.vy
        ox = p.x
        move_body(lv, p, dt)
        if p.dash_t > 0 and p.hit_wall:                  # el dash se corta contra un muro
            p.dash_t = 0.0
            self.add_wave(p.x + p.dash_dir * 6, p.y - 8, "arrowhit")
        if p.on_ground:
            p.boost = 1.0
        moved = abs(p.x - ox)
        if p.on_ground:
            p.walk += moved
            p.step_acc += moved
            p.moved_total += moved
            if self.fighter_mode and not was_ground and fall >= FT_SLAM_MIN_FALL:
                self.fighter_slam(fall)                         # aterrizaje en picada: IMPACTO
            if not was_ground and fall > 90:                    # compresion al aterrizar
                p.land_t = LAND_T
                p.land_pow = max(0.35, min(1.0, fall / 300.0))
                self.landing_dust(p.x, p.y, fall)
            if self.fighter_mode and not was_ground and fall >= FT_SLAM_MIN_FALL:
                p.land_t, p.land_pow = FT_LAND_T, 1.0           # compresion exagerada
            if not was_ground and fall > 170:                   # eco de aterrizaje
                self.add_wave(p.x, p.y - 3, "step", 1.4)
                self.sfx("step")
        if p.sneak:
            p.step_acc = 0.0
        elif p.on_ground and p.step_acc >= STEP_DIST:
            p.step_acc -= STEP_DIST
            self.add_wave(p.x, p.y - 3, "step")
            self.sfx("step")

        # --- haz de luz frontal: se adelanta mas cuanto mas rapido corres
        p.sf = min(1.0, abs(p.vx) / self.walk_speed)
        p.look += (p.face * (10.0 + 16.0 * p.sf) - p.look) * min(1.0, dt * 8.0)

        # --- inclinacion del sprite: hacia delante al correr a maxima velocidad (y en el dash)
        if p.dash_t > 0:
            want = 14.0 * p.dash_dir
        elif p.windup > 0:
            want = -5.0 * p.face                         # se echa hacia atras al armar el tajo
        elif self.fighter_mode and not p.on_ground and p.vy > 200:
            want = 70.0 * p.face                              # PICADA: de cabeza hacia delante y abajo
        elif self.fighter_mode and not p.on_ground and abs(p.vx) > 25:
            want = 60.0 * (1 if p.vx > 0 else -1)             # vuela con el cuerpo inclinado hacia delante
        elif p.on_ground and not p.sneak and p.sf > 0.8 and abs(p.vx) > 1:
            want = 7.0 * (1 if p.vx > 0 else -1) * min(1.0, (p.sf - 0.8) / 0.2)
        else:
            want = 0.0
        p.tilt += (want - p.tilt) * min(1.0, dt * 14.0)
        if p.dash_t > 0:
            self.dash_trail(p)
        if self.fighter_mode and not p.on_ground and (abs(p.vx) > 25 or abs(p.vy) > 25) and random.random() < 0.6:
            life = random.uniform(0.15, 0.3)                  # estela de aire blanca al volar
            self.sparks.append([p.x - p.face * random.uniform(3, 7), p.y - random.uniform(1.0, 13.0),
                                -p.vx * 0.2, -p.vy * 0.2, life, life, (235, 242, 255)])
        if self.fighter_mode and not p.on_ground and p.vy > 200:
            self.fighter_dive_fx(p)                           # estela de la picada
        self.update_fx(dt)

        # --- monstruos
        for m in self.monsters[:]:
            m.update(dt, self)
            if m not in self.monsters:                   # (p. ej. el ladron que escapa)
                continue
            # alerta: el halo aparece cuando el monstruo te ataca y se apaga si lo pierdes
            hunting = (self.tutorial or m.chase_t > 0 or getattr(m, "retreat", 0.0) > 0
                       or getattr(m, "aim", 0.0) > 0)
            m.alert = getattr(m, "alert", 0.0)
            m.alert += ((1.0 if hunting else 0.0) - m.alert) * min(1.0, dt * 6.0)
            if p.dash_t > 0:                             # embestida: golpea una vez a cada monstruo
                if id(m) not in p.dash_hit and boxes_overlap(m, p) and not getattr(m, "phased", False):
                    p.dash_hit.add(id(m))
                    self.damage_monster(m, p.dash_dir)
                continue
            if p.inv <= 0 and boxes_overlap(m, p) and not getattr(m, "phased", False):
                self.hurt_player(m)
                if self.state != "play":
                    return

        self.update_arrows(dt)
        if self.state != "play":
            return
        if self.mode == "endless":
            self.endless_update(dt)
            self.update_traps(dt)
            if self.state != "play":
                return

        pcx, pcy = p.x, p.y - 7
        # --- llave
        if lv.key and self.key_visible and not self.has_key and math.hypot(pcx - lv.key[0], pcy - lv.key[1]) < 11:
            self.has_key = True
            lv.door_open = True
            self.add_wave(lv.key[0], lv.key[1], "key")
            self.sfx("key")
            self.toast("¡Has tomado la llave! Las antorchas se encienden y la puerta de salida se abre.", 3.5)
        # --- puerta
        if lv.door:
            dcx, dcy = lv.door[0] * TILE + 8, lv.door[1] * TILE + 8
            dd = math.hypot(pcx - dcx, pcy - dcy)
            if not self.has_key and dd < 17 and self.sealed_cd <= 0:
                self.sealed_cd = 2.0
                self.add_wave(p.x, p.y - 8, "locked")
                self.sfx("locked")
                if self.mode == "endless" and self.e_boss is not None:
                    self.toast("La puerta sigue sellada: derrota al jefe.", 2.8)
                elif self.mode == "endless":
                    self.toast("La puerta sigue sellada: faltan %d bajas." % max(0, self.e_quota - self.e_room_kills), 2.8)
                elif self.monsters:
                    self.toast("La puerta está sellada. Derrota a todos los monstruos (quedan %d)." % len(self.monsters), 2.8)
                else:
                    self.toast("La puerta está sellada. Encuentra la llave dorada.", 2.8)
            elif self.has_key and dd < 12:
                self.state = "clear"
                self.clear_t = 0.9 if self.mode == "endless" else 2.0
                self.sfx("win")
                return

        # --- peligro / latido
        nearest = min((math.hypot(m.x - p.x, (m.y - m.h / 2) - (p.y - 7)) for m in self.monsters), default=999)
        self.danger = max(0.0, 1.0 - nearest / 64.0)
        if self.danger > 0.05:
            self.heart_t -= dt
            if self.heart_t <= 0:
                self.heart_t = 1.1 - 0.7 * self.danger
                self.sfx("heart")

        # --- mini tutorial (sala de practica)
        if self.tutorial:
            if p.sneak and p.on_ground:
                self.sneak_dist += moved
            t = self.tut
            if t == 0 and p.moved_total > 50:
                self.tut_advance()
            elif t == 1 and self.jumps > 0:
                self.tut_advance()
            elif t == 2 and self.sneak_dist > 25:
                self.tut_advance()
            elif t == 3 and self.attacks > 0:
                self.tut_advance()
            elif t == 4 and self.pulses > 0:
                self.tut_advance()
            elif t == 5 and self.key_visible:
                self.tut_advance()
            elif t == 6 and self.has_key:
                self.tut_advance()
        self.update_waves(dt)
