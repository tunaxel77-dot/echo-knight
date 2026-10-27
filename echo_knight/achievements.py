# -*- coding: utf-8 -*-
"""Logros (ronda 5.3): contadores acumulados, desbloqueo, cartel y pantalla LOGROS del menu.
Los datos viven en la clave 'achievements' de ~/.echo_knight_save.json (save.write_save_file); no toca 'progress' ni 'best'."""
import pygame
from . import save
from .config import *
from .characters import CHAR_ORDER

ACH_IDS = [a[0] for a in ACH_LIST]
ACH_INFO = {a[0]: a for a in ACH_LIST}
_COUNTERS = ("kills", "pulses", "best_streak", "best_room", "best_combo")


def ach_notify(game, name, *args):
    """Avisa al sistema de logros si la clase lo tiene (asi las clases de prueba antiguas siguen valiendo)."""
    f = getattr(game, "ach_event", None)
    if f is not None:
        f(name, *args)


def ach_clean(raw):
    """Valida lo leido del guardado: devuelve siempre un dict completo y seguro."""
    raw = raw if isinstance(raw, dict) else {}
    out = {"unlocked": {}, "chars": []}
    un = raw.get("unlocked")
    if isinstance(un, dict):
        out["unlocked"] = {k: True for k, v in un.items() if k in ACH_INFO and v}
    ch = raw.get("chars")
    if isinstance(ch, list):
        out["chars"] = [c for c in CHAR_ORDER if c in ch]
    for k in _COUNTERS:
        v = raw.get(k, 0)
        out[k] = int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0 else 0
    return out


