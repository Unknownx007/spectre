# ============================================================
#  File: spectre/core/safety.py
#  Enforced safety rails. If any check raises, the operation
#  does not proceed. Bypassing requires editing this file.
# ============================================================
import os
import shutil
import time
from datetime import datetime
from typing import List

from .errors import SafetyError


DEFAULT_RATE_PER_MIN = 5
HARD_MAX_RATE        = 60

CONSUMER_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com",
    "live.com", "yahoo.com", "yahoo.co.uk", "icloud.com", "me.com",
    "aol.com", "protonmail.com", "proton.me", "gmx.com", "yandex.com",
    "qq.com", "163.com", "mail.com", "zoho.com",
}

SAFETY_HEADER       = "X-SPECTRE-Simulation"
SAFETY_HEADER_VALUE = "authorized-security-testing"


# ---- allowlist ------------------------------------------------------
def load_allowlist(path: str) -> set:
    if not os.path.isfile(path):
        raise SafetyError(
            f"allowlist file not found: {path}\n"
            f"create a text file with one email address per line. "
            f"SPECTRE will only send to addresses listed there.")
    with open(path) as f:
        entries = {
            line.strip().lower()
            for line in f
            if line.strip() and not line.startswith("#")
        }
    if not entries:
        raise SafetyError(f"allowlist is empty: {path}")
    return entries


def check_recipient(email: str, allowlist: set,
                    allow_consumer: bool = False) -> None:
    email = email.strip().lower()
    if "@" not in email:
        raise SafetyError(f"invalid recipient: {email!r}")
    if email not in allowlist:
        raise SafetyError(
            f"recipient not on allowlist: {email}")
    domain = email.rsplit("@", 1)[1]
    if domain in CONSUMER_DOMAINS and not allow_consumer:
        raise SafetyError(
            f"recipient is on a consumer email domain: {domain}\n"
            f"consumer domains are blocked by default — pentests "
            f"target corporate inboxes. Override with "
            f"--allow-consumer-domains if you have written consent "
            f"from this specific recipient.")


def validate_targets(targets: List[str], allowlist: set,
                     allow_consumer: bool = False) -> None:
    for t in targets:
        check_recipient(t, allowlist, allow_consumer)


# ---- rate limiter ----------------------------------------------------
class RateLimiter:
    def __init__(self, per_minute: int = DEFAULT_RATE_PER_MIN):
        if per_minute > HARD_MAX_RATE:
            raise SafetyError(
                f"rate limit {per_minute}/min exceeds hard cap "
                f"{HARD_MAX_RATE}/min")
        self.per_minute = per_minute
        self.interval = 60.0 / per_minute
        self._last = 0.0

    def wait(self):
        now = time.time()
        dt = now - self._last
        if dt < self.interval:
            time.sleep(self.interval - dt)
        self._last = time.time()


# ---- authorization ---------------------------------------------------
def require_authorization(confirmed: bool) -> str:
    if not confirmed:
        raise SafetyError(
            "campaign creation requires --i-have-authorization\n"
            "you are confirming that:\n"
            "  1. You have written authorization from every "
            "recipient's organization.\n"
            "  2. You will only send to the allowlist.\n"
            "  3. You will purge all captured data after the engagement.\n"
            "  4. You accept full legal responsibility for your use.\n"
            "This confirmation is recorded in the campaign file.")
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


# ---- headers ---------------------------------------------------------
def enforce_headers(headers: dict) -> dict:
    headers[SAFETY_HEADER] = SAFETY_HEADER_VALUE
    return headers


# ---- purge -----------------------------------------------------------
def purge_directory(path: str) -> None:
    """Overwrite-then-unlink then rmtree."""
    if not os.path.isdir(path):
        return
    for root, _dirs, files in os.walk(path):
        for name in files:
            p = os.path.join(root, name)
            try:
                size = os.path.getsize(p)
                with open(p, "r+b") as f:
                    f.write(os.urandom(size))
                    f.flush()
                    os.fsync(f.fileno())
            except Exception:
                pass
    shutil.rmtree(path, ignore_errors=True)
