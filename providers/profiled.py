from __future__ import annotations

from dataclasses import dataclass

from core.model_profile import ModelProfile
from providers.base import ModelProvider


@dataclass
class ProfiledProvider:
    """Binds a provider implementation to measured model qualification data."""

    provider: ModelProvider
    profile: ModelProfile

    def generate(self, context: dict):
        return self.provider.generate(context)
