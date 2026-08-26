from __future__ import annotations
from pathlib import Path

from core.capability_policy import minimum_tier_for
from core.model_profile import ModelProfile, UNQUALIFIED_PROFILE


class Policy:
    def __init__(
        self,
        workspace: Path,
        model_profile: ModelProfile | None = None,
        *,
        allow_shell: bool = False,
    ) -> None:
        self.workspace = workspace.resolve()
        self.model_profile = model_profile or UNQUALIFIED_PROFILE
        self.allow_shell = allow_shell
        self.allowed_prefixes = ("core.", "filesystem.", "workspace.", "web.")

    def _runtime_allows(self, capability_id: str) -> bool:
        if capability_id.startswith(self.allowed_prefixes):
            return True
        if capability_id == "shell.run" and self.allow_shell:
            return True
        return False

    def authorize(self, capability_id: str, arguments: dict) -> tuple[bool, str]:
        if not self._runtime_allows(capability_id):
            return False, f"capability not approved by runtime policy: {capability_id}"

        minimum_tier = minimum_tier_for(capability_id)
        if not self.model_profile.permits(minimum_tier):
            return (
                False,
                "model trust tier insufficient: "
                f"model={self.model_profile.model} "
                f"tier={self.model_profile.tier.name} "
                f"required={minimum_tier.name} "
                f"capability={capability_id}",
            )

        return True, (
            "allowed by runtime policy and model trust gate: "
            f"tier={self.model_profile.tier.name}"
        )
