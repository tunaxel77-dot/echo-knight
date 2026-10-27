# -*- coding: utf-8 -*-
"""Constantes de ajuste, colores y tipos de onda. Toca aqui para balancear el juego."""


# ----------------------------------------------------------------------------
#  CONFIGURACION
# ----------------------------------------------------------------------------
TILE = 16                       # tile logico 16x16
COLS, ROWS = 24, 13             # arenas ampliadas (antes 20 x 11)
DX, DY = (COLS - 20) // 2, ROWS - 11     # desplazamiento de los disenos originales 20x11
HUD_H = 16
MAP_W, MAP_H = COLS * TILE, ROWS * TILE      # 384 x 208
LW, LH = MAP_W, MAP_H + HUD_H                # 384 x 224 (resolucion logica)
FPS = 60
AMBIENT = (0, 0, 0)             # oscuridad total
PLAYER_GLOW = 0.30              # brillo minimo alrededor del caballero (0 = nada)
GLOW_R = 20                     # radio de ese brillo
BEAM_W, BEAM_H = 76, 48         # haz de luz frontal
GRACE_T = 2.5                   # segundos que los monstruos tardan en despertar
DIAG_BOOST = 1.3                # impulso horizontal del salto diagonal

# fisica
GRAVITY = 720.0
MAX_FALL = 330.0
JUMP_V = 255.0                  # ~45 px de altura maxima (plataformas a 32 px)
WALK_SPEED = 68.0
SNEAK_SPEED = 34.0
SHIELD_MULT = 0.45
GHOUL_CHASE = 46.0
GHOUL_WANDER = 22.0
GHOUL_JUMP = 250.0
BAT_CHASE = 46.0
BAT_IDLE = 16.0

STEP_DIST = 15.0                # distancia entre ecos de pasos
MAX_HP = 3
ATTACK_RANGE = 27.0
PULSE_COOLDOWN = 3.2
ATTACK_COOLDOWN = 0.45
BOW_COOLDOWN = 0.55
ARROW_SPEED = 240.0
ARROW_GRAV = 55.0
DASH_SPEED = 330.0              # dash secreto (modo TUN)
DASH_TIME = 0.19
DASH_COOLDOWN = 0.55
WINDUP_T = 0.07                 # anticipacion del tajo (retroceso de la espada)
LAND_T = 0.16                   # duracion de la compresion al aterrizar
SUPER_CHARGE_T = 2 * BOW_COOLDOWN   # tiempo de carga del super disparo (doble que un disparo normal)
SUPER_SPEED = 520.0             # el super disparo cruza el mapa casi en linea recta

GOLD = (246, 206, 72)
PARCH = (232, 220, 190)
RED = (220, 70, 70)
CYAN = (150, 225, 255)

