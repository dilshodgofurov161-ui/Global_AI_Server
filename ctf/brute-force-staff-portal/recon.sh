#!/usr/bin/env bash
# recon.sh - quick recon of the Staff Portal login form.
# Run from a machine on the lab VPN. Discovers the form action, field names
# and the failure string needed by hydra / brute.py.
set -u
TARGET="${TARGET:-10.15.0.238}"
PORT="${PORT:-9004}"
BASE="http://${TARGET}:${PORT}"

echo "=== GET /  (login page) ==="
curl -s -i -m 10 "${BASE}/" | head -40
echo
echo "=== POST /login  (one wrong attempt) ==="
curl -s -i -m 10 -X POST "${BASE}/login" \
     -d 'username=admin&password=this_is_wrong' | head -40
echo
echo "=== POST /  (some portals post to root) ==="
curl -s -i -m 10 -X POST "${BASE}/" \
     -d 'username=admin&password=this_is_wrong' | head -40
echo
echo "[i] From the output above, note:  form action path, input names, and the"
echo "    exact text shown on a WRONG password (that is hydra's F= string)."
