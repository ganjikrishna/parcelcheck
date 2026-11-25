#!/usr/bin/env python3
"""ParcelCheck local server. Serves the page and cached example results,
and runs live checks through checker.py. Explicit path allowlist: the
prep folder also holds the API key and the sealed answer key, which are
never served.

Bind: 127.0.0.1:8931 (local only; public exposure is a separate deploy step).
Caps: listing text max 20000 chars; 200 live runs per day, counted in
server-cap.json next to this file.
"""
import json, pathlib, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PREP = pathlib.Path.home() / "parcelcheck-prep"
ALLOWED = {"/": "index.html", "/index.html": "index.html",
           "/cached-L01.json": "cached-L01.json", "/cached-L07.json": "cached-L07.json"}
MAX_TEXT = 20000
DAILY_CAP = 200

import checker

def cap_ok():
    f = PREP / "server-cap.json"
    today = time.strftime("%Y-%m-%d")
    try:
        state = json.loads(f.read_text())
    except Exception:
        state = {"day": today, "count": 0}
    if state.get("day") != today:
        state = {"day": today, "count": 0}
    if state["count"] >= DAILY_CAP:
        return False
    state["count"] += 1
    f.write_text(json.dumps(state))
    return True

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        name = ALLOWED.get(self.path)
        if not name:
            self.send_error(404)
            return
        data = (PREP / name).read_bytes()
        ctype = "text/html" if name.endswith(".html") else "application/json"
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/check":
            self.send_error(404)
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            self.send_error(400)
            return
        text = (body.get("text") or "").strip()
        if not text or len(text) > MAX_TEXT:
            self._json(400, {"error": "Listing text missing or over 20000 characters."})
            return
        if not cap_ok():
            self._json(429, {"error": "Daily live run cap reached. Cached examples still work."})
            return
        try:
            result = checker.check(text, body.get("id") or "web")
        except Exception as e:
            self._json(502, {"error": "Checker run failed: " + str(e)[:200]})
            return
        self._json(200, result)

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8931), H).serve_forever()
