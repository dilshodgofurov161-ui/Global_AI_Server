#!/usr/bin/env bash
# ============================================================
# HTB BlockSynergy — QADAM 0+1: muhit tayyorlash va recon
# Ishlatish (Kali, HTB VPN ulangan bo'lishi shart):
#     sudo ./01_recon.sh 10.129.132.212
# ============================================================
set -euo pipefail

TARGET="${1:-10.129.132.212}"
HOST="blocksynergy.htb"
mkdir -p scans loot

if [ "$(id -u)" -ne 0 ]; then
    echo "[!] OGOHLANTIRISH: root emassiz. /etc/hosts va MTU uchun sudo kerak."
    echo "    To'g'ri ishlatish:  sudo ./01_recon.sh $TARGET"
    echo
fi

echo "[*] Target : $TARGET"
echo "[*] Host   : $HOST"
echo

# ---------- 0. /etc/hosts ----------
if command -v getent >/dev/null 2>&1 && getent hosts "$HOST" >/dev/null 2>&1; then
    echo "[=] $HOST allaqachon resolve bo'ladi"
elif grep -qE "[[:space:]]$HOST([[:space:]]|$)" /etc/hosts 2>/dev/null; then
    echo "[=] $HOST allaqachon /etc/hosts da"
else
    echo "[+] /etc/hosts ga qo'shilmoqda (sudo kerak)"
    echo "$TARGET $HOST" | sudo tee -a /etc/hosts >/dev/null
    echo "[+] qo'shildi"
fi

# ---------- 0.1 VPN MTU fix ----------
# Belgisi: ssh banner keladi, keyin KEX da osilib qoladi
#          (ssh -vv -> expecting SSH2_MSG_KEX_ECDH_REPLY)
if ip link show tun0 >/dev/null 2>&1; then
    sudo ip link set dev tun0 mtu 1300
    echo "[+] tun0 MTU = 1300 (KEX hang oldini oladi)"
else
    echo "[!] tun0 topilmadi — HTB VPN hali ulanmagan bo'lishi mumkin"
fi
echo

# ---------- 1. Recon ----------
echo "[*] 1/2: to'liq port sweep (65535)..."
if command -v nmap >/dev/null 2>&1; then
    sudo nmap -p- --min-rate 5000 -Pn -oA scans/full "$TARGET" || \
        nmap -p- --min-rate 5000 -Pn -oA scans/full "$TARGET"

    echo
    echo "[*] 2/2: versiya + default scripts (22,8080)..."
    nmap -Pn -p22,8080 -sV -sC -oA scans/svc "$TARGET"
else
    echo "[!] nmap o'rnatilmagan. O'rnating: sudo apt update && sudo apt install -y nmap"
    exit 1
fi

echo
echo "============================================================"
echo "[+] KUTILGAN NATIJA (faqat 2 ta port):"
echo "      22/tcp   open  ssh    OpenSSH 9.6p1 Ubuntu 3ubuntu13.18"
echo "      8080/tcp open  http   Werkzeug httpd 3.1.3 (Python 3.12.3)"
echo "============================================================"
echo
echo "[+] Keyingi qadam:"
echo "      BASE=http://$HOST:8080 ./02_web_chain.sh"
