import pytest

import cli


def test_harness_is_primary_interactive_command(monkeypatch):
    seen = {}
    monkeypatch.setattr(cli.sys, "argv", ["cogni", "harness", "--provider", "ollama", "--model", "local"])
    monkeypatch.setattr(cli, "_run_chat", lambda args: seen.update(provider=args.provider, model=args.model) or 0)
    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 0
    assert seen == {"provider": "ollama", "model": "local"}


def test_harness_in_top_level_help():
    assert "harness" in cli._parser().format_help()
