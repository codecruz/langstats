---
description: Update the language stats block in your GitHub profile README (or get it to paste by hand)
argument-hint: "[--dry-run]"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run:*)"]
---

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/run" --exit-zero publish $ARGUMENTS
```

Report the result above to the user in one or two lines.

- With `--dry-run`, show the block exactly as printed.
- If GitHub is not connected, langstats printed a block to paste by hand: show it exactly as printed (from `<!--START_SECTION:` to `<!--END_SECTION:`) inside a `markdown` code block, say where to paste it, and mention `gh auth login` + `/langstats:setup` to automate it.
- If it failed because of the configuration, the profile repository or missing markers, tell them to run `/langstats:setup`.

Do not try to fix the README or the configuration yourself.
