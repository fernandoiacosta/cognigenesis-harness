from core.capability_policy import minimum_tier_for
from core.model_profile import TrustTier


def test_read_is_basic():
    assert minimum_tier_for("filesystem.read") == TrustTier.BASIC


def test_shell_is_trusted():
    assert minimum_tier_for("shell.run") == TrustTier.TRUSTED


def test_unknown_capability_requires_extended():
    assert minimum_tier_for("future.experimental") == TrustTier.EXTENDED
