# -*- coding: utf-8 -*-
"""RONDA 6 - Variantes visuales de los monstruos: la MISMA piel de siempre (fantasma, murcielago, esqueleto)
con rasgos propios para distinguirlos de un vistazo: capucha y antifaz (ladron), ojos cian y marca (silenciador),
cola de niebla palida (fantasma invisible), corona dorada (elites), cuernos y capa (esqueleto gigante), cuernos y
ojos amarillos (murcielago grande), corona oscura y ojos rojos (fantasma jefe).

Todo se calcula sobre cuadriculas de pixeles (listas de 16x16 con tuplas RGB o None), sin pygame, para poder
probarlo y previsualizarlo fuera del juego. textures.py las convierte en Surface (ver build_surfaces)."""
from .sprites_data import PAL, GHOUL, BAT_A, BAT_B, BAT_C, SKEL, GH_LEGS_A, GH_LEGS_T, SK_LEGS_A, SK_LEGS_T

EXTRA = {"D": (36, 30, 50), "c": (150, 238, 255), "C": (70, 170, 215), "e": (255, 70, 52), "E": (255, 168, 90),
         "v": (96, 52, 176), "V": (58, 30, 112), "z": (210, 232, 255), "o": (255, 120, 60)}


def _col(ch):
    return EXTRA.get(ch) or PAL.get(ch)


def grid(rows):
    g = [[None] * 16 for _ in range(16)]
    for y, row in enumerate(rows[:16]):
        for x, ch in enumerate(row.ljust(16, ".")[:16]):
            g[y][x] = PAL.get(ch)
    return g


def _variant_rows(rows, cut, tail, bob=False):
    head = rows[:cut] if not bob else rows[1:cut] + [rows[cut - 1]]
    return list(head) + list(tail)


def top(g):
    for y in range(16):
        if any(g[y]):
            return y
    return 0


def copy(g):
    return [row[:] for row in g]


def stamp(g, rows, y0, x0=0):
    """Pinta `rows` (texto, '.' = transparente) con la esquina superior izquierda en (x0, y0)."""
    g = copy(g)
    for dy, row in enumerate(rows):
        y = y0 + dy
        if not 0 <= y < 16:
            continue
        for dx, ch in enumerate(row):
            x = x0 + dx
            if ch not in ". " and 0 <= x < 16:
                g[y][x] = _col(ch)
    return g


def recolor(g, src, dst):
    s, d = _col(src), _col(dst)
    return [[d if c == s else c for c in row] for row in g]


def recolor_rgb(g, src, dst):
    return [[dst if c == src else c for c in row] for row in g]


