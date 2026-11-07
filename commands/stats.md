---
description: Show the languages Claude has worked in (default range from config)
argument-hint: "[--days N] [--project NAME]"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run:*)"]
---

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/run" --exit-zero stats $ARGUMENTS
```

Show the output above to the user exactly as printed, inside a `txt` code block. Do not add analysis unless they ask for it. If it says no activity was recorded, explain that langstats records a heartbeat each time Claude reads or edits a file, so stats appear after some work in a session.
