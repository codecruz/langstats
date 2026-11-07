"""A6-A9: publishing and auto-publish."""

import datetime as dt
import json
import subprocess
import time

import pytest

import langstats

README = "# Hello\n\nIntro text.\n\n<!--START_SECTION:langstats-->\n<!--END_SECTION:langstats-->\n\nFooter.\n"


@pytest.fixture
def git_env(monkeypatch):
    for k, v in {
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
        "GIT_CONFIG_NOSYSTEM": "1",
    }.items():
        monkeypatch.setenv(k, v)


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True).stdout


@pytest.fixture
def profile_repo(tmp_path, git_env):
    """A bare 'remote' and a clone with a README that has the markers."""
    bare = tmp_path / "remote.git"
    git("-c", "init.defaultBranch=main", "init", "--bare", "--quiet", str(bare), cwd=tmp_path)
    clone = tmp_path / "profile"
    git("clone", "--quiet", str(bare), str(clone), cwd=tmp_path)
    (clone / "README.md").write_text(README, encoding="utf-8")
    git("add", "README.md", cwd=clone)
    git("commit", "--quiet", "-m", "init", cwd=clone)
    git("push", "--quiet", "-u", "origin", "HEAD", cwd=clone)
    return bare, clone


def add_heartbeats(home, beats, day=None):
    day = day or dt.date.today()
    path = home / "heartbeats" / ("%s.jsonl" % day.isoformat())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for b in beats:
            fh.write(json.dumps(b) + "\n")


def some_beats(start=None):
    start = start or time.time() - 3600
    return [
        {"v": 1, "ts": start, "lang": "Python"},
        {"v": 1, "ts": start + 300, "lang": "Go"},
        {"ts": start + 400, "lang": "Python"},  # v0.1.0 line without "v"
        {"v": 1, "ts": start + 500, "lang": "Python"},
    ]


def commit_count(cwd):
    return int(git("rev-list", "--count", "HEAD", cwd=cwd).strip())


def test_a6_publish_git_only_touches_section_and_is_idempotent(home, profile_repo, write_config):
    bare, clone = profile_repo
    write_config(readme_repo_path=str(clone))
    add_heartbeats(home, some_beats())
    cfg = langstats.load_config(home)

    assert langstats.publish(home, cfg) == "published"
    text = (clone / "README.md").read_text(encoding="utf-8")
    assert text.startswith("# Hello\n\nIntro text.\n\n<!--START_SECTION:langstats-->\n\n```txt\n")
    assert text.endswith("```\n\n<!--END_SECTION:langstats-->\n\nFooter.\n")
    assert "Python" in text and "Go" in text
    assert commit_count(bare) == 2  # pushed to the remote
    assert git("log", "-1", "--format=%s", cwd=bare).strip() == "chore(readme): update language stats"
    diff = git("diff", "HEAD~1", "--stat", cwd=clone)
    assert "README.md" in diff and "1 file changed" in diff

    assert langstats.publish(home, cfg) == "unchanged"
    assert commit_count(bare) == 2


def test_publish_dry_run_changes_nothing(home, profile_repo, write_config, capsys):
    _, clone = profile_repo
    write_config(readme_repo_path=str(clone))
    add_heartbeats(home, some_beats())
    assert langstats.publish(home, langstats.load_config(home), dry_run=True) == "dry-run"
    assert (clone / "README.md").read_text(encoding="utf-8") == README
    assert "```txt" in capsys.readouterr().out


def test_publish_without_data(home, profile_repo, write_config):
    _, clone = profile_repo
    write_config(readme_repo_path=str(clone))
    assert langstats.publish(home, langstats.load_config(home)) == "no-data"
    assert (clone / "README.md").read_text(encoding="utf-8") == README


