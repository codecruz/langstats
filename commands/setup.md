---
description: Guided setup for langstats (GitHub connection, README section, auto-publish)
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run:*)", "AskUserQuestion"]
---

# langstats setup

You are configuring the langstats plugin for the user. The launcher is:

`"${CLAUDE_PLUGIN_ROOT}/scripts/run"`

Use exactly that command (quoted, with the path as written) for every step below. Never edit `config.json` by hand, and never run `gh auth login` yourself: it is interactive.

Current configuration and status:

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/run" --exit-zero config show
"${CLAUDE_PLUGIN_ROOT}/scripts/run" --exit-zero doctor
```

The `target` line of the status above says how langstats will publish with mode `auto` (the default):

- **`github.com/<login>/<login> via gh`**: the GitHub CLI is logged in, so langstats can update the user's profile README automatically. Go to step 2.
- **`manual`**: GitHub is not connected. Go to step 1.
- **`local clone ...`**: a clone is configured; keep it unless the user wants to change it. Go to step 2.

## Steps

1. **No GitHub connection.** Explain the options and ask which one they want:
   - **Connect GitHub (recommended):** install the GitHub CLI from https://cli.github.com if needed, then type `! gh auth login` in this prompt. When done, run `doctor` again and continue with step 2.
   - **Local clone:** if they already have their profile repository cloned and push access with git, save the path with `config set readme_repo_path <path>` and continue with step 2.
   - **Manual:** run `config set mode manual`. Tell them `/langstats:snippet` prints the block (and copies it to the clipboard when possible) to paste into their README whenever they want. Then go to step 5 (bar style) and finish with step 7.
2. **Repository.** The default is their profile README repository `<login>/<login>`. Ask whether that is right; if they want another repository, save it with `config set readme_repo <owner/repo>`. If `doctor` says the repository was not found, tell them to create the public repository `<login>/<login>` with a README on GitHub first.
3. **Section.** Ask for the section name (default `langstats`, markers `<!--START_SECTION:langstats-->` / `<!--END_SECTION:langstats-->`). Save with `config set section <name>`. Run `doctor`. If only the markers are missing, ask for confirmation before running `"${CLAUDE_PLUGIN_ROOT}/scripts/run" insert-markers`, which appends them at the end of the README, then run `doctor` again.
4. **Several computers.** By default (`share_data` false) only the percentages block is uploaded and each computer publishes its own stats, so the last computer to publish wins. Ask whether they want to add up several computers. Explain that adding up needs the minutes per day and language of the days shown stored in one small file (`.langstats/stats.json`, no computer ids, projects or paths), because percentages alone cannot be combined.
   - **No** (default): keep `share_data` false. Nothing but the block is uploaded.
   - **Yes**: recommend a **private** repository for that file, for example `<login>/langstats-data`. If it does not exist, ask for confirmation and create it with `gh repo create <owner/repo> --private --description "langstats data"`. Save with `config set data_repo <owner/repo>` and `config set share_data true`. They must do the same on every computer.
5. **Bar style.** Run `"${CLAUDE_PLUGIN_ROOT}/scripts/run" style` and show the list. Ask which style they want (keep the current one by default), or whether they prefer their own symbols from empty to full, such as `·🌱🌸`. Save it with `"${CLAUDE_PLUGIN_ROOT}/scripts/run" style <name or symbols>`.
6. **Auto-publish.** Ask whether to publish automatically when a session ends (at most every `publish_interval_hours`, default 12; it runs in the background and never slows the session). Save with `config set auto_publish true|false`.
7. **Finish.** Run `"${CLAUDE_PLUGIN_ROOT}/scripts/run" publish --dry-run` and show the block. Remind them of `/langstats:publish`, `/langstats:snippet`, `/langstats:stats` and `/langstats:style`.

Ask one question at a time and keep the current value as the default when there is one.
