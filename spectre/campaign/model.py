# ============================================================
#  File: spectre/campaign/model.py
# ============================================================
import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class Recipient:
    email: str
    name: str = ""
    sent_at: Optional[str] = None
    opened_at: Optional[str] = None
    clicked_at: Optional[str] = None
    submitted_at: Optional[str] = None


@dataclass
class Campaign:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat(
            timespec="seconds") + "Z")
    authorization_confirmed_at: str = ""
    clone_target: str = ""
    clone_dir: str = ""
    serve_host: str = "127.0.0.1"
    serve_port: int = 8080
    redirect_after: str = "https://example.com"
    email_subject: str = ""
    email_body_template: str = ""
    email_from: str = ""
    email_sender_name: str = ""
    recipients: List[Recipient] = field(default_factory=list)
    status: str = "draft"     # draft / running / stopped / purged

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Campaign":
        recips = [Recipient(**r) for r in d.pop("recipients", [])]
        c = cls(**{k: v for k, v in d.items()
                   if k in cls.__dataclass_fields__})
        c.recipients = recips
        return c

    def save(self, path: str) -> str:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path

    @classmethod
    def load(cls, path: str) -> "Campaign":
        with open(path) as f:
            return cls.from_dict(json.load(f))