# Tipos de onda: color, radio maximo, velocidad (px logicos / s)
WAVES = {
    "step":   dict(color=(115, 160, 255), max_r=50,  speed=88),
    "attack": dict(color=(255, 186, 96),  max_r=95,  speed=175),
    "pulse":  dict(color=(170, 235, 255), max_r=520, speed=250, bw=12.0, k=6, after=0.5),
    "hurt":   dict(color=(255, 70, 60),   max_r=46,  speed=120),
    "key":    dict(color=(255, 215, 90),  max_r=95,  speed=140),
    "locked": dict(color=(255, 90, 70),   max_r=42,  speed=100),
    "death":  dict(color=(205, 100, 255), max_r=55,  speed=110),
    "block":  dict(color=(70, 140, 255),  max_r=62,  speed=135),
    "menu":   dict(color=(150, 200, 255), max_r=175, speed=85),
    "bounce": dict(color=(120, 205, 240), max_r=55,  speed=120, bw=6.0, k=4),
    "aim":    dict(color=(255, 120, 70),  max_r=38,  speed=110),
    "arrowhit": dict(color=(255, 225, 150), max_r=30, speed=90),
    "shot":   dict(color=(255, 225, 150), max_r=34,  speed=110),
    "dash":   dict(color=(150, 225, 255), max_r=70,  speed=190),
    "dash_red": dict(color=(255, 60, 40), max_r=75,  speed=200),     # modo ANAKIN
    "stab":   dict(color=(255, 90, 50),   max_r=60,  speed=150),     # espada clavada (ANAKIN)
    "fshot":  dict(color=(255, 70, 50),   max_r=34,  speed=110),     # FUERZA: disparo normal
    "farrowhit": dict(color=(255, 70, 50), max_r=30, speed=90),
    "fsuperhit": dict(color=(255, 60, 40), max_r=110, speed=230),    # FUERZA: super carga
    "fsuperlight": dict(color=(255, 50, 36), max_r=70, speed=200),
    "superhit":   dict(color=(255, 240, 180), max_r=110, speed=230),
    "superlight": dict(color=(255, 230, 150), max_r=70,  speed=200),
}
# variantes AZULES (skin ANAKIN) de las ondas rojas: se intercambian los canales R y B
for _k in ("dash_red", "stab", "fshot", "farrowhit", "fsuperhit", "fsuperlight"):
    _c = dict(WAVES[_k])
    _c["color"] = _c["color"][::-1]
    WAVES[_k + "_b"] = _c

# ----------------------------------------------------------------------------
#  MODO INFINITO (hard core)  -  ajusta aqui la dificultad
# ----------------------------------------------------------------------------
ENDLESS_START_SHIELD = True     # empieza con escudo (no hay cofres en este modo)
ENDLESS_START_BOW = True        # empieza con arco
ENDLESS_QUOTA_BASE = 4          # bajas necesarias para abrir la puerta en la sala 1
ENDLESS_QUOTA_STEP = 1          # bajas extra por cada sala
ENDLESS_QUOTA_MAX = 20
ENDLESS_ALIVE_BASE = 3          # monstruos simultaneos maximos en la sala 1
ENDLESS_ALIVE_EVERY = 2         # +1 monstruo simultaneo cada N salas
ENDLESS_ALIVE_MAX = 9
ENDLESS_SPAWN_T0 = 3.2          # segundos entre apariciones en la sala 1
ENDLESS_SPAWN_MIN = 1.1         # intervalo minimo de apariciones
ENDLESS_SPAWN_DECAY = 0.12      # lo que baja el intervalo por sala
ENDLESS_SPAWN_SAFE = 80.0       # distancia minima al jugador al aparecer un monstruo
ENDLESS_BAT_FROM = 1            # a partir de que sala salen murcielagos
ENDLESS_SKEL_FROM = 3           # a partir de que sala salen esqueletos
ENDLESS_AGGR_STEP = 0.03        # agresividad extra por sala
ENDLESS_AGGR_MAX = 1.4
HEART_DROP_BASE = 0.10          # prob. base de soltar un corazon (solo si te falta vida)
HEART_DROP_PER_HP = 0.10        # prob. extra por cada corazon que te falta
HEART_DROP_PITY = 0.03          # prob. extra acumulada por cada baja sin premio
HEART_LIFETIME = 14.0           # segundos que dura el corazon en el suelo
WAVES["heart"] = dict(color=(255, 110, 160), max_r=60, speed=120)
WAVES["spawn"] = dict(color=(205, 100, 255), max_r=40, speed=110)

# ----------------------------------------------------------------------------
#  MENU
# ----------------------------------------------------------------------------
MENU_ITEMS = 6                  # botones fijos (+1 CONTINUAR si hay partida guardada); la lista real esta en menu.menu_entries()
MENU_IDX_OPTIONS, MENU_IDX_FULLSCREEN, MENU_IDX_HELP = 3, 4, 5   # indices SIN el boton CONTINUAR (usa menu_activate_id en codigo nuevo)

