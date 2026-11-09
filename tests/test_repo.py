"""Repository hygiene: A12 and JSON files."""

import json

import pytest

from conftest import ROOT

CODE_DIRS = ["scripts", "hooks", "commands"]


def test_a12_no_personal_constants_in_code():
    offenders = []
    for d in CODE_DIRS:
        for path in (ROOT / d).rglob("*"):
            if path.is_file() and "codecruz" in path.read_text(encoding="utf-8", errors="ignore").lower():
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


@pytest.mark.parametrize("path", sorted(p for p in ROOT.rglob("*.json") if ".git" not in p.parts), ids=str)
def test_json_files_parse(path):
    json.loads(path.read_text(encoding="utf-8"))


def test_versions_match():
    import langstats

    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert plugin["version"] == langstats.__version__ == market["plugins"][0]["version"]
    assert 'version = "%s"' % plugin["version"] in pyproject
    assert market["plugins"][0]["name"] == plugin["name"] == "langstats"


def test_languages_json_shape():
    data = json.loads((ROOT / "scripts" / "languages.json").read_text(encoding="utf-8"))
    assert set(data) == {"filenames", "prefixes", "suffixes", "extensions", "shebangs", "non_code", "skip_extensions"}
    for ext in data["extensions"]:
        assert ext.startswith("."), ext
    for ext in data["skip_extensions"]:
        assert ext.startswith(".") and ext not in data["extensions"], ext
    rules = ("filenames", "prefixes", "suffixes", "extensions", "shebangs")
    names = {lang for key in rules for lang in data[key].values()}
    assert set(data["non_code"]) <= names, set(data["non_code"]) - names
