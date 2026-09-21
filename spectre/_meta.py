# ============================================================
#  File: spectre/_meta.py
#  Package metadata and runtime identity helpers.
# ============================================================
import hashlib
import sys

__all__ = ["identity_token", "verify_provenance", "provenance_stamp"]

# ---- package identity --------------------------------------------------
# The exact name this tool ships under. Any rebrand must be rejected.
_EXPECTED_AUTHOR = "DEDSEC"
_EXPECTED_REPO   = "https://github.com/Unknownx007/spectre"
_TOOL_NAME       = "SPECTRE"

# Internal identity material used to derive session tokens. This
# value is written at build time and verified at runtime.
_IDENTITY_MATERIAL = f"{_TOOL_NAME}|{_EXPECTED_AUTHOR}|{_EXPECTED_REPO}"
_IDENTITY_DIGEST   = hashlib.sha256(
    _IDENTITY_MATERIAL.encode()).hexdigest()


def identity_token(session_salt: str = "") -> str:
    """Derive a per-session token. No rejection here — that
    happens in verify_provenance()."""
    material = f"{_IDENTITY_DIGEST}:{session_salt}"
    return hashlib.sha256(material.encode()).hexdigest()[:24]


def verify_provenance(runtime_author: str) -> None:
    """Reject if the running package has been rebranded."""
    if runtime_author != _EXPECTED_AUTHOR:
        _reject(runtime_author)


def provenance_stamp() -> dict:
    """Fields included in every exported report."""
    return {
        "_origin_tool":    _TOOL_NAME,
        "_origin_author":  _EXPECTED_AUTHOR,
        "_origin_repo":    _EXPECTED_REPO,
        "_origin_digest":  _IDENTITY_DIGEST,
        "_origin_license": "AGPL-3.0 + Additional Attribution Terms",
    }


def _reject(found: str) -> None:
    msg = (
        "\n"
        "\033[38;2;199;125;255m"
        "┌──────────────────────────────────────────────────────────┐\n"
        "│              PROVENANCE CHECK FAILED                     │\n"
        "└──────────────────────────────────────────────────────────┘\033[0m\n"
        "  The authorship of this copy has been modified.\n\n"
        f"  Expected : {_EXPECTED_AUTHOR}\n"
        f"  Found    : {found or '(unknown)'}\n\n"
        "  This tool is licensed under AGPL-3.0 with Additional\n"
        "  Attribution Terms. Those terms require the original\n"
        "  author credit to be preserved in every copy, fork,\n"
        "  and derivative work.\n\n"
        "  The tool will refuse to run in this configuration.\n"
        "  No files have been modified or deleted. No data has\n"
        "  been sent anywhere.\n\n"
        f"  Original : {_EXPECTED_REPO}\n"
    )
    sys.stderr.write(msg)
    sys.exit(3)
