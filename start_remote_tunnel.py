import os
import sys
import subprocess

def is_tunnel_process_running():
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq cloudflared.exe" /NH', shell=True).decode('utf-8', errors='ignore')
        return "cloudflared.exe" in out.lower()
    except Exception:
        return False

def run_tunnel(token=None, silent=False):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cloudflared = os.path.join(script_dir, 'cloudflared.exe')
    
    if not os.path.exists(cloudflared):
        print('Error: cloudflared.exe not found.')
        return False

    if is_tunnel_process_running():
        print('Cloudflare Tunnel is already running.')
        return True

    if token and len(token.strip()) > 10:
        t_val = token.strip()
    else:
        token_file = os.path.join(script_dir, 'tunnel_token.txt')
        t_val = None
        if os.path.exists(token_file):
            with open(token_file, 'r', encoding='utf-8') as f:
                t_val = f.read().strip()
                
    if t_val:
        print('Starting Fixed Cloudflare Tunnel with Token...')
        cmd = [cloudflared, 'tunnel', 'run', '--token', t_val]
    else:
        print('Starting Cloudflare Quick Tunnel...')
        cmd = [cloudflared, 'tunnel', '--url', 'http://localhost:8080']

    flags = subprocess.CREATE_NO_WINDOW if (sys.platform == 'win32' and silent) else 0
    subprocess.Popen(cmd, cwd=script_dir, creationflags=flags)
    return True

if __name__ == '__main__':
    tok = sys.argv[1] if len(sys.argv) > 1 else None
    run_tunnel(tok)
