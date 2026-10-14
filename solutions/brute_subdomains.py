#!/usr/bin/env python3
"""
Subdomain bruteforcing (HTB Academy "Information Gathering - Web Edition")

Question: Using the known subdomains for inlanefreight.com
(www, ns1, ns2, ns3, blog, support, customer), find any missing subdomains by
brute-forcing possible domain names. Answer with the complete subdomain.

Brute forces A records with a thread pool and prints every name that resolves.
With SecLists' subdomains-top1million-5000.txt this yields
blog / customer / my / ns1 / ns2 / ns3 / support / www -> the missing one is
`my.inlanefreight.com`.

Lookups use DNS-over-HTTPS (dns.google) by default because plain UDP/53 drops
packets when many threads query at once; pass --udp to use UDP/53 instead.

Usage: python3 solutions/brute_subdomains.py [domain] [wordlist] [--udp]
"""
import concurrent.futures as cf
import json
import os
import random
import socket
import struct
import sys
import time
import urllib.parse
import urllib.request

SECLISTS_URL = ("https://raw.githubusercontent.com/danielmiessler/SecLists/master/"
                "Discovery/DNS/subdomains-top1million-5000.txt")
DOH_URL = "https://dns.google/resolve"


def build_query(name, qtype=1):
    tid = random.randint(0, 0xFFFF)
    header = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    qname = b"".join(bytes([len(p)]) + p.encode() for p in name.split(".")) + b"\x00"
    return header + qname + struct.pack("!HH", qtype, 1)


def resolves_doh(name, timeout=15):
    """True if the name has an answer according to dns.google (DNS-over-HTTPS)."""
    url = "%s?%s" % (DOH_URL, urllib.parse.urlencode({"name": name, "type": "A"}))
    req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    return bool(data.get("Answer"))


def resolves_udp(server, name, timeout=4):
    """True if the name has an answer over plain DNS (UDP/53)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(build_query(name), (server, 53))
        data, _ = sock.recvfrom(4096)
    except OSError:
        return False
    finally:
        sock.close()
    rcode = data[3] & 0x0F
    ancount = struct.unpack("!H", data[6:8])[0]
    return rcode == 0 and ancount > 0


def resolves(name, use_udp=False, attempts=2):
    """Retry a couple of times so a single dropped packet is not reported as NXDOMAIN."""
    for _ in range(attempts):
        try:
            if use_udp:
                if resolves_udp("8.8.8.8", name):
                    return True
            elif resolves_doh(name):
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def load_wordlist(path):
    if not os.path.exists(path):
        print("downloading %s -> %s" % (SECLISTS_URL, path), file=sys.stderr)
        urllib.request.urlretrieve(SECLISTS_URL, path)
    with open(path) as fh:
        return [w.strip() for w in fh if w.strip()]


def main():
    args = [a for a in sys.argv[1:] if a != "--udp"]
    use_udp = "--udp" in sys.argv
    domain = args[0] if args else "inlanefreight.com"
    wordlist = args[1] if len(args) > 1 else "/tmp/subdomains-top1million-5000.txt"

    words = load_wordlist(wordlist)
    print("testing %d names (%s)" % (len(words), "udp/53" if use_udp else "doh"),
          file=sys.stderr)

    found = []
    with cf.ThreadPoolExecutor(max_workers=40) as pool:
        futures = {pool.submit(resolves, "%s.%s" % (w, domain), use_udp): w for w in words}
        for fut in cf.as_completed(futures):
            if fut.result():
                name = "%s.%s" % (futures[fut], domain)
                found.append(name)
                print("FOUND", name, flush=True)
    print("total found: %d -> %s" % (len(found), ", ".join(sorted(found))), file=sys.stderr)


if __name__ == "__main__":
    main()
