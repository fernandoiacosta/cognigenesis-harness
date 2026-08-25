from core.model_profile import ModelProfile, TrustTier


def make_profile(**overrides):
    data = dict(
        provider="test",
        model="test-model",
        reasoning=0.9,
        instruction_fidelity=0.9,
        tool_reliability=0.9,
        uncertainty_calibration=0.9,
        goal_persistence=0.9,
        capability_hallucination_resistance=0.9,
        recovery_behavior=0.9,
        protocol_compatibility=0.9,
    )
    data.update(overrides)
    return ModelProfile(**data)


def test_strong_profile_gets_extended_tier():
    assert make_profile().tier == TrustTier.EXTENDED


def test_critical_weakness_caps_trust():
    profile = make_profile(tool_reliability=0.50)
    assert profile.tier == TrustTier.OBSERVER