# ----------------------------------------------------------------------------
#  PULIDO VISUAL (ronda 1)
# ----------------------------------------------------------------------------
SHAKE_HIT = 1.2                 # temblor al golpear a un monstruo (px logicos)
SHAKE_HURT = 3.0                # al recibir dano
SHAKE_BLOCK = 1.2               # al bloquear con el escudo
SHAKE_PULSE = 2.0               # al lanzar el super eco
SHAKE_DEATH = 6.0               # al morir
SHAKE_MAX = 7.0
SHAKE_DECAY = 14.0              # cuanto baja el temblor por segundo
SLOWMO_SCALE = 0.3              # velocidad del juego en camara lenta
SLOWMO_LAST_KILL = 0.55         # segundos de camara lenta al matar al ultimo monstruo del nivel
FADE_T = 0.5                    # duracion del fundido entre salas

# ----------------------------------------------------------------------------
#  RONDA 2 - MODO INFINITO PROFUNDO (cartas, modificadores, tienda, combo)
# ----------------------------------------------------------------------------
MAX_HP_CAP = 8                  # vida maxima que se puede alcanzar con cartas/tienda
CARD_EVERY = 1                  # una eleccion de cartas cada N salas (0 = nunca)
PERK_SPEED = 0.25               # +25% velocidad por carta de botas
PERK_ECHO = 1.35                # multiplicador del radio de los ecos de pasos/ataque por carta
PERK_SHIELD_ADD = 0.25          # lo que sube la velocidad con escudo (SHIELD_MULT) por carta
PERK_MAGNET = 2.0               # multiplicador del radio de recogida de corazones/monedas
DOUBLE_SHOT_DV = 38.0           # separacion vertical (velocidad) de la 2a flecha del arco doble
MOD_CHANCE = 0.25               # probabilidad de que una sala tenga modificador
MOD_LOWGRAV = 0.55              # gravedad de la sala "gravedad baja" (1.0 = normal)
MOD_FAST = 1.30                 # velocidad de monstruos de la sala "frenetica"
MOD_BANNER_T = 2.6              # segundos que dura el cartel del modificador
COIN_DROP = 0.55                # probabilidad de que un monstruo suelte una moneda
COIN_DROP_SKEL = 0.25           # extra para esqueletos
COIN_LIFETIME = 12.0
COIN_SCORE = 2                  # puntos por recoger una moneda
SHOP_EVERY = 5                  # sala tienda tras cada N salas (0-based: salas 5, 10, ... => sala 6, 11, ...)
SHOP_COLS = (8, 12, 16)         # columnas (de la rejilla real) de los 3 objetos de la tienda
SHOP_HEART, SHOP_CARD, SHOP_MAXHP = 3, 6, 10   # precios en monedas
COMBO_WINDOW = 3.0              # segundos maximos entre bajas para mantener la racha
COMBO_MAX = 5                   # multiplicador maximo
KILL_SCORE = {"ghoul": 10, "bat": 8, "skel": 15}
ROOM_SCORE = 50                 # puntos por superar una sala
WAVES["coin"] = dict(color=(255, 215, 90), max_r=36, speed=110)
WAVES["buy"] = dict(color=(255, 215, 90), max_r=70, speed=140)

