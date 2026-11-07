# langstats

Language stats for [Claude Code](https://claude.com/claude-code).
langstats records which languages Claude reads and edits in each session and
rewrites a block of your GitHub profile README with the percentages, drawn as text bars.

> **What it measures:** the time **Claude** spends working in each language,
> not the time you spend typing in your IDE.

```txt
TypeScript                      ██████░░░░░░░░░░░░░░░░░░░   24.10 %
PHP                             █████░░░░░░░░░░░░░░░░░░░░   20.04 %
Python                          ████▒░░░░░░░░░░░░░░░░░░░░   17.90 %
Markdown                        ███░░░░░░░░░░░░░░░░░░░░░░   12.18 %
Bash                            ██░░░░░░░░░░░░░░░░░░░░░░░   07.45 %
JSON                            █▒░░░░░░░░░░░░░░░░░░░░░░░   05.16 %
Other                           ███▒░░░░░░░░░░░░░░░░░░░░░   13.17 %
```

## Install

```text
/plugin marketplace add codecruz/langstats
/plugin install langstats@codecruz
```

Requirements: Python 3.9+ (`python3`, `python` or `py -3`) and either `git` or the
[`gh`](https://cli.github.com/) CLI. Works on macOS, Linux and Windows.

Tracking starts right away. Then run:

```text
/langstats:setup
```

## Setup

`/langstats:setup` asks a few questions and saves the answers with
`langstats.py config set`:

1. **Mode**: `git` (commit and push from a local clone of your profile repo) or
   `gh` (update the file through the GitHub API, no clone).
2. **Target**: the clone path (`readme_repo_path`) or `owner/repo` (`readme_repo`).
3. **Section name**: the README block to rewrite, between
   `<!--START_SECTION:langstats-->` and `<!--END_SECTION:langstats-->`.
4. **Auto-publish** on session end.

It then checks `git` or `gh auth status`, the repo and the markers, and offers to
append the markers to the end of your README if they are missing.

## Commands

| Command | What it does |
| --- | --- |
| `/langstats:stats [--days N] [--project NAME]` | Language table with time per language and per project. `--days 0` = all time. |
| `/langstats:publish [--dry-run]` | Rewrite the README section. With `--dry-run`, print the block and change nothing. |
| `/langstats:setup` | Guided configuration. |

The script can also be used directly:

```sh
scripts/run stats --days 30
scripts/run publish --dry-run
scripts/run config show
scripts/run config set top_n 5
scripts/run doctor
```

(`scripts\run.cmd` on Windows.)

## Configuration

Stored in `~/.claude/langstats/config.json` (or `$LANGSTATS_HOME/config.json`) and
merged over the defaults. An invalid value never breaks a hook: it is reported and
the default is used.

| Key | Default | Description |
| --- | --- | --- |
| `mode` | `git` | `git` = local clone, `gh` = GitHub API through `gh` |
| `readme_repo_path` | `null` | Local clone of the profile repo (mode `git`) |
| `readme_repo` | `null` | `owner/repo` (mode `gh`) |
| `readme_file` | `README.md` | File inside the repo |
| `section` | `langstats` | Marker name |
| `range_days` | `7` | Days included, today counts as one; `0` = all |
| `top_n` | `7` | Rows in the block, `Other` included |
| `min_percent` | `0.5` | Languages below this go to `Other` |
| `blocks` | `░▒▓█` | Bar characters: empty, partial…, full |
| `bar_length` / `name_width` | `25` / `32` | Bar width, language column width |
| `show_time` / `show_title` | `false` | Add time per language / a date range title |
| `timeout_minutes` | `15` | Longer gaps between heartbeats are not counted |
| `track_reads` | `true` | Count `Read` as activity, not only edits |
| `exclude_languages` | `[]` | Languages left out of the totals |
| `language_overrides` | `{}` | Extension or file name → language, e.g. `{".tpl": "Smarty"}` |
| `ignore_globs` | `.claude`, `node_modules`, `.git`, `vendor`, `dist`, `.venv` | Paths never tracked (matched against each path component and the full path) |
| `auto_publish` | `false` | Publish when a session ends |
| `publish_interval_hours` | `12` | Minimum time between auto-publishes |
| `commit_message` | `chore(readme): update language stats` | Commit message |
| `retention_days` | `365` | Heartbeat files older than this are deleted; `0` = keep |

## How time is counted

Every `Read`, `Edit`, `Write`, `MultiEdit` and `NotebookEdit` writes a heartbeat.
All heartbeats in the range go on a single timeline, so parallel sessions are
never counted twice. The gap between two consecutive heartbeats is added to the
language of the first one if it is no longer than `timeout_minutes`.

## Scheduled publishing (cron)

Instead of `auto_publish`, you can publish on a schedule:

```cron
0 */6 * * * /path/to/langstats/scripts/run publish >> ~/.claude/langstats/cron.log 2>&1
```

The installed plugin lives under `~/.claude/plugins/`; `scripts/run` works from any
directory. On Windows, use Task Scheduler with `scripts\run.cmd publish`.

## Privacy

- Everything stays on your machine in `~/.claude/langstats/heartbeats/*.jsonl`,
  one file per day.
- Heartbeats store a timestamp, the language, the project folder name, the tool
  and a short session id. **File paths and file contents are never stored.**
- Nothing is sent anywhere except the rendered block, and only to the repository
  you configure, when you publish.

## Upgrading from langtime 0.1.0

On first run, `~/.claude/langtime/` (config and heartbeats) is copied to
`~/.claude/langstats/` if that directory does not exist yet. `LANGTIME_HOME` is
replaced by `LANGSTATS_HOME`. Old heartbeat lines are read as they are.

## License

[MIT](LICENSE)
