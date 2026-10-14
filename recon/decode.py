p='g 4(){0 5="6{7!}";0 1=8 a();0 2="/9.c";1.d("e",2,f);1.b(3)}'
k='var|xhr|url|null|generateSerial|flag|HTB|1_4m_7h3_53r14l_g3n3r470r|new|serial|XMLHttpRequest|send|php|open|POST|true|function'.split('|')
import re
# tokens are base36 of index 0..16 -> '0'-'9','a'-'g'
mapd={}
for i in range(17):
    mapd[format(i,'x') if False else __import__('numpy').base_repr(i,36).lower()]=k[i]
def rep(m):
    t=m.group(0)
    return mapd.get(t,t)
out=re.sub(r'[0-9a-z]+', rep, p)
print(out)
