import sys, types, importlib.util, math
# pygame falso minimo: solo lo que usa touch.py en la logica de eventos
pg = types.ModuleType("pygame")
class Ev:
    def __init__(s, type, **kw): s.type = type; s.__dict__.update(kw)
pg.event = types.SimpleNamespace(Event=Ev)
pg.Event = Ev
for i, n in enumerate("KEYDOWN KEYUP FINGERDOWN FINGERMOTION FINGERUP APP_WILLENTERBACKGROUND QUIT".split()):
    setattr(pg, n, 100 + i)
pg.K_ESCAPE, pg.K_RETURN, pg.K_AC_BACK = 27, 13, 4000
pg.SCALED = pg.FULLSCREEN = 0
pg.font = types.SimpleNamespace(Font=lambda *a: None)
pg.draw = types.SimpleNamespace()
pg.Surface = object
sys.modules["pygame"] = pg
sys.path.insert(0, "" + __import__("os").path.dirname(__import__("os").path.abspath(__file__)) + "")
pkg = types.ModuleType("echo_knight"); pkg.__path__ = ["" + __import__("os").path.dirname(__import__("os").path.abspath(__file__)) + "/echo_knight"]; sys.modules["echo_knight"] = pkg
from echo_knight.touch import TouchMixin
import echo_knight.touch as T

class G(TouchMixin):
    def __init__(s):
        s.touch_mode = True; s.state = "play"; s.help = False; s.time = 10.0
        s.WS, s.HS, s.ox = 1493, 672, 170
        s.has_bow = s.anakin_mode = s.fighter_mode = s.tun_mode = s.dash_perk = s.has_shield = False
        s.touch_fingers = {}; s.touch_cache = {}
        s.touch_btns = s._touch_layout()
        s.keys = dict(left=[97], right=[100], jump=[119], shield=[115], sneak=[304], attack=[32], pulse=[113], fire=[102], dash=[114], interact=[101])
    def key_codes(s, a): return tuple(s.keys.get(a, []))
    def _kd(s, k): return Ev(pg.KEYDOWN, key=k)
    def _ku(s, k): return Ev(pg.KEYUP, key=k)
    def open_pause(s): s.state = "paused"

g = G()
def fd(fid, name=None, pos=None, kind=pg.FINGERDOWN):
    if name: b = g._btn_by_name(name); pos = (b["cx"], b["cy"])
    return Ev(kind, finger_id=fid, x=pos[0] / g.WS, y=pos[1] / g.HS)
def tr(*evs): 
    out = g.touch_translate(list(evs)); return [(e.type, getattr(e, "key", None)) for e in out]

# 1) layout: dentro de pantalla, sin solapes entre botones visibles
bs = [b for b in g.touch_btns]
for b in bs:
    assert b["cx"] - b["r"] >= 0 and b["cx"] + b["r"] <= g.WS and b["cy"] - b["r"] >= 0 and b["cy"] + b["r"] <= g.HS, b["name"]
for i, a in enumerate(bs):
    for c in bs[i + 1:]:
        if {a["name"], c["name"]} & {"back"}: continue    # "back" no coexiste con los demas
        d = math.hypot(a["cx"] - c["cx"], a["cy"] - c["cy"])
        assert d >= (a["r"] + c["r"]) * 0.95, ("solape", a["name"], c["name"], round(d), a["r"] + c["r"])
print("layout OK: %d botones, sin salirse ni solaparse" % len(bs))

# 2) mantener derecha
assert tr(fd(1, "right")) == []; assert g.touch_held == {"right"}
# 3) deslizar a izquierda sin soltar
tr(fd(1, "left", kind=pg.FINGERMOTION)); assert g.touch_held == {"left"}, g.touch_held
# 4) saltar con segundo dedo: KEYDOWN + held
assert tr(fd(2, "jump")) == [(pg.KEYDOWN, 119)]; assert g.touch_held == {"left", "jump"}
tr(fd(2, kind=pg.FINGERUP, name="jump")); assert g.touch_held == {"left"}
# 5) atacar / pulso = KEYDOWN de la tecla de KEYMAP
assert tr(fd(3, "attack")) == [(pg.KEYDOWN, 32)]; tr(fd(3, "attack", kind=pg.FINGERUP))
assert tr(fd(4, "pulse")) == [(pg.KEYDOWN, 113)]; tr(fd(4, "pulse", kind=pg.FINGERUP))
# 6) botones ocultos no responden
assert tr(fd(5, "fire")) == [] and 5 not in g.touch_fingers
assert tr(fd(6, "dash")) == [] and tr(fd(7, "shield")) == []
g.has_bow = True; g.has_shield = True
assert tr(fd(5, "fire")) == [(pg.KEYDOWN, 102)]
assert tr(fd(5, "fire", kind=pg.FINGERUP)) == [(pg.KEYUP, 102)], "soltar fuego = KEYUP (dispara)"
assert tr(fd(7, "shield")) == [] and "shield" in g.touch_held; tr(fd(7, "shield", kind=pg.FINGERUP))
# 7) fuego mantenido y cambio de estado: se suelta con KEYUP
tr(fd(8, "fire")); g.state = "dead"
assert (pg.KEYUP, 102) in tr(), "al morir se libera el disparo"; assert g.touch_held == frozenset() and not g.touch_fingers
# 8) pausa por boton, back de Android, segundo plano
g.state = "play"; tr(fd(1, "left", kind=pg.FINGERUP))
assert tr(fd(9, "pause")) == [(pg.KEYDOWN, 27)]; tr(fd(9, "pause", kind=pg.FINGERUP))
assert tr(Ev(pg.KEYDOWN, key=pg.K_AC_BACK)) == [(pg.KEYDOWN, 27)]
tr(Ev(pg.APP_WILLENTERBACKGROUND)); assert g.state == "paused"
# 9) pantallas: atras y toque en muerte
g.state = "options"; assert tr(fd(10, "back")) == [(pg.KEYDOWN, 27)]
g.state = "dead"; g.time = 10.0; tr(); g.time = 10.5
assert tr(fd(11, pos=(700, 300))) == [], "tap demasiado pronto no reinicia"
g.time = 11.2; assert tr(fd(11, pos=(700, 300))) == [(pg.KEYDOWN, 13)]
# 10) ayuda en juego: tocar la cierra
g.state = "play"; g.help = True; assert tr(fd(12, pos=(700, 300))) == [(pg.KEYDOWN, 13)]
# 11) teclas reasignadas se respetan
g.help = False; g.keys["attack"] = [120]; assert tr(fd(13, "attack")) == [(pg.KEYDOWN, 120)]
print("TODAS LAS PRUEBAS DE LOGICA TACTIL OK")
