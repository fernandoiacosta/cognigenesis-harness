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
    (codex / "config.toml").write_text("model = 'test'\n", encoding="utf-8")
    plan = create_codex_plan(codex, state)
    object.__setattr__(plan, "target_dir", str(tmp_path / "escape"))
    with pytest.raises(ValueError, match="bounded"):
        apply_plan(plan, state)


def test_apply_rejects_tampered_content_and_hash(tmp_path: Path) -> None:
    codex = tmp_path / ".codex"
    state = tmp_path / "state"
    codex.mkdir()
    (codex / "config.toml").write_text("model = 'test'\n", encoding="utf-8")
    plan = create_codex_plan(codex, state)
    plan.files["SKILL.md"] = "malicious replacement\n"
    import hashlib
    plan.content_hashes["SKILL.md"] = hashlib.sha256(plan.files["SKILL.md"].encode()).hexdigest()
    with pytest.raises(ValueError, match="identifier"):
        apply_plan(plan, state)


def test_apply_is_not_silently_repeatable(tmp_path: Path) -> None:
    codex = tmp_path / ".codex"
    state = tmp_path / "state"
    codex.mkdir()
    (codex / "config.toml").write_text("model = 'test'\n", encoding="utf-8")
    plan = create_codex_plan(codex, state)
    apply_plan(plan, state)
    with pytest.raises(FileExistsError):
        apply_plan(plan, state)


def test_apply_requires_a_detected_codex_installation(tmp_path: Path) -> None:
    codex = tmp_path / ".codex"
    state = tmp_path / "state"
    codex.mkdir()
    plan = create_codex_plan(codex, state)
    assert plan.detected is False
    with pytest.raises(ValueError, match="not detected"):
        apply_plan(plan, state)


def test_apply_rolls_back_after_partial_write_failure(tmp_path: Path, monkeypatch) -> None:
    codex = tmp_path / ".codex"
    state = tmp_path / "state"
    codex.mkdir()
    (codex / "config.toml").write_text("model = 'test'\n", encoding="utf-8")
    target = codex / "skills" / "cognigenesis"
    target.mkdir(parents=True)
    original = b"original skill\n"
    (target / "SKILL.md").write_bytes(original)
    plan = create_codex_plan(codex, state)

    real_write_text = Path.write_text

    def fail_on_manifest(self, data, *args, **kwargs):
        if self.name == ".cognigenesis-adapter.json":
            raise OSError("simulated interrupted apply")
        return real_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_on_manifest)
    with pytest.raises(OSError, match="interrupted"):
        apply_plan(plan, state)

    assert (target / "SKILL.md").read_bytes() == original
    assert not (target / ".cognigenesis-adapter.json").exists()
    assert not (state / "active.json").exists()
    assert not (state / "backups" / plan.plan_id).exists()
