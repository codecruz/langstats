# langstats

**English** · [Español](README.es.md)

Language stats for [Claude Code](https://claude.com/claude-code).
langstats records which programming languages Claude reads and edits while it
works for you, and turns them into a block for your GitHub profile README, drawn as text bars:

```txt
TypeScript                      ██████░░░░░░░░░░░░░░░░░░░   24.10 %
PHP                             █████░░░░░░░░░░░░░░░░░░░░   20.04 %
Python                          ████▒░░░░░░░░░░░░░░░░░░░░   17.90 %
Markdown                        ███░░░░░░░░░░░░░░░░░░░░░░   12.18 %
Bash                            ██░░░░░░░░░░░░░░░░░░░░░░░   07.45 %
JSON                            █▒░░░░░░░░░░░░░░░░░░░░░░░   05.16 %
Other                           ███▒░░░░░░░░░░░░░░░░░░░░░   13.17 %
```

> **What it measures:** the time **Claude** spends working in each language.
> It does not measure the time you spend typing in your own editor.

- Works on **macOS, Linux and Windows**.
- **Does not slow Claude down**: the hook runs in the background (see [Performance](#performance)).
- **GitHub is optional**: connected, it updates your README by itself; not
  connected, it gives you the block to paste by hand.

## Contents

- [Quick start](#quick-start)
- [Publishing: automatic or by hand](#publishing-automatic-or-by-hand)
- [Commands](#commands)
- [Configuration](#configuration)
- [How time is counted](#how-time-is-counted)
- [Performance](#performance)
- [Privacy](#privacy)
- [Troubleshooting](#troubleshooting)
- [Uninstall](#uninstall)

## Quick start

**1. Install the plugin.** In Claude Code:

```text
/plugin marketplace add codecruz/langstats
/plugin install langstats@codecruz
```

Then start a new session, or run `/reload-plugins`.

**Requirements:** Python 3.9 or newer, available as `python3`, `python` or `py -3`.
Nothing else is needed. The [GitHub CLI](https://cli.github.com/) (`gh`) is
optional; it lets langstats update your README automatically.

**2. Run the guided setup:**

```text
/langstats:setup
```

It detects whether GitHub is connected and asks a few questions: the
repository, the section of the README to update, and whether to publish
automatically.

**3. Work as usual.** Every file Claude reads or edits is recorded. Check your
stats at any time with:

```text
/langstats:stats
```

**4. Publish:**

```text
/langstats:publish
```

## Publishing: automatic or by hand

### Which option is mine?

| Your situation | What langstats does | What you do |
| --- | --- | --- |
| `gh` is installed and you ran `gh auth login` | Updates the section of your profile README (`github.com/<you>/<you>`) through the GitHub API | Nothing: run `/langstats:publish`, or turn on auto-publish |
| You have a local clone of your profile repository | Commits and pushes the change with `git` | Set the clone path in `/langstats:setup` |
| GitHub is not connected | Sends nothing anywhere and gives you the block | Paste the block into your README by hand |

The default mode, `auto`, chooses for you in that order: a configured local
clone first, then the GitHub CLI, then manual.

### Automatic (GitHub connected)

langstats only rewrites the text between two markers in your README and leaves
everything else as it is:

```markdown
<!--START_SECTION:langstats-->
<!--END_SECTION:langstats-->
```

Put those two lines where you want the stats to appear. `/langstats:setup` can
add them for you at the end of the README, after asking first. If the content
has not changed, no commit is made.

To publish without thinking about it, turn on auto-publish:

```text
/langstats:setup        (answer "yes" to auto-publish)
```

With auto-publish on, langstats publishes when a Claude Code session ends, at
most once every 12 hours (`publish_interval_hours`). It runs in a background
process, so closing Claude Code is never delayed. Its output goes to
`~/.claude/langstats/publish.log`.

### By hand (GitHub not connected)

Run:

```text
/langstats:snippet
```

You get a block like this one, also copied to your clipboard when possible and
saved to `~/.claude/langstats/readme-snippet.md`:

````markdown
<!--START_SECTION:langstats-->

```txt
TypeScript                      ██████░░░░░░░░░░░░░░░░░░░   24.10 %
...
```

<!--END_SECTION:langstats-->
````

1. Open your profile repository on GitHub (`github.com/<you>/<you>`) and edit
   `README.md`.
2. Paste the block where you want the stats. If an older block with the same
   markers is already there, replace it whole.
3. Commit.

`/langstats:publish` does the same when GitHub is not connected. If you connect
GitHub later (`gh auth login`), the next publish updates that same section
automatically.

## Commands

| Command | What it does |
| --- | --- |
| `/langstats:setup` | Guided configuration: GitHub connection, repository, README section, auto-publish. |
| `/langstats:stats [--days N] [--project NAME]` | Time and percentage per language, plus time per project. `--days 0` covers all time. |
| `/langstats:publish [--dry-run]` | Updates the README section, or gives you the block to paste when GitHub is not connected. `--dry-run` shows the block and where it would go, and changes nothing. |
| `/langstats:snippet` | Gives you the block with its markers to paste by hand, copied to the clipboard when possible. |

The same actions are available from a terminal through the launcher in the
installed plugin (`~/.claude/plugins/cache/codecruz/langstats/<version>/scripts/`):

```sh
run stats --days 30          # language table for the last 30 days
run publish --dry-run        # show the block without changing anything
run snippet --copy           # block to paste, copied to the clipboard
run doctor                   # check that everything is ready to publish
run config show              # current configuration
run config set top_n 5       # change a setting
run config unset top_n       # back to the default
```

On Windows, use `run.cmd` instead of `run`.

## Configuration

The configuration lives in `~/.claude/langstats/config.json`. You don't need to
edit it: use `/langstats:setup` or `run config set <key> <value>`. An invalid
value never breaks anything; it is reported and the default is used.

| Key | Default | Meaning |
| --- | --- | --- |
| `mode` | `auto` | How to publish: `auto`, `git` (local clone), `gh` (GitHub CLI) or `manual` (block to paste; never contacts GitHub) |
| `readme_repo_path` | none | Path of a local clone of your profile repository |
| `readme_repo` | none | Repository as `owner/repo`. Empty means your profile repository, `<login>/<login>` |
| `readme_file` | `README.md` | File to update inside the repository |
| `section` | `langstats` | Name in the markers `<!--START_SECTION:name-->` / `<!--END_SECTION:name-->` |
| `range_days` | `7` | Days included, today counts as one. `0` = all time |
| `top_n` | `7` | Rows in the block, `Other` included |
| `min_percent` | `0.5` | Languages below this percentage go into `Other` |
| `blocks` | `░▒▓█` | Bar characters, from empty to full. For an emoji style use `·🚀💮` |
| `bar_length` | `25` | Bar width in characters |
| `name_width` | `32` | Width of the language column |
| `show_time` | `false` | Also show the time per language in the README block |
| `show_title` | `false` | Add a "From … To …" date line above the block |
| `timeout_minutes` | `15` | Gaps longer than this between two records are not counted (a pause) |
| `track_reads` | `true` | Count files Claude reads, not only the ones it edits |
| `exclude_languages` | `[]` | Languages left out entirely, e.g. `["Markdown", "JSON"]` |
| `language_overrides` | `{}` | Your own mappings, e.g. `{".tpl": "Smarty"}` |
| `ignore_globs` | `.claude`, `node_modules`, `.git`, `vendor`, `dist`, `.venv` | Folders or patterns that are never recorded |
| `auto_publish` | `false` | Publish when a session ends |
| `publish_interval_hours` | `12` | Minimum hours between two automatic publishes |
| `commit_message` | `chore(readme): update language stats` | Message of the commit that updates the README |
| `retention_days` | `365` | Records older than this are deleted. `0` = keep forever |

Set the environment variable `LANGSTATS_HOME` to store data somewhere other than
`~/.claude/langstats`.

## How time is counted

1. Each time Claude reads or edits a file (`Read`, `Edit`, `Write`, `MultiEdit`,
   `NotebookEdit`), langstats writes a record: the time, the language and the
   project folder name.
2. The language is detected from the file name: exact names first (`Dockerfile`,
   `Makefile`), then compound endings (`.blade.php`), then the extension, then
   the `#!` line for scripts without extension. The rules are in
   [`scripts/languages.json`](scripts/languages.json).
3. All records go on a single timeline, even from sessions running in parallel,
   so time is never counted twice.
4. The time between two consecutive records is added to the language of the
   first one, unless it is longer than `timeout_minutes`: that counts as a pause.

## Performance

langstats is designed to go unnoticed:

- The hook is **asynchronous**: Claude Code starts it and carries on without
  waiting for it.
- Each record costs one short Python process (about 25 ms on a laptop), with no
  network access and no git. The launcher remembers the Python interpreter it
  found, and the code is loaded already compiled.
- Only file reads and edits trigger it. Shell commands, searches and the rest of
  Claude's tools are not touched.
- Publishing never happens inside a hook. At the end of a session langstats only
  checks a date and, if a publish is due, starts it in the background.

## Privacy

- Everything stays on your computer, in `~/.claude/langstats/heartbeats/`, one
  file per day.
- Each record holds the time, the language, the project folder name, the tool
  and a short session id. **File paths and file contents are never stored.**
- The only thing that leaves your computer is the stats block, and only to your
  own repository, when you publish. In manual mode, or while GitHub is not
  connected, nothing is sent at all.

## Troubleshooting

Start with the check command, which says what is missing:

```sh
run doctor
```

| Problem | Solution |
| --- | --- |
| "No activity recorded yet" | Stats appear after Claude has read or edited a few files. At least two records are needed to measure time. |
| "GitHub is not connected" | Install the [GitHub CLI](https://cli.github.com/), run `gh auth login`, then `/langstats:setup`. Or use `/langstats:snippet` and paste by hand. |
| "… was not found" (repository) | Your profile README lives in a public repository named exactly like your username (`<you>/<you>`). Create it on GitHub with a `README.md`. |
| "the README has no … markers" | Add the two marker lines where you want the stats, or let `/langstats:setup` add them. |
| The block keeps changing back | Another tool writes to the same section. Use another `section`. |
| "Python 3.9+ not found" | Install Python 3.9 or newer, or set `LANGSTATS_PYTHON` to the path of your interpreter. |
| Auto-publish does nothing | Check `~/.claude/langstats/publish.log`. It runs at most once every `publish_interval_hours`. |

## Uninstall

```text
/plugin uninstall langstats@codecruz
```

Your data stays in `~/.claude/langstats/`; delete that folder to remove it. The
block in your README stays until you delete it, together with its markers.

## Upgrading from langtime 0.1.0

On first run, the data in `~/.claude/langtime/` (configuration and records) is
copied to `~/.claude/langstats/`, once. The `LANGTIME_HOME` variable is replaced
by `LANGSTATS_HOME`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) · [CHANGELOG.md](CHANGELOG.md)

## License

[MIT](LICENSE)
