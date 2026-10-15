#!/usr/bin/env bash
# ============================================================
# 02_web_chain.sh ni mock serverga qarshi sinash (regressiya testi)
#   ./test_web_chain.sh [port]
# ============================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-18080}"

python3 "$HERE/mock_server.py" "$PORT" >/dev/null 2>"$HERE/mock.log" &
MOCK=$!
trap 'kill "$MOCK" 2>/dev/null || true' EXIT

# mock ko'tarilishini kutish
for _ in $(seq 1 30); do
    if timeout 1 bash -c "exec 3<>/dev/tcp/127.0.0.1/$PORT" 2>/dev/null; then break; fi
    sleep 0.2
done

TMP="$(mktemp -d)"
echo "[test] workdir: $TMP"

BASE="http://127.0.0.1:$PORT" WORK="$TMP/loot" \
    bash "$HERE/02_web_chain.sh" 2>&1 | tee "$TMP/out.txt"

echo
echo "================ ASSERTIONS ================"
fail=0
check() {
    if grep -qF -- "$1" "$TMP/out.txt"; then
        echo "  PASS: $1"
    else
        echo "  FAIL: $1"
        fail=1
    fi
}

check "PUB = MOCK_PUBKEY_a1b2c3d4e5"
check "Added!"
check "NODE_ID = 1"
check "SSRF ISHLADI"
echo "============================================"

if [ "$fail" -eq 0 ]; then
    echo "BARCHA TESTLAR O'TDI ✅"
else
    echo "BA'ZI TESTLAR YIQILDI ❌"
    exit 1
fi
