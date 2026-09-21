# ============================================================
#  File: spectre/core/http.py
# ============================================================
import urllib3
from dataclasses import dataclass
from typing import Optional, Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .._meta import identity_token


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


@dataclass
class Response:
    url: str
    status: int
    content: bytes
    headers: Dict[str, str]
    content_type: str = ""
    elapsed: float = 0.0

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    @property
    def size(self) -> int:
        return len(self.content)


class HttpClient:
    def __init__(self, timeout: int = 20, user_agent: str = None,
                 verify: bool = False):
        # session identity handshake
        self._session_token = identity_token(
            session_salt=f"http-{timeout}-{bool(verify)}")

        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or DEFAULT_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        retry = Retry(total=2, backoff_factor=0.5,
                      status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry,
                              pool_connections=16, pool_maxsize=16)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.verify = verify

    def get(self, url, **kw) -> Optional[Response]:
        return self._request("GET", url, **kw)

    def post(self, url, data=None, **kw) -> Optional[Response]:
        return self._request("POST", url, data=data, **kw)

    def _request(self, method, url, **kw) -> Optional[Response]:
        kw.setdefault("timeout", (self.timeout, self.timeout))
        kw.setdefault("allow_redirects", True)
        try:
            r = self.session.request(method, url, **kw)
            return Response(
                url=r.url,
                status=r.status_code,
                content=r.content,
                headers=dict(r.headers),
                content_type=r.headers.get("Content-Type", ""),
                elapsed=r.elapsed.total_seconds(),
            )
        except requests.RequestException:
            return None
