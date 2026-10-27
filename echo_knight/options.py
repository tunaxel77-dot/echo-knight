# -*- coding: utf-8 -*-
"""Ronda 5.1 - Opciones: volumen, tamano de ventana y REASIGNAR TECLAS (KEYMAP en config.py).
Ajustes guardados en ~/.echo_knight_settings.json (aparte del progreso, que ira en save.py)."""
import copy
import json
import os

from .paths import data_path

import pygame
from .config import *

SETTINGS_FILE = data_path(".echo_knight_settings.json")

KEY_LABELS = {"left": "←", "right": "→", "up": "↑", "down": "↓", "space": "ESPACIO",
              "left shift": "SHIFT IZQ", "right shift": "SHIFT DER"}


def read_settings():
    """Lee el archivo de ajustes (dict vacio si no existe o esta roto). Lo usa tambien core.py antes de abrir la ventana."""
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def clean_keymap(raw):
    """Mezcla un keymap guardado con el de fabrica: solo acciones conocidas, con listas de nombres de tecla."""
    km = copy.deepcopy(KEYMAP)
    if isinstance(raw, dict):
        for act in km:
            v = raw.get(act)
            if isinstance(v, list) and v and all(isinstance(n, str) and n for n in v):
                km[act] = v[:4]
    return km


def key_label(name):
    return KEY_LABELS.get(name, name.upper())


