# CTF yechimlari (target: `154.57.164.70:37327`)

Ikkala savolning javobi quyidagicha topildi (qayta tekshirilgan va takrorlanuvchi):

| Savol | Sahifa | Javob |
|-------|--------|-------|
| 1 | `/lucky.php` | `HTB{d154bl3d_bu770n5_w0n7_570p_m3}` |
| 2 | `/admin.php` | `3dac93b8cd250aa8c1a36fffc79a17a` |
| 3 | `/admin.php` (cookie fuzzing) | oxirgi belgi: `d` → flag: `HTB{burp_1n7rud3r_n1nj4!}` |
| 4 | Metasploit moduli | `CFIDE` |

## 1-savol — `/lucky.php`

Sahifadagi tugma `disabled` bo'lgani uchun brauzer uni bosib formani yubormaydi.
`disabled` atributini olib tashlab (yoki to'g'ridan-to'g'ri `POST`) formani yuborish
yetarli:

```bash
curl -s -X POST -d 'getflag=true' http://154.57.164.70:37327/lucky.php
```

Server har safar tasodifiy javob beradi ("Click for a chance to win a flag!"),
ya'ni bayroq faqat ba'zi urinishlarda qaytadi. Takrorlab yuborganda javob oxirida
quyidagi qator chiqadi:

```html
<p style="text-align:center">HTB{d154bl3d_bu770n5_w0n7_570p_m3}</p>
```

## 2-savol — `/admin.php`

`/admin.php` har doim bir xil `cookie` qiymatini beradi (Set-Cookie sarlavhasi):

```
4d325268597a6b7a596a686a5a4449314d4746684f474d7859544d325a6d5a6d597a63355954453359513d3d
```

Qiymat ketma-ket bir necha marta kodlangan. Har bir qadamda kodlash turini aniqlab
ochib boramiz:

1. **hex** -> `M2RhYzkzYjhjZDI1MGFhOGMxYTM2ZmZmYzc5YTE3YQ==`
2. **base64** -> `3dac93b8cd250aa8c1a36fffc79a17a`  (31 belgi) ✅

Ya'ni javob: **`3dac93b8cd250aa8c1a36fffc79a17a`**.

## 3-savol — `/admin.php` cookie'ning oxirgi belgisi (fuzzing)

2-savolda olingan `3dac93b8cd250aa8c1a36fffc79a17a` qiymati **31 belgi** — bu md5
xeshning oxirgi belgisi tushib qolgan holati. Yo'qolgan belgini topish uchun
SecLists'dagi `Fuzzing/alphanum-case.txt` ro'yxatidan (62 qator: `0-9`, `a-z`, `A-Z`)
foydalanamiz: har bir nomzodni md5 ga qo'shib, 2-savoldagi kodlash zanjiri bilan
qayta kodlaymiz (**base64 → hex**) va `cookie` sifatida yuboramiz:

```python
payload   = "3dac93b8cd250aa8c1a36fffc79a17a" + candidate_char
cookie    = hex(base64(payload))
# GET /admin.php  -> Cookie: cookie=<cookie>
```

Faqat **`d`** harfi bilan yuborilgan so'rov qabul qilinadi (javob 1901 bayt emas,
947 bayt bo'ladi) va sahifada bayroq chiqadi:

```html
HTB{burp_1n7rud3r_n1nj4!}
```

To'liq md5: `3dac93b8cd250aa8c1a36fffc79a17ad`

## 4-savol — Metasploit `coldfusion_locale_traversal`

Modul manbasida so'rov manzillari quyidagicha:

```ruby
urls = [
  "/CFIDE/administrator/enter.cfm", "/CFIDE/wizards/common/_logintowizard.cfm",
  "/CFIDE/administrator/archives/index.cfm", "/CFIDE/administrator/entman/index.cfm",
  "/CFIDE/administrator/logging/settings.cfm"
]
```

Ya'ni `/XXXXX/administrator/` dagi katalog — **`CFIDE`**.
(Manba: `modules/auxiliary/scanner/http/coldfusion_locale_traversal.rb`, CVE-2010-2861.)

## Avtomatik yechish

```bash
python3 solutions/solve.py                 # standart target bilan
python3 solutions/solve.py http://host:port # boshqa manzil uchun
```

Skript 1-savol uchun bayroq chiqmaguncha POST qiladi, so'ng `/admin.php` dan
cookie'ni olib, uzunligi 31 bo'lguncha dekodlaydi.
