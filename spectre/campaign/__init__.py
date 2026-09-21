# ============================================================
#  File: spectre/campaign/__init__.py
# ============================================================
from .model import Campaign, Recipient
from .manager import CampaignManager
__all__ = ["Campaign", "Recipient", "CampaignManager"]