class AchievementsMixin:
    """Logros: ach_event('kill' | 'hurt' | 'pulse' | 'room' | 'boss' | 'buy' | 'combo' | 'victory', ...)."""
    ach = None
    ach_queue = None            # carteles pendientes: [nombre, tiempo restante]
    ach_streak = 0              # bajas seguidas sin recibir dano (no se guarda)
    ach_dirty = False
    ach_scroll = 0
    ach_sel = 0

    # ------------------------------------------------------------ datos
    def init_achievements(self):
        self.ach = ach_clean(save.read_save_file().get("achievements"))
        self.ach_queue, self.ach_streak, self.ach_dirty, self.ach_scroll = [], 0, False, 0

    def _a(self):
        if self.ach is None:
            self.init_achievements()
        return self.ach

    def ach_count(self):
        return len(self._a()["unlocked"])

    def ach_unlocked(self, ident):
        return ident in self._a()["unlocked"]

    def ach_progress(self, ident):
        """(valor actual, meta) del contador de un logro; meta 0 = logro de un solo golpe."""
        a, goal = self._a(), ACH_INFO[ident][3]
        cur = {"streak10": a["best_streak"], "room20": a["best_room"], "pulse50": a["pulses"], "kills100": a["kills"],
               "combo5": a["best_combo"], "chars": len(a["chars"])}.get(ident, 0)
        return min(cur, goal) if goal else (1 if ident in a["unlocked"] else 0), goal

    def ach_flush(self):
        if self.ach_dirty and self.ach is not None:
            save.write_save_file({"achievements": self.ach})
            self.ach_dirty = False

    def ach_unlock(self, ident):
        a = self._a()
        if ident in a["unlocked"]:
            return False
        a["unlocked"][ident] = True
        if self.ach_queue is None:
            self.ach_queue = []
        self.ach_queue.append([ACH_INFO[ident][1], ACH_SHOW_T])
        self.sfx("key")
        self.ach_dirty = True
        self.ach_flush()
        return True

    def ach_tick(self, dt):
        q = self.ach_queue
        if q:
            q[0][1] -= dt
            if q[0][1] <= 0:
                q.pop(0)

    # ------------------------------------------------------------ eventos
    def ach_event(self, name, *args):
        if name == "flush":                         # al morir o volver al menu: guarda contadores y corta la racha
            self.ach_streak = 0
            self.ach_flush()
            return
        if getattr(self, "in_demo", False) or self.state == "menu":      # la demo del menu no cuenta
            return
        a = self._a()
        if name == "kill":
            m = args[0] if args else None
            a["kills"] += 1
            self.ach_streak += 1
            a["best_streak"] = max(a["best_streak"], self.ach_streak)
            self.ach_dirty = True
            if self.ach_streak >= ACH_INFO["streak10"][3]:
                self.ach_unlock("streak10")
            if a["kills"] >= ACH_INFO["kills100"][3]:
                self.ach_unlock("kills100")
            if m is not None and getattr(m, "elite", False):
                self.ach_unlock("elite")
            if a["kills"] % ACH_FLUSH_EVERY == 0:
                self.ach_flush()
        elif name == "hurt":
            self.ach_streak = 0
        elif name == "pulse":
            a["pulses"] += 1
            self.ach_dirty = True
            if a["pulses"] >= ACH_INFO["pulse50"][3]:
                self.ach_unlock("pulse50")
            if a["pulses"] % ACH_FLUSH_EVERY == 0:
                self.ach_flush()
        elif name == "room":                      # args[0] = indice 0-based de la sala a la que acabas de llegar
            e_room = int(args[0])
            a["best_room"] = max(a["best_room"], e_room + 1)
            ch = getattr(self, "char", "knight")
            if e_room >= ACH_ROOM_CHAR and ch in CHAR_ORDER and ch not in a["chars"]:
                a["chars"] = [c for c in CHAR_ORDER if c in a["chars"] or c == ch]
            self.ach_dirty = True
            if a["best_room"] >= ACH_INFO["room20"][3]:
                self.ach_unlock("room20")
            if len(a["chars"]) >= len(CHAR_ORDER):
                self.ach_unlock("chars")
            self.ach_flush()
        elif name == "boss":
            self.ach_unlock("boss")
            self.ach_flush()
        elif name == "buy":
            self.ach_unlock("buy")
            self.ach_flush()
        elif name == "combo":
            a["best_combo"] = max(a["best_combo"], int(args[0]))
            self.ach_dirty = True
            if a["best_combo"] >= ACH_INFO["combo5"][3]:
                self.ach_unlock("combo5")
        elif name == "victory":
            self.ach_unlock("win")
            self.ach_flush()

    # ------------------------------------------------------------ pantalla LOGROS
    def open_achievements(self):
        self.ach_scroll = 0
        self.state = "achievements"
        self.sfx("step")

    def close_achievements(self):
        self.state = "menu"
        self.sfx("step")

    def ach_geometry(self):
        """(panel, y0 de la lista, alto de fila, filas visibles, rect del boton VOLVER)."""
        SW, SH, k = self.SW, self.SH, self.k
        w, h = int(SW * 0.8), int(SH * 0.84)
        r = pygame.Rect((SW - w) // 2, (SH - h) // 2, w, h)
        lh = self.line_h()
        rh = 2 * lh + 4 * k
        y0 = r.y + 4 * k + int(lh * 3.0) + 4 * k
        foot = lh + 6 * k
        vis = max(2, min(len(ACH_LIST), (r.bottom - foot - y0) // rh))
        back = pygame.Rect(r.centerx - int(SW * 0.1), r.bottom - foot, int(SW * 0.2), lh + 3 * k)
        return r, y0, rh, vis, back

    def ach_scroll_by(self, d):
        _, _, _, vis, _ = self.ach_geometry()
        self.ach_scroll = max(0, min(len(ACH_LIST) - vis, self.ach_scroll + int(d)))

    def ach_key(self, key):
        if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_BACKSPACE):
            self.close_achievements()
        elif key in (pygame.K_UP, pygame.K_w):
            self.ach_scroll_by(-1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.ach_scroll_by(1)

    def ach_mouse_click(self, pos):
        p = self.menu_mouse(pos)
        if self.ach_geometry()[4].collidepoint(p):
            self.close_achievements()

    def draw_achievements(self):
        k, SW, SH = self.k, self.SW, self.SH
        r, y0, rh, vis, back = self.ach_geometry()
        dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
        dim.fill((6, 4, 12, 150))
        self.screen.blit(dim, (0, 0))
        self.draw_panel(r, 240)
        lh = self.line_h()
        self.draw_text("LOGROS  %d/%d" % (self.ach_count(), len(ACH_LIST)), r.centerx, r.y + 4 * k, 3.0, GOLD, anchor="c")
        for i in range(self.ach_scroll, min(len(ACH_LIST), self.ach_scroll + vis)):
            ident, nm, ds, goal = ACH_LIST[i]
            ok = self.ach_unlocked(ident)
            y = y0 + (i - self.ach_scroll) * rh
            rc = pygame.Rect(r.x + 4 * k, y, r.w - 8 * k, rh - 2 * k)
            s = pygame.Surface(rc.size, pygame.SRCALPHA)
            s.fill((60, 46, 20, 120) if ok else (26, 22, 34, 120))
            self.screen.blit(s, rc.topleft)
            pygame.draw.rect(self.screen, GOLD if ok else (84, 76, 98), rc, 1)
            self.ach_icon(rc.x + 3 * k, rc.y + k, lh, ok)
            tx = rc.x + 3 * k + lh + 2 * k
            self.draw_text(nm, tx, rc.y + k, 1.0, GOLD if ok else (150, 142, 160))
            self.draw_text(ds, tx, rc.y + k + lh, 1.0, PARCH if ok else (120, 112, 132))
            if goal:
                cur, _ = self.ach_progress(ident)
                self.draw_text("%d/%d" % (cur, goal), rc.right - 3 * k, rc.y + k, 1.0, CYAN if not ok else GOLD, anchor="r")
        if len(ACH_LIST) > vis:
            self.draw_text("↑/↓ o rueda: desplazar", r.x + 4 * k, back.y + k, 1.0, (150, 142, 160))
        sel = back
        pygame.draw.rect(self.screen, (60, 46, 20), sel)
        pygame.draw.rect(self.screen, GOLD, sel, max(1, k // 2))
        self.draw_text("VOLVER (ESC)", sel.centerx, sel.y + 2 * k, 1.0, GOLD, anchor="c")

    def ach_icon(self, x, y, size, ok):
        """Estrella dorada (desbloqueado) o candado gris (bloqueado), dibujados con formas simples."""
        h = size
        if ok:
            cx, cy, r = x + h // 2, y + h // 2, max(3, h // 2)
            pts = [(cx, cy - r), (cx + r // 3, cy - r // 3), (cx + r, cy), (cx + r // 3, cy + r // 3),
                   (cx, cy + r), (cx - r // 3, cy + r // 3), (cx - r, cy), (cx - r // 3, cy - r // 3)]
            pygame.draw.polygon(self.screen, GOLD, pts)
            pygame.draw.polygon(self.screen, (255, 244, 190), pts, 1)
        else:
            col = (130, 122, 146)
            bw, bh = max(5, h * 2 // 3), max(4, h // 2)
            bx, by = x + (h - bw) // 2, y + h - bh
            pygame.draw.rect(self.screen, col, (bx, by, bw, bh))
            pygame.draw.lines(self.screen, col, False, [(bx + 1, by), (bx + 1, by - 3), (bx + bw - 2, by - 3), (bx + bw - 2, by)], 1)

    def draw_ach_banner(self):
        """Cartel de 3 s en la parte de arriba: LOGRO DESBLOQUEADO + nombre."""
        q = self.ach_queue
        if not q:
            return
        k, SW = self.k, self.SW
        lh = self.line_h()
        w, h = int(SW * 0.5), lh * 2 + 6 * k
        r = pygame.Rect((SW - w) // 2, int(self.SH * 0.14), w, h)
        self.draw_panel(r, 225)
        pygame.draw.rect(self.screen, GOLD, r, max(1, k // 2))
        self.draw_text("¡LOGRO DESBLOQUEADO!", r.centerx, r.y + 2 * k, 1.0, CYAN, anchor="c")
        self.draw_text("★ " + q[0][0], r.centerx, r.y + 2 * k + lh, 1.0, GOLD, anchor="c")
