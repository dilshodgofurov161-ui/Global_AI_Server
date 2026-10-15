#!/usr/bin/env python3
"""
Mock BlockSynergy app — FAQAT 02_web_chain.sh mantig'ini lokal sinash uchun.
Real targetga qarshi ishlatilmaydi.

Ishga tushirish:  python3 mock_server.py 18080
"""
import sys
import json
import re
from urllib.parse import unquote_plus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NODES = []  # ro'yxatdan o'tgan node URL lari


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[mock] %s %s\n" % (self.command, self.path))

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    # ---------------- POST ----------------
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode("utf-8", "replace")

        if self.path.startswith("/dashboard/wallet"):
            self._send(200, json.dumps({
                "public_key": "MOCK_PUBKEY_a1b2c3d4e5",
                "private_key": "MOCK_PRIVKEY",
                "filename": "blocksynergy",
            }), "application/json")

        elif self.path.startswith("/broadcast_transaction"):
            self._send(200, json.dumps({"status": "Added!", "txn": "forged-reward"}),
                       "application/json")

        elif self.path.startswith("/dashboard/vip/nodes"):
            m = re.search(r"node=([^\s&]+)", raw)
            if m:
                NODES.append(unquote_plus(m.group(1)))
            self._send(200, "<h1>VIP nodes</h1><p>registered</p>")

        else:
            self._send(404, "nope")

    # ---------------- GET ----------------
    def do_GET(self):
        if self.path.startswith("/dashboard/vip/nodes/test_node/"):
            # SSRF muvaffaqiyatli bo'lsa qaytadigan admin panel kontenti
            self._send(200,
                       "<html><h2>Admin &mdash; Nodes Manage</h2>"
                       "<form action='/admin/nodes/manage'>"
                       "<input name='target'><button>Ping a target</button>"
                       "</form><p>Ping a target</p></html>")

        elif self.path.startswith("/dashboard/vip/nodes"):
            rows = ""
            for i, url in enumerate(NODES):
                nid = i + 1
                rows += (f'<tr><td title="{url}">node-{i}</td>'
                         f'<td><a href="#" onclick="testNode(\'{nid}\')">test</a></td></tr>')
            self._send(200, f"<html><h1>VIP Nodes</h1><table>{rows}</table></html>")

        elif self.path.startswith("/dashboard/wallet"):
            self._send(200, "<h1>Wallet</h1>")

        else:
            self._send(404, "nope")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18080
    print(f"[mock] listening on http://127.0.0.1:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
