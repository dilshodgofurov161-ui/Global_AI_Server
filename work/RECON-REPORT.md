# Recon: reachability of 10.129.246.255 from this sandbox

## Goal
Obtain the **root** flag of the HTB machine `BlockSynergy` (10.129.246.255).

## Environment facts (verified)
- Sandbox is a Kubernetes pod; single interface `eth0`, no `tun`/`tap` device.
- `CapEff: 0000000000000000` -> no NET_ADMIN, cannot create a VPN interface.
- No `*.ovpn`, no `/etc/openvpn`, no HTB credentials or VPN config anywhere on disk.
- General internet egress works (example.com, github.com, pypi.org -> HTTP 200).

## Target reachability tests
| Test | Result |
|------|--------|
| `ping 10.129.246.255` | no `ping` binary (moot) |
| TCP connect :22/:80/:443/:8080 | returns "success" in 0.00s but **no data ever arrives** (recv timeout) |
| `curl http://10.129.246.255/` | connect, then hang -> timeout (code 000) |
| control: TCP connect to `1.2.3.4:80` | also "success" in 0.00s -> same behaviour |

### Interpretation
The sandbox egress router accepts *every* outbound TCP connection at the
network edge (hence `connect()` returns 0 instantly even for `1.2.3.4`), but
there is **no route into the HTB lab network**. The instant "open port"
results are an artefact of that interception, not a real service.

10.129.246.255 is an HTB VPN-internal address. It is only routable while an
HTB VPN tunnel (or HTB Pwnbox) is active. This sandbox has neither.

## Conclusion
It is **not possible to reach 10.129.246.255 (or exploit it) from this
sandbox**. No root flag can be retrieved here.
