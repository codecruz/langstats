"""Language detection, ignore globs, project name."""

import pytest

import langstats


@pytest.mark.parametrize(
    "path, lang",
    [
        ("/a/main.py", "Python"),
        ("/a/App.TSX", "TSX"),
        ("/a/Dockerfile", "Docker"),
        ("/a/Dockerfile.prod", "Docker"),
        ("/a/docker-compose.yml", "Docker"),
        ("/a/Makefile", "Makefile"),
        ("/a/CLAUDE.md", "Markdown"),
        ("/a/README.md", "Markdown"),
        ("/a/.env", "Env"),
        ("/a/.env.local", "Env"),
        ("/a/resources/views/home.blade.php", "Blade Template"),
        ("/a/index.php", "PHP"),
        ("/a/types.d.ts", "TypeScript"),
        ("C:\\Users\\me\\proj\\lib.rs", "Rust"),
        ("/a/analysis.R", "R"),
        ("/a/file.unknownext", "Other"),
        ("/a/LICENSE", "Other"),
        ("/a/gradle.properties", "Properties"),
        ("/a/manifest.webmanifest", "JSON"),
    ],
)
def test_detect(path, lang):
    assert langstats.detect_language(path) == lang


@pytest.mark.parametrize(
    "first_line, lang",
    [
        ("#!/usr/bin/env python3\n", "Python"),
        ("#!/usr/bin/env -S node --harmony\n", "JavaScript"),
        ("#!/bin/bash\n", "Bash"),
        ("#!/bin/sh -e\n", "Shell"),
        ("#!/usr/bin/python3.11\n", "Python"),
        ("echo no shebang\n", "Other"),
    ],
)
def test_shebang(tmp_path, first_line, lang):
    script = tmp_path / "tool"
    script.write_text(first_line + "rest\n", encoding="utf-8")
    assert langstats.detect_language(str(script)) == lang


def test_shebang_only_without_extension(tmp_path):
    script = tmp_path / "tool.txt"
    script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    assert langstats.detect_language(str(script)) == "Text"


def test_overrides_win():
    overrides = {".tpl": "Smarty", "py": "Snake", "Makefile": "Make"}
    assert langstats.detect_language("/a/x.tpl", overrides) == "Smarty"
    assert langstats.detect_language("/a/x.py", overrides) == "Snake"
    assert langstats.detect_language("/a/Makefile", overrides) == "Make"
    assert langstats.detect_language("/a/x.go", overrides) == "Go"


@pytest.mark.parametrize(
    "path, ignored",
    [
        ("/home/me/.claude/settings.json", True),
        ("/p/node_modules/x/index.js", True),
        ("C:\\p\\vendor\\autoload.php", True),
        ("/p/src/dist.py", False),
        ("/p/src/app.py", False),
        ("/p/.venv/lib/site.py", True),
    ],
)
def test_ignore_globs(path, ignored):
    assert langstats.is_ignored(path, langstats.DEFAULTS["ignore_globs"]) is ignored


def test_ignore_wildcards():
    assert langstats.is_ignored("/p/build/out.min.js", ["*.min.js"])
    assert langstats.is_ignored("/p/tmp/a.py", ["/p/tmp/*"])


def test_project_name_uses_git_root(tmp_path):
    root = tmp_path / "kana-boo"
    (root / ".git").mkdir(parents=True)
    (root / "src" / "deep").mkdir(parents=True)
    assert langstats.project_name(str(root / "src" / "deep")) == "kana-boo"
    assert langstats.project_name(str(tmp_path / "loose")) == "loose"
