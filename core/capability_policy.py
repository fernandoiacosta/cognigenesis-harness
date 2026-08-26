from __future__ import annotations

from core.model_profile import TrustTier


CAPABILITY_MINIMUM_TIERS: dict[str, TrustTier] = {
    "core.": TrustTier.OBSERVER,
    "web.search": TrustTier.OBSERVER,
    "web.fetch": TrustTier.OBSERVER,
    "filesystem.read": TrustTier.BASIC,
    "filesystem.list": TrustTier.BASIC,
    "filesystem.write": TrustTier.TRUSTED,
    "workspace.create_project": TrustTier.TRUSTED,
    "shell.run": TrustTier.TRUSTED,
}


def minimum_tier_for(capability_id: str) -> TrustTier:
    if capability_id in CAPABILITY_MINIMUM_TIERS:
        return CAPABILITY_MINIMUM_TIERS[capability_id]

    matching_prefixes = [
        (prefix, tier)
        for prefix, tier in CAPABILITY_MINIMUM_TIERS.items()
        if prefix.endswith(".") and capability_id.startswith(prefix)
    ]
    if matching_prefixes:
        matching_prefixes.sort(key=lambda item: len(item[0]), reverse=True)
        return matching_prefixes[0][1]

    # Unknown capability classes require the highest trust tier but still need
    # an explicit policy allowlist entry before they can execute.
    return TrustTier.EXTENDED
