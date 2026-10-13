import socket, sys, concurrent.futures
host = sys.argv[1]
ports = [int(p) for p in sys.argv[2].split(',')] if len(sys.argv)>2 else list(range(1,65536))
def check(p):
    s = socket.socket()
    s.settimeout(1.2)
    try:
        r = s.connect_ex((host,p))
        if r == 0:
            try:
                s.settimeout(1.0)
                s.send(b'\r\n')
                d = s.recv(128)
            except Exception:
                d = b''
            return (p, d[:60])
    except Exception:
        pass
    finally:
        s.close()
    return None
open_ports=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=400) as ex:
    for res in ex.map(check, ports):
        if res:
            open_ports.append(res)
            print('OPEN', res[0], res[1], flush=True)
print('DONE', sorted(p for p,_ in open_ports))
