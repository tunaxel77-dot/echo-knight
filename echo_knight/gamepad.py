# -*- coding: utf-8 -*-
"""Mando (ronda 5.5). Traduce los eventos JOY* a las MISMAS acciones que el teclado:
- en juego: botones -> teclas de KEYMAP (eventos KEYDOWN/KEYUP sinteticos) y stick/cruceta/gatillo -> acciones mantenidas (pad_held,
  que suma a Game.held() a pygame.key.get_pressed()); Start = pausa.
- en menus (cualquier estado que no sea "play", o con la ayuda abierta): cruceta/stick -> flechas con repeticion, A -> ENTER, B -> ESC.
Asi menu, seleccion de personaje, cartas, opciones, logros, pausa y pantalla de muerte funcionan sin tocar su codigo."""
import pygame
from .config import *


class GamepadMixin:
    pads = None                         # {id de instancia: Joystick}
    pad_held = frozenset()              # acciones mantenidas por el mando (las lee held())
    pad_axes = None
    pad_hat = (0, 0)
    pad_lt = False
    pad_btn_held = None                 # acciones mantenidas por botones (saltar)
    pad_fire_down = False
    pad_last = (0, 0)
    pad_next = 0.0
    pad_mode = False

    def init_gamepad(self):
        self.pads, self.pad_axes, self.pad_btn_held = {}, {}, set()
        self.pad_held, self.pad_hat, self.pad_lt, self.pad_fire_down = frozenset(), (0, 0), False, False
        try:
            pygame.joystick.init()
        except Exception:
            pass

    def pad_connected(self):
        return bool(self.pads)

    # ------------------------------------------------------------ utilidades
    def _kd(self, key):
        return pygame.event.Event(pygame.KEYDOWN, key=key, unicode="", mod=0, scancode=0)

    def _ku(self, key):
        return pygame.event.Event(pygame.KEYUP, key=key, mod=0, scancode=0)

    def pad_menu_mode(self):
        return self.state != "play" or bool(getattr(self, "help", False))

    def pad_vec(self):
        """(dx, dy) de la cruceta o el stick: dx -1 izquierda / 1 derecha, dy -1 arriba / 1 abajo."""
        ax, ay = self.pad_axes.get(PAD_AXIS_X, 0.0), self.pad_axes.get(PAD_AXIS_Y, 0.0)
        hx, hy = self.pad_hat
        dx = hx or (1 if ax > PAD_DEADZONE else -1 if ax < -PAD_DEADZONE else 0)
        dy = -hy or (1 if ay > PAD_VDEAD else -1 if ay < -PAD_VDEAD else 0)
        return dx, dy

    # ------------------------------------------------------------ conexion
    def _pad_open(self, e):
        try:
            j = pygame.joystick.Joystick(e.device_index)
            j.init()
            try:
                iid = j.get_instance_id()
            except Exception:
                iid = e.device_index
            if iid in self.pads:
                return
            self.pads[iid] = j
            try:
                nm = j.get_name()
            except Exception:
                nm = ""
            self.toast("Mando conectado" + (": %s" % nm[:24] if nm else ""), 3.0)
        except Exception:
            pass

    def _pad_close(self, e):
        iid = getattr(e, "instance_id", None)
        self.pads.pop(iid, None)
        out = []
        if not self.pads:
            self.pad_axes, self.pad_hat, self.pad_lt = {}, (0, 0), False
            self.pad_btn_held = set()
            if self.pad_fire_down:
                self.pad_fire_down = False
                codes = self.key_codes("fire")
                if codes:
                    out.append(self._ku(codes[0]))
            self.toast("Mando desconectado", 3.0)
        return out

    # ------------------------------------------------------------ botones
    def _pad_button(self, b, down):
        act = PAD_BUTTONS.get(b)
        if act is None:
            return []
        out = []
        if not down:                                     # soltar siempre se atiende (aunque haya cambiado el estado)
            self.pad_btn_held.discard(act)
            if act == "fire" and self.pad_fire_down:
                self.pad_fire_down = False
                codes = self.key_codes("fire")
                if codes:
                    out.append(self._ku(codes[0]))
            return out
        if getattr(self, "opt_capture", None):           # reasignando una tecla: el mando no interviene
            return []
        if self.pad_menu_mode():
            key = None
            if act == "jump":                            # A = aceptar
                key = pygame.K_RETURN
            elif act == "fire" and self.state != "menu":     # B = volver / cancelar
                key = pygame.K_ESCAPE
            elif act == "pause" and self.state == "paused":
                key = pygame.K_ESCAPE
            return [self._kd(key)] if key is not None else []
        if act == "pause":
            return [self._kd(pygame.K_ESCAPE)]
        codes = self.key_codes(act)
        if not codes:
            return []
        if act == "jump":
            self.pad_btn_held.add("jump")                # mantener A = salto alto / subir volando
        if act == "fire":
            self.pad_fire_down = True
        return [self._kd(codes[0])]

    # ------------------------------------------------------------ bucle
    def pad_translate(self, events):
        """Sustituye los eventos JOY* por eventos de teclado sinteticos y actualiza las acciones mantenidas."""
        if self.pads is None:
            self.init_gamepad()
        out = []
        J = lambda n: getattr(pygame, n, None)
        for e in events:
            t = e.type
            if t == J("JOYDEVICEADDED"):
                self._pad_open(e)
            elif t == J("JOYDEVICEREMOVED"):
                out += self._pad_close(e)
            elif t == J("JOYBUTTONDOWN"):
                out += self._pad_button(e.button, True)
            elif t == J("JOYBUTTONUP"):
                out += self._pad_button(e.button, False)
            elif t == J("JOYAXISMOTION"):
                self.pad_axes[e.axis] = e.value
                if e.axis == PAD_AXIS_LT:
                    self.pad_lt = e.value > PAD_TRIGGER_ON
            elif t == J("JOYHATMOTION"):
                self.pad_hat = tuple(e.value)
            else:
                out.append(e)
        if self.pads:
            out += self._pad_repeat()
        self._pad_update_held()
        return out

    def _pad_repeat(self):
        """En menus: la direccion pulsada genera una flecha y, si se mantiene, se repite."""
        menu = self.pad_menu_mode()
        vec = self.pad_vec()
        now = self.time
        out = []
        if menu != self.pad_mode:                        # cambio de menu <-> juego: no dispara nada por la direccion ya mantenida
            self.pad_mode, self.pad_last, self.pad_next = menu, vec, now + PAD_REPEAT_FIRST
            return out
        if not menu or getattr(self, "opt_capture", None):
            self.pad_last = vec
            return out
        if vec != self.pad_last:
            self.pad_last = vec
            self.pad_next = now + PAD_REPEAT_FIRST
            fire = vec != (0, 0)
        else:
            fire = vec != (0, 0) and now >= self.pad_next
            if fire:
                self.pad_next = now + PAD_REPEAT
        if fire:
            dx, dy = vec
            out.append(self._kd(pygame.K_UP if dy < 0 else pygame.K_DOWN if dy > 0 else pygame.K_LEFT if dx < 0 else pygame.K_RIGHT))
        return out

    def _pad_update_held(self):
        if self.pad_menu_mode() or not self.pads:
            self.pad_held = frozenset()
            return
        h = set(self.pad_btn_held)
        dx, dy = self.pad_vec()
        if dx < 0:
            h.add("left")
        elif dx > 0:
            h.add("right")
        if dy < 0:
            h.add("jump")
        elif dy > 0 or self.pad_lt:
            h.add("shield")
        self.pad_held = frozenset(h)
