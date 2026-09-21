# ============================================================
#  File: spectre/__init__.py
# ============================================================
__version__  = "1.0.0"
__codename__ = "SPECTRE"
__author__   = "DEDSEC"
__motto__    = "Every click is a confession."

from ._meta import verify_provenance as _vp
_vp(__author__)
