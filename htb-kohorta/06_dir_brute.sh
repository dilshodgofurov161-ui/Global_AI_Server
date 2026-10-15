#!/usr/bin/env bash
# ============================================================
# Directory/file brute — curl fallback (feroxbuster/gobuster bo'lmasa)
#
#   BASE=https://cohort.htb bash 06_dir_brute.sh
#   bash 06_dir_brute.sh https://portal.cohort.htb
#   bash 06_dir_brute.sh https://cohort.htb /usr/share/wordlists/dirb/common.txt
# ============================================================
set -uo pipefail

BASE="${1:-https://cohort.htb}"
WL="${2:-}"
OUT="scans/dir"
mkdir -p "$OUT"

ok(){ printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn(){ printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
hit(){ printf '\033[1;35m[HIT]\033[0m %s\n' "$*"; }

# ---------- wordlist ----------
if [ -z "$WL" ] || [ ! -f "$WL" ]; then
    for c in /usr/share/seclists/Discovery/Web-Content/raft-medium-words.txt \
             /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt \
             /usr/share/seclists/Discovery/Web-Content/common.txt \
             /usr/share/wordlists/dirb/common.txt; do
        [ -f "$c" ] && WL="$c" && break
    done
fi
if [ -z "$WL" ] || [ ! -f "$WL" ]; then
    WL="$OUT/builtin.txt"
    cat > "$WL" <<'EOF'
index
home
login
logout
signin
signup
register
account
profile
user
users
admin
administrator
dashboard
portal
panel
manage
management
console
debug
api
v1
v2
graphql
swagger
docs
doc
documentation
wiki
help
support
test
testing
dev
development
staging
temp
tmp
backup
backups
old
new
upload
uploads
files
file
media
images
img
assets
static
css
js
lib
libs
vendor
src
app
apps
bin
includes
inc
config
settings
setup
install
download
downloads
report
reports
data
export
import
status
health
metrics
logs
log
error
errors
robots.txt
sitemap.xml
security.txt
crossdomain.xml
.htaccess
.env
.git/HEAD
.git/config
.svn/entries
.DS_Store
phpinfo.php
info.php
test.php
wp-config.php
config.php
config.json
database.sql
db.sql
dump.sql
backup.zip
backup.tar.gz
EOF
    ok "built-in wordlist: $WL ($(wc -l < "$WL") ta)"
else
    ok "wordlist: $WL"
fi

# ---------- extensions ----------
EXTS="${EXTS:-php,html,txt,js,zip}"
ok "kengaytmalar: $EXTS"

# ---------- baseline ----------
RND="zzz-nonexistent-$$-$RANDOM.txt"
B=$(curl -sk -m 10 -o /dev/null -w '%{http_code} %{size_download}' "$BASE/$RND")
BCODE=${B%% *}; BSIZE=${B##* }
echo "    baseline -> code=$BCODE size=$BSIZE"

# ---------- parallel probe ----------
: > "$OUT/hits.txt"
N=$(nproc 2>/dev/null || echo 4); [ "$N" -gt 15 ] && N=15
export BASE BCODE BSIZE EXTS
probe() {
    p="$1"
    r=$(curl -sk -m 8 -o /dev/null -w '%{http_code} %{size_download}' "$BASE/$p")
    c=${r%% *}; s=${r##* }
    [ "$c" = "000" ] && return 0
    case "$c" in
      200|204|301|302|307|401|403|405|500)
          if [ "$c" != "$BCODE" ] || [ "$s" != "$BSIZE" ]; then
              printf '%s %s %s\n' "$c" "$s" "$p"
          fi ;;
    esac
}
export -f probe

# variantlar: asl + kengaytmalar
{
  cat "$WL"
  while read -r w; do
      case "$w" in *.*) continue ;; esac
      IFS=',' read -ra E <<< "$EXTS"
      for e in "${E[@]}"; do echo "$w.$e"; done
  done < "$WL"
} | sort -u > "$OUT/wordlist_final.txt"

ok "jami so'rov: $(wc -l < "$OUT/wordlist_final.txt")  (parallel: $N)"
xargs -a "$OUT/wordlist_final.txt" -I{} -P "$N" bash -c 'probe "{}"' 2>/dev/null \
    | sort -u -k3 > "$OUT/hits.txt"

echo
if [ -s "$OUT/hits.txt" ]; then
    ok "Topilgan yo'llar:"
    while read -r c s p; do hit "$c  $s  $BASE/$p"; done < "$OUT/hits.txt"
else
    warn "hech narsa topilmadi"
fi