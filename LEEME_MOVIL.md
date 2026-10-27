# Echo Knight — versión MÓVIL (solo celular)

Esta carpeta es la versión para **Android**. La versión de **laptop** es otra carpeta/zip aparte (`echo_knight_laptop`);
no mezcles los archivos. Ambas pueden vivir en repositorios distintos.

Diferencias con la versión laptop:
- Modo táctil **siempre** activo (botones virtuales, ventana ancha con márgenes).
- Opciones solo con volumen (sin tamaño de ventana ni reasignar teclas).
- App con nombre propio: **Echo Knight Movil** (`org.tunaxel.echoknightmovil`).
- Guardado en la carpeta privada de la app.

## 1. Ver cómo se ve en tu Mac (opcional)
```bash
python3 -m venv venv && source venv/bin/activate
pip install pygame
python main.py
```
Verás la ventana ancha con los botones dibujados. Con ratón solo responden los menús; el movimiento necesita pantalla táctil.

## 2. Generar el APK
1. Crea un repositorio de GitHub (por ejemplo `echo-knight-movil`) y sube **el contenido** de esta carpeta
   (`buildozer.spec` en la raíz, y la carpeta oculta `.github`).
2. Pestaña **Actions** → **Compilar APK (Android)** → **Run workflow** (30-40 min la primera vez).
3. Descarga el artefacto **echo-knight-apk** y pásalo al móvil. Permite "instalar apps desconocidas".

## 3. Si falla
- Copia el **primer error en rojo** del registro y pásaselo a Claude junto con `HANDOFF_MOVIL.md`.
- La receta `p4a-recipes/pygame-ce/__init__.py` está **sin probar**; alternativa en
  https://gist.github.com/emersonmx/c5bba202506e3c3d2d828ad278a8d5fe (botón *Raw*).
- Si se cierra al abrir: `adb logcat | grep -i python` con el móvil por USB.
