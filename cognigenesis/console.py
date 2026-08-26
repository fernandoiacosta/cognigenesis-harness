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

console = Console(theme=THEME, highlight=False, soft_wrap=True)
err_console = Console(theme=THEME, stderr=True, highlight=False, soft_wrap=True)


@dataclass(frozen=True)
class RuntimeIdentity:
    provider: str
    model: str
    workspace: str


def banner(version: str, identity: RuntimeIdentity | None = None) -> None:
    title = f"[bold cogni.cyan]COGNIGENESIS[/] [cogni.violet]v{version}[/]"
    subtitle = "Local-first adaptive intelligence harness"
    body = f"{title}\n[cogni.muted]{subtitle}[/]"
    if identity:
        body += (
            f"\n\n[cogni.muted]provider[/]  [cogni.green]{identity.provider}[/]"
            f"\n[cogni.muted]model[/]     {identity.model}"
            f"\n[cogni.muted]workspace[/] {identity.workspace}"
        )
    console.print(Panel(body, border_style="cogni.violet", padding=(1, 2)))


def assistant_message(text: str) -> None:
    console.print(Panel(Markdown(text), title="[cogni.cyan]Cognigenesis[/]", border_style="cogni.cyan", padding=(1, 2)))


def error_message(text: str) -> None:
    err_console.print(Panel(text, title="[cogni.red]Error[/]", border_style="cogni.red"))


def warning_message(text: str) -> None:
    console.print(Panel(text, title="[cogni.amber]Warning[/]", border_style="cogni.amber"))


def success_message(text: str) -> None:
    console.print(f"[cogni.green]✓[/] {text}")


def status_table(rows: list[tuple[str, str, str]]) -> None:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="cogni.muted")
    table.add_column()
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
