import os
import sys
import time
import socket
import urllib.request
import subprocess

PORT = 8080
PING_URL = f"http://127.0.0.1:{PORT}/api/ping"
LOCK_PORT = 48123
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "watchdog_log.txt")
SERVER_LOG = os.path.join(SCRIPT_DIR, "server_runtime.log")

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    entry = f"[{ts}] {msg}\n"
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 500000:
            with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-500:]
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception:
        pass

def acquire_single_instance_lock():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", LOCK_PORT))
        s.listen(1)
        return s
    except Exception:
        return None

def is_ping_ok():
    try:
        req = urllib.request.Request(PING_URL, headers={'User-Agent': 'ILAS-Watchdog/1.0'})
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            return resp.status == 200
    except Exception:
        return False

def get_python_exe():
    real_dir = r"C:\Users\INSTITUT ILAS\AppData\Local\Python\pythoncore-3.14-64"
    pw = os.path.join(real_dir, 'pythonw.exe')
    if os.path.exists(pw):
        return pw
    p = os.path.join(real_dir, 'python.exe')
    if os.path.exists(p):
        return p
    pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    if os.path.exists(pythonw):
        return pythonw
    return sys.executable

def start_and_wait_for_server():
    log("Démarrage du serveur ILAS (Waitress Multi-thread)...")
    app_path = os.path.join(SCRIPT_DIR, 'app.py')
    py_exe = get_python_exe()
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    cmd = [py_exe, app_path, '--no-browser', '--background']
    try:
        # Redirect stdout and stderr to server_runtime.log
        with open(SERVER_LOG, 'a', encoding='utf-8', errors='ignore') as s_out:
            s_out.write(f"\n--- Démarrage Serveur : {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            s_out.flush()
            subprocess.Popen(cmd, cwd=SCRIPT_DIR, stdout=s_out, stderr=s_out, creationflags=flags)
        log("Processus app.py lancé. Attente de la fin de l'initialisation et sauvegarde...")
    except Exception as e:
        log(f"Erreur lors du lancement de app.py : {e}")
        return False

    # Wait up to 35 seconds for migration and startup backup to complete
    for i in range(35):
        time.sleep(1)
        if is_ping_ok():
            log(f"Serveur ILAS prêt et opérationnel après {i+1}s (200 OK).")
            return True

    log("Avertissement : Le serveur a pris plus de 35s pour démarrer.")
    return False

def check_and_start_tunnel():
    try:
        from start_remote_tunnel import run_tunnel, is_tunnel_process_running
        if not is_tunnel_process_running():
            log("Tunnel Cloudflare absent. Relance automatique...")
            run_tunnel(silent=True)
    except Exception as e:
        log(f"Erreur vérification tunnel : {e}")

def main():
    lock_sock = acquire_single_instance_lock()
    if lock_sock is None:
        # Watchdog already running
        return

    log("=== Watchdog Institut ILAS démarré (Surveillance 24/7 active) ===")

    # Initial check
    if not is_ping_ok():
        start_and_wait_for_server()

    check_and_start_tunnel()

    fail_count = 0
    last_tunnel_check = 0

    while True:
        try:
            now = time.time()
            if is_ping_ok():
                if fail_count > 0:
                    log("Serveur ILAS rétabli et fonctionnel (200 OK).")
                    fail_count = 0
            else:
                fail_count += 1
                log(f"Alerte : Serveur ILAS injoignable (tentative {fail_count}/2)...")
                if fail_count >= 2:
                    log("Relance immédiate du serveur ILAS...")
                    start_and_wait_for_server()
                    fail_count = 0

            # Check tunnel every 30 seconds
            if now - last_tunnel_check > 30:
                check_and_start_tunnel()
                last_tunnel_check = now

        except Exception as e:
            log(f"Exception dans la boucle watchdog : {e}")

        time.sleep(5)

if __name__ == '__main__':
    main()
