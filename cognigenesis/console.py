from __future__ import annotations

import sys
from dataclasses import dataclass

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme


THEME = Theme(
    {
        "cogni.cyan": "#62F5FF",
        "cogni.violet": "#8B7CFF",
        "cogni.magenta": "#C96CFF",
        "cogni.green": "#54E6A8",
        "cogni.amber": "#FFC857",
        "cogni.red": "#FF6B7A",
        "cogni.muted": "#A7B0C3",
        "cogni.border": "#1B2440",
    }
)

# Rich's soft_wrap=True deliberately disables normal wrapping. That is useful
# for log streams, but wrong for a bounded chat surface. Leave wrapping enabled
# globally and let Panels/Markdown measure themselves against terminal width.
console = Console(theme=THEME, highlight=False)
err_console = Console(theme=THEME, stderr=True, highlight=False)


@dataclass(frozen=True)
class RuntimeIdentity:
    provider: str
    model: str
    workspace: str


def banner(version: str, identity: RuntimeIdentity | None = None) -> None:
    title = f"[bold cogni.cyan]COGNIGENESIS[/] [cogni.violet]v{version}[/]"
    subtitle = "Cognitive operating environment"
    body = f"{title}\n[cogni.muted]{subtitle}[/]"
    if identity:
        body += (
            f"\n\n[cogni.muted]provider[/]  [cogni.green]{identity.provider}[/]"
            f"\n[cogni.muted]model[/]     {identity.model}"
            f"\n[cogni.muted]workspace[/] {identity.workspace}"
        )
    console.print(
        Panel(body, border_style="cogni.violet", padding=(1, 2), expand=True)
    )


def assistant_message(text: str) -> None:
    """Render Markdown constrained to the current terminal width.

    The panel expands to terminal width and Rich performs normal line wrapping.
    No soft_wrap/no_wrap override is used, so long prose and URLs stay visible.
    """
    renderable = Markdown(text, justify=None)
    panel = Panel(
        renderable,
        title="[bold #62F5FF]Cognigenesis[/]",
        border_style="#62F5FF",
        padding=(1, 2),
        expand=True,
    )
    console.print(panel)


def error_message(text: str) -> None:
    err_console.print(
        Panel(text, title="[cogni.red]Error[/]", border_style="cogni.red", expand=True)
    )


def warning_message(text: str) -> None:
    console.print(
        Panel(text, title="[cogni.amber]Warning[/]", border_style="cogni.amber", expand=True)
    )


def success_message(text: str) -> None:
    console.print(f"[cogni.green]✓[/] {text}")


def status_table(rows: list[tuple[str, str, str]]) -> None:
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column(style="cogni.muted", no_wrap=True)
    table.add_column(overflow="fold")
    for key, value, style in rows:
        table.add_row(key, f"[{style}]{value}[/]" if style else value)
    console.print(table)


def supports_unicode() -> bool:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        "◈".encode(encoding)
        return True
    except UnicodeEncodeError:
        return False