# ----------------------------------------------------------------------------
#  RONDA 3 - ENEMIGOS, JEFES Y TRAMPAS (modo infinito)
# ----------------------------------------------------------------------------
ELITE_FROM = 3                  # indice de sala (0-based) desde el que pueden salir elites (= sala 4)
ELITE_CHANCE = 0.10             # probabilidad de que un monstruo normal sea elite
ELITE_HP_MULT = 2               # vida x2
ELITE_COINS = 2                 # monedas que suelta (x2)
ELITE_HEART_BONUS = 0.15        # probabilidad extra de corazon
ELITE_SCORE_MULT = 2
BOSS_EVERY = 5                  # jefe en las salas de indice 4, 9, 14... (salas 5, 10, 15; la tienda va justo despues)
BOSS_HP_STEP = 0.35             # +35% de vida de jefe por cada jefe ya derrotado
BOSS_SUPER_DMG = 4              # el super disparo no mata de un golpe a un jefe: hace este dano
BOSS_SCORE = 300
BOSS_COINS = 6
BOSS_GIANT_HP = 22
BOSS_GIANT_SHOT_CD = 2.4        # segundos entre abanicos de flechas
BOSS_GIANT_FAN = 0.24           # separacion angular (rad) entre las 3 flechas
BOSS_GIANT_ARROW = 140.0
BOSS_GIANT_JUMP = 285.0
BOSS_GIANT_WALK = 30.0
BOSS_SWARM_BATS = 8
BOSS_SWARM_BIG_HP = 16          # vida del murcielago grande cuando se fusiona (con las 8 vivas)
BOSS_GHOST_HP = 10              # fantasma grande
BOSS_GHOST_CHILD_HP = 3         # cada uno de los 2 fantasmas pequenos (nivel 1)
PHANTOM_FROM = 4                # fantasma invisible: desde la sala (indice) N
THIEF_FROM = 5
SILENCER_FROM = 6
PHANTOM_REVEAL_T = 0.30         # segundos que se ve el fantasma invisible tras tocarlo una onda
THIEF_SPEED = 58.0
THIEF_FLEE_T = 8.0              # si huye con el corazon este tiempo, se escapa
MUTE_T = 4.0                    # segundos sin ecos tras tocarte un silenciador
MUTE_KINDS = ("step", "attack", "pulse", "bounce", "shot", "fshot", "dash", "dash_red", "dash_red_b", "block")
TRAP_FROM = 2                   # los pinchos aparecen desde la sala (indice) N
TRAP_MAX = 4                    # maximo de tramos de pinchos por sala
TRAP_REVEAL_T = 0.45            # segundos que se ven tras tocarlos una onda
TRAP_INV = 1.0                  # invulnerabilidad tras pincharte
KILL_SCORE.update({"phantom": 18, "thief": 14, "silencer": 14})
WAVES["roar"] = dict(color=(255, 90, 60), max_r=130, speed=170)
WAVES["fuse"] = dict(color=(255, 130, 200), max_r=85, speed=150)
WAVES["thief"] = dict(color=(90, 230, 140), max_r=40, speed=110)
WAVES["silence"] = dict(color=(120, 140, 175), max_r=48, speed=110)

# ----------------------------------------------------------------------------
#  RONDA 4 - PERSONAJES (ver characters.py)
# ----------------------------------------------------------------------------
MAGE_HP = 2
MAGE_ORB_SPEED = 125.0          # bola magica lenta (px logicos / s)
MAGE_ORB_BOUNCES = 2            # rebotes en muros antes de desaparecer
MAGE_ORB_LIFE = 4.0             # segundos maximos de vida de la bola
MAGE_ORB_CD = 0.7               # enfriamiento entre bolas
MAGE_ORB_DV = 34.0              # separacion vertical de la 2a bola (carta ARCO DOBLE)
ROGUE_HP = 2
ROGUE_SPEED = 1.30              # +30% de velocidad
ROGUE_ATK_CD = 0.5              # la daga ataca el doble de rapido
ROGUE_REACH = 0.7               # ...pero llega menos lejos
AIR_JUMP_MULT = 0.9             # fuerza del segundo salto (1.0 = igual que el primero)
TANK_HP = 5
TANK_SPEED = 0.75               # -25% de velocidad
TANK_ATK_CD = 1.7               # ataque lento
TANK_PUSH = 2.4                 # el golpe empuja mucho mas
TANK_BLOCK_STUN = 1.0           # un bloqueo atonta 1 s al enemigo
WAVES["orb"] = dict(color=(120, 190, 255), max_r=34, speed=110)
WAVES["airjump"] = dict(color=(120, 235, 160), max_r=34, speed=120)
MUTE_KINDS = MUTE_KINDS + ("orb", "airjump")      # el silenciador tambien apaga estos ecos

