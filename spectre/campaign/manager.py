# ============================================================
#  File: spectre/campaign/manager.py
# ============================================================
import os
from typing import List

from .model import Campaign, Recipient
from ..core import safety
from ..core.logger import Logger
from ..core.errors import CampaignError
from .._meta import identity_token


class CampaignManager:
    def __init__(self, logger: Logger, data_dir: str):
        self._session = identity_token(session_salt="campaign")
        self.log = logger
        self.data_dir = data_dir
        self.campaigns_dir = os.path.join(data_dir, "campaigns")
        os.makedirs(self.campaigns_dir, exist_ok=True)

    def create(self, name: str, clone_target: str, clone_dir: str,
               recipients: List[str], email_from: str,
               email_subject: str, email_body: str,
               serve_host: str = "127.0.0.1",
               serve_port: int = 8080,
               redirect_after: str = "https://example.com",
               authorized: bool = False) -> Campaign:
        # enforce authorization confirmation
        confirmed_at = safety.require_authorization(authorized)

        c = Campaign(
            name=name,
            authorization_confirmed_at=confirmed_at,
            clone_target=clone_target,
            clone_dir=clone_dir,
            serve_host=serve_host,
            serve_port=serve_port,
            redirect_after=redirect_after,
            email_from=email_from,
            email_subject=email_subject,
            email_body_template=email_body,
            recipients=[Recipient(email=r) for r in recipients],
        )
        path = os.path.join(self.campaigns_dir, f"{c.id}.json")
        c.save(path)
        self.log.ok(f"campaign created: {c.id}  ({len(recipients)} targets)")
        self.log.info(f"saved → {path}")
        return c

    def list(self) -> List[dict]:
        out = []
        for f in sorted(os.listdir(self.campaigns_dir)):
            if not f.endswith(".json"):
                continue
            try:
                c = Campaign.load(os.path.join(
                    self.campaigns_dir, f))
                out.append({
                    "id": c.id,
                    "name": c.name,
                    "sent": sum(1 for r in c.recipients if r.sent_at),
                    "opened": sum(1 for r in c.recipients if r.opened_at),
                    "clicked": sum(1 for r in c.recipients if r.clicked_at),
                    "submitted": sum(1 for r in c.recipients
                                     if r.submitted_at),
                    "status": c.status,
                })
            except Exception:
                continue
        return out

    def load(self, campaign_id: str) -> Campaign:
        path = os.path.join(self.campaigns_dir, f"{campaign_id}.json")
        if not os.path.isfile(path):
            raise CampaignError(f"campaign not found: {campaign_id}")
        return Campaign.load(path)

    def save(self, c: Campaign) -> str:
        path = os.path.join(self.campaigns_dir, f"{c.id}.json")
        c.save(path)
        return path
