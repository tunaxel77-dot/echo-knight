# -*- coding: utf-8 -*-
"""Mapas de pixeles (pixel art): caballero, monstruos, objetos, skins."""


PAL = {
    "k": (18, 16, 26), "s": (206, 214, 230), "S": (132, 142, 170), "d": (78, 84, 112),
    "r": (190, 36, 48), "R": (112, 20, 36), "g": (246, 206, 72), "G": (176, 128, 32),
    "f": (234, 184, 142), "b": (116, 74, 42), "w": (240, 238, 230),
    "p": (96, 74, 120), "P": (150, 128, 176), "y": (255, 232, 90), "m": (200, 40, 60),
}

KNIGHT_DOWN = [
    "................",
    ".......rr.......",
    ".....kkkkkk.....",
    "....kssssssk....",
    "....ksSSSSsk....",
    "....kskkkkSk....",
    "....kSSSSSSk....",
    ".....kkkkkk.....",
    "...kkSSSSSSkk...",
    "..kdSrrrrrrSdk..",
    "..kdSrrggrrSdk..",
    "..kfdSrrrrSdfk..",
    "...kkSrrrrSkk...",
    "....kbbbbbbk....",
    "....kSSkkSSk....",
    "....kkk..kkk....",
]
KNIGHT_RIGHT = [
    "................",
    "........rr......",
    ".....kkkkkk.....",
    "....kssssssk....",
    "....kssSSSsk....",
    "....kSSSkkkk....",
    "....kSSSSSSk....",
    ".....kkkkkk.....",
    "....kkSSSSkk....",
    "...kdSrrrrSkkk..",
    "...kdSrrrrkGGk..",
    "...kfSrrrrkGgk..",
    "....kSrrrrkGGk..",
    ".....kbbbbbkk...",
    ".....kSSkSSk....",
    ".....kkk.kkk....",
]
GHOUL = [
    "................",
    ".....kkkkkk.....",
    "....kPPPPPPk....",
    "...kPPPPPPPPk...",
    "...kPyyPPyyPk...",
    "...kPPPPPPPPk...",
    "...kPPmwmwmPk...",
    "....kPPPPPPk....",
    "..kkkpppppkkk...",
    ".kPkppppppkPk...",
    ".kPkppppppkPk...",
    ".kwk.pppp.kwk...",
    "....kppppppk....",
    "....kpp..ppk....",
    "....kkk..kkk....",
    "................",
]
# murcielago de las catacumbas (mismo estilo y paleta que el fantasma)
BAT_A = [
    "................",
    "..k..........k..",
    ".kPk...kk...kPk.",
    ".kPPk.kppk.kPPk.",
    "kPPpPkkppkkPpPPk",
    "kPk.kpmppmpk.kPk",
    "k....kppppk....k",
    ".....kpwppwk....",
    "......kkkkkk....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]
BAT_B = [
    "................",
    "................",
    ".......kk.......",
    "......kppk......",
    ".....kppppk.....",
    "..kk.kpmpmk.kk..",
    ".kPPkkppppkkPPk.",
    "kPPpPkpwppwkPpPk",
    "kPpkPPkkkkPPkpPk",
    "kk..kPPkkPPk..kk",
    "......kk.kk.....",
    "................",
    "................",
    "................",
    "................",
    "................",
]
# fotograma intermedio (alas horizontales) para un aleteo mas fluido
BAT_C = [
    "................",
    "................",
    ".......kk.......",
    "..k...kppk...k..",
    ".kPk.kppppk.kPk.",
    "kPPPkkpmppmkPPPk",
    "k...kkpwppwk...k",
    "......kkkkkk....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]
# esqueleto arquero (mira a la derecha; se voltea para la izquierda)
SKEL = [
    "................",
    ".....kkkkkk.....",
    "....kwwwwwwk....",
    "....kwrwwrwk....",
    "....kwwwwwwk....",
    ".....kwkwwk.....",
    "......kkkk......",
    "....kkwwwwkkb...",
    "...kwkwwwwkwbb..",
    "...kwk.ww.kwbGb.",
    "....kkwwwwkkbGb.",
    ".....kwkwwk.bb..",
    ".....kwwwwk.b...",
    ".....kw..wk.....",
    ".....kk..kk.....",
    "................",
]
KEY = [
    "................",
    "................",
    "....kkkk........",
    "...kggggk.......",
    "..kgGkkGgk......",
    "..kgk..kgk......",
    "..kgGkkGgk......",
    "...kggggkk......",
    "....kkkgGk......",
    ".......gGk......",
    ".......gGkkk....",
    ".......gGggk....",
    ".......gGkkk....",
    ".......gGggk....",
    "........kkk.....",
    "................",
]
CHEST = [
    "................",
    "................",
    "................",
    "................",
    "...kkkkkkkkkk...",
    "..kbbbbbbbbbbk..",
    "..kbGbbbbbbGbk..",
    "..kGGGGGGGGGGk..",
    "..kbbbbggbbbbk..",
    "..kbbbbgkgbbbk..",
    "..kbbbbggbbbbk..",
    "..kbGbbbbbbGbk..",
    "..kbbbbbbbbbbk..",
    "..kkkkkkkkkkkk..",
    "................",
    "................",
]
CHEST_OPEN = [
    "................",
    "................",
    "...kkkkkkkkkk...",
    "..kbGbbbbbbGbk..",
    "..kbbbbbbbbbbk..",
    "..kkkkkkkkkkkk..",
    "..kyyyyyyyyyyk..",
    "..kywyyyyywyyk..",
    "..kyyyyyyyyyyk..",
    "..kGGGGGGGGGGk..",
    "..kbbbbbbbbbbk..",
    "..kbGbbbbbbGbk..",
    "..kbbbbbbbbbbk..",
    "..kkkkkkkkkkkk..",
    "................",
    "................",
]
HEART = ["..##.##..", ".#######.", ".#######.", "..#####..", "...###...", "....#...."]

# --- piernas / pies alternativos para las animaciones (fotogramas extra) ---
KN_LEGS_A = [".....kSSk..kSSk.", ".....kkk....kkk."]     # paso largo (adelante)
KN_LEGS_A2 = ["....kSSk..kSSk..", "....kkk....kkk.."]    # paso largo (atras)
KN_LEGS_T = ["......kSSSk.....", "......kkkkk....."]     # piernas juntas
KN_LEGS_UP = [".....kSSSSSk....", "......kkkkk....."]    # salto: piernas recogidas
GH_LEGS_A = ["...kpp....ppk...", "...kkk....kkk...", "................"]
GH_LEGS_T = ["....kppppppk....", "....kkkkkkkk....", "................"]
SK_LEGS_A = ["....kw....wk....", "....kk....kk....", "................"]
SK_LEGS_T = ["......kwwk......", "......kkkk......", "................"]

# Skin ANAKIN: el caballero con tunica negra de Jedi oscuro (cara visible, sin casco)
AK_PAL = {
    "r": (30, 28, 40), "S": (52, 48, 64), "d": (40, 36, 50), "G": (112, 112, 126),
    "g": (190, 190, 204), "b": (96, 62, 38), "k": (10, 8, 14),
}
AK_RIGHT = list(KNIGHT_RIGHT)
AK_RIGHT[3] = "....kbbbbbbk...."
AK_RIGHT[4] = "....kbbbfffk...."
AK_RIGHT[5] = "....kbbffkfk...."
AK_RIGHT[6] = "....kffffffk...."
AK_FORCE_ROWS = list(AK_RIGHT)
AK_FORCE_ROWS[10] = "...kdSrrrrSffffk"          # brazo extendido al frente (usando la FUERZA)
AK_FORCE_ROWS[11] = "...kfSrrrrkkkkk."
AK_FORCE_ROWS[12] = "....kSrrrrk....."

# --- DARTH VADER: sprites copiados TAL CUAL de la imagen de referencia (31 x 30 celdas).
#     Se reducen a VD_W x VD_H pixeles al cargar. "u"/"x" = luces del panel del pecho.
VD_W, VD_H = 21, 20
VD_LEG0 = 27                      # primera fila de las piernas (para los pasos)
VD_PAL = {
    "0": (14, 14, 18), "1": (14, 14, 18), "2": (14, 14, 18), "3": (14, 14, 18), "4": (18, 18, 22),
    "5": (34, 34, 40), "6": (44, 44, 52), "7": (58, 58, 66), "8": (72, 72, 82), "9": (92, 92, 104),
    "a": (118, 118, 130), "b": (152, 152, 160), "u": (104, 112, 215), "x": (214, 96, 70),
}
VD_IDLE = [
    "...............................",
    "...........43335...............",
    "..........3b978b4..............",
    ".........3b97888b4.............",
    ".........2897886b0.............",
    ".........2a9aa6660.............",
    ".........06a64a660.............",
    "........39b79b3a884............",
    "........077b774a884............",
    "........079b9760a884...........",
    "........0b9b9b60a884...........",
    ".........00000008884...........",
    "..........096660333............",
    "........339898984093...........",
    ".......038b8b8b8a8494..........",
    ".......00698989666394..........",
    ".......0066abu86363992.........",
    "......40606a8x86066093.........",
    "......43606aba86066093.........",
    "......43a36666660a98093........",
    "......4a90b8.8b4a998393........",
    "......49326666649498093........",
    "......466056865a3662093........",
    "......43328505888406093........",
    "......466388463884660994.......",
    "......4662a84628a3660994.......",
    ".......000a83338a0000994.......",
    ".........2860.0680..000........",
    ".........2860.2680.............",
    "........48663.26684............",
]
VD_FORCE = [      # brazo extendido (la FUERZA)
    "...............................",
    "...........00035...............",
    "..........0b978b0..............",
    ".........0b97888b3.............",
    ".........0897886b0.............",
    ".........3a9aa6660.............",
    ".........06a63a660.............",
    "........29b79b3a883............",
    "........377b774a880............",
    "........079b9764a880...........",
    "........0b9b9.74a880...........",
    "00..02...00000008880...........",
    "2a03a90...396660000............",
    "39890900038898980090...........",
    "2a890968a8b8b8b8a8390..........",
    "3899886766a8a8a666390..........",
    ".0000666666bbu86064990.........",
    ".....000006a8x86066490.........",
    "......00606bba86066390.........",
    "......06306666660a98492........",
    "......3060b8b8b0a998390........",
    "......06306666609098390........",
    "......306056865a0660492........",
    "......06338545888306390........",
    "......066388063880664994.......",
    "......0660a80638a0663993.......",
    ".......003a80038a3333993.......",
    ".........0862.0683..343........",
    ".........0862.0682.............",
    "........08660.06680............",
]


# ----------------------------------------------------------------------------
#  RONDA 4: personajes. Cada sprite usa sus propias letras (se definen en su paleta);
#  las filas 14-15 (piernas) las pone build_knight_anim con "S" y "k".
# ----------------------------------------------------------------------------
MAGE_RIGHT = [
    "................",
    ".......kk..oO...",
    "......khhk.Oo...",
    ".....khhhhk.b...",
    "..kHHHHHHHHkb...",
    "....kffkfk..b...",
    "....kwwwwk..b...",
    "...kkTtttTkkb...",
    "..kTTttttTTkf...",
    "..kTttttttTkb...",
    "..kTttyyttTkb...",
    "..kTttttttTkb...",
    "..kTttttttTkb...",
    "..kkTTTTTTkkb...",
    "................",
    "................",
]
MAGE_PAL = {
    "S": (44, 70, 160), "h": (70, 104, 214), "H": (40, 62, 150), "f": (234, 184, 142), "w": (240, 238, 230),
    "t": (84, 124, 232), "T": (48, 76, 170), "y": (255, 224, 90), "b": (120, 78, 44),
    "o": (110, 200, 255), "O": (210, 245, 255),
}
ROGUE_RIGHT = [
    "................",
    ".....kkkkk......",
    "....khhhhhk.....",
    "...khhhhhhhk....",
    "...khhHHHHhk....",
    "...khHffkfHk....",
    "...khHffffHk....",
    "....kkHHHHkk....",
    "...kcCCCCCCckk..",
    "..kcCCCCCCCCck..",
    "..kcCCCCCCCfdddd",
    "..kcCCCCCCCCck..",
    "...kcCCCCCCck...",
    "....kllllllk....",
    "................",
    "................",
]
ROGUE_PAL = {
    "S": (50, 66, 54), "h": (58, 150, 84), "H": (30, 78, 50), "f": (234, 184, 142),
    "c": (22, 36, 28), "C": (44, 84, 58), "l": (120, 84, 46), "d": (214, 224, 236),
}
TANK_RIGHT = [
    "................",
    "......oo........",
    ".....kkkkk......",
    "....kaaaaak.....",
    "....kaAAAAk.....",
    "....kAAvvvk.....",
    "....kAAAAAk.....",
    "...kkaAAAakk....",
    "..kaaAAAAAakkkk.",
    "..kaBAAAAAkeeek.",
    "..kaBAAAAAkegek.",
    "..kaBAAAAAkeeek.",
    "...kkBAAABkkeek.",
    "....kBBBBBkkkk..",
    "................",
    "................",
]
TANK_PAL = {
    "S": (88, 92, 106), "a": (176, 180, 192), "A": (120, 124, 138), "B": (70, 72, 86),
    "v": (255, 190, 70), "o": (230, 110, 40), "e": (110, 124, 168), "g": (246, 206, 72),
}
CHAR_SPRITES = {
    "mage": (MAGE_PAL, MAGE_RIGHT),
    "rogue": (ROGUE_PAL, ROGUE_RIGHT),
    "tank": (TANK_PAL, TANK_RIGHT),
}


# ----------------------------------------------------------------------------
#  SKIN SECRETA "luchador": peleador ORIGINAL de tonos rojizos (cinta naranja, vendas en las manos).
#  Tres poses: reposo, punetazo recto con la mano adelantada y guardia de boxeador.
# ----------------------------------------------------------------------------
FT_PAL = {
    "S": (110, 34, 44), "h": (44, 26, 24), "b": (236, 120, 52), "f": (226, 176, 136), "r": (196, 62, 58),
    "R": (128, 34, 46), "w": (232, 196, 150), "o": (226, 92, 44),
}
FT_IDLE = [
    "................",
    "....k.kkk.k.....",
    "....khhhhhhk....",
    "....kbbbbbbk....",
    "....kffffffk....",
    "....kfffkfk.....",
    "....kffffffk....",
    ".....kffffk.....",
    "...kkrrrrrrkk...",
    "..kfrrrrrrrrfk..",
    "..kfrrRRRRrrfk..",
    "..kwwrrrrrrwwk..",
    "...kkRrrrrRkk...",
    "....kRRRRRRk....",
    "................",
    "................",
]
FT_PUNCH = list(FT_IDLE)                      # puñetazo recto con la mano adelantada
FT_PUNCH[9] = "..kfrrrrrrrkkk.."
FT_PUNCH[10] = "..kfrrRRRRrkffww"
FT_PUNCH[11] = "..kwrrrrrrrkkkk."
FT_CLAP = list(FT_IDLE)                       # aplauso: las dos manos juntas al frente
FT_CLAP[9] = "..kfrrrrrrrkkww."
FT_CLAP[10] = "..kfrrRRRRrkffww"
FT_CLAP[11] = "..kwrrrrrrrkkww."
FT_SLAM = list(FT_IDLE)                       # impacto: puño clavado en el suelo
FT_SLAM[9] = "..kfrrrrrrrkkk.."
FT_SLAM[10] = "..kfrrRRRRrkwwk."
FT_SLAM[11] = "..kwrrrrrrrkffk."
FT_SLAM[12] = "...kkRrrrrRkkwwk"
FT_SLAM[13] = "....kRRRRRRkkffk"
FT_GUARD = list(FT_IDLE)                      # guardia de boxeador: guantes junto a la cara
FT_GUARD[5] = "....kfffkfkoo..."
FT_GUARD[6] = "....kffffffkoo.."
FT_GUARD[7] = ".....kffffkkoo.."
FT_GUARD[11] = "..kfrrrrrrrrfk.."
