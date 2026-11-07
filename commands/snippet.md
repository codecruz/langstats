---
description: Get your language stats block to paste into your README by hand (no GitHub connection needed)
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run:*)"]
---

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/run" --exit-zero snippet --copy
```

Show the user the block above exactly as printed, from `<!--START_SECTION:` to `<!--END_SECTION:` inclusive, inside a `markdown` code block so it can be copied as is. Then tell them in two short lines:

- Paste it into the `README.md` of their profile repository (`github.com/<username>/<username>`). If an older block with the same markers is already there, replace it whole.
- Say whether it was copied to the clipboard, as reported above. To publish automatically instead, they can install the GitHub CLI, run `gh auth login`, then `/langstats:setup`.

If it says there is no activity yet, explain that stats appear after Claude has read or edited some files.
