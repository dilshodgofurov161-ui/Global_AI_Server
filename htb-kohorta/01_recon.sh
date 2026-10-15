#!/usr/bin/env bash
# ============================================================
# Kohorta (HTB, Easy, Linux) — QADAM 1: muhit + recon
#
# Ishlatish (Kali/Pwnbox, HTB VPN ulangan):
#     sudo ./01_recon.sh 10.129.244.174
# ============================================================
set -uo pipefail

TARGET="${1:-10.129.244.174}"
HOST="${2:-kohorta.htb}"
LHOST="${LHOST:-}"
OUT="scans"
mkdir -p "$OUT" loot

say() { printf '\n\033[1;36m[*] %s\033[0m\n' "$*"; }
ok()  { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn(){ printf '\033[1;33m[!]\033[0m %s\n' "$*"; }

[ "$(id -u)" -ne 0 ] && warn "root emassiz — /etc/hosts va MTU uchun sudo kerak"

# ---------- 0. Muhit ----------
say "0. Muhit tayyorlash"

if ! grep -qE "[[:space:]]$HOST([[:space:]]|$)" /etc/hosts 2>/dev/null; then
    echo "$TARGET $HOST" | sudo tee -a /etc/hosts >/dev/null && ok "$HOST -> $TARGET"
else
    ok "$HOST allaqachon /etc/hosts da"
fi

if ip link show tun0 >/dev/null 2>&1; then
    sudo ip link set dev tun0 mtu 1300 && ok "tun0 MTU=1300"
    VPNIP=$(ip -4 addr show tun0 | grep -oP 'inet \K[\d.]+' || true)
    ok "tun0 IP = $VPNIP   (LHOST=$VPNIP)"
else
    warn "WSL'da tun0 yo'q — bu har doim ham muammo emas:"
    warn "  * Windows'da OpenVPN ulangan bo'lsa -> NORMAL (WSL NAT orqali o'tadi)"
    warn "  * Aks holda kerak: sudo openvpn --config ~/vpn/machines_us-3.ovpn"
    warn "  (pastdagi 'Target tirikmi?' testi hal qiluvchi)"
fi

# ---------- 1. Host tirikmi ----------
say "1. Target tirikmi?"
if timeout 5 bash -c "echo > /dev/tcp/$TARGET/80" 2>/dev/null \
   || timeout 5 bash -c "echo > /dev/tcp/$TARGET/22" 2>/dev/null; then
    ok "$TARGET javob beradi"
else
    warn "$TARGET javob bermayapti — mashina o'chgan yoki VPN muammosi"
    warn "Tekshiring: ip -s link show tun0   (RX > 0 bo'lishi kerak)"
fi

# ---------- 2. To'liq port sweep ----------
say "2. To'liq port sweep (65535)"
sudo nmap -p- --min-rate 5000 -Pn -oA "$OUT/full" "$TARGET" || \
     nmap -p- --min-rate 5000 -Pn -oA "$OUT/full" "$TARGET"

PORTS=$(grep -oP '^\d+(?=/tcp\s+open)' "$OUT/full.nmap" 2>/dev/null | paste -sd, - || true)
[ -z "$PORTS" ] && PORTS=$(awk '/^[0-9]+\/tcp +open/{split($1,a,"/");printf "%s%s",(n++?",":""),a[1]}' "$OUT/full.nmap" 2>/dev/null)

if [ -z "$PORTS" ]; then
    warn "Ochiq port topilmadi — $OUT/full.nmap ni ko'ring"
    exit 1
fi
ok "Ochiq portlar: $PORTS"
echo "$PORTS" > "$OUT/ports.txt"

# ---------- 3. Servis + skriptlar ----------
say "3. Versiya va default skriptlar ($PORTS)"
nmap -Pn -p"$PORTS" -sV -sC -oA "$OUT/svc" "$TARGET"

# ---------- 4. OS taxmini ----------
say "4. OS detection"
sudo nmap -Pn -O --osscan-guess "$TARGET" 2>/dev/null | grep -iE 'OS details|Aggressive OS' || true

# ---------- 5. Xulosa ----------
say "XULOSA"
echo "  portlar : $PORTS"
echo "  natijalar: $OUT/full.nmap , $OUT/svc.nmap"
echo
echo "  Keyingi qadam:"
if echo "$PORTS" | grep -qE '(^|,)80(,|$)|(^|,)8080(,|$)|(^|,)8000(,|$)'; then
    echo "    ./02_web_enum.sh $HOST"
fi
echo "    (shell olgach targetda: ./03_privesc.sh)"