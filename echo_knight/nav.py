# -*- coding: utf-8 -*-
"""RONDA 6 - NAVEGACION: los monstruos saben subir, BAJAR y cruzar huecos entre plataformas.

Terrestres (fantasma, esqueleto, ladron...):
  Grafo de "nodos" = casillas (col, fila) donde se puede estar de pie (suelo solido o plataforma
  debajo, casilla libre encima). Aristas:
    WALK  caminar a la casilla contigua
    FALL  salir por el borde de una plataforma y caer hasta el primer suelo de esa columna
    JUMP  saltar hasta 2 filas hacia arriba, salvar un hueco de 2-3 casillas o bajar de un salto
  Se calcula un campo de distancias HACIA el destino (Dijkstra inverso, ~300 nodos) y cada monstruo
  elige la arista que mas le acerca. Los campos se guardan en el nivel (no cambia en toda la sala).

Voladores (murcielagos): campo de distancias por casillas libres (8 vecinos) para rodear muros.

Para poder usarlo solo hace falta que el monstruo tenga x, y (pies), vx, vy, hw, jump_cd, on_ground.
"""
import heapq
import math

from .config import *
from .physics import solid_hit

WALK, FALL, JUMP = 0, 1, 2
AIR_SPEED = 80.0            # velocidad horizontal maxima en el aire (control aereo de los monstruos)
INF = 1e9
MAX_UP = 2                  # filas que puede subir de un salto (32 px; el salto llega a ~43)


def _free(lv, c, r):
    return 0 <= c < COLS and 0 <= r < ROWS and not lv.blocks(c, r, False)


def _floor(lv, c, r):
    return lv.blocks(c, r, False) or lv.is_plat(c, r)


class NavGraph:
    """Grafo de casillas de pie de un nivel. nodes: set; edges: nodo -> [(destino, coste, tipo, dir, x_aterrizaje)]."""

    def __init__(self, lv):
        self.nodes = set()
        for r in range(1, ROWS - 1):
            for c in range(1, COLS - 1):
                if _free(lv, c, r) and _floor(lv, c, r + 1):
                    self.nodes.add((c, r))
        self.edges = {n: [] for n in self.nodes}
        self.rev = {n: [] for n in self.nodes}
        for (c, r) in self.nodes:
            out = self.edges[(c, r)]
            for d in (-1, 1):                                   # caminar / caer por el borde
                nc = c + d
                if not _free(lv, nc, r):
                    continue                                    # muro contiguo: solo se supera saltando
                if (nc, r) in self.nodes:
                    out.append(((nc, r), 1.0, WALK, d, nc * TILE + 8))
                    continue
                for rr in range(r + 1, ROWS - 1):               # sin suelo: cae hasta el primer suelo
                    if not _free(lv, nc, rr):
                        break
                    if (nc, rr) in self.nodes:
                        out.append(((nc, rr), 1.6 + 0.4 * (rr - r), FALL, d, nc * TILE + 8))
                        break
            for h in range(1, MAX_UP + 1):                      # saltar hacia arriba (h filas)
                if not _free(lv, c, r - h):
                    break
                for dx in (-2, -1, 0, 1, 2):
                    tn = (c + dx, r - h)
                    if tn not in self.nodes:
                        continue
                    s = 1 if dx > 0 else -1
                    if all(_free(lv, c + s * i, r - h) for i in range(abs(dx) + 1)):
                        out.append((tn, 3.0 + h + 0.5 * abs(dx), JUMP, s if dx else 0, tn[0] * TILE + 8))
            for s in (-1, 1):                                   # hueco de 2-3 casillas (a nivel o mas abajo)
                for dx in (2, 3):
                    for drop in range(0, 4):
                        tn = (c + s * dx, r + drop)
                        if tn not in self.nodes:
                            continue
                        if not all(_free(lv, c + s * i, r) and _free(lv, c + s * i, r - 1) for i in range(1, dx + 1)):
                            continue
                        if not all(_free(lv, c + s * dx, rr) for rr in range(r, r + drop + 1)):
                            continue
                        if any(_floor(lv, c + s * dx, rr + 1) for rr in range(r, r + drop)):
                            continue                            # una plataforma en medio: no se puede atravesar de arriba abajo
                        out.append((tn, 3.5 + 0.5 * dx + 0.3 * drop, JUMP, s, tn[0] * TILE + 8))
            for e in out:
                self.rev[e[0]].append(((c, r), e[1]))
        self.ok = set()                                         # saltos ya comprobados con la fisica real
        self.fields = {}                                        # destino -> {nodo: coste}
        self.air = {}                                           # casilla destino -> {casilla: coste}


def graph(lv):
    g = getattr(lv, "_nav", None)
    if g is None:
        g = lv._nav = NavGraph(lv)
    return g


