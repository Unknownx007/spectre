# ============================================================
#  File: spectre/send/smtp.py
#  SMTP sender. Enforces safety headers on every message.
# ============================================================
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from ..core import safety
from ..core.logger import Logger
from ..core.errors import SendError


class SmtpSender:
    def __init__(self, logger: Logger, host: str, port: int = 587,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 use_tls: bool = True,
                 rate_per_min: int = safety.DEFAULT_RATE_PER_MIN):
        self.log = logger
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.limiter = safety.RateLimiter(rate_per_min)

    def send(self, to_email: str, from_email: str,
             sender_name: str, subject: str, body_html: str,
             body_text: str = "") -> bool:
        self.limiter.wait()

        msg = EmailMessage()
        msg["From"] = f"{sender_name} <{from_email}>" \
            if sender_name else from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        # enforce safety header — this is the tool's signed marker
        safety.enforce_headers(msg)

        msg.set_content(body_text or "Please view this email in HTML.")
        msg.add_alternative(body_html, subtype="html")

        try:
            if self.use_tls:
                ctx = ssl.create_default_context()
                with smtplib.SMTP(self.host, self.port) as s:
                    s.starttls(context=ctx)
                    if self.username:
                        s.login(self.username, self.password)
                    s.send_message(msg)
            else:
                with smtplib.SMTP(self.host, self.port) as s:
                    if self.username:
                        s.login(self.username, self.password)
                    s.send_message(msg)
            self.log.send(f"→ {to_email}")
            return True
        except Exception as e:
            self.log.err(f"send failed {to_email}: {e}")
            return False
