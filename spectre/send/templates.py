# ============================================================
#  File: spectre/send/templates.py
#  Minimal email templates. %url% is replaced with the landing
#  URL for each recipient (with a per-recipient token).
# ============================================================

IT_TEMPLATE = """
<html><body style="font-family:sans-serif;font-size:14px;color:#222;">
<p>Hi,</p>
<p>We've detected a sign-in from an unrecognized device on your account.
If this was not you, please verify your identity immediately using the
link below to prevent lockout.</p>
<p><a href="%url%">Verify my account</a></p>
<p>If you did not request this, please contact IT support.</p>
<p>— IT Security</p>
</body></html>
"""

PASSWORD_RESET_TEMPLATE = """
<html><body style="font-family:sans-serif;font-size:14px;color:#222;">
<p>Hi,</p>
<p>We received a request to reset your password. Click the link below
to choose a new one.</p>
<p><a href="%url%">Reset password</a></p>
<p>This link expires in 1 hour.</p>
<p>— Support</p>
</body></html>
"""

DOC_SHARE_TEMPLATE = """
<html><body style="font-family:sans-serif;font-size:14px;color:#222;">
<p>Hi,</p>
<p>%sender% has shared a document with you. Sign in to view it.</p>
<p><a href="%url%">Open document</a></p>
<p>— File Sharing</p>
</body></html>
"""


TEMPLATES = {
    "it":     IT_TEMPLATE,
    "reset":  PASSWORD_RESET_TEMPLATE,
    "share":  DOC_SHARE_TEMPLATE,
}


def render(template: str, url: str, sender: str = "Someone") -> str:
    tpl = TEMPLATES.get(template, IT_TEMPLATE)
    return tpl.replace("%url%", url).replace("%sender%", sender)