def mult(g, rgb):
    return [[None if c is None else (c[0] * rgb[0] // 255, c[1] * rgb[1] // 255, c[2] * rgb[2] // 255) for c in row]
            for row in g]


def flip(g):
    return [row[::-1] for row in g]


def clear_from(g, y):
    return [[None if yy >= y else c for c in row] for yy, row in enumerate(g)]


# ---------------------------------------------------------------- fotogramas base (los de siempre)
def ghoul_frames():
    idle = grid(GHOUL)
    a = grid(_variant_rows(GHOUL, 13, GH_LEGS_A))
    t = grid(_variant_rows(GHOUL, 13, GH_LEGS_T, True))
    return {"idle": idle, "walk": [a, t, idle, t]}


def skel_frames():
    idle = grid(SKEL)
    a = grid(_variant_rows(SKEL, 13, SK_LEGS_A))
    t = grid(_variant_rows(SKEL, 13, SK_LEGS_T, True))
    return {"idle": idle, "walk": [idle, a, t, a]}


def bat_frames():
    return [grid(BAT_A), grid(BAT_C), grid(BAT_B), grid(BAT_C)]


def _map(frames, fn):
    """Aplica fn(grid) a todos los fotogramas de un conjunto ghoul/skel ({'idle', 'walk'}) o lista de bat."""
    if isinstance(frames, list):
        return [fn(f) for f in frames]
    return {"idle": fn(frames["idle"]), "walk": [fn(f) for f in frames["walk"]]}


# ---------------------------------------------------------------- rasgos
def _thief(g):
    t = top(g)                                          # capucha oscura + antifaz con los ojos brillando
    g = stamp(g, ["....kDDDDDDk....", "...kDDDDDDDDk...", "...kDyyDDyyDk...", "...kDDDDDDDDk..."], t + 1)
    return mult(g, (110, 255, 150))


def _phantom(g):
    g = clear_from(g, 12)
    g = stamp(g, ["....kPPPPPPk....", "....kp.PP.pk....", ".....k.pp.k....."], 12)
    return mult(g, (205, 232, 255))


def _crown_ghoul(g):
    t = top(g)
    return stamp(g, [".....gkggkg.....", "....kgGggGgk...."], t)


def _crown_bat(g):
    return stamp(g, [".....g.gg.g.....", ".....gGggGg....."], 0)


def _silencer(g):
    g = recolor(g, "m", "c")                            # ojos cian + marca de "silencio" sobre la cabeza
    g = mult(g, (120, 165, 255))
    g = recolor_rgb(g, (200 * 120 // 255, 40 * 165 // 255, 60 * 255 // 255), (150, 238, 255))
    return stamp(g, ["......c..c......", ".......cc......."], 0)


def _giant(g):
    t = top(g)                                          # cuernos de hueso + capa roja + ojos rojos
    g = stamp(g, ["....w......w....", "....kw....wk...."], t - 1 if t >= 1 else 0)
    g = stamp(g, [".R..............", "RRR.............", "RRR.............", "RRR.............", ".RR.............",
                  ".RR.............", "..R............."], t + 6)
    return g


def _bigbat(g):
    g = recolor(g, "m", "y")                            # ojos amarillos + cuernos de hueso
    g = mult(g, (255, 140, 150))
    g = recolor_rgb(g, (255 * 255 // 255, 232 * 140 // 255, 90 * 150 // 255), (255, 232, 90))
    return stamp(g, ["....w......w....", "....kw....wk...."], 0)


def _swarm(g):
    return mult(g, (255, 185, 205))


def _bghost(g):
    t = top(g)                                          # corona oscura + ojos rojos
    g = recolor(g, "y", "e")
    return stamp(g, [".....VkVVkV.....", "....kVvVVvVk...."], t)


def _bghost_kid(g):
    g = recolor(g, "y", "e")
    return mult(g, (255, 215, 255))


def build_all():
    """Devuelve {nombre: fotogramas} para todos los monstruos con rasgos propios."""
    gh, sk, bt = ghoul_frames(), skel_frames(), bat_frames()
    out = {
        "thief": _map(gh, _thief),
        "phantom": _map(gh, _phantom),
        "elite_ghoul": _map(gh, _crown_ghoul),
        "elite_skel": _map(sk, _crown_ghoul),
        "elite_bat": _map(bt, _crown_bat),
        "silencer": _map(bt, _silencer),
        "giant": _map(sk, _giant),
        "bigbat": _map(bt, _bigbat),
        "swarm": _map(bt, _swarm),
        "bghost": _map(gh, _bghost),
        "bghost_kid": _map(gh, _bghost_kid),
        "base_ghoul": gh, "base_skel": sk, "base_bat": bt,
    }
    # elites que ya tienen rasgos propios (ladron, silenciador, fantasma invisible): corona sobre su variante
    out["elite_thief"] = _map(out["thief"], _crown_ghoul)
    out["elite_phantom"] = _map(out["phantom"], _crown_ghoul)
    out["elite_silencer"] = _map(out["silencer"], _crown_bat)
    return out


def build_surfaces(pygame):
    """Convierte todas las cuadriculas en Surface (convert_alpha). Los de esqueleto llevan izquierda y derecha."""
    def surf(g):
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        for y in range(16):
            for x in range(16):
                c = g[y][x]
                if c:
                    s.set_at((x, y), c)
        return s.convert_alpha()

    res = {}
    for name, fr in build_all().items():
        if isinstance(fr, list):
            res[name] = [surf(g) for g in fr]
        elif "skel" in name or name == "giant":
            res[name] = {"right": {"idle": surf(fr["idle"]), "walk": [surf(g) for g in fr["walk"]]},
                         "left": {"idle": surf(flip(fr["idle"])), "walk": [surf(flip(g)) for g in fr["walk"]]}}
        else:
            res[name] = {"idle": surf(fr["idle"]), "walk": [surf(g) for g in fr["walk"]]}
    return res
