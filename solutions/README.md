# CTF yechimlari (target: `154.57.164.70:37327`)

Ikkala savolning javobi quyidagicha topildi (qayta tekshirilgan va takrorlanuvchi):

| Savol | Sahifa | Javob |
|-------|--------|-------|
| 1 | `/lucky.php` | `HTB{d154bl3d_bu770n5_w0n7_570p_m3}` |
| 2 | `/admin.php` | `3dac93b8cd250aa8c1a36fffc79a17a` |

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

## Avtomatik yechish

```bash
python3 solutions/solve.py                 # standart target bilan
python3 solutions/solve.py http://host:port # boshqa manzil uchun
```

Skript 1-savol uchun bayroq chiqmaguncha POST qiladi, so'ng `/admin.php` dan
cookie'ni olib, uzunligi 31 bo'lguncha dekodlaydi.
