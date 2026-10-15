#!/usr/bin/env bash
# ============================================================
# cohort.htb (HTB Kohorta) — vhost / subdomain enumeration
#
#   bash 05_vhost_enum.sh                        # cohort.htb, avtomatik
#   bash 05_vhost_enum.sh cohort.htb 10.129.244.174 https
#
# Wildcard cert (SAN: *.cohort.htb) -> subdomain'lar bor.
# ============================================================
set -uo pipefail

DOMAIN="${1:-cohort.htb}"
TARGET="${2:-10.129.244.174}"
SCHEME="${3:-https}"
OUT="scans/vhost"
mkdir -p "$OUT" loot

ok()  { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn(){ printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
hit() { printf '\033[1;35m[HIT]\033[0m %s\n' "$*"; }

# ---------- wordlist ----------
WL=""
for c in /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt \
         /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
         /usr/share/seclists/Discovery/DNS/namelist.txt \
         /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt; do
    [ -f "$c" ] && WL="$c" && break
done
if [ -z "$WL" ]; then
    WL="$OUT/builtin.txt"
    cat > "$WL" <<'EOF'
www
portal
app
apps
admin
administrator
dashboard
intranet
internal
dev
development
staging
stage
test
testing
qa
uat
prod
production
api
api-dev
api-staging
gateway
auth
sso
login
mail
webmail
smtp
vpn
ftp
files
file
share
uploads
cdn
static
assets
img
images
media
docs
doc
documentation
wiki
confluence
jira
git
gitlab
jenkins
ci
build
monitor
monitoring
grafana
kibana
prometheus
nagios
status
help
support
helpdesk
service
services
hr
people
staff
employee
employees
careers
jobs
finance
billing
payments
pay
crm
erp
sales
marketing
blog
news
shop
store
analytics
data
report
reports
bi
etl
db
database
mysql
postgres
redis
mongo
cache
proxy
lb
backend
frontend
web
web1
web2
srv
server
host
node
node1
node2
cluster
k8s
docker
registry
repo
backup
backups
old
new
v1
v2
beta
alpha
demo
sandbox
lab
labs
research
security
secure
ssl
cert
key
keys
config
secrets
vault
kohorta
cohort
EOF
    ok "built-in wordlist: $WL ($(wc -l < "$WL") ta)"
else
    ok "wordlist: $WL"
fi

# ---------- baseline ----------
RND="zzz-nonexistent-$$-$((RANDOM))"
BASE=$(curl -sk -m 10 -o /dev/null -w '%{http_code} %{size_download}' \
        -H "Host: $RND.$DOMAIN" "$SCHEME://$TARGET/")
BCODE=${BASE%% *}; BSIZE=${BASE##* }
echo "    baseline (Host: $RND.$DOMAIN) -> code=$BCODE size=$BSIZE"
echo "$BCODE $BSIZE" > "$OUT/baseline.txt"

# ---------- enumeration ----------
: > "$OUT/hits.txt"
echo "    $SCHEME://$TARGET/  (Host: FUZZ.$DOMAIN)"

if command -v ffuf >/dev/null 2>&1; then
    ok "ffuf ishlatilmoqda"
    ffuf -u "$SCHEME://$TARGET/" -H "Host: FUZZ.$DOMAIN" -w "$WL" \
         -k -t "$(nproc 2>/dev/null | awk '{print ($1>30)?30:$1}' || echo 20)" \
         -mc all -ac -s -o "$OUT/ffuf.json" -of json 2>/dev/null
    [ -f "$OUT/ffuf.json" ] && jq -r '.results[]? | "\(.status) \(.length) \(.input.FUZZ)"' \
        "$OUT/ffuf.json" 2>/dev/null | sort -u > "$OUT/hits.txt"
else
    warn "ffuf yo'q — curl rejimi (sekinroq)"
    N=$(nproc 2>/dev/null || echo 4); [ "$N" -gt 15 ] && N=15
    export DOMAIN TARGET SCHEME BCODE BSIZE OUT
    probe_one() {
        w="$1"
        r=$(curl -sk -m 8 -o /dev/null -w '%{http_code} %{size_download}' \
              -H "Host: $w.$DOMAIN" "$SCHEME://$TARGET/")
        c=${r%% *}; s=${r##* }
        [ "$c" = "000" ] && return 0
        if [ "$c" != "$BCODE" ] || [ "$s" != "$BSIZE" ]; then
            printf '%s %s %s\n' "$c" "$s" "$w"
        fi
    }
    export -f probe_one
    xargs -a "$WL" -I{} -P "$N" bash -c 'probe_one "{}"' 2>/dev/null \
        | sort -u -k3 > "$OUT/hits.txt"
fi

# ---------- natijalar ----------
echo
if [ -s "$OUT/hits.txt" ]; then
    ok "Topilgan vhost'lar:"
    while read -r code size name; do
        [ -z "${name:-}" ] && continue
        hit "$code  $size  https://$name.$DOMAIN"
    done < "$OUT/hits.txt"
else
    warn "vhost topilmadi — wordlist'ni kattalashtiring yoki DNS'da qidiring"
fi