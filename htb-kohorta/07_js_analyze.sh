#!/usr/bin/env bash
# ============================================================
# JS bundle tahlili — SPA uchun (Kohorta/cohort.htb)
#   JS'da API endpoint, route, kalit va parameterlarni topadi
#
#   bash 07_js_analyze.sh https://cohort.htb
# ============================================================
set -uo pipefail
BASE="${1:-https://cohort.htb}"
OUT="loot/js"
mkdir -p "$OUT"

ok(){ printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn(){ printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
sec(){ printf '\n\033[1;36m=== %s ===\033[0m\n' "$*"; }

say() { printf '\n\033[1;36m[*] %s\033[0m\n' "$*"; }

say "1. HTML dan JS/CSS havolalarni yig'ish"
curl -sk -m 15 "$BASE/" -o "$OUT/index.html"
if [ ! -s "$OUT/index.html" ]; then warn "index.html olinmadi"; exit 1; fi
ok "index.html: $(wc -c < "$OUT/index.html") bayt"

mapfile -t JS < <(grep -oP '(?<=src=")[^"]+\.js(?=")|(?<=href=")[^"]+\.js(?=")' "$OUT/index.html" \
                  | sed 's|^\s*||' | sort -u)
[ ${#JS[@]} -eq 0 ] && mapfile -t JS < <(grep -oP '[\w./-]+\.js' "$OUT/index.html" | sort -u)

for j in "/assets/app.js" "${JS[@]:-}"; do
    [ -z "$j" ] && continue
    case "$j" in http*) url="$j" ;; /*) url="$BASE$j" ;; *) url="$BASE/$j" ;; esac
    f="$OUT/$(echo "$j" | tr '/' '_')"
    curl -sk -m 20 "$url" -o "$f"
    [ -s "$f" ] && ok "$(printf '%6d' "$(wc -c < "$f")") bayt  $url" || warn "olinmadi: $url"
done

sec "2. API / route endpoint'lari"
cat "$OUT"/*.js 2>/dev/null \
  | grep -oP '["'"'"'`](/[a-zA-Z0-9_./{}\-]{2,80})["'"'"'`]' \
  | tr -d '"'"'"'`' | sort -u > "$OUT/endpoints.txt"
grep -vE '^/(assets|static|css|js|img|images|fonts|favicon)' "$OUT/endpoints.txt" \
  | head -60 | sed 's/^/  /'
echo "  ... jami: $(wc -l < "$OUT/endpoints.txt") ta -> $OUT/endpoints.txt"

sec "3. fetch/axios/ajax chaqiruvlari"
cat "$OUT"/*.js 2>/dev/null \
  | grep -oP '(fetch|axios\.\w+|\.open|ajax)\s*\(\s*["'"'"'`][^"'"'"'`]{2,90}["'"'"'`]' \
  | sort -u | head -40 | sed 's/^/  /'

sec "4. HTTP metod + headerlar"
cat "$OUT"/*.js 2>/dev/null \
  | grep -oiP 'method\s*:\s*["'"'"'](GET|POST|PUT|PATCH|DELETE)["'"'"']|["'"'"'](X-[\w-]+|Authorization|Bearer|Cookie)["'"'"']' \
  | sort -u | head -30 | sed 's/^/  /'

sec "5. Parameter nomlari (SQLi/IDOR uchun)"
cat "$OUT"/*.js 2>/dev/null \
  | grep -oP '\b(id|uid|user|user_id|userId|account|account_id|report|report_id|board|board_id|team|org|project|file|filename|path|page|template|lang|debug)\b' \
  | sort | uniq -c | sort -rn | head -30 | sed 's/^/  /'

sec "6. Shubhali qiymatlar (kalit/token/parol)"
cat "$OUT"/*.js 2>/dev/null \
  | grep -oiP '(api[_-]?key|secret|token|password|passwd|pwd|auth)["'"'"'\s:=]{1,4}["'"'"'][^"'"'"']{4,80}["'"'"']' \
  | sort -u | head -30 | sed 's/^/  /'

sec "7. Email / URL / versiya"
cat "$OUT"/*.js 2>/dev/null \
  | grep -oiP '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}' | sort -u | head -20 | sed 's/^/  /'
cat "$OUT"/*.js 2>/dev/null \
  | grep -oP 'https?://[a-zA-Z0-9._/\-]+' | sort -u | head -20 | sed 's/^/  /'

sec "8. Lokal ko'rish"
echo "  sourcemap bo'lsa asl kod chiqadi:"
echo "    curl -sk $BASE/assets/app.js -o loot/app.js"
echo "    curl -sk $BASE/assets/app.js.map -o loot/app.js.map"
echo "  Endpoint'larni tekshirish:"
echo "    while read -r p; do code=\$(curl -sk -o /dev/null -w '%{http_code}' $BASE\$p); echo \"\$code \$p\"; done < $OUT/endpoints.txt | sort -rn | head -40"