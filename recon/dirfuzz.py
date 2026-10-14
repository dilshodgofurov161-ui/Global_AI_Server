import sys, itertools
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = 'http://154.57.164.79:34341'

words = '''index index.php index.html app apps application api v1 v2 admin administrator login signin signup register auth account accounts user users profile profiles dashboard panel cpanel manage management console home main default test tests testing demo dev develop development stage staging debug phpinfo.php info status health healthz ping version about contact search query find lookup submit form upload uploads files file files download downloads docs doc documentation backup backups db database data config configs conf .env settings setup install readme README.md robots.txt sitemap.xml flag flag.txt flags secret secrets key keys token tokens hidden private internal local localhost server srv www web public static assets css js img images media lib libraries src vendor includes include inc functions lib common core cls class classes model models view views controller controllers route routes util utils helper helpers service services auth.php login.php search.php api.php index.php home.php main.php test.php flag.php submit.php form.php upload.php'''.split()

exts = ['', '.php', '.html', '.txt', '.json', '.bak', '/']

def check(path):
    url = BASE + '/' + path
    try:
        req = urllib.request.Request(url, method='GET', headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as r:
            return (r.status, path, r.headers.get('Content-Length'), r.headers.get('Content-Type'))
    except urllib.error.HTTPError as e:
        return (e.code, path, e.headers.get('Content-Length'), e.headers.get('Content-Type'))
    except Exception as e:
        return ('ERR', path, str(e), '')

cands = set()
for w in words:
    for e in exts:
        cands.add(w + e)
cands = sorted(cands)

interesting = []
with ThreadPoolExecutor(max_workers=20) as ex:
    for res in ex.map(check, cands):
        code, path, cl, ct = res
        if code not in (404, 'ERR') and code != 403:
            interesting.append(res)
        elif code == 200:
            interesting.append(res)

for r in interesting:
    print(r)
print('total tried', len(cands), 'interesting', len(interesting))
