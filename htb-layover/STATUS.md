# STATUS — where we stopped (Layover)

> Layover IP is **ephemeral**. HTB machines stop after inactivity; on re-spawn
> the IP **changes**. Always re-read the IP from the HTB dashboard.

## Done ✅

| Step | Result |
|---|---|
| Recon | `22/tcp OpenSSH 9.6p1`, `3389/tcp ms-wbt-server` — only 2 ports |
| RDP | `xfreerdp` works via WSLg. Logged in as `contractor` |
| Jumpbox | hostname `airside-ws01` |
| `sudo -l` | `(ALL : ALL) ALL` ✅ |
| groups | `sudo`, `netdev(111)`, `wireshark(121)` ✅ |
| WiFi ifaces | `wlan2`, `wlan3` present ✅ |
| SSID scan | **`HTB International WiFi`** — open (SECURITY `--`), CHAN 6, signal 100 |
| Firewall probe | ports `22` + `3389` OPEN, `4444` BLOCKED (jumpbox eth0 firewall) |

## Blocker ❌ — pushing files onto the jumpbox

The jumpbox has **no internet** (`curl https://github.com` → `000`) and the RDP
**clipboard does not sync**. Pushing over the VPN fails because the jumpbox
firewall REJECTs everything except 22/3389 (`nc` to 4444 → Connection refused).

`scp` reached the server but `contractor`'s SSH password was rejected
(`Authentications that can continue: publickey,password` →
`Permission denied, please try again.`), because password-SSH is disabled for
that account while RDP still works.

### Resume with ONE of these

```bash
# A) simplest: set a known password from the RDP session (we have sudo)
#    -- run on the JUMPBOX (RDP terminal):
sudo passwd contractor            # set e.g. Passw0rd123
#    -- then from WSL:
sshpass -p 'Passw0rd123' scp -O -o StrictHostKeyChecking=no \
  /tmp/lay/htb-layover/02_wifi_sniff.sh contractor@<IP>:/tmp/sniff.sh

# B) SSH key (no password needed)
#    WSL:     ssh-keygen -t ed25519 -f /tmp/lay_key -N ''; cat /tmp/lay_key.pub
#    JUMPBOX: mkdir -p ~/.ssh; chmod 700 ~/.ssh
#             echo '<PUBKEY>' >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys
#    WSL:     scp -i /tmp/lay_key -O user... contract...

# C) no transfer at all: type the script as a heredoc on the jumpbox
cat > /tmp/sniff.sh <<'EOF'
sudo ip link set wlan2 up
sudo nmcli device wifi connect "HTB International WiFi" ifname wlan2
ip -brief addr show wlan2
sudo nmcli device set wlan3 managed no
sudo ip link set wlan3 down
sudo iw dev wlan3 set type monitor
sudo ip link set wlan3 up
sudo iw dev wlan3 set channel 6
iwconfig wlan3
sudo tshark -i wlan3 -w /tmp/wifi.pcap
EOF
chmod +x /tmp/sniff.sh
```

## Remaining chain (not started yet)

1. **WiFi sniff** → join `HTB International WiFi`, monitor `wlan3` ch 6,
   `tshark` capture → cleartext POST → **`jenny : Fl1ghtDeck2026!`**
   (`portal.international.htb /miles/login.php`)
2. Note the **jumpbox's 10.13.37.x IP** (`ip -brief addr show wlan2`) — needed as
   the RCE callback address.
3. **Craft CMS 5.9.8 RCE** (CVE-2026-44011) → `www-data`
   → `htb-layover/06_craft_rce_stdlib.py` (stdlib only, no `requests`)
   → read `/var/www/portal/.env` (CRAFT_SECURITY_KEY, craftuser DB creds)
4. MySQL `htbairways_settings` → `aporter` relay password
   → `04_decrypt_aporter.php` (Yii2 `decryptByKey`)
5. `ssh aporter@...` → **`/home/aporter/user.txt`** [USER]
6. **CUPS 2.4.16 LPE** (CVE-2026-34990) → `05_cups_lpe.sh`
   → `/etc/sudoers.d/<user>-pwn` → `sudo -n bash` → **`/root/root.txt`** [ROOT]

> Flags are **per-instance** — derive them yourself, never copy from a write-up.

## Repo files

```
htb-layover/01_rdp.sh                 RDP + port check
htb-layover/02_wifi_sniff.sh          WiFi pivot + tshark credential capture
htb-layover/03_craft_rce.py           payload printer + exfil listener
htb-layover/04_decrypt_aporter.php    Yii2 decryptByKey helper
htb-layover/05_cups_lpe.sh            CUPS LPE runner
htb-layover/06_craft_rce_stdlib.py    full stdlib-only Craft RCE  (tested vs mock)
htb-layover/README.md                 full walkthrough
```
