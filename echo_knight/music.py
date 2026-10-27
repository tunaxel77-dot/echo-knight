# -*- coding: utf-8 -*-
"""Musica sintetizada (ronda 5.4): bucle de 3 capas (bajo, arpegio, percusion) sin archivos externos.
Cada capa suena en su propio canal reservado del mixer y se mezcla cambiando el volumen del canal.
Las funciones puras (music_layers, music_targets, step_volumes) se prueban sin pygame."""
import array
import time

import pygame
from .config import *
from .audio import synth

RATE = 22050


# ------------------------------------------------------------ logica pura
def music_layers(state, danger, n_monsters):
    """Ganancia objetivo (0..1) de (bajo, arpegio, percusion) segun el estado y la tension.
    Calma = solo bajo; peligro medio = + arpegio; peligro alto = + percusion."""
    if state == "dead":
        return (0.6, 0.0, 0.0)
    if state in MUSIC_CALM_STATES:
        return (1.0, 0.0, 0.0)
    high = danger >= MUSIC_DANGER_HIGH or n_monsters >= MUSIC_MON_HIGH
    mid = high or danger >= MUSIC_DANGER_MID or n_monsters >= MUSIC_MON_MID
    return (1.0, 1.0 if mid else 0.0, 1.0 if high else 0.0)


def music_targets(layers, vol_music, vol_master, muted):
    """Volumen final de cada canal: capa * vol_music * vol_master * MUSIC_GAIN (0 si esta silenciado)."""
    if muted:
        return [0.0] * len(layers)
    k = max(0.0, min(1.0, vol_music)) * max(0.0, min(1.0, vol_master)) * MUSIC_GAIN
    return [g * k for g in layers]


def step_volumes(cur, tgt, dt, rate=MUSIC_FADE):
    """Acerca cada volumen actual a su objetivo sin saltos (fundido). Devuelve una lista nueva."""
    step = max(0.0, rate * dt)
    return [c + max(-step, min(step, t - c)) for c, t in zip(cur, tgt)]


# ------------------------------------------------------------ generacion
def _mix(notes, n, cache):
    """notes = [(inicio_s, freq, dur_s, vol, tipo, decay, ruido)] -> array('h') de n muestras."""
    acc = [0] * n
    for t0, f, dur, vol, kind, decay, noise in notes:
        key = (f, dur, vol, kind, decay, noise)
        buf = cache.get(key)
        if buf is None:
            buf = cache[key] = synth(f, f * (0.4 if kind == "kick" else 1.0), dur, vol, "sine" if kind == "kick" else kind,
                                     decay, noise)
        i0 = int(t0 * RATE)
        m = min(len(buf), n - i0)
        for j in range(m):
            acc[i0 + j] += buf[j]
    out = array.array("h")
    out.extend(max(-32767, min(32767, v)) for v in acc)
    return out


def build_music_buffers():
    """Devuelve [bajo, arpegio, percusion] como array('h') de IGUAL longitud (el bucle no se desfasa)."""
    beat = 60.0 / MUSIC_BPM
    bar = 4 * beat
    n = int(bar * MUSIC_BARS * RATE)
    roots = (110.0, 87.31, 130.81, 98.0)                           # A2 F2 C3 G2
    chords = ((220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (261.63, 329.63, 392.0), (196.0, 246.94, 293.66))
    cache = {}
    bass, arp, perc = [], [], []
    for b in range(MUSIC_BARS):
        t = b * bar
        r, ch = roots[b % 4], chords[b % 4]
        bass.append((t, r, beat * 1.9, 0.55, "sine", 1.1, 0.0))
        bass.append((t + 2 * beat, r * 1.5 if b % 2 else r, beat * 1.9, 0.5, "sine", 1.1, 0.0))
        for i, idx in enumerate((0, 1, 2, 1, 0, 1, 2, 1)):          # corcheas
            f = ch[idx] * (2.0 if i in (3, 7) else 1.0)
            arp.append((t + i * beat / 2, f, beat * 0.45, 0.13, "square", 2.4, 0.0))
        for q in (0, 2):                                            # bombo en los tiempos 1 y 3
            perc.append((t + q * beat, 120.0, 0.2, 0.7, "kick", 2.0, 0.0))
        for q in (1, 3):                                            # caja en los tiempos 2 y 4
            perc.append((t + q * beat, 800.0, 0.11, 0.28, "noise", 2.0, 0.0))
        for i in range(8):                                          # hi-hat en corcheas
            perc.append((t + i * beat / 2, 6000.0, 0.035, 0.1, "noise", 1.5, 0.0))
    return [_mix(x, n, cache) for x in (bass, arp, perc)]


def build_music():
    """Genera los 3 pygame.mixer.Sound del bucle (una sola vez al arrancar)."""
    return [pygame.mixer.Sound(buffer=b.tobytes()) for b in build_music_buffers()]


# ------------------------------------------------------------ mixin
class MusicMixin:
    """Musica de fondo por capas. Respeta self.muted (tecla M, --sin-sonido), vol_music y vol_master."""
    music_ch = None
    music_snd = None
    music_cur = None
    _room_open = None

    def init_music(self, sound=True):
        self.music_ch, self.music_snd, self.music_cur = [], [], [0.0] * MUSIC_LAYERS
        if not sound:
            return False
        try:
            if pygame.mixer.get_num_channels() < 16:
                pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(MUSIC_LAYERS)             # los efectos no pueden robar los canales 0..2
            self.music_snd = build_music()
            for i, snd in enumerate(self.music_snd):
                ch = pygame.mixer.Channel(i)
                ch.play(snd, loops=-1)
                ch.set_volume(0.0)                              # (play reinicia el volumen: se fija despues)
                self.music_ch.append(ch)
            return True
        except Exception:
            self.music_ch, self.music_snd = [], []
            return False

    def music_tick(self, dt):
        """Llamar cada fotograma desde update(): fundido suave hacia las capas que toca oir."""
        if not self.music_ch:
            return
        layers = music_layers(self.state, getattr(self, "danger", 0.0), len(getattr(self, "monsters", ())))
        tgt = music_targets(layers, self.vol_music, self.vol_master, getattr(self, "muted", False))
        self.music_cur = step_volumes(self.music_cur, tgt, dt)
        for ch, v in zip(self.music_ch, self.music_cur):
            try:
                ch.set_volume(v)
            except Exception:
                pass

    def room_open_fraction(self):
        """Fraccion de casillas sin muro de la sala actual (se cachea por sala)."""
        lv = getattr(self, "level", None)
        if lv is None:
            return 0.0
        if self._room_open is None or self._room_open[0] is not lv:
            cells = [c for row in lv.grid for c in row]
            self._room_open = (lv, sum(1 for c in cells if c != "#") / max(1, len(cells)))
        return self._room_open[1]

    def pulse_sfx_name(self):
        """El super eco suena mas grave en las salas grandes."""
        try:
            return "pulse_deep" if self.room_open_fraction() >= MUSIC_BIG_ROOM else "pulse"
        except Exception:
            return "pulse"
