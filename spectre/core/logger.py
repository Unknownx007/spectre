# ============================================================
#  File: spectre/core/logger.py
# ============================================================
import time
from datetime import datetime

from rich.console import Console

from .. import theme as T
from .._meta import identity_token


LEVEL_STYLE = {
    "INFO":    T.HEX["cyan"],
    "OK":      T.HEX["green"],
    "WARN":    T.HEX["amber"],
    "ERR":     T.HEX["red"],
    "STEP":    T.HEX["purple"],
    "DATA":    T.HEX["text"],
    "HIT":     f"bold {T.HEX['purple_hi']}",
    "SEND":    f"bold {T.HEX['amber']}",
    "CAPTURE": f"bold {T.HEX['green_hi']}",
}


class Logger:
    def __init__(self, verbose: bool = True, quiet: bool = False,
                 console: Console = None):
        self._session_id = identity_token(session_salt="logger")
        self.verbose = verbose
        self.quiet = quiet
        self.console = console or Console()
        self.records = []
        self.started = time.time()

    def _emit(self, level: str, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        rec = {"ts": ts, "level": level, "msg": msg,
               "elapsed": round(time.time() - self.started, 3)}
        self.records.append(rec)
        if self.verbose and not self.quiet:
            style = LEVEL_STYLE.get(level, T.HEX["text"])
            tag = f"[{style}][{level:^7}][/]"
            self.console.print(f"[{T.HEX['text_dim']}]{ts}[/] {tag} {msg}")

    def info(self, m):     self._emit("INFO", m)
    def ok(self, m):       self._emit("OK", m)
    def warn(self, m):     self._emit("WARN", m)
    def err(self, m):      self._emit("ERR", m)
    def step(self, m):     self._emit("STEP", m)
    def data(self, m):     self._emit("DATA", m)
    def hit(self, m):      self._emit("HIT", m)
    def send(self, m):     self._emit("SEND", m)
    def capture(self, m):  self._emit("CAPTURE", m)

    def dump(self):
        return list(self.records)
