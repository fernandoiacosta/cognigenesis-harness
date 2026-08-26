from __future__ import annotations

import os
import sys
from typing import TextIO


def _reconfigure_utf8(stream: TextIO | None) -> None:
    if stream is None:
        return
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def configure_utf8_stdio() -> None:
    """Force UTF-8 text I/O where Python exposes reconfigure().

    Windows console/subprocess stdout may otherwise use cp1252, which crashes on
    perfectly valid model output such as emoji. ACP is JSON over stdio and should
    also remain UTF-8.
    """
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    _reconfigure_utf8(sys.stdout)
    _reconfigure_utf8(sys.stderr)
