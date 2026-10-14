#!/usr/bin/env python3
"""
WHOIS answers (HTB Academy "Information Gathering - Web Edition", Utilising WHOIS)

Q1: whois paypal.com -> registrar IANA ID
Q2: whois tesla.com  -> admin email contact

The .com registry (whois.verisign-grs.com) only returns a "thin" record, so for
tesla.com we follow the advertised Registrar WHOIS Server (whois.markmonitor.com)
to get the contact details.

Usage: python3 solutions/whois_lookup.py [domain ...]
"""
import re
import socket
import sys
import time


def whois_query(server, query, port=43, timeout=20, attempts=3):
    """Send a raw WHOIS query over TCP/43 and return the response text.

    Registrar WHOIS servers (e.g. whois.markmonitor.com) sometimes answer with an
    empty body when queried too often, so retry a couple of times.
    """
    last = ""
    for attempt in range(attempts):
        with socket.create_connection((server, port), timeout=timeout) as sock:
            sock.sendall((query + "\r\n").encode())
            chunks = []
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
        last = b"".join(chunks).decode("utf-8", "replace")
        if last.strip():
            return last
        time.sleep(3)
    return last


def registry_record(domain):
    return whois_query("whois.verisign-grs.com", "domain " + domain)


def registrar_record(registry_text, domain):
    match = re.search(r"Registrar WHOIS Server:\s*(\S+)", registry_text, re.I)
    if not match:
        return None, None
    server = match.group(1)
    return server, whois_query(server, domain)


def field(text, label):
    match = re.search(r"^\s*%s\s*:\s*(\S.*)$" % re.escape(label), text, re.I | re.M)
    return match.group(1).strip() if match else None


def main():
    for domain in (sys.argv[1:] or ["paypal.com", "tesla.com"]):
        print("=" * 60)
        print("domain:", domain)
        registry = registry_record(domain)
        print("  registrar IANA ID :", field(registry, "Registrar IANA ID"))
        print("  registrar         :", field(registry, "Registrar"))
        server, thick = registrar_record(registry, domain)
        if not thick:
            continue
        print("  registrar server  :", server)
        for label in ("Registrant Email", "Admin Email", "Tech Email"):
            value = field(thick, label)
            if value:
                print("  %-17s : %s" % (label, value))


if __name__ == "__main__":
    main()
