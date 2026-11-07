---
description: Update the language stats block in your GitHub profile README
argument-hint: "[--dry-run]"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run:*)"]
---

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/run" --exit-zero publish $ARGUMENTS
```

Report the result above to the user in one or two lines. With `--dry-run`, show the block exactly as printed. If it failed because the configuration is missing or the README has no markers, tell them to run `/langstats:setup`. Do not try to fix the README or the configuration yourself.
