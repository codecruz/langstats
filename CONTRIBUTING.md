# Contributing

**English** · [Español](CONTRIBUTING.es.md)

Thanks for helping. langstats is a single Python 3.9+ script with **no runtime
dependencies**; please keep it that way.

## Project layout

| Path | What it is |
| --- | --- |
| `scripts/langstats.py` | All the logic: hooks, stats, publishing, configuration |
| `scripts/cli.py` | Entry point used by the launchers (lets Python cache the bytecode) |
| `scripts/run`, `scripts/run.cmd` | Launchers for sh and Windows: find Python and run `cli.py` |
| `scripts/languages.json` | File name → language rules |
| `hooks/hooks.json` | The Claude Code hooks |
| `commands/*.md` | The `/langstats:*` slash commands |
| `tests/` | pytest suite |

## Development

```sh
pip install pytest ruff
python -m pytest -q
ruff check . && ruff format --check .
```

Try your copy in Claude Code without installing it:

```sh
LANGSTATS_HOME=/tmp/langstats-dev claude --plugin-dir /path/to/langstats
```

`LANGSTATS_HOME` keeps your test data away from your real stats.

## Adding or fixing a language

Edit `scripts/languages.json`. Detection tries these groups in order and stops at
the first match:

1. `filenames`: exact file names, e.g. `"Dockerfile": "Docker"`.
2. `prefixes` and `suffixes`: compound names, e.g. `"Dockerfile.": "Docker"`,
   `".blade.php": "Blade Template"`.
3. `extensions`: the last extension, with its leading dot, e.g. `".py": "Python"`.
4. `shebangs`: the interpreter in the `#!` line, only for files without extension.

Use the names GitHub Linguist uses, so stats stay comparable. Add a
case to `tests/test_detect.py` and run the tests.

If a mapping is a personal preference rather than a fix, use the
`language_overrides` setting instead of changing the shared rules.

## Rules for changes

- **Hooks must never break or slow down a Claude Code session.** On any error
  they write to stderr and exit with code 0. Do not import heavy modules or call
  the network, git or other programs from the hook path;
  `tests/test_performance.py` checks this.
- Keep the README output format stable.
- One topic per pull request, with tests.
- Update `CHANGELOG.md` under *Unreleased*.

## Releasing

Claude Code only offers an update when the **version number** changes, so every
release must bump it in `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `scripts/langstats.py` (`__version__`) and
`pyproject.toml` (`tests/test_repo.py` checks they match), move *Unreleased* to
the new version in `CHANGELOG.md`, and tag it (`vX.Y.Z`). Users then run
`claude plugin update langstats@codecruz`.
- Update the documentation in **both languages**: `README.md` and `README.es.md`.
