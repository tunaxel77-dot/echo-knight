# -*- coding: utf-8 -*-
"""Clase Game: une todos los mixins y contiene el bucle principal."""
import array
import math
import random
import sys

import pygame
from .config import *
from .texts import *
from .sprites_data import *
from .sprites import *
from .lighting import *
from .physics import *
from .levels_data import *
from .level import *
from .entities import *
from .core import GameCore
from .flow import LevelFlowMixin
from .echoes import EchoMixin
from .combat import CombatMixin
from .skins import SkinsMixin
from .events import EventsMixin
from .update import UpdateMixin
from .render import RenderMixin
from .fx_draw import FxDrawMixin
from .hud import HudMixin
from .text_ui import TextUIMixin
from .screens import ScreensMixin
from .endless import EndlessMixin, parse_seed
from .cards import CardsMixin
from .threats import ThreatsMixin
from .characters import CharactersMixin
from .options import OptionsMixin
from .save import SaveMixin
from .music import MusicMixin
from .pause import PauseMixin
from .gamepad import GamepadMixin
from .motes import MotesMixin
from .achievements import AchievementsMixin
from .demo import DemoMixin
from .menu import MenuMixin
from .polish import PolishMixin
from .touch import TouchMixin


class Game(GameCore, TouchMixin, LevelFlowMixin, EndlessMixin, CardsMixin, ThreatsMixin, CharactersMixin, OptionsMixin, SaveMixin, AchievementsMixin, MusicMixin, PauseMixin, GamepadMixin, MotesMixin, DemoMixin, MenuMixin, PolishMixin, EchoMixin, CombatMixin, SkinsMixin, EventsMixin,
           UpdateMixin, RenderMixin, FxDrawMixin, HudMixin, TextUIMixin, ScreensMixin):
    """Juego completo. Cada mixin vive en su propio archivo."""

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.handle_events()
            self.update(dt)
            self.draw()
            self.draw_touch()
            pygame.display.flip()


def main():
    sound = "--sin-sonido" not in sys.argv
    Game(sound=sound, seed=parse_seed(sys.argv)).run()
