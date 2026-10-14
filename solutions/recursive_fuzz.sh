#!/bin/bash
# HTB Academy "Web Fuzzing" - recursive fuzzing
# Target: http://154.57.164.76:37377/recursive_fuzz/
#
# Recursively fuzzing (ffuf -recursion / raft-small-directories) reveals:
#   /recursive_fuzz/level1/
#   /recursive_fuzz/level1/level2/
#   /recursive_fuzz/level1/level2/level3/
#   /recursive_fuzz/level1/level2/level3/threatcon_level2/   <-- flag
#
# Usage: bash solutions/recursive_fuzz.sh [BASE]
set -u
BASE="${1:-http://154.57.164.76:37377/recursive_fuzz}"

fetch() {  # retry a couple of times, the lab webserver occasionally resets connections
  local url="$1" body=""
  for _ in 1 2 3 4; do
    body=$(curl -s --max-time 15 "$url")
    [ -n "$body" ] && break
    sleep 2
  done
  printf '%s' "$body"
}

for path in / /level1/ /level1/level2/ /level1/level2/level3/ /level1/level2/level3/threatcon_level2/; do
  body=$(fetch "$BASE$path")
  printf '%-46s %s\n' "$path" "$(printf '%s' "$body" | grep -oE '<title>[^<]*</title>')"
  printf '%s' "$body" | grep -oE 'HTB\{[^}]*\}'
done
