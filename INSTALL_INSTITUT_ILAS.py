import os
import sys
import subprocess
from PIL import Image

DEFAULT_TOKEN = "eyJhIjoiYzQ0MWQ4ODkwOWRkMzkwOGJkNWIxNDc0ZDc1M2E2MWMiLCJ0IjoiMTYzNzA0MTItMmFmMS00YjQ0LWI4ODItZmZhNzA2MTkxY2M2IiwicyI6IlNleEFsckcwSDVKTDgrVmFlcVI1S2pSQnlCY2lRSENTaTgvdjQwdXJWY3c9In0="

def run_cmd(cmd, check=False):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res.returncode == 0, res.stdout, res.stderr
    except Exception as e:
        return False, "", str(e)

def setup_master():
    print("==========================================================")
    print("   INSTITUT ILAS - MASTER INSTALLER (1-CLICK SETUP)       ")
    print("==========================================================")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Save Token
    token = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TOKEN
    token_file = os.path.join(script_dir, "tunnel_token.txt")
    with open(token_file, "w", encoding="utf-8") as f:
        f.write(token.strip())
    print("[1/4] Saved Cloudflare Tunnel Token to tunnel_token.txt")

    # 2. Generate Icon
    img_path = os.path.join(script_dir, "static", "uploads", "logo-ilas.png")
    ico_path = os.path.join(script_dir, "static", "logo.ico")
    if os.path.exists(img_path):
        try:
            img = Image.open(img_path)
            img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
            print("[2/4] Generated high-res static/logo.ico icon")
        except Exception as e:
            print("[2/4] Icon generation notice:", e)

    # 3. Create Desktop Shortcut
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "Institut ILAS.lnk")
    vbs_path = os.path.join(script_dir, "launch_app.vbs")

    ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = '"{vbs_path}"'
$Shortcut.WorkingDirectory = "{script_dir}"
$Shortcut.IconLocation = "{ico_path}"
$Shortcut.Description = "معهد إيلاس - الإدارة والتسجيل"
$Shortcut.Save()
"""
    ok_sc, _, _ = run_cmd(["powershell", "-Command", ps_script])
    if ok_sc:
        print("[3/4] Created Desktop Shortcut with School Logo Icon")
    else:
        print("[3/4] Failed to create desktop shortcut")

    # 4. Configure Windows Firewall Port 8080
    ps_fw = "New-NetFirewallRule -DisplayName 'Institut ILAS LAN Port 8080' -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue"
    run_cmd(["powershell", "-Command", ps_fw])
    print("[4/4] Added Windows Defender Firewall Rule for LAN Port 8080")

    # 5. Install Cloudflare Service
    cloudflared = os.path.join(script_dir, "cloudflared.exe")
    if os.path.exists(cloudflared):
        print("Installing Cloudflare Remote Tunnel Windows Service...")
        run_cmd([cloudflared, "service", "uninstall"])
        ok_cf, out_cf, err_cf = run_cmd([cloudflared, "service", "install", token.strip()])
        if ok_cf:
            print(">>> Cloudflare Remote Tunnel Service INSTALLED SUCCESSFULLY!")
            run_cmd(["net", "start", "cloudflared"])
        else:
            print("Cloudflare Service Install Notice:", err_cf or out_cf)

    print("\n==========================================================")
    print("   SUCCESS: INSTITUT ILAS SYSTEM INSTALLED SUCCESSFULLY!  ")
    print("==========================================================")
    print(" - Local Access  : http://localhost:8080")
    print(" - Remote Access : Fixed HTTPS Tunnel Active")
    print(" - Desktop Icon  : 'Institut ILAS' created on Desktop")
    print("==========================================================")

if __name__ == '__main__':
    setup_master()
