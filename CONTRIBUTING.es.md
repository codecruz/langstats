# Contribuir

[English](CONTRIBUTING.md) · **Español**

Gracias por ayudar. langstats es un único script de Python 3.9+ **sin
dependencias en tiempo de ejecución**; por favor, mantenlo así.

## Estructura del proyecto

| Ruta | Qué es |
| --- | --- |
| `scripts/langstats.py` | Toda la lógica: hooks, estadísticas, publicación, configuración |
| `scripts/cli.py` | Punto de entrada de los lanzadores (permite que Python cachee el bytecode) |
| `scripts/run`, `scripts/run.cmd` | Lanzadores para sh y Windows: buscan Python y ejecutan `cli.py` |
| `scripts/languages.json` | Reglas de nombre de archivo → lenguaje |
| `hooks/hooks.json` | Los hooks de Claude Code |
| `commands/*.md` | Los comandos `/langstats:*` |
| `tests/` | Tests con pytest |
| `tools/release.py` | Prepara una versión (ver [Publicar una versión](#publicar-una-versión)) |

## Desarrollo

```sh
pip install pytest ruff
python -m pytest -q
ruff check . && ruff format --check .
```

Prueba tu copia en Claude Code sin instalarla:

```sh
LANGSTATS_HOME=/tmp/langstats-dev claude --plugin-dir /ruta/a/langstats
```

`LANGSTATS_HOME` mantiene tus datos de prueba lejos de tus estadísticas reales.

## Añadir o corregir un lenguaje

Edita `scripts/languages.json`. La detección prueba estos grupos en orden y se
queda con la primera coincidencia:

1. `filenames`: nombres de archivo exactos, por ejemplo `"Dockerfile": "Docker"`.
2. `prefixes` y `suffixes`: nombres compuestos, por ejemplo `"Dockerfile.": "Docker"`,
   `".blade.php": "Blade Template"`.
3. `extensions`: la última extensión, con su punto, por ejemplo `".py": "Python"`.
4. `shebangs`: el intérprete de la línea `#!`, solo para archivos sin extensión.

Usa los nombres de GitHub Linguist para que las estadísticas sean
comparables. Añade un caso en `tests/test_detect.py` y ejecuta los tests.

Si una asociación es una preferencia personal y no una corrección, usa el ajuste
`language_overrides` en lugar de cambiar las reglas compartidas.

## Normas para los cambios

- **Los hooks nunca deben romper ni ralentizar una sesión de Claude Code.** Ante
  cualquier error escriben en stderr y salen con código 0. No importes módulos
  pesados ni llames a la red, a git u otros programas desde la ruta del hook;
  `tests/test_performance.py` lo comprueba.
- Mantén estable el formato de la salida del README.
- Un tema por pull request, con tests.
- Actualiza `CHANGELOG.md` en *Unreleased*.
- Actualiza la documentación en **los dos idiomas**: `README.md` y `README.es.md`.

## Publicar una versión

Claude Code solo actualiza el plugin cuando cambia su **número de versión**, así
que un push sin versión nueva nunca llega a los usuarios. Para publicar:

1. Describe los cambios en *Unreleased* de `CHANGELOG.md`.
2. Ejecuta `python3 tools/release.py X.Y.Z`. Pone la versión en
   `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
   `scripts/langstats.py` y `pyproject.toml`, y pasa *Unreleased* a la nueva
   versión en `CHANGELOG.md`.
3. Haz commit (`release: X.Y.Z`) y push a `main`.

Cuando el CI pasa, el workflow Release etiqueta el commit como `vX.Y.Z` y publica
una release en GitHub con su sección del changelog. Quien tenga la
actualización automática activada recibe la versión nueva en su siguiente
sesión; el resto ejecuta `claude plugin update langstats@codecruz`.
