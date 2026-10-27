# -*- coding: utf-8 -*-
"""Generador de salas aleatorias para el MODO INFINITO.

generate_room(seed, room_no) devuelve un spec compatible con Level (igual que arena()).
Las plataformas se colocan por pisos (filas 8, 6, 4, 2 del diseno original) y cada una
queda siempre al alcance de otra mas baja, asi que ninguna sala es imposible.
"""
import random

from .config import *
from .levels_data import arena

TIERS = (8, 6, 4, 2)               # filas (coordenadas originales); cada piso sube 32 px
COL_MIN, COL_MAX = 1, 18           # columnas utiles (coordenadas originales)
ROOM_NAMES = ["Sala del Eco", "Cripta Cambiante", "Galería Hueca", "Cámara Susurrante",
              "Pozo Sin Fondo", "Nave Rota", "Osario Vivo", "Corredor del Abismo",
              "Cripta Inquieta", "Sótano Maldito"]
MAX_GAP = 2                        # hueco horizontal maximo entre un piso y el de abajo


def _reachable(seg, lower):
    """True si el segmento 'seg' puede alcanzarse saltando desde algun segmento de 'lower'."""
    c0, c1 = seg
    return any(l0 - MAX_GAP <= c1 and l1 + MAX_GAP >= c0 for (l0, l1) in lower)


def make_layout(rnd):
    """Lista de plataformas [(fila, c0, c1), ...] en coordenadas originales."""
    plats = []
    lower = [(COL_MIN, COL_MAX)]                 # el suelo cubre todo
    for r in TIERS:
        segs = []
        for _ in range(rnd.randint(1, 3)):
            ln = rnd.randint(3, 6)
            c0 = rnd.randint(COL_MIN, COL_MAX - ln + 1)
            c1 = c0 + ln - 1
            if any(c0 <= s1 + 1 and c1 >= s0 - 1 for (s0, s1) in segs):
                continue                          # no pegar segmentos del mismo piso
            if _reachable((c0, c1), lower):
                segs.append((c0, c1))
        if not segs:                              # garantiza al menos una plataforma por piso
            for _ in range(20):
                ln = rnd.randint(3, 6)
                c0 = rnd.randint(COL_MIN, COL_MAX - ln + 1)
                if _reachable((c0, c0 + ln - 1), lower):
                    segs.append((c0, c0 + ln - 1))
                    break
        if not segs:
            break
        for (c0, c1) in segs:
            plats.append((r, c0, c1))
        lower = segs
        if r <= 4 and rnd.random() < 0.25:        # a veces la sala es mas baja
            break
    return plats


MOD_INFO = {
    "lowgrav": ("GRAVEDAD BAJA", "Saltas mucho más alto."),
    "dark": ("OSCURIDAD TOTAL", "Las antorchas no se encienden ni con la puerta abierta."),
    "fast": ("MONSTRUOS FRENÉTICOS", "Los monstruos van un 30% más rápido."),
    "vents": ("TORMENTA DE AIRE", "Hay el doble de corrientes de aire."),
}
MODS = tuple(MOD_INFO)


def is_shop_room(room_no):
    """Sala tienda: cada SHOP_EVERY salas (indices 0-based 5, 10, 15...). 0 = desactivadas."""
    return bool(SHOP_EVERY) and room_no > 0 and room_no % SHOP_EVERY == 0


BOSS_INFO = (
    ("ESQUELETO GIGANTE", "Abanico y lluvia de flechas, saltos con ondas, embestidas e invoca esqueletos."),
    ("EL ENJAMBRE", "Si dañas a uno se funden: picados, chillido sónico, barridos, bombardeo e invocación."),
    ("FANTASMA PARTIDO", "Se teletransporta tras de ti, lanza espíritus rebotantes y al morir se divide en dos."),
)


def is_boss_room(room_no):
    """Sala de jefe: indices 4, 9, 14... (justo antes de la tienda). 0 = sin jefes."""
    return bool(BOSS_EVERY) and room_no % BOSS_EVERY == BOSS_EVERY - 1


