#!/usr/bin/env python3
"""
Virtual host bruteforcing (HTB Academy "Information Gathering - Web Edition")

Target: http://154.57.164.64:38845/ , vhost zone: inlanefreight.htb

The default vhost answers every request with the same page (116 bytes here), so a
valid vhost is detected by a *different* response size:

    Host: web17611.inlanefreight.htb  -> 106 bytes  (title "web17611")
    Host: vm5.inlanefreight.htb       ->  96 bytes
    Host: browse.inlanefreight.htb    -> 102 bytes
    Host: admin.inlanefreight.htb     -> 100 bytes
    Host: support.inlanefreight.htb   -> 104 bytes
    Host: anything-else               -> 116 bytes  (default)

Answers:
  web -> web17611.inlanefreight.htb
  vm  -> vm5.inlanefreight.htb
  br  -> browse.inlanefreight.htb
  a   -> admin.inlanefreight.htb
  su  -> support.inlanefreight.htb

Usage:
  python3 solutions/vhost_bruteforce.py [wordlist ...]
  python3 solutions/vhost_bruteforce.py --numbers web:0-20000 vm:0-60
"""
import concurrent.futures as cf
import sys
import urllib.request

TARGET = "http://154.57.164.64:38845/"
ZONE = "inlanefreight.htb"


def fetch(word, baseline):
    """Return (word, status, size, snippet) when the Host header changes the response."""
    req = urllib.request.Request(TARGET, headers={"Host": "%s.%s" % (word, ZONE)})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
            status = resp.status
    except Exception:
        return None
    if len(body) == baseline:
        return None
    return (word, status, len(body), body[:80].decode("utf-8", "replace").replace("\n", " "))


def baseline_size():
    req = urllib.request.Request(TARGET, headers={"Host": "zzqdoesnotexist." + ZONE})
    return len(urllib.request.urlopen(req, timeout=10).read())


def load_words(args):
    words = []
    if "--numbers" in args:
        for spec in args[args.index("--numbers") + 1:]:
            prefix, rng = spec.split(":")
            lo, hi = (int(x) for x in rng.split("-"))
            words.extend("%s%d" % (prefix, i) for i in range(lo, hi + 1))
    for path in [a for a in args if not a.startswith("--") and ":" not in a]:
        with open(path) as fh:
            words.extend(w.strip() for w in fh if w.strip())
    return words


def main():
    words = load_words(sys.argv[1:])
    if not words:
        print(__doc__)
        return
    baseline = baseline_size()
    print("baseline size: %d, testing %d words" % (baseline, len(words)), file=sys.stderr)

    hits = []
    with cf.ThreadPoolExecutor(max_workers=40) as pool:
        for res in pool.map(lambda w: fetch(w, baseline), words):
            if res:
                hits.append(res)
                print("HIT %-16s status=%s size=%s :: %s" % res, flush=True)
    print("total hits: %d" % len(hits), file=sys.stderr)


if __name__ == "__main__":
    main()
