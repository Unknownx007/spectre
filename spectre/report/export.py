# ============================================================
#  File: spectre/report/export.py
#  Campaign report. Every report carries the provenance stamp.
# ============================================================
import json
from datetime import datetime
from typing import List

from .._meta import provenance_stamp


def export_json(payload: dict, path: str) -> str:
    payload = dict(payload)
    payload.update(provenance_stamp())
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path


MD_TEMPLATE = """# SPECTRE Campaign Report — {name}

**Campaign ID:** `{cid}`
**Generated:** {ts}
**Tool:** SPECTRE v1.0.0 — DEDSEC
**Authorized:** {auth_ts}

---

## Summary

| Metric | Count |
|---|---|
| Recipients | {n_total} |
| Emails sent | {n_sent} |
| Opened | {n_opened} |
| Clicked link | {n_clicked} |
| Submitted credentials | **{n_submitted}** |

---

## Captured Submissions

{captures}

---

## Recipients

{recipients}

---

*"Every click is a confession." — DEDSEC*
"""


def _captures_md(captures: List[dict]) -> str:
    if not captures:
        return "_No submissions captured._"
    lines = ["| # | Time | Username | Password | IP |",
             "|---|---|---|---|---|"]
    for i, c in enumerate(captures, 1):
        lines.append(
            f"| {i} | {c.get('ts','')} | `{c.get('username','')}` "
            f"| `{c.get('password','')}` | `{c.get('ip','')}` |")
    return "\n".join(lines)


def _recipients_md(recips: List[dict]) -> str:
    if not recips:
        return "_No recipients._"
    lines = ["| Email | Sent | Opened | Clicked | Submitted |",
             "|---|---|---|---|---|"]
    for r in recips:
        lines.append(
            f"| {r.get('email','')} "
            f"| {r.get('sent_at') or '-'} "
            f"| {r.get('opened_at') or '-'} "
            f"| {r.get('clicked_at') or '-'} "
            f"| {r.get('submitted_at') or '-'} |")
    return "\n".join(lines)


def export_markdown(campaign: dict, captures: List[dict],
                    path: str) -> str:
    md = MD_TEMPLATE.format(
        name=campaign.get("name", "Unnamed"),
        cid=campaign.get("id", ""),
        ts=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        auth_ts=campaign.get("authorization_confirmed_at", ""),
        n_total=len(campaign.get("recipients", [])),
        n_sent=sum(1 for r in campaign.get("recipients", [])
                   if r.get("sent_at")),
        n_opened=sum(1 for r in campaign.get("recipients", [])
                     if r.get("opened_at")),
        n_clicked=sum(1 for r in campaign.get("recipients", [])
                      if r.get("clicked_at")),
        n_submitted=len(captures),
        captures=_captures_md(captures),
        recipients=_recipients_md(campaign.get("recipients", [])),
    )
    with open(path, "w") as f:
        f.write(md)
    return path