def test_a7_readme_without_markers(home, profile_repo, write_config):
    bare, clone = profile_repo
    (clone / "README.md").write_text("# No markers here\n", encoding="utf-8")
    git("commit", "--quiet", "-am", "drop markers", cwd=clone)
    git("push", "--quiet", cwd=clone)
    write_config(readme_repo_path=str(clone))
    add_heartbeats(home, some_beats())
    with pytest.raises(langstats.LangstatsError, match="START_SECTION:langstats"):
        langstats.publish(home, langstats.load_config(home))
    assert (clone / "README.md").read_text(encoding="utf-8") == "# No markers here\n"
    assert git("status", "--porcelain", cwd=clone) == ""


def test_a8_git_mode_without_clone_mentions_setup(home, write_config, capsys):
    write_config(mode="git")
    assert langstats.main(["publish"]) == 1
    err = capsys.readouterr().err
    assert "/langstats:setup" in err and "readme_repo_path" in err


def test_a8_gh_mode_without_connection_mentions_setup(home, write_config, capsys):
    write_config(mode="gh")
    assert langstats.main(["publish"]) == 1
    err = capsys.readouterr().err
    assert "/langstats:setup" in err and "gh auth login" in err and "/langstats:snippet" in err


def test_auto_mode_without_github_gives_block_to_paste(home, write_config, capsys):
    add_heartbeats(home, some_beats())
    assert langstats.main(["publish"]) == 0
    out = capsys.readouterr().out
    assert "nothing was published" in out
    assert "<!--START_SECTION:langstats-->\n\n```txt\n" in out and "<!--END_SECTION:langstats-->" in out
    assert "gh auth login" in out
    saved = (home / "readme-snippet.md").read_text(encoding="utf-8")
    assert saved.startswith("<!--START_SECTION:langstats-->") and saved in out
    assert "last_publish" not in langstats.read_state(home)


def test_manual_snippet_pastes_into_readme_like_publish(home, write_config):
    """Pasting the manual snippet over an old block gives what publish would write."""
    add_heartbeats(home, some_beats())
    cfg = langstats.load_config(home)
    block = langstats.render_block(home, cfg)
    snippet = langstats.snippet_text("langstats", block)
    assert README.replace("<!--START_SECTION:langstats-->\n<!--END_SECTION:langstats-->\n", snippet) == (
        langstats.replace_section(README, "langstats", block)
    )


def test_auto_mode_with_gh_targets_profile_repo(home, monkeypatch):
    add_heartbeats(home, some_beats())
    monkeypatch.setattr(langstats, "gh_login", lambda: "octo")
    seen = {}

    def fake_get(repo, path):
        seen["get"] = repo
        return README, "sha"

    monkeypatch.setattr(langstats, "_gh_get", fake_get)
    monkeypatch.setattr(langstats, "_gh_put", lambda repo, *a: seen.setdefault("put", repo))
    assert langstats.publish(home, langstats.load_config(home)) == "published"
    assert seen == {"get": "octo/octo", "put": "octo/octo"}


def test_auto_mode_prefers_configured_clone(home, profile_repo, write_config, monkeypatch):
    _, clone = profile_repo
    write_config(readme_repo_path=str(clone))
    monkeypatch.setattr(langstats, "gh_login", lambda: "octo")
    assert langstats.resolve_target(langstats.load_config(home)) == ("git", clone)


def test_manual_mode_never_calls_gh(home, write_config, monkeypatch):
    write_config(mode="manual", readme_repo="me/me")
    monkeypatch.setattr(langstats, "gh_login", lambda: pytest.fail("gh must not be called"))
    assert langstats.resolve_target(langstats.load_config(home)) == ("manual", None)


def test_snippet_command(home, capsys, monkeypatch):
    add_heartbeats(home, some_beats())
    copied = []
    monkeypatch.setattr(langstats, "copy_to_clipboard", lambda text: copied.append(text) or "pbcopy")
    assert langstats.main(["snippet", "--copy"]) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("<!--START_SECTION:langstats-->") and captured.out == copied[0]
    assert "clipboard (pbcopy)" in captured.err


def test_snippet_without_data(home, capsys):
    assert langstats.main(["snippet"]) == 0
    assert "no activity" in capsys.readouterr().out


