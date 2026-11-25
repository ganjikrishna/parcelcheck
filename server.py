"""ParcelCheck local-only development server.

Serves the ParcelCheck frontend and cached examples from the prep
folder, bound to 127.0.0.1 port 8931 (local-only, 127.0.0.1:8931).

Only an explicit allowlist is ever served: "/" and "/index.html"
serve index.html, "/cached-L01.json" serves cached-L01.json, and
"/cached-L07.json" serves cached-L07.json. The prep folder also
holds the API key and the sealed answer key, which must never be
served, so the allowlist is explicit and nothing else in the prep
folder is served; all other paths return 404.

POST /check runs checker.check for live listings. Caps: listing
text is limited to 20000 chars, and at most 200 live runs per day
counted in server-cap.json in the prep folder.
"""

import json
import os
import sys
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PREP_DIR = Path(os.environ.get("PARCELCHECK_DIR") or Path(__file__).resolve().parent)
if str(PREP_DIR) not in sys.path:
    sys.path.insert(0, str(PREP_DIR))

import checker  # noqa: E402

HOST = "127.0.0.1"
PORT = 8931
MAX_TEXT_CHARS = 20000
DAILY_RUN_CAP = 200
CAP_FILE = PREP_DIR / "server-cap.json"

ALLOWLIST = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/cached-L01.json": ("cached-L01.json", "application/json; charset=utf-8"),
    "/cached-L07.json": ("cached-L07.json", "application/json; charset=utf-8"),
}

_cap_lock = threading.Lock()


def _consume_daily_run():
    """Increment the daily counter if under the cap.

    Returns True if a run is allowed (counter incremented and saved
    before running), False if the daily cap has been reached.
    """
    today = date.today().isoformat()
    with _cap_lock:
        count = 0
        try:
            state = json.loads(CAP_FILE.read_text(encoding="utf-8"))
            if isinstance(state, dict) and state.get("day") == today:
                try:
                    count = int(state.get("count", 0))
                except (TypeError, ValueError):
                    count = 0
        except Exception:
            count = 0
        if count >= DAILY_RUN_CAP:
            return False
        count += 1
        try:
            CAP_FILE.write_text(
                json.dumps({"day": today, "count": count}), encoding="utf-8"
            )
        except Exception:
            pass
        return True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def _send_bytes(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _send_json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8")

    def _send_not_found(self):
        self._send_bytes(404, b"Not Found", "text/plain; charset=utf-8")

    def do_GET(self):
        path = urlparse(self.path).path
        entry = ALLOWLIST.get(path)
        if entry is None:
            self._send_not_found()
            return
        filename, content_type = entry
        try:
            data = (PREP_DIR / filename).read_bytes()
        except OSError:
            self._send_not_found()
            return
        self._send_bytes(200, data, content_type)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/check":
            self._send_not_found()
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "Bad JSON."})
            return
        if not isinstance(body, dict):
            self._send_json(400, {"error": "Bad JSON."})
            return
        raw_text = body.get("text")
        text = raw_text.strip() if isinstance(raw_text, str) else ""
        if not text or len(text) > MAX_TEXT_CHARS:
            self._send_json(
                400,
                {"error": "Listing text missing or over 20000 characters."},
            )
            return
        if not _consume_daily_run():
            self._send_json(
                429,
                {"error": "Daily live run cap reached. Cached examples still work."},
            )
            return
        listing_id = body.get("id") or "web"
        try:
            result = checker.check(text, listing_id)
        except Exception as exc:
            self._send_json(
                502,
                {"error": "Checker run failed: " + str(exc)[:200]},
            )
            return
        try:
            payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
        except Exception as exc:
            self._send_json(
                502,
                {"error": "Checker run failed: " + str(exc)[:200]},
            )
            return
        self._send_bytes(200, payload, "application/json; charset=utf-8")


ParcelCheckHandler = Handler


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
