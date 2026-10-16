#!/usr/bin/env bash
# HTB Enigma - Phase 1b: NFS fallback when `mount -t nfs` returns
#   "mount.nfs: access denied by server while mounting"
#
# That error means mountd refused us. Common causes:
#   * version mismatch   -> force vers=3 (mount.nfs defaults to 4.2)
#   * "illegal port"     -> the export has `secure` (default) and our client
#                           is not coming from a privileged (<1024) port.
#                           WSL2's NFS client hits this a lot.
#   * WSL2 quirks        -> try libnfs below, which talks NFS directly
#                           and does not need the kernel mount path.
#
# Strategy: 1) libnfs (no mount)   2) mount variants
#
# Usage: ./02_nfs_fallback.sh <TARGET_IP> [REMOTE_PATH] [FILE]
set -uo pipefail

IP="${1:?usage: $0 <TARGET_IP> [REMOTE_PATH] [FILE]}"
RPATH="${2:-/srv/nfs/onboarding}"
RFILE="${3:-New_Employee_Access.pdf}"
URL="nfs://${IP}${RPATH}"
OUT="/tmp/${RFILE}"

echo "=============================================="
echo "  NFS fallback  ->  $URL"
echo "=============================================="

# ---------------------------------------------------------------- 1) libnfs
if ! command -v nfs-cat >/dev/null; then
  echo "[*] installing libnfs-utils + poppler-utils (sudo)"
  sudo apt-get update -qq && sudo apt-get install -y libnfs-utils poppler-utils
fi

if command -v nfs-ls >/dev/null; then
  echo
  echo "[*] nfs-ls -D (list exports)"
  nfs-ls -D "nfs://${IP}" || true

  echo
  echo "[*] nfs-ls ${URL}"
  nfs-ls "${URL}" || true

  echo
  echo "[*] nfs-cat -> ${OUT}"
  if nfs-cat "${URL}/${RFILE}" > "${OUT}" 2>/dev/null && [ -s "${OUT}" ]; then
    echo "[+] got ${OUT} ($(stat -c%s "${OUT}") bytes)"
    echo "--- PDF TEXT ---"
    pdftotext "${OUT}" - 2>/dev/null || strings "${OUT}" | head -60
    echo "----------------"
    exit 0
  fi
  echo "[-] libnfs failed, trying mount variants..."
fi

# ------------------------------------------------------------ 2) mount tries
MNT=/mnt/enigma
sudo mkdir -p "$MNT"
sudo umount -f "$MNT" 2>/dev/null; sudo umount -l "$MNT" 2>/dev/null

try_mount() {
  echo
  echo "[*] mount -o $1"
  if sudo mount -t nfs -o "$1" "${IP}:${RPATH}" "$MNT" 2>/dev/null; then
    echo "[+] mounted with: $1"
    ls -la "$MNT"
    PDF=$(find "$MNT" -iname '*.pdf' | head -1)
    [ -n "$PDF" ] && { echo "--- PDF TEXT ---"; pdftotext "$PDF" - 2>/dev/null || strings "$PDF" | head -60; }
    exit 0
  fi
  echo "[-] failed"
}

try_mount "vers=3,resvport,nolock"
try_mount "vers=3,resvport,nolock,proto=tcp,mountproto=tcp,port=2049"
try_mount "vers=3,resvport,nolock,proto=udp"
try_mount "vers=4.2,resvport"
try_mount "vers=4,resvport"

echo
echo "!! all attempts failed."
echo "   The server is likely rejecting our source port (privileged-port / WSL2 issue)."
echo "   Workarounds:"
echo "     * run the same commands from a real Kali VM (VirtualBox/VMware), not WSL"
echo "     * verbose debug:  sudo mount -t nfs -o vers=3,resvport ${IP}:${RPATH} ${MNT} -vvvv"
exit 1
