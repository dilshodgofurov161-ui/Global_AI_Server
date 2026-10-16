#!/usr/bin/env python3
"""
mock_basic.py - tiny local replica of the "Monitoring Console" (HTTP Basic Auth)
used ONLY to self-test brute.py --basic-auth without the lab network.

    python3 mock_basic.py 9005
    python3 brute.py --url http://127.0.0.1:9005/ --username operator \
                     --basic-auth --wordlist wordlist.txt --threads 8
"""
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

USER = "operator"
PASSWORD = "summer2023"
FLAG = "HTB{m0ck_basic_auth_flag}"


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

    def do_GET(self):
        auth = self.headers.get("Authorization", "")
        ok = False
        if auth.startswith("Basic "):
            try:
                u, _, p = base64.b64decode(auth[6:]).decode().partition(":")
                ok = (u == USER and p == PASSWORD)
            except Exception:
                ok = False
        if ok:
            self._send(200, "<h1>Monitoring console</h1><p>%s</p>" % FLAG)
        else:
            self._send(401, "<h1>401 Unauthorized</h1>",
                       {"WWW-Authenticate": 'Basic realm="monitoring"'})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9005
    print("mock basic-auth console on http://127.0.0.1:%d  (%s / %s)"
          % (port, USER, PASSWORD))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
