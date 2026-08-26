from __future__ import annotations

import json
from importlib.resources import files


def text(name: str) -> str:
    return files("cognigenesis.resources").joinpath(name).read_text(encoding="utf-8")


def json_resource(name: str) -> dict:
    return json.loads(text(name))
