from io import StringIO

from rich.console import Console

import cognigenesis.console as console_module


def test_assistant_panel_wraps_to_terminal_width(monkeypatch):
    output = StringIO()
    narrow = Console(file=output, width=48, color_system=None, force_terminal=False)
    monkeypatch.setattr(console_module, "console", narrow)

    console_module.assistant_message(
        "This is a deliberately long Cognigenesis response sentence that must "
        "wrap within the visible panel instead of disappearing beyond the right edge."
    )

    lines = output.getvalue().splitlines()
    assert lines
    assert max(len(line) for line in lines) <= 48
