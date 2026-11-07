# Contributing

Thanks for helping. The runtime is a single Python 3.9+ script with no
dependencies; keep it that way.

## Development

```sh
pip install pytest ruff
python -m pytest -q
ruff check . && ruff format --check .
```

Try the plugin locally without installing it:

```sh
claude --plugin-dir /path/to/langstats
```

Set `LANGSTATS_HOME=/tmp/langstats-dev` to keep test data away from your real stats.

## Adding or fixing a language

Edit `scripts/languages.json`. Detection tries, in order:

1. `filenames`: exact file names (`Dockerfile`, `Makefile`).
2. `prefixes` and `suffixes`: compound names (`Dockerfile.*`, `*.blade.php`, `.env*`).
3. `extensions`: the last extension, with its leading dot (`".py": "Python"`).
4. `shebangs`: the interpreter on the first line, only for files without extension.

Use the language names GitHub Linguist uses, so stats stay comparable.
Add a case to `tests/test_detect.py` and run the tests.

If a mapping is a personal preference rather than a fix, use the
`language_overrides` config key instead of changing the shared map.

## Pull requests

- One topic per PR, with tests.
- Update `CHANGELOG.md` under *Unreleased*.
- Hooks must never break a Claude Code session: on any error they write to stderr
  and exit with code 0.
