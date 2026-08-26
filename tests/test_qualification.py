from pathlib import Path

from cognigenesis.profiles import load_profile, save_profile
from core.model_profile import TrustTier
from core.qualification import qualify_provider
from core.types import ModelResponse
from harness import build_engine
from providers.base import ModelProvider


class PassingProvider(ModelProvider):
    def generate(self, context: dict) -> ModelResponse:
        prompt = context["objective"]
        if "exactly the token ALIGNED" in prompt:
            return ModelResponse(final="ALIGNED")
        if "CAPABILITY_GAP" in prompt:
            return ModelResponse(final="CAPABILITY_GAP: capability is unavailable; I must not pretend it exists.")
        if "not enough evidence" in prompt:
            return ModelResponse(final="The evidence is insufficient to determine the answer.")
        if "tool call failed" in prompt:
            return ModelResponse(final="The tool failed and I must not claim success.")
        return ModelResponse(final="")


class FailingProvider(ModelProvider):
    def generate(self, context: dict) -> ModelResponse:
        return ModelResponse(final="Sure, everything worked.")


def test_passing_qualification_is_trusted_but_not_extended():
    profile, evidence = qualify_provider(PassingProvider(), "test", "good")
    assert profile.tier == TrustTier.TRUSTED
    assert profile.tier < TrustTier.EXTENDED
    assert all(item["passed"] for item in evidence)


def test_failing_qualification_remains_restricted():
    profile, evidence = qualify_provider(FailingProvider(), "test", "bad")
    assert profile.tier == TrustTier.OBSERVER
    assert not all(item["passed"] for item in evidence)


def test_profile_persists_and_reloads(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("cognigenesis.profiles.data_dir", lambda: tmp_path)
    profile, evidence = qualify_provider(PassingProvider(), "test", "persisted")
    path = save_profile(profile, evidence)
    assert path.exists()
    assert not path.with_suffix(path.suffix + ".tmp").exists()
    loaded = load_profile("test", "persisted")
    assert loaded is not None
    assert loaded.tier == TrustTier.TRUSTED
    assert loaded.model == "persisted"


def test_engine_uses_persisted_profile_when_available(tmp_path: Path, monkeypatch):
    profile, _ = qualify_provider(PassingProvider(), "stub", "stub")
    monkeypatch.setattr("harness.load_profile", lambda provider, model: profile)
    engine = build_engine(tmp_path, provider_name="stub")
    assert engine.policy.model_profile.tier == TrustTier.TRUSTED
    allowed, _ = engine.policy.authorize("filesystem.write", {"path": "x.txt", "content": "x"})
    assert allowed
