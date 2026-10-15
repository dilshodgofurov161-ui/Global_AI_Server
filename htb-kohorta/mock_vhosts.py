#!/usr/bin/env python3
"""Mock cohort.htb — 05_vhost_enum.sh mantig'ini sinash uchun.
Host headeriga qarab har xil javob beradi."""
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT = b"<h1>cohort.htb default page</h1>"
VHOSTS = {
    "portal.cohort.htb": (200, b"<h1>Employee Portal - login</h1>" + b"P" * 200),
    "admin.cohort.htb":  (302, b""),
    "git.cohort.htb":    (200, b"<h1>GitLab</h1>" + b"G" * 50),
}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        host = (self.headers.get("Host") or "").split(":")[0].lower()
        entry = VHOSTS.get(host)
        if entry and entry[0] == 302:
            self.send_response(302)
            self.send_header("Location", "/login")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        code, body = entry if entry else (200, DEFAULT)
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18099
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()