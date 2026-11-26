import os
import sys
import subprocess
import winreg
from pathlib import Path
from typing import Set, List
from blocklist import BlocklistManager
from config import LOG_FILE

HOSTS_PATH = Path(r"C:\Windows\System32\drivers\etc\hosts")
BLOCKER_MARKER_START = "# === ADULT_BLOCKER_START ==="
BLOCKER_MARKER_END = "# === ADULT_BLOCKER_END ==="

class SystemGuard:
    def __init__(self, blocklist_mgr: BlocklistManager):
        self.blocklist_mgr = blocklist_mgr

    def is_admin(self) -> bool:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def disable_browser_doh(self) -> bool:
        if not self.is_admin():
            return False

        try:
            chrome_key = r"SOFTWARE\Policies\Google\Chrome"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, chrome_key) as key:
                winreg.SetValueEx(key, "DnsOverHttpsMode", 0, winreg.REG_SZ, "off")

            edge_key = r"SOFTWARE\Policies\Microsoft\Edge"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, edge_key) as key:
                winreg.SetValueEx(key, "DnsOverHttpsMode", 0, winreg.REG_SZ, "off")

            firefox_key = r"SOFTWARE\Policies\Mozilla\Firefox"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, firefox_key) as key:
                winreg.SetValueEx(key, "DNSOverHTTPS", 0, winreg.REG_DWORD, 0)

            return True
        except Exception as e:
            return False

    def restore_browser_doh(self) -> bool:
        if not self.is_admin():
            return False
        try:
            for key_path, val_name in [
                (r"SOFTWARE\Policies\Google\Chrome", "DnsOverHttpsMode"),
                (r"SOFTWARE\Policies\Microsoft\Edge", "DnsOverHttpsMode"),
                (r"SOFTWARE\Policies\Mozilla\Firefox", "DNSOverHTTPS")
            ]:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, val_name)
                except FileNotFoundError:
                    pass
            return True
        except Exception:
            return False

    def flush_dns(self):
        try:
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True, check=False)
        except Exception:
            pass

    def apply_hosts_blocking(self, max_hosts: int = 35000) -> bool:
        r"""
        Injects adult domains sinkhole into C:\Windows\System32\drivers\etc\hosts.
        Requires Administrator privileges.
        """
        if not self.is_admin():
            return False

        if not HOSTS_PATH.exists():
            return False

        try:
            content = HOSTS_PATH.read_text(encoding="utf-8", errors="ignore")
            clean_lines = []
            in_blocker_section = False

            for line in content.splitlines():
                if BLOCKER_MARKER_START in line:
                    in_blocker_section = True
                    continue
                if BLOCKER_MARKER_END in line:
                    in_blocker_section = False
                    continue
                if not in_blocker_section:
                    clean_lines.append(line)

            blocker_lines = [
                "",
                BLOCKER_MARKER_START,
                "# Managed automatically by Adult Website Blocker"
            ]

            count = 0
            for domain in sorted(self.blocklist_mgr.domains):
                blocker_lines.append(f"0.0.0.0 {domain}")
                if not domain.startswith("www."):
                    blocker_lines.append(f"0.0.0.0 www.{domain}")
                count += 2
                if count >= max_hosts:
                    break

            blocker_lines.append(BLOCKER_MARKER_END)
            blocker_lines.append("")

            new_content = "\n".join(clean_lines) + "\n" + "\n".join(blocker_lines)

            try:
                os.chmod(HOSTS_PATH, 0o666)
            except Exception:
                pass

            HOSTS_PATH.write_text(new_content, encoding="utf-8")
            self.flush_dns()
            return True
        except Exception as e:
            return False

    def remove_hosts_blocking(self) -> bool:
        if not self.is_admin():
            return False

        if not HOSTS_PATH.exists():
            return False

        try:
            content = HOSTS_PATH.read_text(encoding="utf-8", errors="ignore")
            clean_lines = []
            in_blocker_section = False

            for line in content.splitlines():
                if BLOCKER_MARKER_START in line:
                    in_blocker_section = True
                    continue
                if BLOCKER_MARKER_END in line:
                    in_blocker_section = False
                    continue
                if not in_blocker_section:
                    clean_lines.append(line)

            HOSTS_PATH.write_text("\n".join(clean_lines) + "\n", encoding="utf-8")
            self.flush_dns()
            return True
        except Exception as e:
            return False
