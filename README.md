# Echo Knight — VERSIÓN MÓVIL (solo celular)

Ejecutar:  `pip install pygame`  →  `python main.py`   (`--sin-sonido` para silenciar)

## Dónde tocar cada cosa

| Quiero cambiar…                                   | Archivo                      |
|---------------------------------------------------|------------------------------|
| Velocidades, vida, cooldowns, colores, ondas      | `echo_knight/config.py`      |
| Dificultad del modo infinito                      | `config.py` (bloque MODO INFINITO) |
| Textos del tutorial y panel de controles          | `texts.py`                   |
| Pixel art (caballero, monstruos, objetos, skins)  | `sprites_data.py`            |
| Cómo se construyen/animan los sprites             | `sprites.py`, `textures.py`  |
| Niveles del modo niveles                          | `levels_data.py`             |
| Salas aleatorias del modo infinito                | `rooms.py`                   |
| Reglas del modo infinito (spawns, corazones, puerta) | `endless.py`              |
| Jugador / Ghoul / Bat / Skeleton / Arrow          | `entities.py`                |
| Ataque, escudo, arco, daño                        | `combat.py`                  |
| Skins secretas, dash                              | `skins.py`, `fx_draw.py`     |
| Teclas y menú (entrada)                           | `events.py`                  |
| Lógica por fotograma                              | `update.py`                  |
| Dibujo del mundo / luces                          | `render.py`, `lighting.py`   |
| HUD, textos, pantallas, menú                      | `hud.py`, `text_ui.py`, `screens.py` |
| Sonidos                                           | `audio.py`                   |
| Carga de niveles / menú                           | `flow.py`                    |

`game.py` une todos los mixins en la clase `Game`.

## Modo infinito
- Salas aleatorias (siempre alcanzables), monstruos que aparecen sin parar.
- Cuota de bajas por sala → se abre la puerta → sala nueva.
- La vida pasa de sala en sala. Los monstruos sueltan corazones de vez en cuando
  (más probable cuanto menos vida tengas; ver `HEART_DROP_*` en `config.py`).
- Récord guardado en `~/.echo_knight_best.json`.

## Cómo añadir cosas
- **Nuevo monstruo**: clase en `entities.py` (copia `Ghoul`), sprites en `sprites_data.py`/`textures.py`,
  dibujo en `render.py` (rama de `render_world`), y añádelo en `endless_pick_kind/endless_spawn`.
- **Nuevo modo**: mixin nuevo (como `endless.py`), añadirlo a `game.py`, opción en `screens.draw_menu`
  y `events.py` (menú). `menu_sel` admite más opciones ampliando esas dos funciones.
- **Nuevo personaje/skin**: ver `skins.py` (`set_skin`, `feed_secret`) y `sprites.py` (`build_knight_anim`).

## Android / táctil (nuevo)
- En esta versión el modo táctil está SIEMPRE activo: `python main.py` abre la ventana con los botones (el ratón no mueve al caballero).
- `echo_knight/touch.py`: controles táctiles. `echo_knight/paths.py`: carpeta de guardado (en Android, la privada de la app).
- Compilar el APK: ver `LEEME_MOVIL.md`. Estado y siguientes pasos: `HANDOFF_MOVIL.md`.
