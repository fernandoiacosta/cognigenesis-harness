from __future__ import annotations

from pathlib import Path

import pytest

from cognigenesis.integrations import (
    apply_plan,
    create_codex_plan,
    discover_codex,
    load_plan,
    restore_integration,
    verify_integration,
)


def test_codex_inside_armor_plan_apply_verify_restore(tmp_path: Path) -> None:
    codex = tmp_path / ".codex"
    state = tmp_path / "state"
    codex.mkdir()
    (codex / "config.toml").write_text("model = 'test'\n", encoding="utf-8")
    existing = codex / "skills" / "cognigenesis"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("original\n", encoding="utf-8")

    discovered = discover_codex(codex)
    assert discovered["detected"] is True
    assert discovered["credentials_inspected"] is False

    plan = create_codex_plan(codex, state)
    assert plan.proposed_only is True
    assert load_plan(plan.plan_id, state) == plan
    assert (existing / "SKILL.md").read_text(encoding="utf-8") == "original\n"

    record = apply_plan(plan, state)
    assert record["credentials_copied"] is False
    assert verify_integration(state)["verified"] is True
    assert "Fernando Acosta" in (existing / "SKILL.md").read_text(encoding="utf-8")

    restored = restore_integration(state)
    assert restored["restored"] is True
    assert (existing / "SKILL.md").read_text(encoding="utf-8") == "original\n"
    assert not (existing / ".cognigenesis-adapter.json").exists()
    assert verify_integration(state)["active"] is False


def test_apply_rejects_tampered_plan(tmp_path: Path) -> None:
    codex = tmp_path / ".codex"
    state = tmp_path / "state"
    codex.mkdir()
    plan = create_codex_plan(codex, state)
    object.__setattr__(plan, "target_dir", str(tmp_path / "escape"))
    with pytest.raises(ValueError, match="bounded"):
        apply_plan(plan, state)


def test_apply_is_not_silently_repeatable(tmp_path: Path) -> None:
    codex = tmp_path / ".codex"
    state = tmp_path / "state"
    codex.mkdir()
    plan = create_codex_plan(codex, state)
    apply_plan(plan, state)
    with pytest.raises(FileExistsError):
        apply_plan(plan, state)
