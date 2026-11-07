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

Requirements: Python 3.9+ (`python3`, `python` or `py -3`). Works on macOS,
Linux and Windows. The [GitHub CLI](https://cli.github.com/) is optional: with
it, langstats updates your README by itself; without it, you get the block to
paste by hand.

Tracking starts right away. Then run:

```text
/langstats:setup
```

## Publishing: automatic or by hand

The default `mode` is `auto`, which picks the first option that applies:

1. **A local clone** (`readme_repo_path` set): commit and push from it with `git`.
2. **GitHub connected** (`gh auth login` done): update the section of your
   profile README, `github.com/<login>/<login>`, through the GitHub API, or the
   repository in `readme_repo`. No clone needed.
3. **Not connected**: nothing is sent anywhere. `/langstats:publish` and
   `/langstats:snippet` print the block with its markers, copy it to the
   clipboard when possible and save it to `~/.claude/langstats/readme-snippet.md`,
   so you can paste it into your README yourself:

````markdown
<!--START_SECTION:langstats-->

```txt
TypeScript                      ██████░░░░░░░░░░░░░░░░░░░   24.10 %
...
```

<!--END_SECTION:langstats-->
````

Paste it where you want the stats, replacing the previous block if there is one.
Once you connect GitHub, the next publish updates exactly that section and
nothing else in the README.

Force one behaviour with `mode`: `git`, `gh` or `manual` (never contacts GitHub).

## Setup

`/langstats:setup` checks whether GitHub is connected and walks you through it:

- **Connected**: confirms the repository (your profile README by default), the
  section name, and whether to auto-publish when a session ends. If the markers
  are missing, it offers to append them to the end of the README.
- **Not connected**: explains how to connect (`gh auth login`), use a local
  clone, or stay in manual mode with `/langstats:snippet`.

Answers are saved with `langstats.py config set`; `config.json` is never edited
by hand.

## Commands

| Command | What it does |
| --- | --- |
| `/langstats:stats [--days N] [--project NAME]` | Language table with time per language and per project. `--days 0` = all time. |
| `/langstats:publish [--dry-run]` | Update the README section, or print the block to paste when GitHub is not connected. With `--dry-run`, show the block and the target and change nothing. |
| `/langstats:snippet` | Print the block with its markers to paste by hand, and copy it to the clipboard when possible. |
| `/langstats:setup` | Guided configuration. |

The script can also be used directly:

```sh
scripts/run stats --days 30
scripts/run publish --dry-run
scripts/run snippet --copy
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
| `mode` | `auto` | `auto`, `git` (local clone), `gh` (GitHub API through `gh`) or `manual` (print the block to paste) |
| `readme_repo_path` | `null` | Local clone of the profile repo |
| `readme_repo` | `null` | `owner/repo`; with `gh` and no value, your profile repo `<login>/<login>` |
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

## Performance

langstats is built to be invisible:

- The `PostToolUse` hook is **async**: Claude Code does not wait for it.
- Each call is one short Python process (about 25 ms on a laptop): the launcher
  caches the interpreter it found in `~/.claude/langstats/.python`, the code
  is loaded from cached bytecode, and the hook path skips argparse, subprocess
  and every network or git call.
- Only `Read`, `Edit`, `Write`, `MultiEdit` and `NotebookEdit` trigger it; bash
  commands, searches and everything else are not hooked.
- Publishing never runs inside a hook. `SessionEnd` only checks a timestamp and,
  when auto-publish is due, starts a detached background process.

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
- Nothing is sent anywhere except the rendered block, and only to your
  repository, when you publish. In `manual` mode, or while GitHub is not
  connected, nothing leaves your machine.

## Upgrading from langtime 0.1.0

On first run, `~/.claude/langtime/` (config and heartbeats) is copied to
`~/.claude/langstats/` if that directory does not exist yet. `LANGTIME_HOME` is
replaced by `LANGSTATS_HOME`. Old heartbeat lines are read as they are.

## License

[MIT](LICENSE)
