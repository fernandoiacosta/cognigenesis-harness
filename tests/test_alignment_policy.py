from pathlib import Path

from core.model_profile import ModelProfile, TrustTier
from core.policy import Policy


def profile(tier: TrustTier):
    values = {
        TrustTier.OBSERVER: 0.5,
        TrustTier.BASIC: 0.68,
        TrustTier.TRUSTED: 0.8,
        TrustTier.EXTENDED: 0.92,
    }
    v = values[tier]
    return ModelProfile(
        provider="test",
        model=tier.name.lower(),
        reasoning=v,
        instruction_fidelity=v,
        tool_reliability=v,
        uncertainty_calibration=v,
        goal_persistence=v,
        capability_hallucination_resistance=v,
        recovery_behavior=v,
        protocol_compatibility=v,
    )


def test_observer_cannot_use_shell(tmp_path: Path):
    policy = Policy(tmp_path, model_profile=profile(TrustTier.OBSERVER))
    allowed, _ = policy.authorize("shell.run", {})
    assert not allowed


def test_extended_model_still_requires_policy_allowlist(tmp_path: Path):
    policy = Policy(tmp_path, model_profile=profile(TrustTier.EXTENDED))
    allowed, _ = policy.authorize("network.unbounded", {})
    assert not allowed
