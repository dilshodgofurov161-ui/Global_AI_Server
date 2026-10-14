#!/usr/bin/env python3
"""
HTB Academy "Information Gathering - Web Edition" - Skills Assessment

Target: http://154.57.164.81:36251 (vHost inlanefreight.htb)

Answers:
  1. IANA ID of the registrar of inlanefreight.com        -> 468 (Amazon Registrar, Inc.)
  2. HTTP server powering inlanefreight.htb               -> nginx
  3. API key in the hidden admin directory                -> e963d863ee0e82ba7080fbf558ca0d3f
     (vhost web1337.inlanefreight.htb -> robots.txt: Disallow: /admin_h1dd3n)
  4. Email found while crawling                           -> 1337testing@inlanefreight.htb
     (dev.web1337.inlanefreight.htb, linked "Next" page chain)
  5. API key the developers will be changing to           -> ba988b835be4aa97d068941dc852ff33
     (HTML comment: <!-- Remember to change the API key to ... -->)

Usage: python3 solutions/infogath_skills_assessment.py [TARGET]
"""
import re
import socket
import sys
import urllib.request
from urllib.parse import urljoin

TARGET = "http://154.57.164.81:36251"
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
LINK_RE = re.compile(r'href="([^"]+)"')
API_KEY_RE = re.compile(r"API is still accessible with the key ([0-9a-f]{32})")
NEW_KEY_RE = re.compile(r"change the API key to ([0-9a-f]{32})")


def http(path, vhost, base=TARGET):
    req = urllib.request.Request(urljoin(base + "/", path.lstrip("/")), headers={"Host": vhost})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", "replace")


def whois_registrar_iana(domain):
    """Read the registrar IANA ID from the registry WHOIS (TCP/43)."""
    with socket.create_connection(("whois.verisign-grs.com", 43), timeout=20) as sock:
        sock.sendall(("domain " + domain + "\r\n").encode())
        data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    match = re.search(r"Registrar IANA ID:\s*(\d+)", data.decode("utf-8", "replace"), re.I)
    return match.group(1) if match else "n/a"


def crawl_chain(vhost, limit=600):
    """Follow the 'Next' link chain and collect emails and HTML comments."""
    path, emails, comments, pages = "/", set(), set(), 0
    while pages < limit:
        try:
            body = http(path, vhost)
        except Exception:
            break
        pages += 1
        emails.update(EMAIL_RE.findall(body))
        comments.update(c.strip() for c in COMMENT_RE.findall(body))
        links = [l for l in LINK_RE.findall(body) if not l.startswith(("http", "//"))]
        if not links:
            break
        path = links[0]
    return emails, comments, pages


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else TARGET

    print("Q1 registrar IANA ID :", whois_registrar_iana("inlanefreight.com"))

    req = urllib.request.Request(base + "/", headers={"Host": "inlanefreight.htb"})
    server = urllib.request.urlopen(req, timeout=15).headers.get("Server", "")
    print("Q2 server software   :", server.split("/")[0])

    robots = http("/robots.txt", "web1337.inlanefreight.htb", base)
    disallow = re.search(r"Disallow:\s*(\S+)", robots)
    admin_dir = disallow.group(1) if disallow else "/admin_h1dd3n"
    print("   hidden admin dir  :", admin_dir, "(from robots.txt)")

    admin = http(admin_dir + "/", "web1337.inlanefreight.htb", base)
    key = API_KEY_RE.search(admin)
    print("Q3 admin API key     :", key.group(1) if key else "n/a")

    emails, comments, pages = crawl_chain("dev.web1337.inlanefreight.htb")
    print("Q4 email             :", ", ".join(sorted(emails)) or "n/a", "(%d pages crawled)" % pages)
    new_key = None
    for comment in comments:
        m = NEW_KEY_RE.search(comment)
        if m:
            new_key = m.group(1)
    print("Q5 key to change to  :", new_key or "n/a")


if __name__ == "__main__":
    main()
