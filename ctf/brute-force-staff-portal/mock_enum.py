#!/usr/bin/env python3
"""
mock_enum.py - local replica of the "Acme intranet" login used to self-test
enum_users.py and gen_wordlist.py (challenge 10).

    python3 mock_enum.py 9010

Behaviour:
  * /        and /login  -> login form
  * /team    -> OSINT page (names / e-mails)  [GET]
  * POST /login:
        unknown username  -> "Unknown username."
        valid + bad pass  -> "Incorrect password."
        valid + good pass -> flag

Valid accounts (admin is deliberately out of reach):
    jdoe   / Sunshine1988!      (crackable from the /team OSINT)
    admin  / <random strong>    (NOT crackable)
"""
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ACCOUNTS = {
    "jdoe": "Sunshine1988!",
    "admin": "Zq7#vLp2!xR9mKd4Wt6Y (not crackable)",
}
FLAG = "HTB{m0ck_user_enum_flag}"

TEAM_PAGE = """<!doctype html><html><head><title>Acme - Our Team</title></head><body>
<h1>Our Team</h1>
<ul>
  <li>John Doe (jdoe) - Security Engineer. Born 1988-03-12.
      Dog named <b>Sunshine</b>. Loves the Acme SecureDesk product line.</li>
  <li>Maria Roe - Sysadmin. Contact: mroe@acme.corp</li>
  <li>Admin - contact admin@acme.corp (do not e-mail)</li>
</ul>
<p>Internal intranet. Company: Acme Corp.</p>
</body></html>"""

LOGIN_PAGE = """<!doctype html><html><head><title>Acme Intranet Login</title></head>
<body><h1>Acme Intranet</h1>
<form method="POST" action="/login">
  <input name="username"><input name="password" type="password">
  <button>Log in</button></form></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        b = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/team":
            self._send(200, TEAM_PAGE)
        else:
            self._send(200, LOGIN_PAGE)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        f = urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8", "replace"))
        u = (f.get("username") or [""])[0]
        p = (f.get("password") or [""])[0]
        if u not in ACCOUNTS:
            self._send(200, "<h1>Login</h1><p>Unknown username.</p>")
        elif ACCOUNTS[u] == p:
            self._send(200, "<h1>Welcome %s</h1><p>%s</p>" % (u, FLAG))
        else:
            self._send(200, "<h1>Login</h1><p>Incorrect password.</p>")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9010
    print("mock Acme intranet on http://127.0.0.1:%d  (jdoe/Sunshine1988!)" % port)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
