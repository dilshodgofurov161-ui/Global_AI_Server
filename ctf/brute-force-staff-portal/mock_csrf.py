#!/usr/bin/env python3
"""
mock_csrf.py - tiny local replica of "SecureDesk" (single-use, session-bound
CSRF token) used ONLY to self-test brute.py --csrf-fresh.

    python3 mock_csrf.py 9009
    python3 brute.py --url http://127.0.0.1:9009/login \
                     --login-page http://127.0.0.1:9009/login \
                     --username jdoe --csrf-fresh \
                     --wordlist wordlist.txt --fail "Invalid" --threads 8

Key behaviour: the token is SINGLE-USE and bound to a session cookie, so a
naive brute force (one token reused) fails. --csrf-fresh gets a new token +
new session for every attempt.
"""
import os
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

USER = "jdoe"
PASSWORD = "sunshine"
FLAG = "HTB{m0ck_csrf_flag}"

SESSIONS = {}  # sid -> {"token": t, "used": bool}


def form_page(token, msg=""):
    return ("<!doctype html><html><head><title>SecureDesk</title></head><body>"
            "%s"
            "<form method='POST' action='/login'>"
            "<input name='username'>"
            "<input name='password' type='password'>"
            "<input type='hidden' name='csrf_token' value='%s'>"
            "<button>Sign in</button></form></body></html>" % (msg, token))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, extra=None):
        b = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(b)

    def _cookie(self):
        c = self.headers.get("Cookie", "")
        m = re.search(r"session=([^;]+)", c)
        return m.group(1) if m else None

    def do_GET(self):
        sid = os.urandom(8).hex()
        token = os.urandom(16).hex()
        SESSIONS[sid] = {"token": token, "used": False}
        self._send(200, form_page(token),
                   {"Set-Cookie": "session=%s; Path=/" % sid})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        f = urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8", "replace"))
        sid = self._cookie()
        tok = (f.get("csrf_token") or [""])[0]
        user = (f.get("username") or [""])[0]
        pw = (f.get("password") or [""])[0]

        sess = SESSIONS.get(sid) if sid else None
        if not sess or sess["used"] or tok != sess["token"]:
            self._send(200, form_page("", "<h1>Login failed</h1>"
                                      "<p>Invalid CSRF token.</p>"))
            return
        sess["used"] = True  # single-use
        if user == USER and pw == PASSWORD:
            self._send(200, "<h1>Welcome %s</h1><p>%s</p>" % (USER, FLAG))
        else:
            self._send(200, form_page("", "<h1>Login failed</h1>"
                                      "<p>Invalid username or password.</p>"))

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9009
    print("mock SecureDesk (CSRF) on http://127.0.0.1:%d  (%s / %s)"
          % (port, USER, PASSWORD))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