def node_at(lv, x, y):
    """Nodo de pie en el punto (x, y=pies): el propio si lo es; si esta en el aire, el que hay debajo."""
    G = graph(lv)
    c, r = int(x // TILE), int((y - 0.01) // TILE)
    if (c, r) in G.nodes:
        return (c, r)
    for rr in range(r + 1, ROWS - 1):
        if not _free(lv, c, rr):
            return None
        if (c, rr) in G.nodes:
            return (c, rr)
    return None


def standing_node(lv, x, y, hw=5.0):
    """Nodo sobre el que esta de pie el cuerpo (sin buscar debajo); None si no esta apoyado en ninguno.
    Si el centro ya asoma al vacio pero el cuerpo aun se apoya en la casilla contigua, devuelve esa."""
    G = graph(lv)
    c, r = int(x // TILE), int((y - 0.01) // TILE)
    if (c, r) in G.nodes:
        return (c, r)
    best, bd = None, 1e9
    for nc in (c - 1, c + 1):
        if (nc, r) in G.nodes:
            d = abs(x - (nc * TILE + 8))
            if d < TILE / 2 + hw and d < bd:
                best, bd = (nc, r), d
    return best


def ground_field(lv, goal):
    G = graph(lv)
    f = G.fields.get(goal)
    if f is not None:
        return f
    if len(G.fields) > 40:
        G.fields.clear()
    dist = {goal: 0.0}
    heap = [(0.0, goal)]
    while heap:
        d, n = heapq.heappop(heap)
        if d > dist.get(n, INF):
            continue
        for (frm, cost) in G.rev.get(n, ()):
            nd = d + cost
            if nd < dist.get(frm, INF):
                dist[frm] = nd
                heapq.heappush(heap, (nd, frm))
    G.fields[goal] = dist
    return dist


def los(lv, x0, y0, x1, y1):
    """Linea de vision entre dos puntos (las plataformas no tapan; los muros si)."""
    dx, dy = x1 - x0, y1 - y0
    n = max(1, int(max(abs(dx), abs(dy)) // 4))
    for i in range(1, n):
        t = i / float(n)
        if lv.is_wall(int((x0 + dx * t) // TILE), int((y0 + dy * t) // TILE)):
            return False
    return True


# ---------------------------------------------------------------------------------------------
#  Control aereo: tras saltar o caer, el monstruo se dirige al centro de la casilla de aterrizaje
# ---------------------------------------------------------------------------------------------
def air_steer(m):
    tx = getattr(m, "air_tx", None)
    if tx is None or m.on_ground or m.stun > 0:
        return
    m.vx = max(-AIR_SPEED, min(AIR_SPEED, (tx - m.x) * 10.0))


def _sim_jump(lv, x, y, tx, d, target):
    """Simula un salto con la misma fisica que move_body (+ control aereo) y dice si aterriza en `target`."""
    vx, vy = d * AIR_SPEED * 0.8, -GHOUL_JUMP
    hw, h, dt = 5.0, 14.0, 1.0 / 60.0
    for _ in range(160):
        vx = max(-AIR_SPEED, min(AIR_SPEED, (tx - x) * 10.0))
        vy = min(vy + GRAVITY * dt, MAX_FALL)
        nx = x + vx * dt
        if not solid_hit(lv, nx, y, hw, h, False):
            x = nx
        ny = y + vy * dt
        if vy >= 0:
            row = int((ny - 0.01) // TILE)
            land = solid_hit(lv, x, ny, hw, h, False)
            if not land and ny > row * TILE and y <= row * TILE + 0.01:
                for c in range(int((x - hw) // TILE), int((x + hw - 0.01) // TILE) + 1):
                    if lv.is_plat(c, row):
                        land = True
                        break
            if land:
                return (int(x // TILE), row - 1) == target and abs(x - tx) < 9.0
            y = ny
        elif solid_hit(lv, x, ny, hw, h, False):
            vy = 0.0
        else:
            y = ny
    return False


def _check(lv, me, e):
    """Comprueba (una sola vez) que el salto e realmente funciona; si no, lo borra del grafo."""
    if e[2] != JUMP:
        return True
    G = graph(lv)
    key = (me, e[0], e[3])
    if key in G.ok:
        return True
    lx = me[0] * TILE + 8 + e[3] * 3.0
    y0 = (me[1] + 1) * TILE
    if all(_sim_jump(lv, lx + off, y0, e[4], e[3], e[0]) for off in (-2.5, 2.5)):
        G.ok.add(key)
        return True
    G.edges[me].remove(e)
    G.rev[e[0]] = [q for q in G.rev[e[0]] if q[0] != me]
    G.fields.clear()
    return False


def _execute(m, me, e, speed):
    """Velocidad horizontal (y salto si toca) para recorrer la arista e desde el nodo me."""
    to, cost, kind, d, land_x = e
    if kind == WALK:
        m.air_tx = None
        return d * speed
    if kind == FALL:
        m.air_tx = land_x                    # al salir del borde corrige hacia la casilla de aterrizaje
        return d * speed
    lx = me[0] * TILE + 8 + d * 3.0          # punto de salida: junto al borde (centro si es salto vertical)
    if abs(m.x - lx) > 2.5:
        m.air_tx = None
        return (1 if lx > m.x else -1) * min(speed, 40.0) if abs(m.x - lx) > 6 else (1 if lx > m.x else -1) * 18.0
    if m.jump_cd > 0:
        return 0.0
    m.vy = -GHOUL_JUMP
    m.jump_cd = 0.7
    m.air_tx = land_x
    m.on_ground = False
    return d * AIR_SPEED * 0.8


def walk_toward(m, g, gx, gy, speed):
    """Velocidad horizontal para que el monstruo terrestre `m` (en el suelo) vaya hacia (gx, gy).
    Si hay que saltar, lo hace (pone m.vy). Devuelve None si no hay camino (usar el metodo antiguo)."""
    lv = g.level
    me = standing_node(lv, m.x, m.y)
    goal = node_at(lv, gx, gy)
    if me is None or goal is None:
        return None
    if me == goal:
        m.air_tx = None
        dx = gx - m.x
        return (1 if dx > 0 else -1) * speed if abs(dx) > 3 else 0.0
    for _ in range(6):
        f = ground_field(lv, goal)
        if me not in f:
            return None
        best, bs = None, INF
        for e in graph(lv).edges[me]:
            s = e[1] + f.get(e[0], INF)
            if s < bs:
                best, bs = e, s
        if best is None:
            return None
        if _check(lv, me, best):
            return _execute(m, me, best, speed)
    return None


def flee_from(m, g, px, py, speed):
    """Como walk_toward pero ALEJANDOSE del punto (px, py): elige la arista que mas aumenta la distancia."""
    lv = g.level
    me = standing_node(lv, m.x, m.y)
    pn = node_at(lv, px, py)
    if me is None or pn is None:
        return None
    f = ground_field(lv, pn)
    here = f.get(me, 0.0)
    best, bs = None, -INF
    for e in graph(lv).edges[me]:
        s = f.get(e[0], here + 12.0) - 0.15 * e[1]
        if s > bs:
            best, bs = e, s
    if best is None or bs <= here - 0.9:
        return 0.0                           # acorralado: se queda
    if not _check(lv, me, best):
        return 0.0                           # ese salto no era posible: el grafo ya lo ha borrado
    return _execute(m, me, best, speed)


# ---------------------------------------------------------------------------------------------
#  Voladores
# ---------------------------------------------------------------------------------------------
_NB = ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
       (1, 1, 1.4), (1, -1, 1.4), (-1, 1, 1.4), (-1, -1, 1.4))


def air_field(lv, goal):
    G = graph(lv)
    f = G.air.get(goal)
    if f is not None:
        return f
    if len(G.air) > 40:
        G.air.clear()
    dist = {goal: 0.0}
    heap = [(0.0, goal)]
    while heap:
        d, n = heapq.heappop(heap)
        if d > dist.get(n, INF):
            continue
        for dc, dr, w in _NB:
            nb = (n[0] + dc, n[1] + dr)
            if not _free(lv, nb[0], nb[1]):
                continue
            if dc and dr and not (_free(lv, n[0] + dc, n[1]) and _free(lv, n[0], n[1] + dr)):
                continue                      # no corta esquinas
            nd = d + w
            if nd < dist.get(nb, INF):
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))
    G.air[goal] = dist
    return dist


def air_waypoint(lv, x, y, gx, gy):
    """Punto al que debe volar un murcielago en (x, y) para llegar a (gx, gy) rodeando los muros."""
    if los(lv, x, y, gx, gy):
        return gx, gy
    goal = (int(gx // TILE), int(gy // TILE))
    if not _free(lv, goal[0], goal[1]):
        return gx, gy
    f = air_field(lv, goal)
    cell = (int(x // TILE), int(y // TILE))
    if cell not in f:
        return gx, gy
    best, bs = cell, f[cell]
    for dc, dr, w in _NB:
        nb = (cell[0] + dc, cell[1] + dr)
        s = f.get(nb, INF)
        if s < bs:
            if dc and dr and not (_free(lv, cell[0] + dc, cell[1]) and _free(lv, cell[0], cell[1] + dr)):
                continue
            best, bs = nb, s
    if best == cell:
        return gx, gy
    return best[0] * TILE + 8, best[1] * TILE + 8
