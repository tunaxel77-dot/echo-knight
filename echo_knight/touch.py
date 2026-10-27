# -*- coding: utf-8 -*-
"""Control tactil (Android). Misma idea que gamepad.py: los toques se traducen a las MISMAS acciones que el teclado.

- En juego: botones virtuales (izq./der./salto/ataque/disparo/dash/super eco/escudo/sigilo/interactuar/pausa).
  Las acciones mantenidas (mover, saltar, escudo, sigilo) las lee Game.held() desde `touch_held`;
  las pulsaciones sueltas se convierten en KEYDOWN/KEYUP sinteticos de KEYMAP (respeta las teclas reasignadas).
- En menus: SDL ya convierte el toque en eventos de raton (los menus ya los manejan). Aqui solo se anade
  un boton "atras" (= ESC), tocar para continuar en las pantallas de muerte / victoria y el boton ATRAS de Android.
- La ventana es mas ancha que el juego (margenes laterales) para que los botones no tapen la accion:
  `self.display` es la ventana real y `self.screen` un subsurface centrado de tamano SW x SH, asi que todo el
  codigo de dibujo existente sigue funcionando sin cambios.

Activacion: automatica en Android, o `python main.py --tactil` en el ordenador para probarlo.
"""
import math
import sys

import pygame
from .config import *
from .paths import is_android

TOUCH_K = 3                     # escala del juego en modo tactil (1152 x 672 logicos); sube a 4 si el movil va sobrado
HOLD_ACTIONS = ("left", "right", "jump", "shield", "sneak")
TAP_ACTIONS = ("attack", "pulse", "fire", "dash", "interact")
BACK_STATES = ("options", "select", "achievements", "cards")
END_STATES = ("dead", "victory")
BTN_COL = (236, 230, 214)
BTN_FILL = (24, 20, 34)


def want_touch(argv=None):
    argv = sys.argv if argv is None else argv
    return True                     # VERSION MOVIL: siempre modo tactil (en la version laptop es opcional)


