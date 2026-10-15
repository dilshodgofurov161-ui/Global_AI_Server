#!/usr/bin/env bash
# ============================================================
# Kohorta (HTB, Easy, Linux) — QADAM 2: web enumeration
#
# Ishlatish:
#   ./02_web_enum.sh kohorta.htb            # http://kohorta.htb
#   ./02_web_enum.sh kohorta.htb 8080       # http://kohorta.htb:8080
# ============================================================
set -uo pipefail

HOST="${1:-cohort.htb}"
PORT="${2:-443}"
# BASE ni env orqali bekor qilish mumkin:  BASE=https://cohort.htb bash 02_web_enum.sh
if [ -n "${BASE:-}" ]; then :; elif [ "$PORT" = "443" ]; then BASE="https://$HOST"
elif [ "$PORT" = "80" ]; then BASE="http://$HOST"; else BASE="http://$HOST:$PORT"; fi
CURL="curl -sk"          # -k: self-signed cert (HTB boxlar uchun)
OUT="scans/web"
mkdir -p "$OUT"

say() { printf '\n\033[1;36m[*] %s\033[0m\n' "$*"; }
ok()  { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn(){ printf '\033[1;33m[!]\033[0m %s\n' "$*"; }

has() { command -v "$1" >/dev/null 2>&1; }

# ---------- Wordlist ----------
WL=""
for c in /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt \
         /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
         /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt \
         /usr/share/wordlists/dirb/common.txt \
         /usr/share/seclists/Discovery/Web-Content/common.txt; do
    [ -f "$c" ] && WL="$c" && break
done
[ -z "$WL" ] && warn "wordlist topilmadi (seclists o'rnating)" || ok "wordlist: $WL"

say "Target: $BASE"

# ---------- 1. Texnologiya ----------
say "1. Texnologiya aniqlash"
has whatweb && whatweb -a 3 "$BASE" | tee "$OUT/whatweb.txt"
$CURL -sSI -m 10 "$BASE" | tee "$OUT/headers.txt"

# ---------- 2. Standart fayllar ----------
say "2. Standart fayllar"
for p in robots.txt sitemap.xml .git/HEAD .env backup.zip backup.tar.gz \
         config.php info.php phpinfo.php server-status; do
    code=$($CURL -sS -m 8 -o /dev/null -w '%{http_code}' "$BASE/$p")
    [ "$code" != "404" ] && [ "$code" != "000" ] && echo "  [$code] $BASE/$p"
done | tee "$OUT/default_files.txt"

# ---------- 3. Dir brute ----------
if [ -n "$WL" ]; then
    say "3. Papka/fayl qidirish"
    if has feroxbuster; then
        feroxbuster -u "$BASE" -w "$WL" -t 30 -d 2 -k --silent -o "$OUT/ferox.txt"
    elif has gobuster; then
        gobuster dir -u "$BASE" -w "$WL" -t 30 -k -x php,html,txt,js,zip \
                 -o "$OUT/gobuster.txt" -q
    elif has ffuf; then
        ffuf -u "$BASE/FUZZ" -w "$WL" -k -mc 200,204,301,302,307,401,403 \
             -t 30 -o "$OUT/ffuf.json" -of json
    else
        warn "feroxbuster/gobuster/ffuf yo'q — o'rnating: sudo apt install feroxbuster"
        warn "  yoki:  bash 06_dir_brute.sh $HOST"
    fi
fi

# ---------- 4. Vhost (wildcard cert bo'lsa MUHIM) ----------
say "4. Vhost enumeration"
warn "05_vhost_enum.sh ishlatiladi (ffuf yoki curl fallback)"
[ -f 05_vhost_enum.sh ] && bash 05_vhost_enum.sh "$HOST" "$HOST" >/dev/null 2>&1
[ -s scans/vhost/hits.txt ] && { ok "topilgan vhost'lar:"; cat scans/vhost/hits.txt | sed 's/^/    /'; }

# ---------- 5. Xulosa ----------
say "XULOSA"
for f in "$OUT"/whatweb.txt "$OUT"/default_files.txt "$OUT"/gobuster.txt "$OUT"/ferox.txt; do
    [ -s "$f" ] && grep -vE '^\s*$' "$f" | head -30 | sed "s|^|  [$(basename "$f")] |"
done
echo
echo "  Qiziqarli narsa topsangiz (login, upload, /admin, .git, backup) —"
echo "  keyingi qadam o'shanga qarab: default creds / LFI / upload / CVE"
echo
echo "  Shell olgach TARGETDA ishga tushiring: ./03_privesc.sh"