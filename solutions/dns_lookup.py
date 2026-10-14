#!/usr/bin/env python3
"""
DNS answers (HTB Academy "Information Gathering - Web Edition", Digging DNS)

Q1: Which IP address maps to inlanefreight.com?          -> A record
Q2: Which domain is returned when querying the PTR
    record for 134.209.24.248?                            -> reverse lookup
Q3: What is the full domain returned when you query
    the mail records for facebook.com?                    -> MX record

Queries are sent over DNS-over-HTTPS (dns.google), so no dig/nslookup is needed.

Usage: python3 solutions/dns_lookup.py
"""
import json
import urllib.parse
import urllib.request

RESOLVER = "https://dns.google/resolve"
TYPE_NAMES = {1: "A", 5: "CNAME", 12: "PTR", 15: "MX", 16: "TXT", 2: "NS"}


def query(name, rtype):
    """Return the list of answer strings for name/type via DoH."""
    url = "%s?%s" % (RESOLVER, urllib.parse.urlencode({"name": name, "type": rtype}))
    req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)
    return [a.get("data", "") for a in data.get("Answer", [])]


def main():
    print("Q1  A    inlanefreight.com      ->", ", ".join(query("inlanefreight.com", "A")))
    ptr = query("248.24.209.134.in-addr.arpa", "PTR")
    print("Q2  PTR  134.209.24.248         ->", ", ".join(ptr).rstrip("."))
    mx = query("facebook.com", "MX")
    print("Q3  MX   facebook.com           ->", ", ".join(mx))


if __name__ == "__main__":
    main()