class OptionsMixin:
    """Pantalla OPCIONES (estado "options") + teclas reasignables + volumen + tamano de ventana."""

    # valores por defecto de clase (Game.__new__ en las pruebas sigue funcionando)
    keymap = None
    vol_master = VOL_MASTER_DEFAULT
    vol_music = VOL_MUSIC_DEFAULT
    opt_return = "menu"
    opt_sel = 0
    opt_capture = None
    opt_drag = None
    _kc_cache = None

    # ------------------------------------------------------------ ajustes
    def init_options(self):
        d = read_settings()
        self.keymap = clean_keymap(d.get("keymap"))
        self.vol_master = self._clamp01(d.get("vol_master", VOL_MASTER_DEFAULT))
        self.vol_music = self._clamp01(d.get("vol_music", VOL_MUSIC_DEFAULT))
        self.opt_return, self.opt_sel, self.opt_capture, self.opt_drag = "menu", 0, None, None
        self._kc_cache = None
        self.apply_volume()

    @staticmethod
    def _clamp01(v):
        try:
            return max(0.0, min(1.0, float(v)))
        except Exception:
            return 0.5

    def save_settings(self):
        d = dict(keymap=self.get_keymap(), vol_master=round(self.vol_master, 3),
                 vol_music=round(self.vol_music, 3), window_k=self.k)
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(d, f)
        except Exception:
            pass

    def apply_volume(self):
        for snd in getattr(self, "sounds", {}).values():
            try:
                snd.set_volume(self.vol_master)
            except Exception:
                pass

    def set_window_scale(self, k):
        """Cambia el tamano de la ventana (escala 2..5). En pantalla completa no hace nada."""
        k = max(WINDOW_K_MIN, min(WINDOW_K_MAX, int(k)))
        if self.touch_mode or k == self.k or self.fullscreen:       # en movil la ventana la fija el sistema
            return False
        self.k = k
        self.SW, self.SH = LW * k, LH * k
        self.screen = pygame.display.set_mode((self.SW, self.SH))
        self.scaled = pygame.Surface((self.SW, self.SH)).convert()
        self.text_cache.clear()
        return True

    # ------------------------------------------------------------ teclas
    def get_keymap(self):
        return self.keymap if self.keymap is not None else KEYMAP

    def key_codes(self, action):
        """Codigos de pygame de la accion (cache; se invalida al reasignar)."""
        if self._kc_cache is None:
            self._kc_cache = {}
        if action not in self._kc_cache:
            codes = []
            for nm in self.get_keymap().get(action, []):
                try:
                    codes.append(pygame.key.key_code(nm))
                except Exception:
                    pass
            self._kc_cache[action] = tuple(codes)
        return self._kc_cache[action]

    def key_is(self, key, action):
        return key in self.key_codes(action)

    def held(self, pressed, action):
        """True si alguna tecla de la accion esta pulsada (pressed = pygame.key.get_pressed())."""
        return action in self.pad_held or action in self.touch_held or any(pressed[c] for c in self.key_codes(action))     # (+ mando, ronda 5.5)

    def key_text(self, action):
        return " / ".join(key_label(n) for n in self.get_keymap().get(action, [])[:2])

    def rebind(self, action, key_name):
        """Pone key_name como tecla PRINCIPAL de action. Devuelve (ok, mensaje). Si otra accion la usaba como principal,
        intercambian (la otra recibe la antigua de esta); si la tenia de secundaria, se le quita."""
        key_name = (key_name or "").lower()
        if not key_name or key_name in RESERVED_KEYS:
            return False, "Esa tecla está reservada (%s)." % key_label(key_name or "?")
        km = self.get_keymap()
        if self.keymap is None:
            self.keymap = km = copy.deepcopy(KEYMAP)
        old = km[action][0] if km[action] else None
        msg = "%s: %s" % (dict(KEY_ACTIONS)[action], key_label(key_name))
        for other, names in km.items():
            if other == action or key_name not in names:
                continue
            if names[0] == key_name and old:
                names[0] = old                       # intercambio
                msg += "  (intercambiada con %s)" % dict(KEY_ACTIONS)[other]
            else:
                names.remove(key_name)
        rest = [n for n in km[action][1:] if n != key_name]
        km[action] = [key_name] + rest
        self._kc_cache = None
        self.save_settings()
        return True, msg

    def reset_keymap(self):
        self.keymap = copy.deepcopy(KEYMAP)
        self._kc_cache = None
        self.save_settings()

    # ------------------------------------------------------------ filas de la pantalla
    def opt_rows(self):
        rows = [("slider", "vol_master", "Volumen general"), ("slider", "vol_music", "Volumen de música")]
        if not self.touch_mode:                      # (en movil no hay ventana ni teclas que reasignar)
            rows += [("window", "window", "Tamaño de ventana")]
            rows += [("key", a, lab) for a, lab in KEY_ACTIONS]
            rows += [("reset", "reset", "Restablecer teclas")]
        rows += [("back", "back", "Volver")]
        return rows

    def open_options(self, ret):
        self.opt_return, self.opt_sel, self.opt_capture, self.opt_drag = ret, 0, None, None
        self.state = "options"
        self.sfx("step")

    def close_options(self):
        self.opt_capture = self.opt_drag = None
        self.save_settings()
        self.state = self.opt_return
        self.sfx("step")

    def opt_geometry(self):
        """(panel, y0, row_h) segun el tamano actual."""
        SW, SH, k = self.SW, self.SH, self.k
        w = int(SW * 0.66)
        r = pygame.Rect((SW - w) // 2, int(SH * 0.03), w, int(SH * 0.94))
        y0 = r.y + self.line_h(3.0) + 8 * k
        foot = self.line_h() * 2 + 4 * k
        n = len(self.opt_rows())
        return r, y0, max(1, (r.bottom - foot - y0) // n)

    def opt_rects(self):
        r, y0, rh = self.opt_geometry()
        return [pygame.Rect(r.x + 3 * self.k, y0 + i * rh, r.w - 6 * self.k, rh - 2) for i in range(len(self.opt_rows()))]

    def opt_slider_rect(self, row_rect):
        w = int(row_rect.w * 0.34)
        return pygame.Rect(row_rect.right - w - 6 * self.k, row_rect.centery - 2 * self.k, w, 4 * self.k)

    # ------------------------------------------------------------ cambios de valor
    def opt_adjust(self, i, d):
        kind, ident, _ = self.opt_rows()[i]
        if kind == "slider":
            setattr(self, ident, self._clamp01(round(getattr(self, ident) + d * VOL_STEP, 3)))
            self.apply_volume()
            self.sfx("step")
        elif kind == "window":
            if self.fullscreen:
                self.toast("Sal de pantalla completa (F11) para cambiar el tamaño", 2.5)
            elif self.set_window_scale(self.k + d):
                self.save_settings()

    def opt_set_slider(self, i, pos):
        kind, ident, _ = self.opt_rows()[i]
        tr = self.opt_slider_rect(self.opt_rects()[i])
        v = self._clamp01(round((pos[0] - tr.x) / float(max(1, tr.w)) * 10) / 10.0)
        setattr(self, ident, v)
        self.apply_volume()

    def opt_activate(self, i):
        kind, ident, _ = self.opt_rows()[i]
        if kind == "key":
            self.opt_capture = ident
            self.toast_text, self.toast_t = "", 0.0
        elif kind == "reset":
            self.reset_keymap()
            self.toast("Teclas restablecidas", 2.0)
            self.sfx("key")
        elif kind == "back":
            self.close_options()

    # ------------------------------------------------------------ entrada
    def options_key(self, key):
        if key == pygame.K_F11:
            self.toggle_fullscreen()
            return
        if self.opt_capture:                         # esperando la nueva tecla
            if key == pygame.K_ESCAPE:
                self.opt_capture = None
                return
            ok, msg = self.rebind(self.opt_capture, pygame.key.name(key))
            self.toast(msg, 2.5)
            if ok:
                self.opt_capture = None
                self.sfx("key")
            return
        n = len(self.opt_rows())
        if key == pygame.K_ESCAPE:
            self.close_options()
        elif key in (pygame.K_UP, pygame.K_w):
            self.opt_sel = (self.opt_sel - 1) % n
            self.sfx("step")
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.opt_sel = (self.opt_sel + 1) % n
            self.sfx("step")
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.opt_adjust(self.opt_sel, -1)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.opt_adjust(self.opt_sel, 1)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.opt_activate(self.opt_sel)

    def options_mouse_move(self, pos, dragging=False):
        pos = self.menu_mouse(pos)
        if dragging and self.opt_drag is not None:
            self.opt_set_slider(self.opt_drag, pos)
            return
        if self.opt_capture:
            return
        for i, r in enumerate(self.opt_rects()):
            if r.collidepoint(pos):
                self.opt_sel = i
                return

    def options_mouse_click(self, pos):
        pos = self.menu_mouse(pos)
        if self.opt_capture:
            self.opt_capture = None
            return
        for i, r in enumerate(self.opt_rects()):
            if not r.collidepoint(pos):
                continue
            self.opt_sel = i
            kind = self.opt_rows()[i][0]
            if kind == "slider":
                if self.opt_slider_rect(r).inflate(8 * self.k, 8 * self.k).collidepoint(pos):
                    self.opt_drag = i
                    self.opt_set_slider(i, pos)
            elif kind == "window":
                self.opt_adjust(i, -1 if pos[0] < r.centerx else 1)
            else:
                self.opt_activate(i)
            return

    def options_mouse_up(self):
        if self.opt_drag is not None:
            self.opt_drag = None
            self.sfx("step")
            self.save_settings()

    # ------------------------------------------------------------ dibujo
    def draw_options(self):
        k, SW, SH = self.k, self.SW, self.SH
        r, y0, rh = self.opt_geometry()
        dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
        dim.fill((6, 4, 12, 150))
        self.screen.blit(dim, (0, 0))
        self.draw_panel(r, 240)
        self.draw_text("OPCIONES", r.centerx, r.y + 4 * k, 3.0, GOLD, anchor="c")
        lh = self.line_h()
        for i, (row, rc) in enumerate(zip(self.opt_rows(), self.opt_rects())):
            kind, ident, lab = row
            sel = i == self.opt_sel
            if sel:
                s = pygame.Surface(rc.size, pygame.SRCALPHA)
                s.fill((60, 46, 20, 150))
                self.screen.blit(s, rc.topleft)
                pygame.draw.rect(self.screen, GOLD, rc, max(1, k // 2))
            ty = rc.centery - lh // 2
            col = GOLD if sel else PARCH
            self.draw_text(lab, rc.x + 4 * k, ty, 1.0, col)
            if kind == "slider":
                v = getattr(self, ident)
                tr = self.opt_slider_rect(rc)
                pygame.draw.rect(self.screen, (40, 34, 52), tr)
                pygame.draw.rect(self.screen, CYAN, (tr.x, tr.y, int(tr.w * v), tr.h))
                pygame.draw.rect(self.screen, (176, 132, 56), tr, 1)
                kx = tr.x + int(tr.w * v)
                pygame.draw.rect(self.screen, GOLD if sel else PARCH, (kx - k, tr.y - k, 2 * k, tr.h + 2 * k))
                self.draw_text("%d%%" % round(v * 100), tr.x - 3 * k, ty, 1.0, col, anchor="r")
            elif kind == "window":
                txt = "PANTALLA COMPLETA" if self.fullscreen else "◄  %d×%d  ►" % (LW * self.k, LH * self.k)
                self.draw_text(txt, rc.right - 6 * k, ty, 1.0, col, anchor="r")
            elif kind == "key":
                if self.opt_capture == ident:
                    c2 = (255, 240, 170) if int(self.time * 4) % 2 == 0 else GOLD
                    self.draw_text("PULSA UNA TECLA…  (ESC cancela)", rc.right - 6 * k, ty, 1.0, c2, anchor="r")
                else:
                    self.draw_text(self.key_text(ident), rc.right - 6 * k, ty, 1.0, col, anchor="r")
        hint = "Toca y arrastra para cambiar el volumen" if self.touch_mode else "↑/↓ elegir   ←/→ cambiar   ENTER: reasignar tecla   ESC: volver"
        if self.toast_t > 0 and self.toast_text:
            hint = self.toast_text
        self.draw_text(hint, r.centerx, r.bottom - lh * 2, 1.0, GOLD if self.toast_t > 0 else (190, 178, 150), anchor="c")
