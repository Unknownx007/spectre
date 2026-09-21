# ============================================================
#  File: spectre/banner.py
#  SPECTRE — hooded figure logo, gradient animation, responsive.
# ============================================================
import random
import shutil
import sys
import time

from rich.console import Console
from rich.text import Text
from rich.align import Align

from . import theme as T


# ================================================================
QUOTES = [
    "Every click is a confession.",
    "Trust is a protocol. We speak it fluently.",
    "You cannot firewall the human heart.",
    "The password was always going to be the weak link.",
    "Firewalls don't click. People do.",
    "Credentials are just stories we tell the door.",
    "The inbox is the new perimeter. Most are wide open.",
    "A phishing email is a question. The click is the answer.",
    "We don't break the lock. We ask for the key.",
    "The user is not the vulnerability. The hurry is.",
    "Somewhere between the email and the click, trust became a weapon.",
    "We do not steal. We simulate. The difference is everything.",
]


def quote() -> str:
    return random.choice(QUOTES)


# ================================================================
#  Three logo sizes — chosen by terminal width
# ================================================================
LOGO_FULL = r"""
              ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
           ▄█▀▀             ▀▀█▄
         ▄█▀                   ▀█▄
        ██                       ██
       ██   ████▄       ▄████    ██
      ██   ███████     ███████    ██
      ██   ███████     ███████    ██
      ██    ▀████▀     ▀████▀     ██
       ██                         ██
        ██    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀    ██
        ██                       ██
         ██                     ██
          ██                   ██
           ██                 ██
            ██               ██
             ██             ██
              ██           ██
               ██         ██
                ██       ██
                 ██     ██
                  ██   ██
                   ██ ██
                    ███
                     ▀
"""

LOGO_COMPACT = r"""
        ▄▄▄▄▄▄▄▄▄
      ▄█▀       ▀█▄
     ██  ▄██ ██▄  ██
    ██   ███ ███   ██
    ██    ▀█ █▀    ██
     ██           ██
      ██         ██
       ██       ██
        ██     ██
         ██   ██
          ██ ██
           ███
            ▀
"""

LOGO_TINY = r"""
     ▄▄▄▄▄▄▄
   ▄█▀     ▀█▄
  ██  ▄█ █▄  ██
  ██  ██ ██  ██
   ██       ██
    ██     ██
     ██   ██
      ██ ██
       ███
"""


# ================================================================
#  Color helpers
# ================================================================
_PURPLE_RGB = (199, 125, 255)
_GREEN_RGB  = (0, 255, 156)
_CYAN_RGB   = (0, 212, 255)

_RST   = "\033[0m"
_BOLD  = "\033[1m"


def _rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient_color(t):
    """t=0 -> purple, t=0.5 -> cyan, t=1 -> green."""
    if t < 0.5:
        rgb = _lerp(_PURPLE_RGB, _CYAN_RGB, t * 2)
    else:
        rgb = _lerp(_CYAN_RGB, _GREEN_RGB, (t - 0.5) * 2)
    return _rgb(*rgb)


# ================================================================
#  Terminal-width helpers
# ================================================================
def _term_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


