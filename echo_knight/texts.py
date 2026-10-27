# -*- coding: utf-8 -*-
"""Textos: tutorial y panel de controles."""


TUT_MSGS = [
    "TUTORIAL 1/7 · Todo está a oscuras. Muévete con A / D (o FLECHAS): cada paso lanza un eco de luz.",
    "2/7 · Salta con W, Z o FLECHA arriba. Mantén pulsado para saltar más alto. Salta moviéndote para un SALTO DIAGONAL con impulso.",
    "3/7 · Sigilo: mantén SHIFT mientras caminas. No haces eco de pasos y los monstruos te oyen menos.",
    "4/7 · Ataca con ESPACIO (o X): la espada lanza una onda ámbar, pero el ruido atrae monstruos.",
    "5/7 · SÚPER ECO: pulsa Q. Ilumina toda la sala y rebota en los muros. ¡Pero atrae monstruos!",
    "6/7 · ¡Un fantasma de práctica! Derrótalo (2 golpes). OJO: los monstruos son INVISIBLES en la oscuridad; solo los verás cerca de tu luz o con un halo cuando te ataquen. Cuando no quede ninguno aparece la llave.",
    "7/7 · ¡Ha aparecido la llave dorada! Búscala con tus ecos y tómala: las antorchas se encenderán.",
    "¡Listo! La sala se ilumina y la puerta está abierta. Más adelante hallarás un escudo (S) y un arco (F) en cofres. ¡Corre a la PUERTA!",
]

CONTROLS = [
    (["A", "D"],            "Mover (o FLECHAS izq. / der.).\nCada paso lanza un pequeño eco."),
    (["W", "|", "Z"],       "Saltar (o FLECHA arriba). Con dirección:\nsalto diagonal con impulso."),
    (["ESPACIO", "|", "X"], "Atacar: golpe + onda ámbar. En el aire:\ntajo diagonal con rebote en enemigos."),
    (["S"],                 "Escudo: mantén S o FLECHA abajo.\nSe obtiene en el cofre del nivel 2."),
    (["E"],                 "Abrir cofres / interactuar."),
    (["Q"],                 "Súper eco: ilumina la sala y solidifica\nlos PUENTES FANTASMA. ¡Atrae monstruos!"),
    (["F", "|", "C"],       "Arco (cofre del nivel 5): toca = flecha.\nMantén y suelta = SÚPER DISPARO."),
    (["SHIFT"],             "Sigilo: lento y sin eco de pasos."),
    (["P"],                 "Reiniciar el nivel (pulsa P dos veces)."),
    (["ESC"],               "Pausa."),
    (["H"],                 "Mostrar / ocultar esta ayuda."),
    (["M", "|", "F11"],     "Sonido / Pantalla completa."),
]


# --- Version tactil (Android): mismos pasos del tutorial y panel de ayuda sin teclas ---
TUT_MSGS_TOUCH = [
    "TUTORIAL 1/7 · Todo está a oscuras. Mantén los botones de FLECHA de la izquierda para moverte: cada paso lanza un eco de luz.",
    "2/7 · Salta con el botón grande de abajo a la derecha. Mantén pulsado para saltar más alto. Salta moviéndote para un SALTO DIAGONAL con impulso.",
    "3/7 · Sigilo: mantén el botón SIG mientras caminas. No haces eco de pasos y los monstruos te oyen menos.",
    "4/7 · Ataca con el botón de la ESPADA: lanza una onda ámbar, pero el ruido atrae monstruos.",
    "5/7 · SÚPER ECO: toca el botón de círculos. Ilumina toda la sala y rebota en los muros. ¡Pero atrae monstruos!",
    TUT_MSGS[5],
    TUT_MSGS[6],
    "¡Listo! La sala se ilumina y la puerta está abierta. Más adelante hallarás un escudo y un arco en cofres. ¡Corre a la PUERTA!",
]

CONTROLS_TOUCH = [
    (["◄", "►"],      "Mover: mantén el botón. Desliza el dedo\nde uno a otro sin soltar. Cada paso hace eco."),
    (["SALTO"],       "Botón grande: saltar. Mantén = más alto.\nCon dirección: salto diagonal con impulso."),
    (["ESPADA"],      "Atacar: golpe + onda ámbar. En el aire:\ntajo diagonal con rebote en enemigos."),
    (["ESCUDO"],      "Mantén el botón del escudo. Se obtiene\nen el cofre del nivel 2."),
    (["E"],           "Abrir cofres / interactuar / comprar."),
    (["ECO"],         "Súper eco: ilumina la sala y solidifica\nlos PUENTES FANTASMA. ¡Atrae monstruos!"),
    (["FLECHA"],      "Arco (cofre del nivel 5): toca = flecha.\nMantén y suelta = SÚPER DISPARO."),
    (["SIG"],         "Sigilo: lento y sin eco de pasos."),
    (["| |"],         "Pausa (arriba a la derecha)."),
]
