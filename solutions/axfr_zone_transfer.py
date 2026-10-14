#!/usr/bin/env python3
"""
DNS zone transfer (HTB Academy "Information Gathering - Web Edition")

Questions:
  1. After performing a zone transfer for inlanefreight.htb on the target system,
     how many DNS records are retrieved?                     -> 22
  2. IP address for ftp.admin.inlanefreight.htb              -> 10.10.34.2
  3. Largest IP allocated within the 10.10.200 range         -> 10.10.200.14

Two modes:
  * live   : python3 solutions/axfr_zone_transfer.py 10.129.235.84 inlanefreight.htb
             (AXFR over TCP/53; needs network access to the lab host)
  * offline: python3 solutions/axfr_zone_transfer.py --file <dig-axfr-output.txt>
             (parses a saved transfer; used to verify the counting logic against
              solutions/fixtures/inlanefreight.htb.zone)
"""
import ipaddress
import random
import socket
import struct
import sys

QTYPE = {"A": 1, "NS": 2, "CNAME": 5, "SOA": 6, "PTR": 12, "MX": 15, "TXT": 16, "AXFR": 252}
TYPE_NAMES = {v: k for k, v in QTYPE.items()}


# ----------------------------------------------------------------- live AXFR
def build_query(name, qtype=252):
    tid = random.randint(0, 0xFFFF)
    header = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    qname = b"".join(bytes([len(p)]) + p.encode() for p in name.split(".")) + b"\x00"
    return header + qname + struct.pack("!HH", qtype, 1)


def parse_name(data, off):
    labels, jumped, end = [], False, off
    while True:
        length = data[off]
        if length == 0:
            off += 1
            if not jumped:
                end = off
            break
        if length & 0xC0 == 0xC0:
            ptr = struct.unpack("!H", data[off:off + 2])[0] & 0x3FFF
            if not jumped:
                end = off + 2
                jumped = True
            off = ptr
            continue
        labels.append(data[off + 1:off + 1 + length].decode("utf-8", "replace"))
        off += 1 + length
        if not jumped:
            end = off
    return ".".join(labels), end


def parse_message(data):
    """Return (records, soa_count) for a DNS message; records are (name, type, value)."""
    qdcount, ancount = struct.unpack("!HH", data[4:8])
    off = 12
    for _ in range(qdcount):
        _, off = parse_name(data, off)
        off += 4
    records, soa = [], 0
    for _ in range(ancount):
        name, off = parse_name(data, off)
        rtype, _rclass, _ttl, rdlength = struct.unpack("!HHIH", data[off:off + 10])
        off += 10
        rdata = data[off:off + rdlength]
        off += rdlength
        if rtype == 1:
            value = socket.inet_ntoa(rdata)
        elif rtype in (2, 5, 12):
            value = parse_name(data, off - rdlength)[0]
        elif rtype == 15:
            pref = struct.unpack("!H", rdata[:2])[0]
            value = "%d %s" % (pref, parse_name(data, off - rdlength + 2)[0])
        elif rtype == 6:
            soa += 1
            value = "SOA"
        else:
            value = rdata.hex()
        records.append((name, TYPE_NAMES.get(rtype, str(rtype)), value))
    return records, soa


def axfr(server, zone, port=53, timeout=20):
    sock = socket.create_connection((server, port), timeout=timeout)
    pkt = build_query(zone)
    sock.sendall(struct.pack("!H", len(pkt)) + pkt)
    records, soa_seen, messages = [], 0, 0
    while True:
        header = sock.recv(2)
        if len(header) < 2:
            break
        length = struct.unpack("!H", header)[0]
        data = b""
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                break
            data += chunk
        messages += 1
        recs, soa = parse_message(data)
        records.extend(recs)
        soa_seen += soa
        if soa_seen >= 2:
            break
    sock.close()
    return records, messages


# -------------------------------------------------------------- offline parse
def parse_text(text):
    """Parse the output of `dig axfr` (one resource record per line)."""
    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        parts = line.split()
        if len(parts) < 4 or parts[2].upper() != "IN":
            continue
        name, rtype, value = parts[0], parts[3].upper(), " ".join(parts[4:])
        records.append((name, rtype, value))
    return records


# ------------------------------------------------------------------ analysis
def analyse(records):
    total = len(records)
    ftp = [v for n, t, v in records if n.lower().startswith("ftp.admin.") and t == "A"]
    ips = []
    for _n, t, v in records:
        if t != "A":
            continue
        try:
            ips.append(ipaddress.ip_address(v))
        except ValueError:
            pass
    in_range = [ip for ip in ips if ip in ipaddress.ip_network("10.10.200.0/24")]
    print("Q1  total records           : %d" % total)
    print("Q2  ftp.admin.<zone>        : %s" % (ftp[0] if ftp else "n/a"))
    print("Q3  largest 10.10.200.x     : %s"
          % (max(in_range) if in_range else "n/a"))


def main():
    if "--file" in sys.argv:
        path = sys.argv[sys.argv.index("--file") + 1]
        with open(path) as fh:
            records = parse_text(fh.read())
        print("# parsed %s (offline)" % path)
        analyse(records)
        return

    server = sys.argv[1] if len(sys.argv) > 1 else "10.129.235.84"
    zone = sys.argv[2] if len(sys.argv) > 2 else "inlanefreight.htb"
    records, messages = axfr(server, zone)
    print("# AXFR %s @ %s : %d messages" % (zone, server, messages))
    for name, rtype, value in records:
        print("%-42s %-6s %s" % (name, rtype, value))
    analyse(records)


if __name__ == "__main__":
    main()