def _center(text: str) -> str:
    text = text.rstrip("\n")
    w = _term_width()
    n = len(text)
    if n >= w:
        return text
    return " " * ((w - n) // 2) + text


def _pick_logo() -> str:
    """Choose the logo variant that fits the current terminal."""
    w = _term_width()
    if w >= 70:
        return LOGO_FULL
    if w >= 45:
        return LOGO_COMPACT
    return LOGO_TINY


def _logo_lines() -> list:
    """Return the current logo as a list of stripped lines."""
    raw = _pick_logo().split("\n")
    while raw and not raw[0].strip():
        raw.pop(0)
    while raw and not raw[-1].strip():
        raw.pop()
    return [ln.rstrip() for ln in raw]


# ================================================================
#  Renderers
# ================================================================
def _header_strip() -> None:
    bar = "▓▒░"
    label = "  S P E C T R E   ·   O N L I N E  "
    mid = f"{bar}{label}{bar}"
    color = _rgb(*_PURPLE_RGB)
    sys.stdout.write("\n")
    sys.stdout.write(_center(color + mid + _RST) + "\n")
    sys.stdout.write(
        _center(_rgb(*_PURPLE_RGB) + "─" * len(mid) + _RST) + "\n\n")
    sys.stdout.flush()


def _draw_logo(lines, delay=0.055):
    n = max(len(lines) - 1, 1)
    for i, line in enumerate(lines):
        t = i / n
        color = _gradient_color(t)
        sys.stdout.write(color + _center(line) + _RST + "\n")
        sys.stdout.flush()
        time.sleep(delay)


def _shimmer_pass(lines, delay=0.035):
    n = len(lines)
    for sweep in range(n):
        sys.stdout.write(f"\033[{n}A")
        for i, line in enumerate(lines):
            if i == sweep:
                sys.stdout.write("\033[97m" + _center(line) + _RST + "\n")
            else:
                t = i / max(n - 1, 1)
                sys.stdout.write(
                    _gradient_color(t) + _center(line) + _RST + "\n")
        sys.stdout.flush()
        time.sleep(delay)
    # final stable frame
    sys.stdout.write(f"\033[{n}A")
    for i, line in enumerate(lines):
        t = i / max(n - 1, 1)
        sys.stdout.write(
            _gradient_color(t) + _center(line) + _RST + "\n")
    sys.stdout.flush()


def _wordmark(console):
    w = _term_width()
    purple = _rgb(*_PURPLE_RGB)
    green = _rgb(*_GREEN_RGB)
    if w >= 55:
        sys.stdout.write(
            _center(purple + _BOLD + "S  P  E  C  T  R  E" + _RST) + "\n")
        sys.stdout.write(
            _center(green + "P H I S H I N G   S I M U L A T I O N   "
                    "F R A M E W O R K" + _RST) + "\n\n")
    else:
        sys.stdout.write(
            _center(purple + _BOLD + "S P E C T R E" + _RST) + "\n")
        sys.stdout.write(
            _center(green + "phishing simulation" + _RST) + "\n\n")
    sys.stdout.flush()


def _info_bar(console, version):
    info = Text()
    info.append("version ", style=T.HEX["text_dim"])
    info.append(f"v{version}", style=T.HEX["purple_hi"])
    info.append("   ·   ", style=T.HEX["text_mute"])
    info.append("built by ", style=T.HEX["text_dim"])
    info.append("DEDSEC", style=f"bold {T.HEX['purple_hi']}")
    info.append("   ·   ", style=T.HEX["text_mute"])
    info.append("authorized testing only", style=T.HEX["text_dim"])
    console.print(Align.center(info))
    console.print()
    console.print(Align.center(
        f"[italic {T.HEX['amber']}]\"{quote()}\"[/]"))
    console.print()


def _footer_strip():
    w = min(_term_width() - 4, 72)
    if w < 10:
        w = 10
    color = _rgb(*_GREEN_RGB)
    sys.stdout.write(_center(color + "─" * w + _RST) + "\n\n")
    sys.stdout.flush()


# ================================================================
#  Public entry points
# ================================================================
def print_banner(console=None, version="1.0.0", animate=True):
    console = console or Console()

    _header_strip()

    lines = _logo_lines()

    if animate:
        _draw_logo(lines, delay=0.055)
        # only shimmer in reasonably wide terminals — shimmer is
        # useless on a 3-line tiny logo
        if len(lines) >= 10:
            _shimmer_pass(lines, delay=0.035)
    else:
        for i, line in enumerate(lines):
            t = i / max(len(lines) - 1, 1)
            sys.stdout.write(
                _gradient_color(t) + _center(line) + _RST + "\n")
        sys.stdout.flush()

    sys.stdout.write("\n")
    sys.stdout.flush()

    _wordmark(console)
    _info_bar(console, version)
    _footer_strip()


def print_compact(console=None, version="1.0.0"):
    console = console or Console()
    purple = _rgb(*_PURPLE_RGB)
    console.print(f"{purple}◈ SPECTRE{RST} "
                  f"[{T.HEX['text_dim']}]v{version} · DEDSEC[/]")


def print_disclaimer(console=None):
    from rich.panel import Panel
    console = console or Console()
    body = Text.from_markup(
        f"[bold {T.HEX['red']}]⚠  READ BEFORE USE  ⚠[/]\n\n"
        f"[{T.HEX['text']}]SPECTRE clones login pages, serves them on "
        f"[b]localhost[/b] only, sends simulation emails to a "
        f"recipient allowlist you control, and records every "
        f"submission on a local dashboard.[/]\n\n"
        f"[{T.HEX['green_hi']}]The tool will NEVER:[/]\n"
        f"  • Publish the cloned page to the public internet\n"
        f"  • Send to recipients not on your allowlist\n"
        f"  • Scrape, buy, or auto-import recipient lists\n"
        f"  • Operate without your typed authorization confirmation\n\n"
        f"[{T.HEX['amber']}]You MUST have:[/]\n"
        f"  • Written authorization from every recipient's organization\n"
        f"  • Explicit consent from each individual if testing staff\n"
        f"  • Legal clearance to perform phishing simulations\n\n"
        f"[{T.HEX['red']}]Using SPECTRE against anyone without their "
        f"organization's written authorization is a criminal offense "
        f"under CFAA §1030, CMA §1-3, PECA §3 & §23, and equivalent "
        f"statutes worldwide.[/]\n\n"
        f"[bold {T.HEX['white']}]You are solely responsible for your use. "
        f"Every action this tool takes is attributed to you and you alone.[/]"
    )
    panel = Panel(
        body,
        title=f"[bold {T.HEX['purple_hi']}]⚠  LEGAL & ETHICAL NOTICE  ⚠[/]",
        border_style=T.HEX["purple"],
        padding=(1, 2),
    )
    console.print()
    console.print(panel)
    console.print()
