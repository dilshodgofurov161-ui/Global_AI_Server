#!/usr/bin/env python3
"""
mock_server.py - tiny local replica of the "Staff Portal" login, used ONLY to
self-test brute.py without touching the lab network.

Run:
    python3 mock_server.py 9004        # listens on 127.0.0.1:9004
Then:
    python3 brute.py --url http://127.0.0.1:9004/login \
        --login-page http://127.0.0.1:9004/ \
        --username admin --wordlist wordlist.txt --fail "Invalid" --threads 20

It behaves like the real portal:  GET / returns the login form,
POST /login checks credentials, "Invalid credentials" on failure and the
flag on success. Password is chosen from wordlist.txt.
"""
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PASSWORD = "summer2023"          # pretend this came from rockyou.txt
FLAG = "HTB{m0ck_fl4g_r3pl4c3_m3}"

LOGIN_FORM = """<!doctype html><html><head><title>Acme Staff Portal</title></head>
<body><h1>Acme Staff Portal</h1>
<form method="POST" action="/login">
  <input type="text" name="username" placeholder="Username">
  <input type="password" name="password" placeholder="Password">
  <button type="submit">Log in</button>
</form></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/login"):
            self._send(200, LOGIN_FORM)
        else:
            self._send(404, "<h1>404</h1>")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n).decode("utf-8", "replace")
        form = urllib.parse.parse_qs(raw)
        user = (form.get("username") or [""])[0]
        pw = (form.get("password") or [""])[0]
        if user == "admin" and pw == PASSWORD:
            self._send(200, "<h1>Welcome admin</h1><p>%s</p>" % FLAG)
        else:
            self._send(200, "<h1>Login</h1><p>Invalid credentials</p>")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9004
    print("mock portal on http://127.0.0.1:%d  (admin / %s)" % (port, PASSWORD))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