def test_doctor_reports_manual_mode(home, capsys):
    assert langstats.main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "manual" in out and "gh auth login" in out and "ready to publish (manual)" in out


def test_exit_zero_reports_but_does_not_fail(home, write_config, capsys):
    write_config(mode="git")
    assert langstats.main(["--exit-zero", "publish"]) == 0
    assert "/langstats:setup" in capsys.readouterr().err


def test_publish_records_last_publish(home, profile_repo, write_config):
    _, clone = profile_repo
    write_config(readme_repo_path=str(clone))
    add_heartbeats(home, some_beats())
    assert langstats.main(["publish"]) == 0
    assert langstats.read_state(home)["last_publish"] > time.time() - 60


def test_gh_mode(home, write_config, monkeypatch):
    write_config(mode="gh", readme_repo="me/me")
    add_heartbeats(home, some_beats())
    store = {"text": README, "puts": 0}

    def fake_get(repo, path):
        assert (repo, path) == ("me/me", "README.md")
        return store["text"], "sha1"

    def fake_put(repo, path, text, sha, message):
        store["text"], store["puts"] = text, store["puts"] + 1

    monkeypatch.setattr(langstats, "_gh_get", fake_get)
    monkeypatch.setattr(langstats, "_gh_put", fake_put)
    cfg = langstats.load_config(home)
    assert langstats.publish(home, cfg) == "published"
    assert "```txt" in store["text"]
    assert langstats.publish(home, cfg) == "unchanged"
    assert store["puts"] == 1


# --- A9: auto-publish -------------------------------------------------------


def auto_cfg(**over):
    cfg = dict(langstats.DEFAULTS, auto_publish=True, readme_repo_path="/some/clone")
    cfg.update(over)
    return cfg


def test_a9_should_auto_publish_respects_interval():
    now = 1_000_000.0
    assert langstats.should_auto_publish(auto_cfg(), {}, now)
    assert not langstats.should_auto_publish(auto_cfg(), {"last_publish": now - 11 * 3600}, now)
    assert langstats.should_auto_publish(auto_cfg(), {"last_publish": now - 12 * 3600}, now)
    assert not langstats.should_auto_publish(auto_cfg(), {"last_attempt": now - 60}, now)
    assert not langstats.should_auto_publish(auto_cfg(auto_publish=False), {}, now)
    assert not langstats.should_auto_publish(auto_cfg(mode="git", readme_repo_path=None), {}, now)
    assert not langstats.should_auto_publish(auto_cfg(mode="manual"), {}, now)
    assert langstats.should_auto_publish(auto_cfg(readme_repo_path=None), {}, now)  # auto: resolved later
    assert langstats.should_auto_publish(auto_cfg(publish_interval_hours=0), {"last_publish": now}, now)


def test_a9_session_end_spawns_detached_and_returns(home, write_config, monkeypatch):
    write_config(auto_publish=True, readme_repo_path="/some/clone")
    calls = []
    monkeypatch.setattr(langstats, "spawn_detached", lambda args, log: calls.append(args))
    t0 = time.time()
    assert langstats.main(["session-end"]) == 0
    assert time.time() - t0 < 2
    assert len(calls) == 1 and calls[0][-2:] == ["publish", "--auto"]
    assert langstats.read_state(home)["last_attempt"] >= t0
    # second session end inside the interval: nothing spawned
    assert langstats.main(["session-end"]) == 0
    assert len(calls) == 1


def test_a9_session_end_disabled(home, monkeypatch):
    calls = []
    monkeypatch.setattr(langstats, "spawn_detached", lambda args, log: calls.append(args))
    assert langstats.main(["session-end"]) == 0
    assert calls == []


def test_spawn_detached_does_not_wait(tmp_path):
    import sys

    t0 = time.time()
    langstats.spawn_detached([sys.executable, "-c", "import time; time.sleep(3)"], tmp_path / "log.txt")
    assert time.time() - t0 < 2
