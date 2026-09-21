# ============================================================
#  File: spectre/core/ui.py
# ============================================================
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import theme as T


def section(console: Console, title: str) -> None:
    txt = Text()
    txt.append("  ▓▒░ ", style=T.HEX["purple_dim"])
    txt.append(title.upper(), style=f"bold {T.HEX['purple']}")
    txt.append("  ░▒▓", style=T.HEX["purple_dim"])
    console.print()
    console.rule(txt, style=T.HEX["purple_dim"], align="left")


def kv_table(console: Console, rows):
    t = Table(show_header=False, box=None, padding=(0, 2))
    t.add_column(justify="right", style=T.HEX["text_dim"])
    t.add_column(justify="left", style=T.HEX["text"])
    for k, v in rows:
        t.add_row(k, str(v))
    console.print(t)


def campaigns_table(console: Console, campaigns: list, title="CAMPAIGNS"):
    if not campaigns:
        console.print(f"  [{T.HEX['text_dim']}]no campaigns.[/]")
        return
    t = Table(
        title=f"[bold {T.HEX['purple']}]{title}[/]",
        title_justify="left",
        border_style=T.HEX["line"],
        header_style=f"bold {T.HEX['green_hi']}",
        padding=(0, 1),
    )
    t.add_column("ID", style=T.HEX["purple_hi"])
    t.add_column("NAME", style=T.HEX["text"])
    t.add_column("SENT", justify="right")
    t.add_column("OPENED", justify="right")
    t.add_column("CLICKED", justify="right")
    t.add_column("SUBMITTED", justify="right", style=T.HEX["green_hi"])
    t.add_column("STATUS", style=T.HEX["text_dim"])
    for c in campaigns:
        t.add_row(
            c.get("id", ""),
            c.get("name", ""),
            str(c.get("sent", 0)),
            str(c.get("opened", 0)),
            str(c.get("clicked", 0)),
            str(c.get("submitted", 0)),
            c.get("status", "active"),
        )
    console.print(t)


def captures_table(console: Console, captures: list, title="CAPTURED CREDENTIALS"):
    if not captures:
        console.print(f"  [{T.HEX['text_dim']}]no captures yet.[/]")
        return
    t = Table(
        title=f"[bold {T.HEX['green_hi']}]{title}[/]",
        title_justify="left",
        border_style=T.HEX["line"],
        header_style=f"bold {T.HEX['green_hi']}",
        padding=(0, 1),
    )
    t.add_column("#", justify="right", style=T.HEX["text_dim"])
    t.add_column("TIME", style=T.HEX["text_dim"])
    t.add_column("EMAIL", style=T.HEX["purple_hi"])
    t.add_column("USERNAME", style=T.HEX["text"])
    t.add_column("PASSWORD", style=f"bold {T.HEX['green_hi']}")
    t.add_column("IP", style=T.HEX["text_dim"])
    t.add_column("UA", overflow="fold", style=T.HEX["text_mute"])
    for i, c in enumerate(captures, 1):
        t.add_row(
            str(i),
            c.get("ts", ""),
            c.get("email", ""),
            c.get("username", ""),
            c.get("password", ""),
            c.get("ip", ""),
            (c.get("user_agent", "") or "")[:40],
        )
    console.print(t)


def highlight(console: Console, title: str, body: str,
              style: str = None) -> None:
    style = style or T.HEX["purple"]
    # Text.from_markup parses [bold], [#hex], etc. inside body
    text = Text.from_markup(body, style=T.HEX["text"])
    panel = Panel(
        text,
        title=f"[bold {style}]{title}[/]",
        border_style=style,
        padding=(1, 2),
    )
    console.print(panel)
