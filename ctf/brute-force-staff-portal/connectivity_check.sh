#!/usr/bin/env bash
# connectivity_check.sh - diagnose why hydra says "cannot connect" to the lab.
#
# Run this FIRST, before hydra. It answers the one question that matters:
#   "Do I actually have a route to the target?"
#
# Usage:  ./connectivity_check.sh            (defaults to 10.15.0.238:9004)
#         TARGET=10.15.1.54 PORT=9004 ./connectivity_check.sh
set -u

TARGET="${TARGET:-10.15.1.54}"
PORT="${PORT:-9004}"

echo "== 1. VPN tunnel interface (tun0/tun1) =="
if ip -o addr show 2>/dev/null | grep -q 'tun'; then
  ip -o addr show | grep 'tun'
  echo "   [+] tunnel up"
else
  echo "   [!] NO tun interface found -> HTB VPN is NOT connected."
  echo "       Fix: run the .ovpn inside WSL:  sudo openvpn --config htb.ovpn"
  echo "       wait for 'Initialization Sequence Completed', then re-run."
fi
echo

echo "== 2. Route to target =="
ip route get "$TARGET" 2>&1 | head -3
echo

echo "== 3. Ping the target =="
if ping -c 2 -W 2 "$TARGET" >/dev/null 2>&1; then
  echo "   [+] $TARGET responds to ping"
else
  echo "   [!] no ping reply (ICMP may be filtered, this is NOT decisive on its own)"
fi
echo

echo "== 4. TCP connect to port $PORT (decisive) =="
if command -v nc >/dev/null 2>&1; then
  if nc -z -w 3 "$TARGET" "$PORT"; then
    echo "   [+] TCP $TARGET:$PORT OPEN -> target reachable, hydra should work"
  else
    echo "   [!] TCP $TARGET:$PORT UNREACHABLE -> hydra 'cannot connect' is expected"
  fi
else
  # bash-only fallback (/dev/tcp)
  if timeout 4 bash -c "exec 3<>/dev/tcp/$TARGET/$PORT" 2>/dev/null; then
    echo "   [+] TCP $TARGET:$PORT open"
  else
    echo "   [!] TCP $TARGET:$PORT unreachable"
  fi
fi
echo

echo "== 5. HTTP banner (should be the login page, not empty) =="
curl -s -m 8 -i "http://${TARGET}:${PORT}/" | head -15
echo
echo "[i] If step 4 says UNREACHABLE: connect/restart the VPN and re-run."
echo "[i] Also try the other lab IP, e.g. TARGET=10.15.1.54 ./connectivity_check.sh"
