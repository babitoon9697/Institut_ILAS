import socket
import sys
import os
import time
import subprocess

PORT = 8080
URL = f"http://127.0.0.1:{PORT}"

def is_server_running():
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=1):
            return True
    except (socket.error, TimeoutError):
        return False

def get_python_exe(gui=True):
    real_dir = r"C:\Users\INSTITUT ILAS\AppData\Local\Python\pythoncore-3.14-64"
    target = 'pythonw.exe' if gui else 'python.exe'
    p = os.path.join(real_dir, target)
    if os.path.exists(p):
        return p
    alt = os.path.join(os.path.dirname(sys.executable), target)
    if os.path.exists(alt):
        return alt
    return sys.executable

def ensure_watchdog_running():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    watchdog_path = os.path.join(script_dir, 'server_watchdog.py')
    pythonw = get_python_exe(gui=True)
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    try:
        subprocess.Popen([pythonw, watchdog_path], cwd=script_dir, creationflags=flags)
    except Exception:
        pass

def launch_browser():
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "msedge.exe"
    ]
    
    for path in edge_paths:
        try:
            subprocess.Popen([path, f"--app={URL}"])
            return
        except Exception:
            continue
            
    import webbrowser
    webbrowser.open(URL)

if __name__ == '__main__':
    # Guarantee the 24/7 watchdog is running
    ensure_watchdog_running()

    if not is_server_running():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(script_dir, 'app.py')
        pythonw = get_python_exe(gui=True)
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        subprocess.Popen([pythonw, app_path, '--no-browser', '--background'], cwd=script_dir, creationflags=flags)
        
        for _ in range(40):
            time.sleep(0.25)
            if is_server_running():
                break

    try:
        from start_remote_tunnel import run_tunnel
        run_tunnel(silent=True)
    except Exception:
        pass

    if '--background' not in sys.argv and '--no-browser' not in sys.argv:
        launch_browser()
