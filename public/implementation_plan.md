# AIYIM v4.0 — Offline Pentester Education Chatbot

Sizning hozirgi AIYIM chatbot'ingiz **Groq API** ga ulanib ishlaydi. Uni **to'liq offline**, hech qanday API ga ulanmaydigan, o'zining ichki bilimlar bazasi (knowledge base) asosida javob beradigan **pentesting ta'lim chatbot**iga aylantiramiz.

## Asosiy O'zgarishlar

### Qanday ishlaydi (yangi arxitektura):
1. **Katta bilimlar bazasi** — 500+ dan ortiq pentesting mavzulari bo'yicha batafsil ma'lumotlar JavaScript ichiga joylashtiriladi
2. **Aqlli qidiruv tizimi** — Foydalanuvchi savolini tahlil qilib, eng mos javobni topadi (keyword matching + fuzzy search + category routing)
3. **Kontekstli javoblar** — Har bir javob professional formatda, kodlar, buyruqlar va diagrammalar bilan beriladi
4. **API kerak emas** — Hamma narsa brauzerda ishlaydi

### Qamrab olinadigan mavzular (Tools & Techniques):

| Kategoriya | Mavzular |
|-----------|----------|
| 🔍 **Reconnaissance** | Nmap, Masscan, Amass, Subfinder, theHarvester, Shodan, Censys, Google Dorking, WHOIS, DNS enum |
| 🌐 **Web Hacking** | SQL Injection, XSS, SSRF, CSRF, LFI/RFI, XXE, IDOR, Command Injection, File Upload, Deserialization |
| 🔑 **Auth Attacks** | Brute Force, Hydra, Hashcat, John the Ripper, Password Spraying, Credential Stuffing |
| ⬆️ **Privilege Escalation** | Linux PrivEsc (SUID, sudo, cron, kernel), Windows PrivEsc (Token, DLL, Services), LinPEAS, WinPEAS |
| 🏛️ **Active Directory** | Kerberoasting, AS-REP, Pass-the-Hash, Golden Ticket, DCSync, BloodHound, Mimikatz, Rubeus |
| 🔓 **Post-Exploitation** | Persistence, Lateral Movement, Pivoting, Data Exfiltration, C2 Frameworks |
| 🛡️ **Evasion** | WAF Bypass, IDS/IPS Evasion, AMSI Bypass, AV Evasion, Obfuscation |
| 📡 **Network** | Wireshark, tcpdump, ARP Spoofing, MITM, Responder, SMB Relay |
| 📱 **Mobile** | Android/iOS pentesting, APK analysis, Frida, MobSF |
| ☁️ **Cloud** | AWS/Azure/GCP pentesting, SSRF to metadata, S3 misconfiguration |
| 🔧 **Tools** | Metasploit, Burp Suite, SQLMap, Gobuster, ffuf, Nikto, dirsearch |
| 📋 **Methodology** | OWASP Top 10, PTES, OSSTMM, MITRE ATT&CK, Kill Chain |
| 📝 **Reporting** | Bug Bounty report writing, PoC yaratish, CVSS scoring |

## Texnik Rejasi

### O'zgaritiladigan fayllar:

> [!IMPORTANT]
> Barcha o'zgarishlar faqat `public/` papkada bo'ladi. Server-side kod kerak emas.

---

### [MODIFY] [app.js](file:///c:/Users/gulchehra/Desktop/Global_AI_Server/public/app.js)
- Groq API ga `fetch` qiladigan qismlar olib tashlanadi
- Yangi `PentestBrain` class qo'shiladi — ichki bilimlar bazasi + aqlli qidiruv
- `handleSend()` funksiyasi o'zgaradi — API o'rniga `PentestBrain.getResponse()` chaqiriladi
- Streaming effekti saqlanadi (harf-harf chiqish simulyatsiyasi)
- OSINT funksiyalari saqlanadi (DuckDuckGo, DNS — ular to'g'ridan-to'g'ri API emas)

### [NEW] [pentest-brain.js](file:///c:/Users/gulchehra/Desktop/Global_AI_Server/public/pentest-brain.js)
- **500+ mavzuni** qamrab olgan katta bilimlar bazasi
- Har bir mavzu uchun: sarlavha, kalit so'zlar, batafsil javob (markdown formatda, kod misollari bilan)
- Aqlli qidiruv: keyword scoring, synonym matching, category routing
- Streaming simulyatsiya (harf-harf chiqarish uchun generator)

### [MODIFY] [index.html](file:///c:/Users/gulchehra/Desktop/Global_AI_Server/public/index.html)
- AI Engine tanlash qismidan model dropdown olib tashlanadi (API kerak emas)
- Yangi `pentest-brain.js` script qo'shiladi
- Welcome ekranida yangilangan ma'lumotlar

### [MODIFY] [style.css](file:///c:/Users/gulchehra/Desktop/Global_AI_Server/public/style.css)
- Minimal o'zgarishlar — yangi elementlar uchun stil

## Open Questions

> [!IMPORTANT]
> 1. OSINT funksiyalarini (DNS lookup, HTTP headers tekshirish) saqlaymizmi? Ular hozir serverga murojaat qiladi (`/api/osint/...`). Agar server ham kerak bo'lmasa, ularni olib tashlayman.
> 2. Hozirgi chatbot versiyasi v3.0. Yangi versiyani v4.0 deb belgilashmaydi?

## Verification Plan

### Manual Verification
- `index.html` ni brauzerda ochib, turli pentesting savollari berish
- Javoblarning to'g'riligi va formatini tekshirish
- Streaming effektining ishlashini tekshirish
- Offline rejimda (internet o'chiq) ishlashini tekshirish
