# ============================================================
#  File: spectre/core/errors.py
# ============================================================
class SpectreError(Exception): pass
class HttpError(SpectreError): pass
class CloneError(SpectreError): pass
class ServeError(SpectreError): pass
class CampaignError(SpectreError): pass
class SafetyError(SpectreError): pass
class SendError(SpectreError): pass
