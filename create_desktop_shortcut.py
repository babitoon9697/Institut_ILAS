import os
import sys

def create_shortcut():
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    proj_dir = os.path.dirname(os.path.abspath(__file__))
    vbs_path = os.path.join(proj_dir, 'launch_app.vbs')
    ico_path = os.path.join(proj_dir, 'static', 'logo.ico')
    shortcut_path = os.path.join(desktop, 'Institut ILAS.lnk')

    try:
        import win32com.client
        shell = win32com.client.Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = 'wscript.exe'
        shortcut.Arguments = f'"{vbs_path}"'
        shortcut.WorkingDirectory = proj_dir
        if os.path.exists(ico_path):
            shortcut.IconLocation = ico_path
        shortcut.Description = 'معهد إيلاس - الإدارة والتسجيل'
        shortcut.save()
        print('SUCCESS: Created Desktop Shortcut with School Logo Icon on Desktop!')
        return True
    except Exception as err:
        print('Using PowerShell fallback to create shortcut...')
        ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = '"{vbs_path}"'
$Shortcut.WorkingDirectory = "{proj_dir}"
$Shortcut.IconLocation = "{ico_path}"
$Shortcut.Description = "معهد إيلاس - الإدارة والتسجيل"
$Shortcut.Save()
"""
        import subprocess
        res = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        if res.returncode == 0:
            print('SUCCESS: Created Desktop Shortcut via PowerShell!')
            return True
        else:
            print('PowerShell Error:', res.stderr)
            return False

if __name__ == '__main__':
    create_shortcut()