# ----------------------------------------------------------------------------
#  SKIN SECRETA "luchador" (escribe luchador en partida)
# ----------------------------------------------------------------------------
FT_FLY_SPEED = 190.0            # velocidad de ascenso / descenso en vuelo (px logicos / s)
FT_FLY_ACCEL = 10.0             # que tan rapido alcanza esa velocidad
FT_FLY_HSPEED = 1.8             # multiplicador de la velocidad horizontal en vuelo
FT_FLY_AIR_ACC = 1500.0         # aceleracion horizontal en vuelo
FT_SIZE = (21, 21)              # tamano del sprite (como DARTH VADER: 21 x 20)
FT_SLAM_MIN_FALL = 230.0        # velocidad de caida minima para que el aterrizaje cree una onda
FT_SLAM_RADIUS = 46.0           # alcance base del impacto (crece con la velocidad de caida)
FT_DIVE_SPEED = 400.0           # velocidad de la PICADA (mantener S en el aire)
FT_DIVE_AFTER = 0.25            # segundos con S pulsado en el aire antes de lanzarte en picada
FT_LAND_T = 0.34                # duracion de la compresion exagerada al impactar
FT_BONUS_HP = 2                 # corazones extra mientras llevas la skin
FT_BLOCK_STUN = 0.9             # la guardia atonta al atacante
FT_PUNCH_CD = 0.6               # el puñetazo cuerpo a cuerpo es mas rapido...
FT_PUNCH_REACH = 1.3            # ...llega mas lejos...
FT_PUNCH_DMG = 1                # ...y pega mas fuerte
FT_PUNCH_PUSH = 1.8             # ...y empuja mas
WAVES["clap"] = dict(color=(245, 248, 255), max_r=170, speed=280)
WAVES["slam"] = dict(color=(235, 240, 255), max_r=70, speed=200)
MUTE_KINDS = MUTE_KINDS + ("clap", "slam")
FT_SHOT_CD = 0.5                # enfriamiento del punetazo de aire (disparo)
FT_AIR_SPEED = 300.0
FT_AIR_LIFE = 0.5               # segundos de vida de la onda de aire (alcance ~150 px)
FT_AIR_PUSH = 2.2               # empuje del punetazo de aire
WAVES["attack_air"] = dict(color=(235, 242, 255), max_r=95, speed=175)
WAVES["airpunch"] = dict(color=(240, 246, 255), max_r=55, speed=150)
WAVES["dash_air"] = dict(color=(240, 246, 255), max_r=70, speed=190)
MUTE_KINDS = MUTE_KINDS + ("attack_air", "airpunch", "dash_air")

# ----------------------------------------------------------------------------
#  RONDA 5.1 - OPCIONES (teclas reasignables, volumen, tamano de ventana)
# ----------------------------------------------------------------------------
# Nombres de tecla de pygame (pygame.key.name / key_code). La primera es la principal: es la que se reasigna.
KEYMAP = {
    "left":     ["a", "left"],
    "right":    ["d", "right"],
    "jump":     ["w", "up", "z"],
    "shield":   ["s", "down"],
    "sneak":    ["left shift", "right shift"],
    "attack":   ["space", "x"],
    "pulse":    ["q"],
    "fire":     ["f", "c"],
    "dash":     ["r"],
    "interact": ["e"],
}
KEY_ACTIONS = [("left", "Izquierda"), ("right", "Derecha"), ("jump", "Saltar"), ("shield", "Escudo / agacharse"),
               ("sneak", "Sigilo"), ("attack", "Atacar"), ("pulse", "Super eco"), ("fire", "Disparar (arco / bola)"),
               ("dash", "Dash"), ("interact", "Interactuar (E)")]
RESERVED_KEYS = ("escape", "f11", "h", "p", "m", "o", "return", "enter")   # teclas fijas del sistema: no se pueden asignar
VOL_MASTER_DEFAULT = 0.8
VOL_MUSIC_DEFAULT = 0.6
VOL_STEP = 0.1                  # paso con las flechas en los deslizadores
WINDOW_K_MIN, WINDOW_K_MAX = 2, 5   # escala de la ventana (LW*k x LH*k)

