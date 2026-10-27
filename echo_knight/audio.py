# -*- coding: utf-8 -*-
"""Sonidos sintetizados (sin archivos externos)."""
import array
import math
import random
import sys

import pygame


def synth(f0, f1, dur, vol=0.3, kind="sine", decay=2.5, noise=0.0, rate=22050):
    n = int(rate * dur)
    buf = array.array("h")
    phase = 0.0
    for i in range(n):
        t = i / n
        f = f0 + (f1 - f0) * t
        phase += 2 * math.pi * f / rate
        if kind == "sine":
            v = math.sin(phase)
        elif kind == "square":
            v = 1.0 if math.sin(phase) > 0 else -1.0
        else:
            v = random.uniform(-1, 1)
        if noise:
            v += random.uniform(-1, 1) * noise
        v *= (1 - t) ** decay * vol
        buf.append(int(max(-1.0, min(1.0, v)) * 32767))
    return buf


def to_sound(buf):
    return pygame.mixer.Sound(buffer=buf.tobytes())


def build_sounds():
    s = {}
    s["step"] = to_sound(synth(640, 560, 0.09, 0.16, decay=3))
    s["jump"] = to_sound(synth(260, 520, 0.12, 0.2, decay=2))
    s["slash"] = to_sound(synth(900, 200, 0.16, 0.25, kind="noise", decay=2))
    s["pulse"] = to_sound(synth(220, 900, 0.55, 0.28, decay=1.8))
    s["pulse_deep"] = to_sound(synth(110, 520, 0.8, 0.32, decay=1.6))      # super eco en una sala grande: mas grave y largo
    s["hit"] = to_sound(synth(190, 80, 0.14, 0.3, kind="square", decay=2))
    s["hurt"] = to_sound(synth(130, 55, 0.28, 0.35, kind="square", decay=1.5, noise=0.4))
    s["block"] = to_sound(synth(520, 340, 0.16, 0.35, kind="square", decay=1.6))
    s["locked"] = to_sound(synth(95, 70, 0.22, 0.4, decay=1.5))
    s["heart"] = to_sound(synth(58, 44, 0.16, 0.6, decay=2))
    s["bow"] = to_sound(synth(620, 240, 0.12, 0.22, kind="square", decay=2.5))
    s["dash"] = to_sound(synth(380, 1250, 0.2, 0.22, kind="noise", decay=2.2))
    sup = array.array("h")
    sup.extend(synth(180, 1500, 0.28, 0.3, kind="noise", decay=1.6))
    sup.extend(synth(1500, 400, 0.22, 0.25, decay=2.0))
    s["super"] = to_sound(sup)
    arp = array.array("h")
    for f in (523, 659, 784, 1046):
        arp.extend(synth(f, f, 0.09, 0.25, decay=1.2))
    s["key"] = to_sound(arp)
    win = array.array("h")
    for f in (392, 523, 659, 784):
        win.extend(synth(f, f, 0.14, 0.28, kind="square", decay=1.0))
    s["win"] = to_sound(win)
    return s
