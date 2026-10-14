#!/usr/bin/env python3
"""
HTB Academy "Web Fuzzing" - vhost & subdomain fuzzing with GoBuster wordlists

Target: http://154.57.164.65:35361 (vHost zone inlanefreight.htb)

Answers:
  1. GoBuster vhost fuzzing with common.txt, prefix "web-"
     -> web-beans.inlanefreight.htb      (200; default vhost returns 404/153B)
  2. GoBuster dns fuzzing of inlanefreight.com with subdomains-top1million-5000.txt,
     prefix "su"
     -> support.inlanefreight.com

Usage: python3 solutions/gobuster_vhost_subdomain.py
"""
import concurrent.futures as cf
import json
import re
import sys
import urllib.parse
import urllib.request

TARGET = "http://154.57.164.65:35361/"
ZONE = "inlanefreight.htb"
WORDLISTS = {
    "common": "/tmp/common.txt",
    "subdomains": "/tmp/subdomains-top1million-5000.txt",
}
PREFIXES = ["web-", "su"]


def words_starting_with(path, prefix):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return sorted({w.strip() for w in fh
                           if w.strip() and w.strip().lower().startswith(prefix)})
    except FileNotFoundError:
        return []


def vhost_status(word):
    req = urllib.request.Request(TARGET, headers={"Host": "%s.%s" % (word, ZONE)})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return word, resp.status, len(resp.read())
    except urllib.error.HTTPError as exc:
        return word, exc.code, 0
    except Exception:
        return word, None, 0


def subdomain_exists(name):
    url = "https://dns.google/resolve?" + urllib.parse.urlencode({"name": name, "type": "A"})
    req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return name, bool(json.load(resp).get("Answer"))
    except Exception:
        return name, False


def main():
    print("== Q1 vhost fuzz (common.txt, prefix 'web-')")
    words = words_starting_with(WORDLISTS["common"], "web-")
    print("   testing %d words" % len(words), file=sys.stderr)
    with cf.ThreadPoolExecutor(max_workers=20) as pool:
        for word, status, size in pool.map(vhost_status, words):
            if status == 200:
                print("   %s.%s  (200, %d bytes)" % (word, ZONE, size))

    print("== Q2 subdomain fuzz (subdomains-top1million-5000.txt, prefix 'su')")
    words = words_starting_with(WORDLISTS["subdomains"], "su")
    print("   testing %d words" % len(words), file=sys.stderr)
    with cf.ThreadPoolExecutor(max_workers=20) as pool:
        for name, ok in pool.map(subdomain_exists, ["%s.inlanefreight.com" % w for w in words]):
            if ok:
                print("   %s" % name)


if __name__ == "__main__":
    main()
