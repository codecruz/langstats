# langstats

[English](README.md) · **Español**

Estadísticas de lenguajes para [Claude Code](https://claude.com/claude-code).
langstats registra en qué lenguajes de programación lee y edita Claude mientras
trabaja para ti, y los convierte en un bloque para el README de tu perfil de
GitHub, dibujado con barras de texto:

```txt
TypeScript                      ██████░░░░░░░░░░░░░░░░░░░   24.10 %
PHP                             █████░░░░░░░░░░░░░░░░░░░░   20.04 %
Python                          ████▒░░░░░░░░░░░░░░░░░░░░   17.90 %
Markdown                        ███░░░░░░░░░░░░░░░░░░░░░░   12.18 %
Bash                            ██░░░░░░░░░░░░░░░░░░░░░░░   07.45 %
JSON                            █▒░░░░░░░░░░░░░░░░░░░░░░░   05.16 %
Other                           ███▒░░░░░░░░░░░░░░░░░░░░░   13.17 %
```

> **Qué mide:** el tiempo que **Claude** trabaja en cada lenguaje.
> No mide el tiempo que pasas tú escribiendo en tu propio editor.

- Funciona en **macOS, Linux y Windows**.
- **Tus propios iconos**: barras con flores 🌸, cohetes 🚀, corazones 💖, lunas 🌕 o
  los símbolos que quieras (ver [Estilo de las barras](#estilo-de-las-barras)).
- **No ralentiza a Claude**: el hook se ejecuta en segundo plano (ver [Rendimiento](#rendimiento)).
- **GitHub es opcional**: si está conectado, actualiza tu README solo; si no,
  te da el bloque para pegarlo a mano.

## Contenido

- [Inicio rápido](#inicio-rápido)
- [Publicar: automático o a mano](#publicar-automático-o-a-mano)
- [Varios ordenadores](#varios-ordenadores)
- [Estilo de las barras](#estilo-de-las-barras)
- [Comandos](#comandos)
- [Configuración](#configuración)
- [Cómo se cuenta el tiempo](#cómo-se-cuenta-el-tiempo)
- [Rendimiento](#rendimiento)
- [Privacidad](#privacidad)
- [Solución de problemas](#solución-de-problemas)
- [Desinstalar](#desinstalar)

## Inicio rápido

**1. Instala el plugin.** En Claude Code:

```text
/plugin marketplace add codecruz/langstats
/plugin install langstats@codecruz
```

Después abre una sesión nueva o ejecuta `/reload-plugins`.

**Requisitos:** Python 3.9 o posterior, disponible como `python3`, `python` o
`py -3`. No hace falta nada más. La [CLI de GitHub](https://cli.github.com/)
(`gh`) es opcional: permite que langstats actualice tu README automáticamente.

**2. Ejecuta la configuración guiada:**

```text
/langstats:setup
```

Detecta si GitHub está conectado y te hace unas pocas preguntas: el repositorio,
la sección del README que se actualiza y si quieres publicar automáticamente.

**3. Trabaja como siempre.** Cada archivo que Claude lee o edita queda
registrado. Consulta tus estadísticas cuando quieras con:

```text
/langstats:stats
```

**4. Publica:**

```text
/langstats:publish
```

## Publicar: automático o a mano

### ¿Qué opción es la mía?

| Tu situación | Qué hace langstats | Qué haces tú |
| --- | --- | --- |
| Tienes `gh` instalado y has ejecutado `gh auth login` | Actualiza la sección del README de tu perfil (`github.com/<tú>/<tú>`) mediante la API de GitHub | Nada: ejecuta `/langstats:publish` o activa la publicación automática |
| Tienes un clon local del repositorio de tu perfil | Hace commit y push del cambio con `git` | Indica la ruta del clon en `/langstats:setup` |
| GitHub no está conectado | No envía nada a ningún sitio y te da el bloque | Pegas el bloque en tu README a mano |

El modo por defecto, `auto`, elige por ti en ese orden: primero un clon local
configurado, después la CLI de GitHub y, si no hay ninguno, el modo manual.

### Automático (GitHub conectado)

langstats solo reescribe el texto que hay entre dos marcadores de tu README y
deja todo lo demás como está:

```markdown
<!--START_SECTION:langstats-->
<!--END_SECTION:langstats-->
```

Pon esas dos líneas donde quieras que aparezcan las estadísticas.
`/langstats:setup` puede añadirlas por ti al final del README, preguntándote
antes. Si el contenido no ha cambiado, no se hace ningún commit.

Para publicar sin tener que acordarte, activa la publicación automática:

```text
/langstats:setup        (responde "sí" a la publicación automática)
```

Con la publicación automática activada, langstats publica al cerrar una sesión
de Claude Code, como mucho una vez cada 12 horas (`publish_interval_hours`). Se
ejecuta en un proceso en segundo plano, así que cerrar Claude Code nunca se
retrasa. Su salida queda en `~/.claude/langstats/publish.log`.

### A mano (GitHub no conectado)

Ejecuta:

```text
/langstats:snippet
```

Obtienes un bloque como este, que además se copia al portapapeles cuando es
posible y se guarda en `~/.claude/langstats/readme-snippet.md`:

````markdown
<!--START_SECTION:langstats-->

```txt
TypeScript                      ██████░░░░░░░░░░░░░░░░░░░   24.10 %
...
```

<!--END_SECTION:langstats-->
````

1. Abre en GitHub el repositorio de tu perfil (`github.com/<tú>/<tú>`) y edita
   `README.md`.
2. Pega el bloque donde quieras las estadísticas. Si ya hay un bloque anterior
   con los mismos marcadores, sustitúyelo entero.
3. Haz commit.

`/langstats:publish` hace lo mismo cuando GitHub no está conectado. Si más
adelante conectas GitHub (`gh auth login`), la siguiente publicación actualizará
esa misma sección automáticamente.

## Varios ordenadores

**Por defecto solo se sube el bloque de porcentajes**, y nada más. Cada
ordenador publica las estadísticas de su propio trabajo, así que si usas varios
ordenadores, el último en publicar sustituye el bloque.

Para **sumar varios ordenadores**, activa `share_data` en cada uno:

```sh
run config set share_data true
```

Para sumar hace falta saber cuánto tiempo llevó cada lenguaje, porque los
porcentajes solos no se pueden combinar (el 50 % de una hora no es lo mismo que
el 50 % de cinco minutos). Así que con `share_data` activado:

- El repositorio recibe **un único archivo pequeño**, `.langstats/stats.json`,
  con los minutos sumados de todos tus ordenadores por día y lenguaje:

  ```json
  {"days":{"2026-11-07":{"Python":5400,"TypeScript":1800}},"v":1}
  ```

- **No contiene nombres ni identificadores de ordenadores, ni proyectos, ni
  rutas, ni horas del día.** Nadie puede saber por él cuántos ordenadores tienes
  ni qué hizo cada uno.
- Solo guarda **los días que muestra el bloque** (los últimos 7 por defecto). Los
  días anteriores se borran en cada publicación, así que no se acumula nada.
- Cada ordenador recuerda, solo en sí mismo, lo que aportó la última vez
  (`~/.claude/langstats/shared-contribution.json`). Al publicar, cambia su
  aportación anterior por la nueva, así que nada se cuenta dos veces.

**Recomendado:** guarda ese archivo en un **repositorio privado**, para que tu
perfil público siga mostrando solo porcentajes:

```sh
gh repo create <tú>/langstats-data --private
run config set data_repo <tú>/langstats-data
```

Haz lo mismo en cada ordenador. Tu README público solo mostrará el bloque.
`/langstats:setup` te pregunta por esto y puede crear el repositorio por ti.

> En modo manual (sin conexión con GitHub), cada ordenador solo conoce sus
> propios datos: `/langstats:snippet` muestra las estadísticas del ordenador
> donde lo ejecutas.

## Estilo de las barras

Los símbolos de las barras los eliges tú. Mira todos los estilos con una vista
previa:

```text
/langstats:style
```

```txt
  bars      █████████░░░░░░   ░ ▒ ▓ █
  flowers   🌸🌸🌸🌸🌸🌸🌸🌸🌸······   · 🌱 🌸
  rocket    💮💮💮💮💮💮💮💮💮······   · 🚀 💮
  hearts    💖💖💖💖💖💖💖💖💖······   · 💗 💖
  moon      🌕🌕🌕🌕🌕🌕🌕🌕🌕🌑🌑🌑🌑🌑🌑   🌑 🌓 🌕
  stars     ★★★★★★★★★☆☆☆☆☆☆   ☆ ★
  dots      ●●●●●●●●●○○○○○○   ○ ◐ ●
  squares   🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜⬜   ⬜ 🟩
  ascii     #########------   - = #
```

Elige uno por su nombre. Así se ve cada uno en tu README (los estilos con
emojis, con `bar_length 15`; mira la nota más abajo):

```text
/langstats:style bars
```

```txt
Python      ███████████▒░░░░░░░░░░░░░   45.00 %
TypeScript  ███████▓░░░░░░░░░░░░░░░░░   30.00 %
Go          ███▓░░░░░░░░░░░░░░░░░░░░░   15.00 %
```

```text
/langstats:style flowers
```

```txt
Python      🌸🌸🌸🌸🌸🌸🌸········   45.00 %
TypeScript  🌸🌸🌸🌸🌱··········   30.00 %
Go          🌸🌸🌱············   15.00 %
```

```text
/langstats:style rocket
```

```txt
Python      💮💮💮💮💮💮💮········   45.00 %
TypeScript  💮💮💮💮🚀··········   30.00 %
Go          💮💮🚀············   15.00 %
```

```text
/langstats:style hearts
```

```txt
Python      💖💖💖💖💖💖💖········   45.00 %
TypeScript  💖💖💖💖💗··········   30.00 %
Go          💖💖💗············   15.00 %
```

```text
/langstats:style moon
```

```txt
Python      🌕🌕🌕🌕🌕🌕🌕🌑🌑🌑🌑🌑🌑🌑🌑   45.00 %
TypeScript  🌕🌕🌕🌕🌓🌑🌑🌑🌑🌑🌑🌑🌑🌑🌑   30.00 %
Go          🌕🌕🌓🌑🌑🌑🌑🌑🌑🌑🌑🌑🌑🌑🌑   15.00 %
```

```text
/langstats:style stars
```

```txt
Python      ★★★★★★★★★★★☆☆☆☆☆☆☆☆☆☆☆☆☆☆   45.00 %
TypeScript  ★★★★★★★★☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆   30.00 %
Go          ★★★★☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆   15.00 %
```

```text
/langstats:style dots
```

```txt
Python      ●●●●●●●●●●●◐○○○○○○○○○○○○○   45.00 %
TypeScript  ●●●●●●●◐○○○○○○○○○○○○○○○○○   30.00 %
Go          ●●●●○○○○○○○○○○○○○○○○○○○○○   15.00 %
```

```text
/langstats:style squares
```

```txt
Python      🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜⬜   45.00 %
TypeScript  🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   30.00 %
Go          🟩🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   15.00 %
```

```text
/langstats:style ascii
```

```txt
Python      ###########=-------------   45.00 %
TypeScript  #######=-----------------   30.00 %
Go          ####---------------------   15.00 %
```

O usa tus propios símbolos, **de vacío a lleno**. Con dos símbolos basta (vacío
y lleno); con tres o más, los del medio marcan un paso lleno a medias:

```text
/langstats:style "·🌱🌸"       vacío · , medio 🌱 , lleno 🌸
/langstats:style "-#"          vacío - , lleno #
/langstats:style "· ❤️ 💖"     separados por espacios
```

Algunos ejemplos:

```text
/langstats:style "·🌱🌸"
```

```txt
Python      🌸🌸🌸🌸🌸🌸🌸········   45.00 %
TypeScript  🌸🌸🌸🌸🌱··········   30.00 %
Go          🌸🌸🌱············   15.00 %
```

```text
/langstats:style "▱▰"
```

```txt
Python      ▰▰▰▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱▱   45.00 %
TypeScript  ▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱   30.00 %
Go          ▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱   15.00 %
```

```text
/langstats:style "⚪🔵"
```

```txt
Python      🔵🔵🔵🔵🔵🔵🔵⚪⚪⚪⚪⚪⚪⚪⚪   45.00 %
TypeScript  🔵🔵🔵🔵🔵⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪   30.00 %
Go          🔵🔵⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪   15.00 %
```

```text
/langstats:style "· ❤️ 💖"
```

```txt
Python      💖💖💖💖💖💖💖········   45.00 %
TypeScript  💖💖💖💖❤️··········   30.00 %
Go          💖💖❤️············   15.00 %
```

Separa los símbolos con espacios cuando un emoji esté formado por varios
caracteres (como ❤️ o las banderas); si una barra se ve rota, suele ser por eso.

El nuevo estilo se usa en la siguiente publicación. Los emojis ocupan casi el
doble que otros caracteres, así que quizá quieras una barra más corta:
`run config set bar_length 15`.

## Comandos

| Comando | Qué hace |
| --- | --- |
| `/langstats:setup` | Configuración guiada: conexión con GitHub, repositorio, sección del README, publicación automática. |
| `/langstats:stats [--days N] [--project NOMBRE]` | Tiempo y porcentaje por lenguaje, y tiempo por proyecto. `--days 0` abarca todo el historial. |
| `/langstats:publish [--dry-run]` | Actualiza la sección del README, o te da el bloque para pegar si GitHub no está conectado. `--dry-run` muestra el bloque y dónde iría, sin cambiar nada. |
| `/langstats:snippet` | Te da el bloque con sus marcadores para pegarlo a mano, copiado al portapapeles cuando es posible. |
| `/langstats:style [nombre \| símbolos]` | Sin argumentos, lista los estilos de barra con una vista previa. Con un nombre (`flowers`) o tus propios símbolos (`"·🌱🌸"`), cambia el estilo. |

Las mismas acciones están disponibles desde una terminal con el lanzador del
plugin instalado (`~/.claude/plugins/cache/codecruz/langstats/<versión>/scripts/`):

```sh
run stats --days 30          # tabla de lenguajes de los últimos 30 días
run publish --dry-run        # muestra el bloque sin cambiar nada
run snippet --copy           # bloque para pegar, copiado al portapapeles
run style flowers            # cambia el estilo de las barras
run doctor                   # comprueba que todo está listo para publicar
run config show              # configuración actual
run config set top_n 5       # cambia un ajuste
run config unset top_n       # vuelve al valor por defecto
```

En Windows, usa `run.cmd` en lugar de `run`.

## Configuración

La configuración se guarda en `~/.claude/langstats/config.json`. No hace falta
editarla: usa `/langstats:setup` o `run config set <clave> <valor>`. Un valor no
válido nunca rompe nada: se avisa y se usa el valor por defecto.

| Clave | Por defecto | Significado |
| --- | --- | --- |
| `mode` | `auto` | Cómo publicar: `auto`, `git` (clon local), `gh` (CLI de GitHub) o `manual` (bloque para pegar; nunca contacta con GitHub) |
| `readme_repo_path` | ninguno | Ruta de un clon local del repositorio de tu perfil |
| `readme_repo` | ninguno | Repositorio como `propietario/repo`. Vacío significa el repositorio de tu perfil, `<login>/<login>` |
| `readme_file` | `README.md` | Archivo que se actualiza dentro del repositorio |
| `section` | `langstats` | Nombre de los marcadores `<!--START_SECTION:nombre-->` / `<!--END_SECTION:nombre-->` |
| `range_days` | `7` | Días incluidos; hoy cuenta como uno. `0` = todo el historial |
| `top_n` | `7` | Filas del bloque, `Other` incluida |
| `min_percent` | `0.5` | Los lenguajes por debajo de este porcentaje van a `Other` |
| `blocks` | `░▒▓█` | Símbolos de la barra, de vacío a lleno: un nombre de estilo (`flowers`, `rocket`, `hearts`…) o tus propios símbolos. Lo más fácil es `/langstats:style` |
| `bar_length` | `25` | Ancho de la barra en caracteres |
| `name_width` | `32` | Ancho de la columna del lenguaje |
| `show_time` | `false` | Muestra también el tiempo por lenguaje en el bloque del README |
| `show_title` | `false` | Añade una línea de fechas "From … To …" encima del bloque |
| `timeout_minutes` | `15` | Los huecos entre dos registros más largos que esto no cuentan (es una pausa) |
| `track_reads` | `true` | Cuenta los archivos que Claude lee, no solo los que edita |
| `exclude_languages` | `[]` | Lenguajes que se dejan fuera del todo, por ejemplo `["HTML", "CSS"]` |
| `count_non_code` | `false` | Cuenta también los formatos de datos, configuración y texto (Markdown, JSON, YAML, TOML, XML...) y los archivos no reconocidos. La lista es `non_code` en `scripts/languages.json` |
| `language_overrides` | `{}` | Tus propias asociaciones, por ejemplo `{".tpl": "Smarty"}` |
| `ignore_globs` | `.claude`, `node_modules`, `.git`, `vendor`, `dist`, `.venv` | Carpetas o patrones que nunca se registran |
| `auto_publish` | `false` | Publica al cerrar una sesión |
| `publish_interval_hours` | `12` | Horas mínimas entre dos publicaciones automáticas |
| `commit_message` | `chore(readme): update language stats` | Mensaje del commit que actualiza el README |
| `retention_days` | `365` | Los registros de este ordenador más antiguos se borran. `0` = guardarlos siempre |
| `share_data` | `false` | Suma varios ordenadores. Desactivado: solo se sube el bloque de porcentajes. Activado: también un archivo pequeño con los minutos sumados (ver [Varios ordenadores](#varios-ordenadores)) |
| `data_file` | `.langstats/stats.json` | Archivo con los totales sumados y anónimos de tus ordenadores (ver [Varios ordenadores](#varios-ordenadores)) |
| `data_repo` | ninguno | Guarda ese archivo en otro repositorio, por ejemplo uno privado, `<tú>/langstats-data` |

Define la variable de entorno `LANGSTATS_HOME` para guardar los datos en otro
sitio que no sea `~/.claude/langstats`.

## Cómo se cuenta el tiempo

1. Cada vez que Claude lee o edita un archivo (`Read`, `Edit`, `Write`,
   `MultiEdit`, `NotebookEdit`), langstats escribe un registro: la hora, el
   lenguaje y el nombre de la carpeta del proyecto. Imágenes, PDF, fuentes,
   audio, vídeo y binarios (`skip_extensions` en `languages.json`) no son código,
   así que no se registran; una entrada en `language_overrides` para alguno de
   ellos vuelve a contarlo.
2. El lenguaje se detecta por el nombre del archivo: primero nombres exactos
   (`Dockerfile`, `Makefile`), luego terminaciones compuestas (`.blade.php`),
   luego la extensión y, para scripts sin extensión, la línea `#!`. Las reglas
   están en [`scripts/languages.json`](scripts/languages.json).
3. Todos los registros van a una única línea de tiempo, incluso los de sesiones
   en paralelo, así que el tiempo nunca se cuenta dos veces.
4. El tiempo entre dos registros consecutivos se suma al lenguaje del primero,
   salvo que supere `timeout_minutes`: eso cuenta como una pausa.

## Rendimiento

langstats está pensado para que no se note:

- El hook es **asíncrono**: Claude Code lo lanza y sigue trabajando sin
  esperarlo.
- Cada registro cuesta un proceso de Python breve (unos 25 ms en un portátil),
  sin acceso a la red y sin git. El lanzador recuerda el intérprete de Python
  que encontró y el código se carga ya compilado.
- Solo lo activan las lecturas y ediciones de archivos. Los comandos de terminal,
  las búsquedas y el resto de herramientas de Claude no se tocan.
- La publicación nunca ocurre dentro de un hook. Al cerrar una sesión, langstats
  solo comprueba una fecha y, si toca publicar, lo hace en segundo plano.

## Privacidad

- Todo se queda en tu ordenador, en `~/.claude/langstats/heartbeats/`, un
  archivo por día.
- Cada registro guarda la hora, el lenguaje, el nombre de la carpeta del
  proyecto, la herramienta y un identificador corto de sesión. **Nunca se
  guardan rutas ni contenido de archivos.**
- Al publicar, **a tu repositorio solo va el bloque de estadísticas**: nombres
  de lenguajes y porcentajes, sin tiempos.
- Solo si activas `share_data` para sumar varios ordenadores se sube además un
  archivo pequeño con los minutos sumados por día y lenguaje, sin
  identificadores de ordenador, proyectos ni rutas, idealmente a un repositorio
  privado (ver [Varios ordenadores](#varios-ordenadores)).
- En modo manual, o mientras GitHub no esté conectado, no se envía nada.

## Solución de problemas

Empieza por el comando de comprobación, que te dice qué falta:

```sh
run doctor
```

| Problema | Solución |
| --- | --- |
| "No activity recorded yet" | Las estadísticas aparecen cuando Claude ha leído o editado unos cuantos archivos. Hacen falta al menos dos registros para medir tiempo. |
| "GitHub is not connected" | Instala la [CLI de GitHub](https://cli.github.com/), ejecuta `gh auth login` y después `/langstats:setup`. O usa `/langstats:snippet` y pega el bloque a mano. |
| "… was not found" (repositorio) | El README de tu perfil vive en un repositorio público que se llama exactamente como tu usuario (`<tú>/<tú>`). Créalo en GitHub con un `README.md`. |
| "the README has no … markers" | Añade las dos líneas de marcadores donde quieras las estadísticas, o deja que `/langstats:setup` las añada. |
| El bloque vuelve a cambiar solo | Otra herramienta escribe en la misma sección. Usa otra `section`. |
| "Python 3.9+ not found" | Instala Python 3.9 o posterior, o define `LANGSTATS_PYTHON` con la ruta de tu intérprete. |
| Cada ordenador sustituye las estadísticas del otro | Es el comportamiento por defecto. Activa `share_data` en todos los ordenadores para sumarlos (ver [Varios ordenadores](#varios-ordenadores)). |
| Las estadísticas salen dobles tras reinstalar | Un ordenador que perdió `~/.claude/langstats/` no puede retirar su aportación anterior; desaparece sola cuando esos días salen del rango (7 días por defecto). |
| La publicación automática no hace nada | Revisa `~/.claude/langstats/publish.log`. Se ejecuta como mucho una vez cada `publish_interval_hours`. |

## Desinstalar

```text
/plugin uninstall langstats@codecruz
```

Tus datos se quedan en `~/.claude/langstats/`; borra esa carpeta para
eliminarlos. El bloque de tu README sigue ahí hasta que lo borres, junto con sus
marcadores.

## Actualizar desde langtime 0.1.0

En la primera ejecución, los datos de `~/.claude/langtime/` (configuración y
registros) se copian una sola vez a `~/.claude/langstats/`. La variable
`LANGTIME_HOME` se sustituye por `LANGSTATS_HOME`.

## Contribuir

Consulta [CONTRIBUTING.es.md](CONTRIBUTING.es.md) · [CHANGELOG.md](CHANGELOG.md)

## Licencia

[MIT](LICENSE)
