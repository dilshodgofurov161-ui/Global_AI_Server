import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = 'http://154.57.164.79:34341'
words = [w.strip() for w in open('/workspace/recon/common.txt') if w.strip() and not w.startswith('#')]

def check(path):
    url = BASE + '/' + path
    try:
        req = urllib.request.Request(url, method='GET', headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            return (r.status, path, r.headers.get('Content-Length'), r.headers.get('Content-Type'))
    except urllib.error.HTTPError as e:
        return (e.code, path, e.headers.get('Content-Length'), e.headers.get('Content-Type'))
    except Exception as e:
        return ('ERR', path, type(e).__name__, '')

cands = []
seen=set()
for w in words:
    for p in (w, w+'.php', w+'.html', w+'.txt', w+'/'):
        if p not in seen:
            seen.add(p); cands.append(p)

hits=[]
with ThreadPoolExecutor(max_workers=30) as ex:
    for res in ex.map(check, cands):
        if res[0] not in (404,):
            hits.append(res)
            print(res, flush=True)
print('tried', len(cands), 'hits', len([h for h in hits if h[0]!="ERR"]), 'errs', len([h for h in hits if h[0]=="ERR"]))
