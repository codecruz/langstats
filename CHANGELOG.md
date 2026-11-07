# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/codecruz/langstats/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/codecruz/langstats/releases/tag/v0.2.0
