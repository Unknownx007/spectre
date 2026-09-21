<div align="center">

<img width="948" height="768" alt="1" src="https://github.com/user-attachments/assets/5898a7b4-7569-4f6d-8b37-3fe62c895af8" />

**built by DEDSEC · "Every click is a confession."**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-c77dff?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-c77dff?style=flat-square)]()
[![License](https://img.shields.io/badge/license-AGPL--3.0%20%2B%20Attribution-ff003c?style=flat-square)]()
[![Status](https://img.shields.io/badge/status-v1.0.0-00ff9c?style=flat-square)]()

</div>

---

<div align="center">

# ⚠ LICENSED SOFTWARE — READ BEFORE USE

</div>

> **SPECTRE is licensed under AGPL-3.0 with Additional Attribution Terms.**
>
> *"Free to use, modify, and share. Not free to rebrand, rename, or claim as your own."*

### ✅ You **MAY**

- Use SPECTRE for personal, educational, or commercial security testing
- Modify it, extend it, add new features or templates
- Redistribute your modified version — **as long as** the license and attribution stay intact
- Include it in authorized engagements and security awareness programs
- Fork it and build on it (credit your additions to yourself)

### ❌ You **MAY NOT**

- **Rename or rebrand the tool** — the name "SPECTRE" stays
- **Remove or replace the author name "DEDSEC"** in the banner, credits, README, or reports
- **Claim authorship** or present the tool, or a fork of it, as your own original work
- **Reupload to another repository** without the LICENSE file, credits, and this notice
- **Strip the ASCII banner or startup text** that identifies the tool
- **Redistribute as closed-source** — AGPL requires source disclosure
- **Sell it as a rebranded product** without written permission from DEDSEC

### 🚫 You **MUST NOT** (Ethical & Legal)

- **Use SPECTRE against anyone without their organization's written authorization**
- **Send to recipients who have not consented to the test**
- **Use it for stalking, harassment, doxxing, or fraud**
- **Target employees, family members, or strangers** who have not agreed to be tested
- **Publish the Cloudflare tunnel URL** to anyone outside your authorized test scope

Violations are **copyright infringement**. They will be reported via DMCA
takedown and publicly disclosed with evidence.

### 📜 Why this license

I built this tool. I gave it away for free. You can use it, learn from it,
extend it. What you **cannot** do is take my work, change the author name
to yours, and pass it off as your own. That is theft, and it will be treated
as such.

**Official source:** [github.com/Unknownx007/spectre](https://github.com/Unknownx007/spectre)

Any copy hosted anywhere else without these credits intact is an unauthorized redistribution.

---

## ⚠ Legal & Ethical Notice

> **SPECTRE is a phishing simulation framework. It clones login pages, hosts them locally or via a Cloudflare tunnel, and records credentials submitted through the cloned form.**
>
> **Use ONLY on:**
> - Your own organization's employees, with HR/legal signoff
> - Authorized engagements with **written authorization** from every recipient's organization
> - Individuals who have **explicitly consented** to be tested
>
> Phishing simulations against anyone else are **criminal offenses** under:
> - **CFAA §1030** (United States)
> - **Computer Misuse Act §1–3** (United Kingdom)
> - **PECA §3 & §23** (Pakistan)
> - **StGB §202a–c** (Germany)
> - **GDPR Art. 32** (EU — for any captured personal data)
> - Equivalent statutes in nearly every jurisdiction
>
> Every action this tool takes is attributed to **you and you alone**.
> DEDSEC assumes no liability for misuse.

---

## What is SPECTRE?

SPECTRE is an automated phishing simulation framework. One command:

```
spectre https://target-org.com/login
```

...clones the login page, hosts it locally, prints the URL, and shows you
every credential submission in real time.

Optional `--cloudflare` flag starts a public tunnel so you can point a
phone, tablet, or remote test device at the page from anywhere.

Built for **authorized** security awareness testing. Not for real phishing.

---

## Features

| Feature | Description |
|---|---|
| **Auto mode** | One command: clone + host + live capture. No chain of subcommands required. |
| **Login page cloner** | Rewrites all assets locally, strips analytics/trackers, instruments every form. |
| **Local HTTP server** | Serves the cloned page on `127.0.0.1:8080` (or any port/host you choose). |
| **Cloudflare tunnel** | Optional `--cloudflare` flag. QUIC → HTTP/2 fallback, tunnel verified reachable before the URL is printed. |
| **Live terminal capture** | Every submission prints to the terminal in real time, with credentials, IP, and user-agent. |
| **GUI dashboard** | Optional `--gui` flag opens a PySide6 window with a live-updating table of captures. |
| **Multi-campaign management** | `spectre campaign` subcommands manage separate allowlisted campaigns. |
| **SMTP delivery** | Sends simulation emails to allowlisted recipients only. |
| **Report generation** | Automatic JSON + Markdown report at exit, with all captures and metadata. |
| **Enforced allowlist** | Every recipient must be in a text file you create. No scraping, no bulk imports. |
| **Consumer domain guard** | Gmail, Yahoo, Outlook, iCloud, and 15+ other consumer domains blocked by default. |
| **Rate limiting** | 5 emails/min default, hard cap 60/min. |
| **Provenance guard** | Refuses to run if the DEDSEC authorship has been stripped. |
| **Purge command** | `spectre purge <id>` overwrites and deletes all campaign data. |

---

## Safety rails

SPECTRE enforces its own rules in code. Bypassing them requires deliberately
editing the source.

1. **Recipient allowlist required.** Every email recipient must be listed in a
   plain-text file you explicitly create. There is no "paste list" mode.
2. **Every email carries `X-SPECTRE-Simulation: authorized-security-testing`.**
   Recipients who inspect headers see it's a test.
3. **Consumer email domains blocked by default.** Gmail, Yahoo, Outlook,
   iCloud, etc. — override only with `--allow-consumer-domains`.
4. **Typed authorization confirmation.** `--i-have-authorization` records a
   timestamp in every campaign file.
5. **Local-only by default.** The server binds to `127.0.0.1`. The public
   tunnel is opt-in and requires a second confirmation prompt.
6. **Cloudflare tunnel warning.** Before the tunnel starts, SPECTRE prints a
   full-red panel explaining the risks and requires a second `y/n`.
7. **Automatic report on exit.** Every run writes a JSON + Markdown report
   with all captures.
8. **Purge command.** `spectre purge <id>` overwrites files with random
   bytes, fsyncs, then unlinks.

---

## Requirements

### System

- **Python 3.10+**
- **cloudflared** (optional, only for `--cloudflare` mode)

### Python packages

```
requests>=2.31.0
beautifulsoup4>=4.12.0
rich>=13.7.0
flask>=3.0.0
PySide6>=6.6.0
flaredantic>=0.1.0
```

All installed automatically by `pip install -e .`

---

## Install

```bash
git clone https://github.com/Unknownx007/spectre.git
cd spectre

python3 -m venv venv
source venv/bin/activate           # Linux / macOS
# venv\Scripts\activate            # Windows

pip install -e .
```
### FOR TERMUX 

```
## For some users  Pyside6  will give an issue not to install to fix that for below instructions:

pkg install tur-repo -y
pkg install x11-repo -y
pkg update
pkg install pyside6 -y

# Then make a new venv with python and delete the old one :
python -m venv --system-site-packahes venv
source venv/bin/activate
pip install requests>=2.31.0 beautifulsoup4>=4.12.0 rich>=13.7.0 flask>=3.0.0 flaredantic>=0.1.0
pip install -e . --no-deps

# Now the Spectre should be installed

```

Verify:

```bash
spectre --version
# SPECTRE 1.0.0 (DEDSEC)
```

## REMEMBER NOT TO USE " --gui "" IN TERMUX
---

### Installing cloudflared (only for `--cloudflare` mode)

Three options:

**Option 1 — one command:**

```bash
spectre setup
```

Auto-detects your OS and installs cloudflared:

| OS | Method |
|---|---|
| Arch / Manjaro | `sudo pacman -S cloudflared` |
| Debian / Ubuntu / Kali | adds Cloudflare APT repo, then `apt install cloudflared` |
| Fedora / RHEL / Rocky | adds Cloudflare RPM repo, then `dnf install cloudflared` |
| Termux (Android) | `pkg install cloudflared` |
| macOS | `brew install cloudflared` |
| Other Linux | downloads the correct binary from GitHub → `/usr/local/bin/` |

Preview without running:

```bash
spectre setup --dry-run
```

**Option 2 — manual install:**

<details>
<summary>Debian / Ubuntu / Kali</summary>

```bash
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
  | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] \
https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt-get update && sudo apt-get install -y cloudflared
```
</details>

<details>
<summary>Arch / Manjaro</summary>

```bash
sudo pacman -S cloudflared
```
</details>

<details>
<summary>Fedora / RHEL / Rocky</summary>

```bash
curl -fsSL https://pkg.cloudflare.com/cloudflare-repo-$(rpm -E %rhel).rpm \
  -o /tmp/cf.rpm && sudo rpm -i /tmp/cf.rpm
sudo dnf install -y cloudflared
```
</details>

<details>
<summary>Termux (Android)</summary>

```bash
pkg update && pkg install cloudflared
```
</details>

<details>
<summary>macOS</summary>

```bash
brew install cloudflared
```
</details>

**Option 3 — pure Python (no system install):**

```bash
pip install flaredantic
```

SPECTRE will download cloudflared **once** into
`~/.local/share/spectre/cloudflared` and reuse it on every future run.

---

## Usage

### Auto mode (recommended)

```bash
spectre https://target-org.com/login
```

That's it. The tool:

1. Clones the login page
2. Starts a local HTTP server
3. Prints the URL
4. Live-tails every credential submission to the terminal
5. Writes a report when you press Ctrl+C

### Auto mode with public URL

```bash
spectre https://target-org.com/login --cloudflare
```

Adds a Cloudflare quick tunnel. Prints a `https://random-words.trycloudflare.com`
URL that reaches your local server from anywhere.

### Auto mode with GUI dashboard

```bash
spectre https://target-org.com/login --gui
```

Opens a PySide6 window with a live capture table in addition to the terminal tail.

### Auto mode — LAN-accessible (no tunnel)

```bash
spectre https://target-org.com/login --host 0.0.0.0 --port 8080
```

Reachable from any device on your Wi-Fi via `http://<your-laptop-ip>:8080/`.

### Auto mode — custom output and behavior

```bash
spectre https://target-org.com/login \
    --output ./my-engagement \
    --redirect https://target-org.com/ \
    --banner \
    --i-have-authorization
```

| Flag | Purpose |
|---|---|
| `--output DIR` | Where to save the cloned page (default: `~/spectre_data/pages/<host>`) |
| `--port N` | Local port (default 8080) |
| `--host HOST` | Bind address (default 127.0.0.1) |
| `--redirect URL` | Where to send users after capture (default https://example.com) |
| `--banner` | Inject a "phishing simulation" warning strip into the cloned page |
| `--gui` | Open the PySide6 dashboard window |
| `--cloudflare` | Start a public Cloudflare tunnel |
| `--keep` | Keep cloned files (they're kept anyway; this suppresses the note) |
| `--i-have-authorization` | Skip the confirmation prompt (only if you already have written permission) |

### Advanced subcommands

| Command | Purpose |
|---|---|
| `spectre clone <url> -o <dir>` | Clone only — no serve |
| `spectre serve <dir>` | Serve an existing cloned page |
| `spectre campaign new ...` | Create a scoped, allowlist-driven campaign |
| `spectre campaign list` | List campaigns |
| `spectre campaign show <id>` | Show campaign detail |
| `spectre dashboard <id>` | Open the GUI dashboard for a campaign |
| `spectre report <id>` | Export a JSON + Markdown report |
| `spectre purge <id>` | Overwrite + delete all data for a campaign |
| `spectre setup` | Install cloudflared for your OS |

---

## Example session

```
$ spectre https://target-org.com/login --cloudflare

```

---

## Output layout

```
~/spectre_data/
├── pages/
│   └── <host>/
│       ├── index.html           cloned page
│       └── assets/              rewritten assets
├── campaigns/
│   └── <campaign-id>.json       campaign definition
├── captures-<campaign-id>.jsonl one JSON record per submission
└── reports/
    ├── report-<campaign-id>.md  human-readable
    └── report-<campaign-id>.json machine-readable
```

### Capture record schema

```json
{
  "ts": "2026-09-21T23:24:50Z",
  "campaign": "20260921-232441",
  "ip": "10.0.0.42",
  "user_agent": "Mozilla/5.0 ...",
  "referer": "https://random-words.trycloudflare.com/",
  "username": "alice@corp",
  "password": "hunter2",
  "raw": { "username": "alice@corp", "password": "hunter2" }
}
```

### Report schema

```json
{
  "campaign": {
    "id": "20260921-232441",
    "name": "target-org.com",
    "created_at": "...",
    "authorization_confirmed_at": "...",
    "clone_target": "https://target-org.com/login",
    "clone_dir": "...",
    "serve_host": "127.0.0.1",
    "serve_port": 8080,
    "redirect_after": "https://example.com",
    "cloudflare_url": "https://random-words.trycloudflare.com",
    "status": "stopped"
  },
  "captures": [ ... ],
  "_origin_tool": "SPECTRE",
  "_origin_author": "DEDSEC",
  "_origin_repo": "https://github.com/Unknownx007/spectre",
  "_origin_digest": "...",
  "_origin_license": "AGPL-3.0 + Additional Attribution Terms"
}
```

Every report carries the DEDSEC provenance fields. Even a rebranded copy
leaves a DEDSEC watermark in its output.

---

## Directory layout

```
spectre/
├── spectre/
│   ├── __init__.py           provenance check at import
│   ├── __main__.py           auto mode + subcommands
│   ├── _meta.py              provenance guard
│   ├── banner.py             hooded figure + gradient animation
│   ├── theme.py              purple/green palette
│   ├── core/
│   │   ├── errors.py
│   │   ├── logger.py
│   │   ├── http.py
│   │   ├── safety.py         enforced allowlist / rate limit / etc.
│   │   └── ui.py             rich panels / tables
│   ├── clone/
│   │   └── cloner.py         asset rewriting + form instrumentation
│   ├── serve/
│   │   └── server.py         Flask capture server
│   ├── campaign/
│   │   ├── model.py
│   │   └── manager.py
│   ├── send/
│   │   ├── smtp.py
│   │   └── templates.py
│   ├── track/
│   │   └── dashboard.py      PySide6 GUI
│   └── report/
│       └── export.py         JSON + Markdown
├── pyproject.toml
├── requirements.txt
├── README.md
├── LICENSE
├── AUTHORS.md
└── .gitignore
```

---

## Troubleshooting

### Cloudflare Error 1033

"Tunnel error — host configured as Cloudflare Tunnel, unable to resolve."

**Cause:** tunnel is registered with the edge but the backend connection
never completes. Usually because your ISP throttles UDP/7844 (QUIC).

**Fix:** SPECTRE already handles this. It tries QUIC first, verifies the URL
is reachable, and falls back to HTTP/2 automatically. If both fail, check:

```bash
# Run manually to see the raw error
cloudflared tunnel --url http://127.0.0.1:8080 --protocol http2 --edge-ip-version 4
```

If manual works but SPECTRE doesn't, open an issue with both outputs.

### `spectre: command not found` after `pip install -e .`

The venv isn't active. Run `source venv/bin/activate` first.

### Warning: "This is a development server" from Flask

Cosmetic. Flask prints this on every start. SPECTRE suppresses the werkzeug
log lines via a logger level adjustment.

### Cloudflare tunnel downloads slowly / fails midway

GitHub's release CDN occasionally throttles. Retry `spectre --cloudflare`
once or twice. If it consistently fails, install cloudflared as a system
binary with `spectre setup`.

---

## Credits

**Built by DEDSEC.**

Conceptual lineage:

- **GoPhish** — allowlist-driven campaign model, safety-first design
- **Evilginx2** — reverse-proxy login cloning
- **SET (Social Engineering Toolkit)** — automated clone-and-capture workflow
- **Modlishka** — instrumentation design for credential capture

SPECTRE combines their ideas in one opinionated, safety-railed, Python 3.10+
package with a terminal-first UX and an optional GUI.

---

## License

SPECTRE — Phishing Simulation Framework
Copyright (c) 2026 DEDSEC
Licensed under AGPL-3.0 with Additional Terms (Section 7)

================================================================================
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

The full text of AGPL-3.0 is available at:
    https://www.gnu.org/licenses/agpl-3.0.txt

================================================================================
ADDITIONAL TERMS — Section 7 of the AGPL
================================================================================

In accordance with Section 7 of the AGPL-3.0, the following additional terms
apply to SPECTRE. These terms are non-waivable and apply to all copies,
modifications, and derivative works of the Software.

1. ATTRIBUTION OF AUTHORSHIP

   All copies, forks, derivative works, and redistributions of SPECTRE MUST
   retain, in full and unaltered form:

     • The copyright notice above (Copyright (c) 2026 DEDSEC)
     • This LICENSE file, including all additional terms
     • The author name "DEDSEC" in the CREDITS, AUTHORS, and README files
     • The provenance guard in `spectre/_meta.py` (unmodified)
     • The full text of this license displayed via `spectre --license`

2. PRESERVATION OF TOOL IDENTITY

   You may NOT:
     • Rename, rebrand, or republish SPECTRE under a different name
       without written permission from DEDSEC
     • Replace, obscure, or remove the "SPECTRE" name from the startup
       banner, ASCII logo, terminal output, documentation, or reports
     • Replace the "DEDSEC" attribution with your own name, handle, or brand
     • Present SPECTRE, or any substantial derivative of it, as your
       original work

   You MAY:
     • Add your own name as a "modifier" alongside the original author
       (e.g., "SPECTRE by DEDSEC, modified by <your-name>")
     • Fork SPECTRE and clearly state in your fork that it is a derivative
       of SPECTRE by DEDSEC
     • Add new features, modules, or templates — those additions may be
       credited to you

3. NOTIFICATION OF MODIFICATION

   Every modified copy MUST carry a prominent notice stating:
     • That the file has been modified
     • The date of modification
     • The name of the modifier

4. OPEN SOURCE OBLIGATION (AGPL §13)

   Any deployment of SPECTRE (or a modified version) as a network service
   MUST make the complete corresponding source code available to users of
   that service, in accordance with the AGPL-3.0.

5. NO WARRANTY

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
   OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
   THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
   DEALINGS IN THE SOFTWARE.

================================================================================
ENFORCEMENT
================================================================================

Violations of these additional terms — including rebranding, removal of
author credits, or closed-source redistribution — constitute copyright
infringement under the Berne Convention and the Digital Millennium Copyright
Act (DMCA).

Confirmed violations will be:
     • Reported to the platform hosting the infringing copy
     • Reported via GitHub DMCA takedown if applicable
     • Publicly disclosed with evidence

To request permission for commercial rebranding or a license exception,
contact DEDSEC through the official repository:

    https://github.com/Unknownx007/spectre

---
<div align="center">

*"We do not steal. We simulate. The difference is everything."*

</div>
---
