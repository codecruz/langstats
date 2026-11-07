# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.4.0] - 2026-11-07

### Changed
- The default `section` is now `langstats` (markers `<!--START_SECTION:langstats-->` /
  `<!--END_SECTION:langstats-->`). If your README still has markers with another name,
  rename them or keep the old name with `config set section <name>`.
- The README shows an example of every bar style and of custom icons.

## [0.3.0] - 2026-11-07

### Added
- Optional `share_data` (off by default, so only the percentages block is ever
  uploaded): several computers add up instead of overwriting each other. The repository
  keeps one anonymous file, `.langstats/stats.json`, with the combined seconds per
  day and language of the days shown (no computer ids, projects or paths; older
  days are pruned). Each computer replaces only its own share, remembered
  locally. `data_repo` keeps that file in a separate (private) repository.
  Concurrent publishes are detected and retried.
- Configurable bar style: `/langstats:style` lists the styles with a preview
  (`bars`, `flowers` 🌸, `rocket` 🚀, `hearts`, `moon`, `stars`, `dots`, `squares`,
  `ascii`) and sets one by name or with your own symbols, from empty to full.
  Symbols can be separated by spaces, so emoji made of several characters work.
  `/langstats:setup` asks for the style.

### Fixed
- A publish with no data no longer resets the auto-publish interval.

### Documentation
- README and CONTRIBUTING rewritten for clarity and available in English and
  Spanish (`README.es.md`, `CONTRIBUTING.es.md`), with quick start,
  troubleshooting and uninstall sections.

## [0.2.0] - 2026-11-07

First public release, renamed from the personal prototype `langtime` (v0.1.0).

### Added
- `mode: auto` (default): publishes through a local clone if configured, through
  the GitHub API when `gh` is logged in (to the profile README `<login>/<login>`
  by default), and otherwise falls back to manual.
- Manual publishing for users without a GitHub connection: `/langstats:snippet`
  (and `publish` while not connected) prints the block with its markers, copies it
  to the clipboard when possible and saves it to `readme-snippet.md`.
- `/langstats:setup`: guided configuration that detects the GitHub connection,
  with a `doctor` check and an optional insertion of the section markers.
- `langstats.py config show|set|unset|path` so the configuration is never edited by hand.
- `gh` mode: update the README through the GitHub API, no local clone needed.
- `scripts/languages.json`: language maps can be extended by pull request; new
  `language_overrides` config key.
- `retention_days` (default 365): heartbeat files older than that are deleted.
- Heartbeats carry a schema version (`"v": 1`); lines without it are still read.
- Cross-platform launchers `scripts/run` (sh) and `scripts/run.cmd` that try
  `python3`, `python` and `py -3`.
- Test suite (pytest), CI on Linux, macOS and Windows with Python 3.9 and 3.12, ruff.

### Performance
- The `PostToolUse` and `SessionStart` hooks run async, so they never block Claude.
- The launchers cache the Python interpreter; `scripts/cli.py` loads the code from
  cached bytecode; the hook path skips argparse, subprocess and typing.
  About 25 ms per call, down from about 60 ms.

### Changed
- Renamed `langtime` → `langstats` everywhere; `LANGSTATS_HOME` replaces `LANGTIME_HOME`.
- No personal defaults: `readme_repo_path` and `readme_repo` default to `null`.
- Default bar blocks are now `░▒▓█` (the classic default).
- Slash commands run the script from `${CLAUDE_PLUGIN_ROOT}` directly; the copy made
  at `SessionStart` is gone, so commands work right after installing.
- An invalid config never breaks a hook: it is reported on stderr and defaults are used.

### Migration
- `~/.claude/langtime/` is copied to `~/.claude/langstats/` once, on first run,
  when the destination does not exist yet.

[Unreleased]: https://github.com/codecruz/langstats/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/codecruz/langstats/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/codecruz/langstats/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/codecruz/langstats/releases/tag/v0.2.0