# ---------------------------------------------------------------- RONDA 5.3: LOGROS
# (id, nombre, descripcion, meta del contador que se muestra como progreso; 0 = logro de un solo golpe)
ACH_LIST = [
    ("streak10", "INTOCABLE", "Mata a 10 monstruos seguidos sin recibir daño.", 10),
    ("room20", "SIN FONDO", "Llega a la sala 20 del modo infinito.", 20),
    ("boss", "CAZAJEFES", "Derrota a un jefe del modo infinito.", 0),
    ("pulse50", "GRITO PROFUNDO", "Usa el súper eco 50 veces (se acumula entre partidas).", 50),
    ("win", "HASTA EL FONDO", "Termina el último nivel y gana el modo niveles.", 0),
    ("kills100", "CAZADOR", "Consigue 100 bajas en total (se acumula entre partidas).", 100),
    ("buy", "CLIENTE", "Compra algo en una tienda del modo infinito.", 0),
    ("combo5", "COMBO X5", "Consigue un combo de x5 en el modo infinito.", 5),
    ("chars", "TODOTERRENO", "Supera la sala 5 del modo infinito con cada uno de los 4 personajes.", 4),
    ("elite", "ÉLITE ABATIDO", "Derrota a un monstruo élite.", 0),
]
ACH_SHOW_T = 3.0                # segundos que se ve el cartel de logro desbloqueado
ACH_FLUSH_EVERY = 10            # cada cuantas bajas / super ecos se guardan los contadores en disco
ACH_ROOM_CHAR = 5               # sala del modo infinito que hay que SUPERAR con cada personaje (indice 5 = sala 6)

# ---------------------------------------------------------------- RONDA 5.4: MUSICA SINTETIZADA
MUSIC_BPM = 96                  # bucle de 4 compases (~10 s) en La menor: Am - F - C - G
MUSIC_BARS = 4
MUSIC_LAYERS = 3                # bajo, arpegio, percusion (cada capa en su propio canal reservado del mixer)
MUSIC_GAIN = 0.5                # volumen maximo de cada capa (antes de vol_music * vol_master)
MUSIC_FADE = 0.7                # velocidad de los fundidos entre capas (unidades de volumen por segundo)
MUSIC_DANGER_MID = 0.05         # peligro (monstruo muy cerca) a partir del cual entra el arpegio
MUSIC_DANGER_HIGH = 0.5         # ... y la percusion
MUSIC_MON_MID = 1               # monstruos vivos para que entre el arpegio
MUSIC_MON_HIGH = 4              # monstruos vivos para que entre la percusion
MUSIC_CALM_STATES = ("menu", "select", "options", "achievements", "cards", "paused", "victory", "dead")
MUSIC_BIG_ROOM = 0.55           # fraccion de casillas libres a partir de la cual el eco del super eco suena mas grave

# ---------------------------------------------------------------- LUCHADOR: SUPER DISPARO v2 (onda de choque grande)
# Mantener F/C carga (barra + esfera de energia que crece); al llenarse parpadea y espera hasta que sueltes (ya NO sale sola).
# Soltar con la carga llena lanza una ONDA DE CHOQUE gigante que viaja, atraviesa y empuja a todos los monstruos.
FT_SUPER_CHARGE_T = 0.7         # segundos de carga necesarios
FT_SUPER_CD = 0.9               # enfriamiento tras lanzarla (la carga NO avanza mientras dura)
FT_SUPER_SPEED = 250.0          # velocidad de la onda
FT_SUPER_LIFE = 1.1             # segundos que vuela (~275 px)
FT_SUPER_DMG = 4                # dano a cada monstruo que atraviesa (los jefes lo reciben igual)
FT_SUPER_PUSH = 3.6             # empuje
FT_SUPER_VREACH = 22.0          # altura extra de golpe por encima/debajo del cuerpo (la onda es alta)

