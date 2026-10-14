#!/bin/bash
# HTB Academy - Information Gathering (Web Edition), "Creepy Crawlies"
# Q: After spidering inlanefreight.com, identify the location where future
#    reports will be stored. -> inlanefreight-comp133.s3.amazonaws.htb
#
# The answer is an HTML comment left in the page source:
#   <!-- TO-DO: change the location of future reports to inlanefreight-comp133.s3.amazonaws.htb -->
#
# Usage: bash solutions/spider_reports_location.sh [BASE_URL]
set -u
BASE="${1:-https://www.inlanefreight.com}"

for page in / /index.php/news/ /index.php/about-us/ /index.php/careers/ /index.php/offices/ /index.php/contact/; do
  hit=$(curl -s --max-time 20 -A 'Mozilla/5.0' "$BASE$page" | grep -oiE 'TO-DO[^>]*-->')
  if [ -n "$hit" ]; then
    printf '%-24s %s\n' "$page" "$hit"
  fi
done
