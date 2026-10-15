#!/usr/bin/env bash
# ============================================================
# VPN + target ulanish tekshiruvi (READ-ONLY, hech narsani o'zgartirmaydi)
#
#   ./04_vpn_check.sh 10.129.244.174
#   ./04_vpn_check.sh 10.129.244.174 --fix     # WSL openvpn'ni o'chiradi
# ============================================================
set -uo pipefail

TARGET="${1:-10.129.244.174}"
FIX="${2:-}"

sec() { printf '\n\033[1;36m=== %s ===\033[0m\n' "$*"; }
ok()  { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
bad() { printf '\033[1;31m[-]\033[0m %s\n' "$*"; }
warn(){ printf '\033[1;33m[!]\033[0m %s\n' "$*"; }

WIN() { /mnt/c/Windows/System32/$1.exe 2>/dev/null; }
HASWIN=0; [ -x /mnt/c/Windows/System32/ipconfig.exe ] && HASWIN=1

# ---------- 1. Windows VPN ----------
sec "1. Windows VPN holati"
WINIP=""
if [ "$HASWIN" = 1 ]; then
    WINOUT=$(WIN ipconfig | tr -d '\r')
    echo "$WINOUT" | grep -aiE "adapter|IPv4|OpenVPN|TAP" | grep -aiE "adapter|10\.10\.|10\.129\." | head -20
    WINIP=$(echo "$WINOUT" | grep -oP '10\.10\.\d+\.\d+' | head -1 || true)
    [ -n "$WINIP" ] && ok "Windows tunnel IP = $WINIP" || bad "Windows'da 10.10.x.x topilmadi — VPN ulanmagan"
else
    warn "/mnt/c Windows mount yo'q — Windows tekshiruvi o'tkazildi"
fi

# ---------- 2. WSL openvpn jarayonlari ----------
sec "2. openvpn jarayonlari"
WSLVPN=$(pgrep -a openvpn 2>/dev/null || true)
if [ -n "$WSLVPN" ]; then
    warn "WSL'da openvpn ISHLAYAPTI:"
    echo "$WSLVPN" | sed 's/^/    /'
    if [ -n "$WINIP" ]; then
        bad "KONFLIKT: Windows ham, WSL ham ulangan -> WSL openvpn'ni O'CHIRING"
        if [ "$FIX" = "--fix" ]; then
            sudo pkill -f openvpn; sleep 2
            ok "WSL openvpn o'chirildi"
            WSLVPN=""
        else
            echo "    -> ./04_vpn_check.sh $TARGET --fix  (yoki: sudo pkill -f openvpn)"
        fi
    else
        ok "WSL openvpn ishlayapti (Windows VPN yo'q) — bu normal"
    fi
else
    ok "WSL'da openvpn yo'q"
fi

# ---------- 3. WSL tun0 ----------
sec "3. WSL tun0 interfeysi"
if ip link show tun0 >/dev/null 2>&1; then
    ip -s link show tun0 | head -8
    RX=$(ip -s link show tun0 | awk '/RX:/{getline; print $2}')
    ok "tun0 bor, RX=$RX"
else
    ok "WSL'da tun0 yo'q (Windows VPN ishlatilsa normal)"
fi

# ---------- 4. Marshrut ----------
sec "4. $TARGET ga marshrut"
ip route get "$TARGET" 2>/dev/null || true

# ---------- 5. TCP test ----------
sec "5. TCP ulanish testi ($TARGET)"
OPEN=""
for p in 22 80 8080 8000 443 21 445; do
    if timeout 4 bash -c "echo > /dev/tcp/$TARGET/$p" 2>/dev/null; then
        ok "port $p OCHIQ"; OPEN="$OPEN $p"
    fi
done
[ -z "$OPEN" ] && bad "hech qanday port javob bermadi"

# ---------- 6. Xulosa ----------
sec "XULOSA"
if [ -n "$OPEN" ]; then
    ok "TARGET YETIB BORILADI — portlar:$OPEN"
    echo
    echo "  Keyingi qadam:"
    echo "    sudo ./01_recon.sh $TARGET"
    echo "    ./02_web_enum.sh kohorta.htb"
    exit 0
fi

bad "Target yetib borilmaydi"
echo
if [ -n "$WINIP" ] && [ -z "$WSLVPN" ]; then
    echo "  Windows VPN ISHLAYAPTI ($WINIP), lekin WSL uni ko'rmayapti."
    echo "  Variantlar (tartib bilan):"
    echo "    A) WSL2 mirrored rejim (Windows 11 22H2+):"
    echo "         printf '[wsl2]\\nnetworkingMode=mirrored\\n' > /mnt/c/Users/\$USER/.wslconfig"
    echo "         wsl.exe --shutdown   # keyin WSL'ni qayta oching"
    echo "    B) Pwnbox ishlatish (brauzerda, eng ishonchli)"
    echo "    C) Telefon hotspot + WSL'da openvpn"
elif [ -n "$WSLVPN" ]; then
    echo "  WSL openvpn ishlayapti lekin trafik o'tmayapti (RX=0 ehtimoli)."
    echo "  Tekshiring: ip -s link show tun0   -> RX hisoblagichi"
    echo "  Yechim: telefon hotspot yoki Pwnbox (ISP DPI bloklayapti)"
elif [ "$HASWIN" = 1 ]; then
    echo "  Windows VPN ulanmagan. Windows'da OpenVPN Connect'ni ulang,"
    echo "  yoki WSL ichida: sudo openvpn --config ~/vpn/machines_us-3.ovpn"
else
    echo "  VPN umuman yo'q. Pwnbox yoki WSL'da openvpn ishlatish kerak."
fi
exit 1