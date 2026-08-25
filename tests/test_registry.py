from core.registry import CapabilityRegistry
from core.types import Capability


def test_registry_round_trip():
    registry = CapabilityRegistry()
    registry.register(Capability("demo.echo", "Echo input", lambda args: args))
    assert registry.get("demo.echo") is not None
    assert registry.get("demo.echo").execute({"x": 1}) == {"x": 1}
