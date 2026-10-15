#!/usr/bin/env bash
# 07_js_analyze.sh ni mock SPA ustida sinash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T="$(mktemp -d)"; PORT=18110

mkdir -p "$T/assets"
cat > "$T/index.html" <<'EOF'
<!doctype html><html><head><title>Cohort Analytics</title>
<link rel="stylesheet" href="/assets/styles.css"></head>
<body><div id="app"></div><script src="/assets/app.js" defer></script></body></html>
EOF

cat > "$T/assets/app.js" <<'EOF'
const API="/api/v1";
async function loadReport(id){ return fetch(`/api/v1/reports/${id}?format=json`) }
fetch("/api/v1/boards",{method:"POST",headers:{"Content-Type":"application/json","X-Requested-With":"fetch","Authorization":"Bearer test"}})
fetch("/api/v1/employees")
fetch("/api/v1/upload",{method:"POST"})
fetch("/auth/login",{method:"POST"})
fetch("/debug/status")
fetch("/api/v1/export?template=report&lang=en")
const API_KEY="ak_live_9f3c2b7a1d4e";
const secret="s3cr3t-cohort-2026";
const adminEmail="admin@cohort.htb";
const docs="https://docs.cohort.htb/help";
function go(){ location.href="/admin/panel" }
async function q(){ return fetch(`/api/v1/users/${userId}/reports/${report_id}`) }
EOF
cp "$T/assets/app.js" "$T/assets/app.js.map" 2>/dev/null || true

( cd "$T" && timeout 60 python3 -m http.server "$PORT" >/dev/null 2>&1 & )
sleep 1.5

cd "$T"
timeout 60 bash "$HERE/07_js_analyze.sh" "http://127.0.0.1:$PORT" 2>&1

echo
echo "================ ASSERTIONS ================"
fail=0
chk(){ if grep -qF -- "$1" "$T/loot/js/endpoints.txt" "$T/loot/js"/*.js 2>/dev/null; then echo "  PASS: $1"; else echo "  FAIL: $1"; fail=1; fi; }
chk "/api/v1/boards"
chk "/api/v1/employees"
chk "/auth/login"
chk "/debug/status"
chk "/admin/panel"
chk "ak_live_9f3c2b7a1d4e"
chk "admin@cohort.htb"
echo "============================================"
[ "$fail" -eq 0 ] && echo "BARCHA TESTLAR O'TDI ✅" || { echo "YIQILDI ❌"; exit 1; }