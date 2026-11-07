---
description: Choose the symbols of your stats bars (flowers 🌸, rocket 🚀, hearts, your own emoji...)
argument-hint: "[style name | your own symbols, e.g. \"·🌱🌸\"]"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run:*)"]
---

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/run" --exit-zero style $ARGUMENTS
```

Show the output above to the user exactly as printed, inside a `txt` code block.

- If no style was given, it is the list of available styles with a preview. Tell them to choose one with `/langstats:style <name>`, or to use their own symbols from empty to full, for example `/langstats:style "·🌱🌸"`, or separated by spaces for emoji made of several characters, for example `/langstats:style "· ❤️ 💖"`.
- If a style was set, confirm it in one line and say it is used on the next `/langstats:publish`.
- If it reported an invalid value, explain the accepted forms above.