# ---------------------------------------------------------------- MENU DE PAUSA
PAUSE_CONFIRM_T = 2.5           # segundos para confirmar REINICIAR / MENU PRINCIPAL (pulsar otra vez)

# ---------------------------------------------------------------- RONDA 5.5: MANDO (tipo Xbox)
# Los botones del mando se traducen a las MISMAS acciones que KEYMAP (y a las teclas de menu): sin mando no cambia nada.
PAD_BUTTONS = {0: "jump", 2: "attack", 1: "fire", 3: "interact", 4: "dash", 5: "pulse", 7: "pause"}   # A X B Y LB RB Start
PAD_BUTTON_LABELS = "A saltar / aceptar   X atacar   B disparar / volver   Y interactuar   LB dash   RB super eco   LT escudo   Start pausa"
PAD_AXIS_X, PAD_AXIS_Y, PAD_AXIS_LT = 0, 1, 4       # stick izquierdo (x, y) y gatillo izquierdo
PAD_DEADZONE = 0.3              # zona muerta horizontal del stick
PAD_VDEAD = 0.6                 # zona muerta vertical (mas grande: evita saltar / agacharse sin querer)
PAD_TRIGGER_ON = 0.3            # el gatillo cuenta como pulsado por encima de este valor (reposo: -1 o 0)
PAD_REPEAT_FIRST = 0.35         # segundos hasta que una direccion mantenida en un menu empieza a repetirse
PAD_REPEAT = 0.12               # ... y cada cuanto se repite

# ---------------------------------------------------------------- POLVO FLOTANDO EN EL HAZ DE LUZ (ronda 1)
MOTE_COUNT = 26                 # motas de polvo alrededor del caballero (solo se ven donde llega la luz del haz o de las antorchas)
MOTE_BOX = (80.0, 46.0, 34.0)   # mitad de ancho, alto por encima y por debajo del caballero donde viven las motas
MOTE_SPEED = 5.0                # deriva lenta (px / s)
MOTE_LIFE = (3.0, 7.0)          # vida de cada mota (aparece y se apaga con fundido)


# ----------------------------------------------------------------------------
#  RONDA 6 - JEFES CON FASES Y MUCHOS ATAQUES (ver entities.py: BossAI y los tres jefes)
#  Fase 1: vida > 66%, fase 2: 33-66%, fase 3: < 33% (furia). Cada jefe derrotado sube `power`.
# ----------------------------------------------------------------------------
BOSS_THINK = (1.5, 1.05, 0.75)        # pausa entre ataques en cada fase (segundos)
BOSS_THINK_POWER = 0.08               # la pausa se acorta un 8% por cada jefe ya derrotado (minimo x0.5)
BOSS_MINIONS_MAX = 4                  # esbirros vivos a la vez (los invoca el jefe)
BOSS_GIANT_CHARGE = 150.0             # velocidad de la embestida del esqueleto gigante
BOSS_GIANT_RAIN_ARROW = 175.0         # velocidad de las flechas de la lluvia
BOSS_SHOCK_SPEED = 105.0              # velocidad de las ondas rasantes que deja su aterrizaje
BOSS_BAT_SCREECH_SPEED = 82.0         # velocidad de las bolas sonicas del chillido
BOSS_BAT_SWEEP_SPEED = 215.0          # velocidad del barrido horizontal del murcielago grande
BOSS_BAT_DIVE_SPEED = 2.8             # multiplicador de velocidad en picado
BOSS_GHOST_LUNGE = 150.0              # velocidad de la embestida del fantasma
BOSS_GHOST_ORB_SPEED = 92.0           # velocidad de las bolas espectrales
WAVES["screech"] = dict(color=(255, 150, 215), max_r=64, speed=95)
WAVES["wail"] = dict(color=(190, 140, 255), max_r=64, speed=95)
WAVES["tele"] = dict(color=(255, 70, 50), max_r=26, speed=70)
