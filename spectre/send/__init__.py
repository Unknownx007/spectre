# ============================================================
#  File: spectre/send/__init__.py
# ============================================================
from .smtp import SmtpSender
from . import templates
__all__ = ["SmtpSender", "templates"]