class TouchMixin:
    touch_mode = False
    touch_scaled = False
    touch_held = frozenset()
    touch_fingers = None
    touch_btns = None
    touch_cache = None
    _tstate = None
    _tstate_since = 0.0
    WS = HS = ox = 0
    display = None

    # ------------------------------------------------------------ ventana
    def setup_touch_window(self):
        """Crea la ventana ancha (juego centrado + margenes para botones). Devuelve la escala k."""
        self.touch_mode = True
        info = pygame.display.Info()
        dw, dh = (info.current_w or 0), (info.current_h or 0)
        if dw <= 0 or dh <= 0 or not is_android():
            dw, dh = 20, 9                                   # escritorio (--tactil): proporcion de un movil alargado
        if dw < dh:
            dw, dh = dh, dw                                  # siempre horizontal
        k = TOUCH_K
        self.k = k
        self.SW, self.SH = LW * k, LH * k
        self.HS = self.SH
        self.WS = max(self.SW, int(round(self.SH * dw / float(dh))))
        self.ox = (self.WS - self.SW) // 2
        flags = (pygame.SCALED | pygame.FULLSCREEN) if is_android() else pygame.SCALED
        try:
            self.display = pygame.display.set_mode((self.WS, self.HS), flags)
            self.touch_scaled = True
        except Exception:
            self.display = pygame.display.set_mode((self.WS, self.HS))
            self.touch_scaled = False
        self.screen = self.display.subsurface((self.ox, 0, self.SW, self.SH))
        self.touch_fingers, self.touch_cache = {}, {}
        self.touch_btns = self._touch_layout()
        return k

    def _touch_layout(self):
        """Botones: dict(name, action, kind, cx, cy, r). Coordenadas de la ventana (display)."""
        WS, HS = self.WS, self.HS
        u = HS / 672.0
        L, R = int(26 * u), WS - int(26 * u)

        def B(name, action, kind, cx, cy, r):
            return dict(name=name, action=action, kind=kind, cx=int(cx), cy=int(cy), r=int(r * u))

        by = HS - 112 * u
        return [
            B("left", "left", "hold", L + 62 * u, by, 58),
            B("right", "right", "hold", L + 192 * u, by, 58),
            B("shield", "shield", "hold", L + 127 * u, HS - 236 * u, 44),
            B("sneak", "sneak", "hold", L + 262 * u, HS - 232 * u, 38),
            B("jump", "jump", "hold", R - 74 * u, HS - 128 * u, 68),
            B("attack", "attack", "tap", R - 218 * u, HS - 92 * u, 58),
            B("fire", "fire", "tap", R - 82 * u, HS - 274 * u, 46),
            B("pulse", "pulse", "tap", R - 214 * u, HS - 218 * u, 42),
            B("dash", "dash", "tap", R - 334 * u, HS - 96 * u, 40),
            B("interact", "interact", "tap", R - 338 * u, HS - 192 * u, 36),
            B("pause", "pause", "tap", WS - 52 * u, 52 * u, 30),
            B("back", "back", "tap", 52 * u, 52 * u, 30),
        ]

    def _btn_visible(self, b):
        n = b["name"]
        if n in ("back",):
            return self.state in BACK_STATES
        if n == "pause":
            return self.state == "play" and not self.help
        if self.state != "play" or self.help:
            return False
        if n == "fire":
            return bool(self.has_bow or self.anakin_mode or self.fighter_mode)
        if n == "dash":
            return bool(self.tun_mode or self.anakin_mode or self.fighter_mode or self.dash_perk)
        if n == "shield":
            return bool(self.has_shield or self.fighter_mode)
        return True

    def _touch_hit(self, pos, only=None):
        """Boton bajo el dedo (el de centro mas cercano dentro de su radio + margen)."""
        best, bd = None, 1e9
        for b in self.touch_btns:
            if only is not None and b["name"] not in only:
                continue
            if not self._btn_visible(b):
                continue
            d = math.hypot(pos[0] - b["cx"], pos[1] - b["cy"])
            if d <= b["r"] * 1.18 and d < bd:
                best, bd = b, d
        return best

    def touch_pos(self, e):
        return (e.x * self.WS, e.y * self.HS)

    def _btn_by_name(self, name):
        for b in self.touch_btns:
            if b["name"] == name:
                return b
        return None

    # ------------------------------------------------------------ eventos
    def touch_translate(self, events):
        """Consume los eventos FINGER* y devuelve el resto + teclas sinteticas. Tambien: boton ATRAS de Android = ESC,
        y pasar a segundo plano abre la pausa."""
        if self.touch_fingers is None:
            self.touch_fingers = {}
        if self._tstate != self.state:
            self._tstate, self._tstate_since = self.state, self.time
        FD, FM, FU = (getattr(pygame, n, None) for n in ("FINGERDOWN", "FINGERMOTION", "FINGERUP"))
        bg = getattr(pygame, "APP_WILLENTERBACKGROUND", None)
        back = getattr(pygame, "K_AC_BACK", None)
        out = []
        for e in events:
            t = e.type
            if self.touch_mode and t == FD:
                out += self._touch_down(e)
            elif self.touch_mode and t == FM:
                out += self._touch_move(e)
            elif self.touch_mode and t == FU:
                out += self._touch_up(e)
            elif bg is not None and t == bg:
                if self.state == "play" and not self.help:
                    out += self._release_all()
                    self.open_pause()
            elif t == pygame.KEYDOWN and back is not None and e.key == back:
                out.append(self._kd(pygame.K_ESCAPE))
            else:
                out.append(e)
        if self.touch_mode:
            if self.touch_fingers and (self.state != "play" or self.help):
                out += self._release_all()               # cambio de estado con dedos puestos (muerte, pausa...)
            self._touch_update_held()
        return out

    def _release_all(self):
        out = []
        if any(n == "fire" for n in self.touch_fingers.values()):
            codes = self.key_codes("fire")
            if codes:
                out.append(self._ku(codes[0]))
        self.touch_fingers.clear()
        self.touch_held = frozenset()
        return out

    def _touch_down(self, e):
        pos = self.touch_pos(e)
        st = self.state
        if st == "play" and self.help:
            return [self._kd(pygame.K_RETURN)]
        if st == "play":
            b = self._touch_hit(pos)
            if b is None:
                return []
            self.touch_fingers[e.finger_id] = b["name"]
            return self._touch_press(b["name"])
        if st in END_STATES:
            if self.time - self._tstate_since > 0.8:      # evita reiniciar sin querer con los dedos aun en los botones
                return [self._kd(pygame.K_RETURN)]
            return []
        if st in BACK_STATES:
            b = self._touch_hit(pos, only=("back",))
            if b is not None:
                return [self._kd(pygame.K_ESCAPE)]
        return []

    def _touch_press(self, name):
        if name == "pause":
            return [self._kd(pygame.K_ESCAPE)]
        b = self._btn_by_name(name)
        if b["action"] not in TAP_ACTIONS and b["action"] != "jump":
            return []                                      # izq./der./escudo/sigilo: se leen como acciones mantenidas
        codes = self.key_codes(b["action"])
        return [self._kd(codes[0])] if codes else []

    def _touch_move(self, e):
        """Deslizar el dedo entre IZQ. y DER. cambia de boton sin levantarlo; el resto de botones se quedan pegados."""
        name = self.touch_fingers.get(e.finger_id)
        if name not in ("left", "right") or self.state != "play":
            return []
        b = self._touch_hit(self.touch_pos(e), only=("left", "right"))
        if b is not None and b["name"] != name:
            self.touch_fingers[e.finger_id] = b["name"]
        return []

    def _touch_up(self, e):
        name = self.touch_fingers.pop(e.finger_id, None)
        if name == "fire":
            codes = self.key_codes("fire")
            if codes:
                return [self._ku(codes[0])]                # soltar = disparar (normal o super)
        return []

    def _touch_update_held(self):
        if self.state != "play" or self.help or not self.touch_fingers:
            self.touch_held = frozenset()
            return
        self.touch_held = frozenset(a for a in self.touch_fingers.values() if a in HOLD_ACTIONS)

    # ------------------------------------------------------------ dibujo
    def _btn_surface(self, b, pressed):
        key = (b["name"], pressed)
        s = self.touch_cache.get(key)
        if s is not None:
            return s
        r = b["r"]
        s = pygame.Surface((2 * r + 4, 2 * r + 4), pygame.SRCALPHA)
        c = (r + 2, r + 2)
        pygame.draw.circle(s, BTN_FILL + (170 if pressed else 95,), c, r)
        pygame.draw.circle(s, BTN_COL + (235 if pressed else 150,), c, r, 3 if pressed else 2)
        self._btn_icon(s, b["name"], c, r, BTN_COL + (255 if pressed else 215,))
        self.touch_cache[key] = s
        return s

    def _btn_icon(self, s, name, c, r, col):
        cx, cy = c
        d = pygame.draw
        w = max(3, r // 9)
        if name in ("left", "right", "back"):
            sg = 1 if name == "right" else -1
            d.polygon(s, col, [(cx + sg * .38 * r, cy), (cx - sg * .26 * r, cy - .42 * r), (cx - sg * .26 * r, cy + .42 * r)])
        elif name == "jump":
            d.polygon(s, col, [(cx, cy - .42 * r), (cx - .46 * r, cy + .30 * r), (cx + .46 * r, cy + .30 * r)])
        elif name == "shield":
            d.polygon(s, col, [(cx - .42 * r, cy - .40 * r), (cx + .42 * r, cy - .40 * r), (cx + .42 * r, cy + .05 * r),
                               (cx, cy + .50 * r), (cx - .42 * r, cy + .05 * r)], w)
        elif name == "attack":
            d.line(s, col, (cx - .34 * r, cy + .34 * r), (cx + .42 * r, cy - .42 * r), w + 1)
            d.line(s, col, (cx - .42 * r, cy + .02 * r), (cx - .02 * r, cy + .42 * r), w)
            d.line(s, col, (cx - .34 * r, cy + .34 * r), (cx - .50 * r, cy + .50 * r), w)
        elif name == "fire":
            d.line(s, col, (cx - .46 * r, cy + .02 * r), (cx + .36 * r, cy + .02 * r), w)
            d.polygon(s, col, [(cx + .52 * r, cy + .02 * r), (cx + .22 * r, cy - .24 * r), (cx + .22 * r, cy + .28 * r)])
            d.line(s, col, (cx - .46 * r, cy + .02 * r), (cx - .62 * r, cy - .20 * r), w - 1)
            d.line(s, col, (cx - .46 * r, cy + .02 * r), (cx - .62 * r, cy + .24 * r), w - 1)
        elif name == "pulse":
            for f in (.20, .42, .64):
                d.circle(s, col, c, int(f * r), max(2, w - 1))
        elif name == "dash":
            for off in (-.22, .22):
                d.lines(s, col, False, [(cx + (off - .16) * r, cy - .34 * r), (cx + (off + .16) * r, cy),
                                        (cx + (off - .16) * r, cy + .34 * r)], w)
        elif name == "pause":
            d.rect(s, col, (cx - .34 * r, cy - .36 * r, .24 * r, .72 * r))
            d.rect(s, col, (cx + .10 * r, cy - .36 * r, .24 * r, .72 * r))
        else:                                              # interact / sneak: texto
            txt = {"interact": "E", "sneak": "SIG"}.get(name, "?")
            f = pygame.font.Font(None, int(r * (1.25 if len(txt) == 1 else 0.95)))
            t = f.render(txt, True, col)
            s.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))

    def draw_touch(self):
        """Margenes negros + botones encima del juego. Se llama despues de draw() y antes de flip()."""
        if not self.touch_mode:
            return
        d = self.display
        if self.ox > 0:
            d.fill((0, 0, 0), (0, 0, self.ox, self.HS))
            d.fill((0, 0, 0), (self.ox + self.SW, 0, self.WS - self.ox - self.SW, self.HS))
        down = set(self.touch_fingers.values()) if self.touch_fingers else ()
        for b in self.touch_btns:
            if self._btn_visible(b):
                s = self._btn_surface(b, b["name"] in down)
                d.blit(s, (b["cx"] - b["r"] - 2, b["cy"] - b["r"] - 2))
