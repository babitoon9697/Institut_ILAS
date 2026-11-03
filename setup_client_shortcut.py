import os
import sys
import subprocess

def create_client_shortcut(server_ip="192.168.1.182", port=8080):
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    shortcut_path = os.path.join(desktop, 'Institut ILAS.lnk')
    target_url = f"http://{server_ip}:{port}"
    
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

    ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{edge_path}"
$Shortcut.Arguments = '--app={target_url}'
$Shortcut.Description = "معهد إيلاس - الإدارة والتسجيل"
$Shortcut.Save()
"""
    res = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"SUCCESS: Client Desktop Shortcut created for {target_url} on Desktop!")
    else:
        print("Error:", res.stderr)

if __name__ == '__main__':
    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.182"
    create_client_shortcut(ip)
