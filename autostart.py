import os
import sys
import winreg
from pathlib import Path
from config import BASE_DIR

STARTUP_FOLDER = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "AdultWebsiteBlocker"

def get_python_path() -> str:
    return sys.executable

def enable_autostart() -> tuple[bool, str]:
    """
    Enables automatic start on system boot/login pointing to the protected LocalAppData runtime copy.
    """
    python_exe = get_python_path()
    runtime_daemon = Path(os.environ.get("LOCALAPPDATA", "")) / "AdultWebBlocker" / "runtime" / "daemon.py"
    daemon_script = str(runtime_daemon)
    
    messages = []
    success = False

    # 1. Create silent launcher in Windows Startup Folder
    try:
        STARTUP_FOLDER.mkdir(parents=True, exist_ok=True)
        vbs_path = STARTUP_FOLDER / f"{APP_NAME}.vbs"
        vbs_content = f'CreateObject("Wscript.Shell").Run """{python_exe}"" ""{daemon_script}""", 0, False\n'
        vbs_path.write_text(vbs_content, encoding="utf-8")
        messages.append("Created silent launcher in Windows Startup folder.")
        success = True
    except Exception as e:
        messages.append(f"Failed Startup folder launcher: {e}")

    # 2. Register hidden launcher in HKCU Run Key
    try:
        cmd_str = f'wscript.exe "{vbs_path}"'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd_str)
        messages.append("Registered in Windows Registry Run key (HKCU).")
        success = True
    except Exception as e:
        messages.append(f"Failed registry autostart: {e}")

    return success, " | ".join(messages)

def disable_autostart() -> tuple[bool, str]:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except Exception:
        pass

    vbs_path = STARTUP_FOLDER / f"{APP_NAME}.vbs"
    if vbs_path.exists():
        try:
            vbs_path.unlink()
        except Exception:
            pass

    return True, "Autostart entries disabled."

if __name__ == "__main__":
    ok, msg = enable_autostart()
    print("Autostart status:", msg)