def boss_index(room_no):
    """Que jefe toca (rota entre los 3 segun el numero de sala)."""
    return (room_no // BOSS_EVERY) % len(BOSS_INFO)


def pick_modifier(seed, room_no):
    """Modificador de la sala (o None). Depende solo de (semilla, sala): misma semilla = mismas salas."""
    if is_shop_room(room_no):
        return None
    rnd = random.Random(seed * 1000003 + room_no * 9176 + 17)
    return rnd.choice(MODS) if rnd.random() < MOD_CHANCE else None


def make_traps(rnd, plats, vents, room_no):
    """Tramos de pinchos [(fila, c0, c1), ...] en coordenadas originales (10 = suelo).
    Reglas: nunca en el punto de salida (cols 1-5 del suelo) ni delante de la puerta (cols >= 15 del suelo),
    nunca en los bordes de una plataforma (siempre queda 1 casilla libre a cada lado) y no sobre corrientes de aire."""
    if room_no < TRAP_FROM:
        return []
    want = min(TRAP_MAX, 1 + (room_no - TRAP_FROM) // 3)
    vcols = set()
    for (c, _h) in vents:
        vcols.update((c - 1, c, c + 1, c + 2))
    cands = []                                     # (fila, c0, c1) posibles de 2 casillas
    for (r, a, b) in plats:
        for c0 in range(a + 1, b - 1):             # deja >= 1 casilla libre a cada lado
            if c0 + 1 <= b - 1 and c0 not in vcols and c0 + 1 not in vcols:
                cands.append((r, c0, c0 + 1))
    for c0 in range(6, 14):                        # suelo: lejos del inicio y de la puerta
        if c0 not in vcols and c0 + 1 not in vcols:
            cands.append((10, c0, c0 + 1))
    rnd.shuffle(cands)
    out = []
    for cand in cands:
        if len(out) >= want:
            break
        if all(not (cand[0] == o[0] and cand[1] <= o[2] + 3 and cand[2] >= o[1] - 3) for o in out):
            out.append(cand)
    return out


def generate_room(seed, room_no, mod=None):
    rnd = random.Random(seed)
    plats = make_layout(rnd)
    vents = []
    if rnd.random() < 0.35:                       # corriente de aire ocasional
        vents.append((rnd.randint(2, 15), rnd.choice((5, 6, 7))))
    base_vents = list(vents)                      # los pinchos solo evitan estas: el diseno no depende del modificador
    if mod == "vents":                            # el doble de corrientes (minimo 2)
        target = max(2, len(vents) * 2)
        for _ in range(40):
            if len(vents) >= target:
                break
            col = rnd.randint(2, 15)
            if all(abs(col - v[0]) > 2 for v in vents):
                vents.append((col, rnd.choice((5, 6, 7))))
    name = "%s %d" % (rnd.choice(ROOM_NAMES), room_no + 1)
    traps = [] if (is_boss_room(room_no) or is_shop_room(room_no)) else make_traps(random.Random(seed * 7 + room_no * 131 + 3), plats, base_vents, room_no)
    return arena(name, plats=plats, ghouls=[], bats=[], key=None, start=(2, 9),
                 vents=vents, ledges=False, traps=traps)


def generate_shop(seed, room_no):
    """Sala tienda: suelo plano, sin monstruos (los objetos los coloca endless.py)."""
    return arena("Tienda del Eco %d" % (room_no + 1), plats=[], ghouls=[], bats=[], key=None,
                 start=(2, 9), vents=[], ledges=False)


def spawn_points(level):
    """(suelo, aire): casillas libres para monstruos terrestres y voladores."""
    g = level.grid
    ground, air = [], []
    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if g[r][c] != ".":
                continue
            below = g[r + 1][c]
            if below in "#=":
                ground.append((c, r))
            if 2 <= r <= ROWS - 4:
                air.append((c, r))
    return ground, air
