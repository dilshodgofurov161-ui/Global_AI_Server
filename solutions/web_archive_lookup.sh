#!/bin/bash
# HTB Academy - Information Gathering (Web Edition), "Web Archives"
# Answers, each verified against the Wayback Machine (web.archive.org):
#   1. Pen testing labs on 08-Aug-2018            -> 74
#   2. Members on 10-Jun-2017                     -> 3054
#   3. facebook.com redirect (March 2002)         -> http://site.aboutface.com/
#   4. paypal.com "beam money to anyone" (Oct 99) -> Palm 0rganizer
#   5. Nov 1998 Google prototype host             -> http://google.stanford.edu/
#   6. www.iana.org last updated (March 2000)     -> 17-December-99
#   7. wikipedia.com articles (09-Feb-2003)       -> 104155
#
# Usage: bash solutions/web_archive_lookup.sh
set -u

wayback() {  # $1 = timestamp, $2 = url
  for _ in 1 2 3; do
    body=$(curl -sL --max-time 45 "https://web.archive.org/web/${1}id_/${2}")
    [ -n "$body" ] && { printf '%s' "$body"; return; }
    sleep 5
  done
}

echo "Q1 labs 08-Aug-2018      : $(wayback 20180808080705 https://www.hackthebox.eu/ | grep -oE 'currently has [0-9]+ vulnerable machines' | grep -oE '[0-9]+')"
echo "Q2 members 10-Jun-2017   : $(wayback 20170610042259 http://hackthebox.eu/ | grep -oE '[0-9]+ members' | head -1)"
echo "Q3 facebook.com Mar-2002 : $(wayback 20020328015153 http://www.facebook.com/ | grep -oiE 'URL=http://[a-z.]+' | head -1 | cut -d= -f2)/"
echo "Q4 paypal.com Oct-1999   : $(wayback 19991001000000 http://www.paypal.com/ | grep -oE 'beam money to anyone with a.{0,90}' | sed 's/&#153;//g;s/<[^>]*>//g' | head -1)"
echo "Q5 google.com Nov-1998   : $(wayback 19981111000000 http://google.com/ | grep -oiE 'http://google\.stanford\.edu' | head -1)/"
echo "Q6 iana.org Mar-2000     : $(wayback 20000301000000 http://www.iana.org/ | grep -oE '[0-9]{1,2}-[A-Za-z]+-[0-9]{2}' | head -1)"
echo "Q7 wikipedia 09-Feb-2003 : $(wayback 20030209000000 http://www.wikipedia.com/ | grep -oE 'working on [0-9]+' | head -1 | grep -oE '[0-9]+')"

