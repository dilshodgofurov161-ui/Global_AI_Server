#!/usr/bin/env bash
# HTB Layover - Phase 1: RDP into the jumpbox and enumerate it.
# Usage: ./01_rdp.sh <TARGET_IP> [USER] [PASSWORD]
set -uo pipefail

IP="${1:?usage: $0 <TARGET_IP> [USER] [PASSWORD]}"
USER="${2:-contractor}"
PASS="${3:-Contractor2026!}"

echo "=============================================="
echo "  Layover - RDP to jumpbox  $IP"
echo "=============================================="

# --- pick a freerdp binary ---
FRDP=""
for c in xfreerdp xfreerdp3; do command -v "$c" >/dev/null && FRDP="$c" && break; done
if [ -z "$FRDP" ]; then
  echo "[*] installing a FreeRDP client..."
  sudo apt-get update -qq && sudo apt-get install -y freerdp2-x11 || {
    echo "!! install FreeRDP manually (freerdp2-x11 or freerdp3-x11)"; exit 1; }
  FRDP=$(command -v xfreerdp || command -v xfreerdp3)
fi
echo "[*] using $FRDP"

cat <<EOF

[*] Launching RDP session. On the desktop run:

      whoami; id
      sudo -l
      ip a; iwconfig; nmcli device
      ss -tlnp

    Expected on airside-ws01:
      contractor
      uid=1001(contractor) gid=1001(contractor)
        groups=...,27(sudo),111(netdev),121(wireshark)
      User contractor may run the following commands on airside-ws01:
          (ALL : ALL) ALL

    WiFi interfaces wlan2 / wlan3 (mac80211_hwsim) - they are the pivot.
    The target itself has NO web server; everything runs on 10.13.37.0/24.

EOF

# --- quick reachability sanity check from here ---
echo "[*] port check:"
for p in 22 3389; do
  (echo > "/dev/tcp/${IP}/${p}") >/dev/null 2>&1 \
    && echo "    $p open" || echo "    $p closed/filtered"
done

echo
read -r -p "[?] Start the RDP session now? [y/N] " ans
if [ "${ans,,}" = "y" ]; then
  exec "$FRDP" /v:"$IP" /u:"$USER" /p:"$PASS" /cert:ignore /dynamic-resolution
fi
