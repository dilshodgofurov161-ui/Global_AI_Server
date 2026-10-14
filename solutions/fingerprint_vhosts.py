#!/usr/bin/env python3
"""
Web server fingerprinting (HTB Academy "Information Gathering - Web Edition")

Target: 10.129.235.92 (ACADEMY-ATCKKAPS-APP01)
vHosts: app.inlanefreight.local, dev.inlanefreight.local

Questions / answers:
  1. Apache version on app.inlanefreight.local      -> 2.4.41
     (`Server: Apache/2.4.41 (Ubuntu)`)
  2. CMS used on app.inlanefreight.local            -> Joomla
     (whatweb: MetaGenerator[Joomla! - Open Source Content Management])
  3. OS of the dev.inlanefreight.local webserver    -> Ubuntu
     (`Server: Apache/2.4.41 (Ubuntu)`)

Two modes:
  live   : python3 solutions/fingerprint_vhosts.py 10.129.235.92 app.inlanefreight.local
  offline: python3 solutions/fingerprint_vhosts.py --file <saved `curl -I` output>
           (used here to verify the parsing against
            solutions/fixtures/app.inlanefreight.local.headers)
"""
import re
import sys
import urllib.request

SERVER_RE = re.compile(r"Apache/([\d.]+)\s*\(([^)]+)\)")
CMS_SIGNATURES = {
    "Joomla": (r"joomla", r"/components/com_", r"option=com_"),
    "WordPress": (r"wp-content", r"wp-includes", r"wordpress"),
    "Drupal": (r"drupal", r"sites/default/files"),
}


def fingerprint(text):
    """Return (apache_version, os, cms) from an HTTP header/body dump."""
    version = os_name = None
    match = SERVER_RE.search(text)
    if match:
        version, os_name = match.group(1), match.group(2)
    cms = None
    lowered = text.lower()
    for name, patterns in CMS_SIGNATURES.items():
        if any(re.search(p, lowered) for p in patterns):
            cms = name
            break
    return version, os_name, cms


def fetch(host, vhost, scheme="http", timeout=15):
    req = urllib.request.Request("%s://%s/" % (scheme, host), headers={"Host": vhost})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        head = "".join("%s: %s\n" % (k, v) for k, v in resp.getheaders())
        return head + "\n" + resp.read().decode("utf-8", "replace")


def main():
    if "--file" in sys.argv:
        with open(sys.argv[sys.argv.index("--file") + 1]) as fh:
            text = fh.read()
        version, os_name, cms = fingerprint(text)
        print("apache version : %s" % version)
        print("operating system: %s" % os_name)
        print("cms            : %s" % (cms or "n/a (no CMS signature in header dump)"))
        return

    host = sys.argv[1] if len(sys.argv) > 1 else "10.129.235.92"
    for vhost in sys.argv[2:] or ["app.inlanefreight.local", "dev.inlanefreight.local"]:
        text = fetch(host, vhost)
        version, os_name, cms = fingerprint(text)
        print("%-28s apache=%s os=%s cms=%s" % (vhost, version, os_name, cms or "-"))


if __name__ == "__main__":
    main()
