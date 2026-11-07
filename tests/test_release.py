"""tools/release.py: bumps every version field and closes the changelog."""

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FILES = [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", "pyproject.toml", "scripts/langstats.py"]


def load_release():
    spec = importlib.util.spec_from_file_location("release", ROOT / "tools" / "release.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def repo(tmp_path):
    for name in FILES + ["CHANGELOG.md"]:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / name, tmp_path / name)
    return tmp_path


def add_unreleased(repo, text="### Fixed\n- Something.\n"):
    path = repo / "CHANGELOG.md"
    content = path.read_text(encoding="utf-8").replace("## [Unreleased]\n", "## [Unreleased]\n\n" + text, 1)
    path.write_text(content, encoding="utf-8")


def bumped(version):
    major, minor, patch = (int(p) for p in version.split("."))
    return "%d.%d.%d" % (major, minor, patch + 1)


def test_release_bumps_everything(repo):
    release = load_release()
    old = release.current_version(repo)
    new = bumped(old)
    add_unreleased(repo)
    assert release.main([new, "--date", "2030-01-02", "--root", str(repo)]) == 0
    plugin = json.loads((repo / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((repo / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert plugin["version"] == market["plugins"][0]["version"] == new
    assert 'version = "%s"' % new in (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert '__version__ = "%s"' % new in (repo / "scripts" / "langstats.py").read_text(encoding="utf-8")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [Unreleased]\n\n## [%s] - 2030-01-02\n\n### Fixed\n- Something.\n" % new in changelog
    assert "compare/v%s...HEAD" % new in changelog
    assert "[%s]: https://github.com/codecruz/langstats/compare/v%s...v%s" % (new, old, new) in changelog


@pytest.mark.parametrize("version", ["0.1.0", "1.2", "v9.9.9"])
def test_release_rejects_bad_versions(repo, version):
    release = load_release()
    add_unreleased(repo)
    before = {name: (repo / name).read_text(encoding="utf-8") for name in FILES}
    assert release.main([version, "--root", str(repo)]) == 1
    assert before == {name: (repo / name).read_text(encoding="utf-8") for name in FILES}


def test_release_needs_unreleased_changes(repo):
    release = load_release()
    new = bumped(release.current_version(repo))
    if "## [Unreleased]\n\n## [" not in (repo / "CHANGELOG.md").read_text(encoding="utf-8"):
        pytest.skip("Unreleased already has changes")
    assert release.main([new, "--root", str(repo)]) == 1


def test_changelog_has_current_version():
    release = load_release()
    version = release.current_version(ROOT)
    assert "\n## [%s] - " % version in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
