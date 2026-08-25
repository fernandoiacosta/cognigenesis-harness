from pathlib import Path
import pytest

from core.registry import CapabilityRegistry
from tools.filesystem import register_filesystem_tools


def test_filesystem_rejects_escape(tmp_path: Path):
    registry = CapabilityRegistry()
    register_filesystem_tools(registry, tmp_path)
    tool = registry.get("filesystem.read")
    assert tool is not None

    with pytest.raises(PermissionError):
        tool.execute({"path": "../outside.txt"})
