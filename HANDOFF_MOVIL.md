# HANDOFF — VERSIÓN MÓVIL de Echo Knight (continuar en otra cuenta)

> Pega esto al empezar la nueva conversación junto con el .zip del proyecto:
> *"Lee HANDOFF_MOVIL.md y continúa desde «Siguiente paso». Responde en español."*

## Dos versiones separadas
- **Móvil** (esta carpeta): `touch.want_touch()` devuelve siempre True; opciones solo con volumen; app `echoknightmovil`.
- **Laptop** (carpeta/zip aparte, código original sin cambios): teclado/mando/ratón, sin modo táctil.
Cualquier mejora de **contenido** (jefes, biomas, cartas...) conviene hacerla en una y copiarla a la otra; lo táctil es solo del móvil.

## Qué es el proyecto
Juego pygame de plataformas en la oscuridad (ecos de luz, niveles, modo infinito, jefes, cartas, logros, personajes, mando).
~9 200 líneas, 100 % Python + pygame, sin archivos de audio/imagen (todo se sintetiza/dibuja por código).
Arquitectura: `echo_knight/game.py` une mixins (uno por archivo; tabla en `README.md`). Resolución lógica 384×224 escalada ×`k`.

## Qué se hizo en esta sesión
| Cambio | Archivos |
|---|---|
| **Controles táctiles**: 10 botones + pausa/atrás, mantener IZQ/DER con deslizamiento, multitáctil, disparo = soltar. Se traducen a las mismas acciones del teclado (respeta teclas reasignadas). | `echo_knight/touch.py` (nuevo) |
| Ventana ancha en modo táctil: `self.display` = ventana real, `self.screen` = subsurface centrado del juego → **todo el dibujo existente funciona sin tocarlo**. Márgenes laterales para los botones. | `touch.py`, `core.py` |
| Ratón/toque en menús con desplazamiento de margen (`menu_mouse`) | `menu.py` |
| `held()` suma `touch_held`; `K_AC_BACK` (atrás de Android) = ESC; pasar a segundo plano = pausa; sin F11 ni cambio de tamaño en móvil | `options.py`, `events.py`, `touch.py` |
| Guardado en carpeta privada de Android (`ANDROID_PRIVATE`) | `echo_knight/paths.py` (nuevo), `save.py`, `options.py`, `endless.py` |
| Textos de tutorial y ayuda sin teclas en modo táctil | `texts.py`, `screens.py`, `text_ui.py`, `pause.py` |
| Empaquetado: `buildozer.spec`, receta local pygame-ce, workflow de GitHub Actions | `buildozer.spec`, `p4a-recipes/`, `.github/workflows/android.yml` |
| Limpieza: se quitó `venv/` (macOS), `__pycache__`, `.DS_Store`, `Jugar.command` | — |

En esta versión el modo táctil está siempre activo.

## Qué está verificado y qué NO
- ✅ Todos los archivos compilan (`python -m compileall`).
- ✅ `python test_logica_tactil.py`: lógica de toques con pygame simulado (layout sin solapes, mover/deslizar, saltar, atacar, disparo mantenido y liberado al morir, botones ocultos, pausa, atrás, fondo, tap en muerte, teclas reasignadas).
- ❌ **Nunca se ejecutó con pygame real** (en la sesión de Claude `pypi.org` estaba bloqueado: no se pudo instalar pygame). Hay que ejecutar `python main.py` en una máquina con pygame y corregir lo que salga. Riesgos concretos:
  - `pygame.SCALED | FULLSCREEN` y coordenadas de ratón/dedo en Android (si los menús o botones salen desplazados, revisar `menu_mouse` y `touch_pos` en `touch.py`).
  - Aspecto de los botones (tamaños/posiciones en `_touch_layout`, coordenadas relativas a la altura 672); no se vio ninguna captura.
  - Botones que tapan el HUD inferior izquierdo en pantallas 16:9 sin márgenes.
- ❌ **Nunca se compiló el APK.** La receta `p4a-recipes/pygame-ce/__init__.py` está escrita de memoria (sin probar).
- ❌ Rendimiento en móvil sin medir (ver abajo).

## Siguiente paso (en este orden)
1. En un Mac/PC con pygame: `python main.py`. Comprobar que arranca, ver los botones, hacer capturas, ajustar `_touch_layout`.
2. Subir a GitHub y lanzar el workflow (`LEEME_MOVIL.md`). Pegar a Claude el **primer error** del registro y iterar hasta tener un APK.
3. Probar en el móvil real: ¿mide bien los toques?, ¿FPS?, ¿tarda mucho en arrancar?
4. **Rendimiento** si hace falta: `audio.py`/`music.py` sintetizan en Python puro al arrancar (cachear a archivos .wav en la carpeta de datos la primera vez); las luces usan superficies 384×208 por fotograma; `TOUCH_K` (touch.py) = 3, bajar a 2 acelera.
5. Después, mejoras de contenido en tandas pequeñas (un APK nuevo por tanda).

## Ideas de mejora pendientes (priorizadas)
1. Indicador visual direccional de sonidos/ecos (accesibilidad y uso sin audio en móvil).
2. Progresión entre partidas (monedas/fragmentos → mejoras y skins; ya existe `try_buy`).
3. Reto diario con semilla por fecha en el modo infinito (`--semilla` ya existe → `endless.parse_seed`).
4. Selector de dificultad; modo «una vida».
5. Jefes en el modo infinito (cada N salas).
6. Más biomas (paleta, antorchas, enemigos por mundo) y salas secretas.
7. Idiomas: separar textos de `texts.py` y los literales de menús/pausa/opciones.
8. Opciones de accesibilidad (daltónico, brillo, vibración) y de táctil (tamaño/posición de botones, zurdos).
9. Vibración al recibir daño (Android), guardado automático al pasar a segundo plano.

## Notas técnicas útiles
- Entrada: `events.handle_events` → `touch_translate(pad_translate(pygame.event.get()))`. Los dedos nunca llegan a los menús como FINGER*: SDL ya genera eventos de ratón desde el toque y los menús los manejan.
- Un cambio de estado con dedos puestos libera todo (`_release_all`) para que no quede un disparo cargando.
- Tras morir hay 0,8 s antes de que un toque reinicie (evita reinicios accidentales).
- `core.py`: en modo táctil se ignora `window_k` guardado en opciones.
- No usar `~` para guardar: usar `paths.data_path(nombre)`.

## Tokens
Al cerrar esta sesión quedaban ~14,9 M de 15 M tokens de contexto disponibles: el traspaso es por comodidad, no porque se agotaran.

- Opciones en móvil: `options.opt_rows()` oculta ventana/teclas cuando `touch_mode`.
