import base64, re

html = open('/workspace/recon/xss_page.html').read()
m = re.search(r'eval\(atob\("([^"]+)"\)\)', html)
outer = m.group(1)
print('outer b64 :', outer)
s = base64.b64decode(outer).decode()
print('outer dec :', s)
inner = re.search(r"atob\('([^']+)'\)", s).group(1)
print('inner b64 :', inner)
print('COOKIE    :', base64.b64decode(inner).decode())
