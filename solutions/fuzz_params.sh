#!/bin/bash
# HTB Academy "Web Fuzzing" - GET/POST parameter fuzzing
# Target: http://154.57.164.71:40811
#
# get.php?x=FUZZ  and  post.php (body: y=FUZZ) answer "Incorrect parameter value"
# for wrong values. Fuzzing the values with SecLists' common.txt finds:
#   x=OA_HTML -> HTB{g3t_fuzz1ng_succ3ss}
#   y=SUNWmc  -> HTB{p0st_fuzz1ng_succ3ss}
#
# Usage: bash solutions/fuzz_params.sh [BASE]
set -u
BASE="${1:-http://154.57.164.71:40811}"

echo "GET  x=OA_HTML : $(curl -s --max-time 15 -G --data-urlencode 'x=OA_HTML' "$BASE/get.php")"
echo "POST y=SUNWmc  : $(curl -s --max-time 15 -X POST --data-urlencode 'y=SUNWmc' "$BASE/post.php")"
