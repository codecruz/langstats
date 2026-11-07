---
description: Guided setup for langstats (README repo, mode, section, auto-publish)
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run:*)", "AskUserQuestion"]
---

# langstats setup

You are configuring the langstats plugin for the user. The launcher is:

`"${CLAUDE_PLUGIN_ROOT}/scripts/run"`

Use exactly that command (quoted, with the path as written) for every step below. Never edit `config.json` by hand.

Current configuration:

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/run" --exit-zero config show
```

## Steps

1. **Mode.** Ask the user how the README should be updated:
   - `git`: a local clone of their profile repo (`<user>/<user>`); langstats commits and pushes from it.
   - `gh`: through the GitHub API with the `gh` CLI; no clone needed.
2. **Target.**
   - Mode `git`: ask for the path of the local clone. Save it with `config set readme_repo_path <path>`.
   - Mode `gh`: ask for the repository as `owner/repo`. Save it with `config set readme_repo <owner/repo>`.
   Save the mode with `config set mode <git|gh>`. If the README is not `README.md`, set `readme_file`.
3. **Section.** Ask for the section name (default `langstats`, markers `<!--START_SECTION:langstats-->` / `<!--END_SECTION:langstats-->`). Save with `config set section <name>`.
4. **Auto-publish.** Ask whether to publish automatically when a session ends (at most every `publish_interval_hours`, default 12). Save with `config set auto_publish true|false`.
5. **Check.** Run `"${CLAUDE_PLUGIN_ROOT}/scripts/run" doctor`. It verifies `git` or `gh auth status` according to the mode, the repo, the README and the markers.
   - If only the markers are missing, ask the user for confirmation before running `"${CLAUDE_PLUGIN_ROOT}/scripts/run" insert-markers`, which appends them at the end of the README. Then run `doctor` again.
   - For any other problem, explain the fix (for example `gh auth login`) and stop.
6. **Finish.** Run `"${CLAUDE_PLUGIN_ROOT}/scripts/run" publish --dry-run` and show the block. Tell the user they can publish with `/langstats:publish` and view stats with `/langstats:stats`.

Ask one question at a time and keep the current value as the default when there is one.
