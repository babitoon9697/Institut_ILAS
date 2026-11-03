import os
import sys
import time
import socket
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

PORT = 8080
URL = f"http://127.0.0.1:{PORT}"

def is_server_running():
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
            return True
    except (socket.error, TimeoutError):
        return False

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

def run_splash():
    root = tk.Tk()
    root.overrideredirect(True)
    
    width, height = 450, 270
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - width) // 2
    y = (sh - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.configure(bg="#0B3D6E")

    canvas = tk.Canvas(root, width=width, height=height, bg="#0B3D6E", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(script_dir, "static", "uploads", "logo-ilas.png")
    
    if os.path.exists(logo_path):
        try:
            pil_img = Image.open(logo_path).resize((85, 85), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)
            root.logo_img = tk_img
            canvas.create_image(width // 2, 60, image=tk_img)
        except Exception:
            pass

    canvas.create_text(width // 2, 130, text="معهد إيلاس - Institut ILAS", fill="#ffffff", font=("Segoe UI", 16, "bold"))
    canvas.create_text(width // 2, 160, text="جاري تشغيل النظام... Démarrage du système...", fill="#bae6fd", font=("Segoe UI", 10))

    style = ttk.Style()
    style.theme_use('default')
    style.configure("Custom.Horizontal.TProgressbar", thickness=6, troughcolor='#0369a1', background='#10b981')

    pbar = ttk.Progressbar(root, style="Custom.Horizontal.TProgressbar", mode="indeterminate", length=300)
    canvas.create_window(width // 2, 200, window=pbar)
    pbar.start(10)

    canvas.create_text(width // 2, 240, text="© Institut ILAS - système d'administration", fill="#94a3b8", font=("Segoe UI", 8))

    def check_and_finish():
        if not is_server_running():
            real_dir = r"C:\Users\INSTITUT ILAS\AppData\Local\Python\pythoncore-3.14-64"
            pythonw = os.path.join(real_dir, 'pythonw.exe')
            if not os.path.exists(pythonw):
                pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
            if not os.path.exists(pythonw):
                pythonw = sys.executable
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            subprocess.Popen([pythonw, app_path, '--no-browser', '--background'], cwd=script_dir, creationflags=flags)

        # Start tunnel silently if not running
        try:
            from start_remote_tunnel import run_tunnel
            run_tunnel(silent=True)
        except Exception:
            pass

        # Ensure watchdog is running
        try:
            watchdog_path = os.path.join(script_dir, 'server_watchdog.py')
            real_dir = r"C:\Users\INSTITUT ILAS\AppData\Local\Python\pythoncore-3.14-64"
            pythonw = os.path.join(real_dir, 'pythonw.exe')
            if not os.path.exists(pythonw):
                pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
            if not os.path.exists(pythonw):
                pythonw = sys.executable
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            subprocess.Popen([pythonw, watchdog_path], cwd=script_dir, creationflags=flags)
        except Exception:
            pass

        max_retries = 30
        for _ in range(max_retries):
            if is_server_running():
                break
            time.sleep(0.2)

        launch_browser()
        root.after(200, root.destroy)

    threading.Thread(target=check_and_finish, daemon=True).start()
    root.mainloop()

if __name__ == '__main__':
    try:
        from start_remote_tunnel import run_tunnel
        run_tunnel(silent=True)
    except Exception:
        pass

    if is_server_running():
        launch_browser()
    else:
        run_splash()
