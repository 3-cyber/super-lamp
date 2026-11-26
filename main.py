import os
import sys
import time
import subprocess
from pathlib import Path

from config import (
    BASE_DIR, CONFIG_FILE, LOG_FILE, DATA_DIR
)
from security import SecurityManager
from blocklist import BlocklistManager
from system_guard import SystemGuard
from daemon import is_daemon_running, PID_FILE, BlockerDaemon

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_banner():
    print("=" * 65)
    print("        SECURE ADULT WEBSITE BLOCKER & SYSTEM SHIELD")
    print("=" * 65)

class BlockerController:
    def __init__(self):
        self.security = SecurityManager()
        self.blocklist = BlocklistManager()
        self.system_guard = SystemGuard(self.blocklist)

    def prompt_pin_verification(self, action_name: str) -> bool:
        """Prompts user for PIN/Password before allowing access."""
        is_locked, remaining = self.security.is_locked_out()
        if is_locked:
            print(f"\n[-] Access Denied: Too many failed attempts. Try again in {remaining} seconds.")
            input("Press Enter to exit...")
            return False

        print(f"\n[*] Security Password / PIN required to {action_name}.")
        pin = input("Enter Master Password / PIN (or 'RECOVER' for recovery key): ").strip()
        
        if pin.upper() == "RECOVER":
            rec_key = input("Enter 24-character Emergency Recovery Key: ").strip()
            ok, msg = self.security.verify_recovery_key(rec_key)
            if ok:
                print("[+] Recovery key verified!")
                return True
            else:
                print(f"[-] {msg}")
                return False

        ok, msg = self.security.verify_pin(pin)
        if ok:
            return True
        else:
            print(f"[-] {msg}")
            input("Press Enter to exit...")
            return False

    def start_blocker(self):
        if is_daemon_running():
            print("\n[*] Website Blocker is ALREADY RUNNING.")
            return

        print("\n[*] Launching Website Blocker background daemon...")
        
        if getattr(sys, 'frozen', False):
            # In compiled PyInstaller executable, spawn daemon mode directly
            subprocess.Popen(
                [sys.executable, "--daemon"],
                cwd=str(BASE_DIR),
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            python_exe = sys.executable
            pythonw_exe = Path(python_exe).parent / "pythonw.exe"
            runner = str(pythonw_exe) if pythonw_exe.exists() else python_exe
            daemon_script = str(BASE_DIR / "daemon.py")
            subprocess.Popen(
                [runner, daemon_script],
                cwd=str(BASE_DIR),
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )

        time.sleep(1)
        if is_daemon_running():
            print("[+] Website Blocker is now ACTIVE and protecting your PC.")
        else:
            print("[*] Blocker process started. Check logs/blocker.log for details.")

    def stop_blocker(self):
        if not is_daemon_running():
            print("\n[*] Website Blocker is NOT currently running.")
            return

        if not self.prompt_pin_verification("STOP the website blocker"):
            return

        try:
            pid = int(PID_FILE.read_text().strip())
            import psutil
            proc = psutil.Process(pid)
            proc.terminate()
            print("[+] Background blocker daemon stopped.")
        except Exception as e:
            print(f"[-] Error stopping daemon: {e}")

        if self.system_guard.is_admin():
            self.system_guard.remove_hosts_blocking()
            self.system_guard.restore_browser_doh()

    def run_menu(self):
        clear_screen()
        print_banner()

        # Gate entire interface behind password authentication if set
        if self.security.is_pin_set():
            if not self.prompt_pin_verification("OPEN Website Blocker Console"):
                print("\n[!] Authentication failed. The blocker console will not open without the password.")
                time.sleep(2)
                sys.exit(1)

        while True:
            clear_screen()
            print_banner()

            running = is_daemon_running()
            domains_count = len(self.blocklist.domains)
            is_admin = self.system_guard.is_admin()

            print(f"  Status:         {'[PROTECTED / ACTIVE]' if running else '[STOPPED / INACTIVE]'}")
            print(f"  Adult Domains:  {domains_count:,} blocked websites")
            print(f"  Privilege:      {'[ADMINISTRATOR]' if is_admin else '[STANDARD USER - Elevated recommended]'}")
            print("-" * 65)
            print("  [1] Start Website Blocker Protection")
            print("  [2] Stop Website Blocker (Requires Password)")
            print("  [3] Update / Sync Latest Adult Blocklists")
            print("  [4] Add a Custom Domain to Blocklist")
            print("  [5] Change Master Password / PIN")
            print("  [6] View Blocked Activity Logs")
            print("  [7] Exit Console (Protection continues running in background)")
            print("=" * 65)

            choice = input("Select an option (1-7): ").strip()

            if choice == "1":
                self.start_blocker()
                input("\nPress Enter to continue...")
            elif choice == "2":
                self.stop_blocker()
                input("\nPress Enter to continue...")
            elif choice == "3":
                print("\n[*] Downloading comprehensive adult domain list (~75k domains)...")
                added = self.blocklist.sync_online_blocklist()
                print(f"[+] Download complete! {added} new adult domains added.")
                input("\nPress Enter to continue...")
            elif choice == "4":
                domain = input("\nEnter domain to block (e.g. example.com): ").strip()
                if domain:
                    if self.blocklist.add_custom_domain(domain):
                        print(f"[+] '{domain}' added to blocklist.")
                    else:
                        print("[-] Invalid domain format.")
                input("\nPress Enter to continue...")
            elif choice == "5":
                if self.prompt_pin_verification("change your Master Password"):
                    new_pin = input("Enter new Master Password: ").strip()
                    ok, msg, rec_key = self.security.set_pin(new_pin)
                    print(f"[{'+' if ok else '-'}] {msg}")
                    if ok:
                        print(f"New Emergency Recovery Key: {rec_key}")
                input("\nPress Enter to continue...")
            elif choice == "6":
                clear_screen()
                print("=== RECENT BLOCKED ACTIVITY LOGS ===")
                if LOG_FILE.exists():
                    lines = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for line in lines[-30:]:
                        print(line)
                else:
                    print("No logs recorded yet.")
                input("\nPress Enter to return to menu...")
            elif choice == "7":
                print("\nExiting console. Protection remains active in background.")
                break

def main():
    if "--daemon" in sys.argv:
        # Background daemon mode
        daemon = BlockerDaemon()
        daemon.start()
        sys.exit(0)
    elif "--set-init-password" in sys.argv:
        # Installer initial password configuration flag
        idx = sys.argv.index("--set-init-password")
        if idx + 1 < len(sys.argv):
            init_pass = sys.argv[idx + 1]
            sec = SecurityManager()
            ok, msg, rec_key = sec.set_pin(init_pass)
            if ok:
                rec_file = DATA_DIR / "RECOVERY_KEY_IMPORTANT.txt"
                rec_file.write_text(
                    f"====================================================\n"
                    f"      WEBSITE BLOCKER EMERGENCY RECOVERY KEY\n"
                    f"====================================================\n\n"
                    f"Recovery Key: {rec_key}\n\n"
                    f"If you ever forget your password, you will need this key.\n"
                    f"DO NOT LOSE THIS KEY!\n",
                    encoding="utf-8"
                )
            sys.exit(0 if ok else 1)
        sys.exit(1)
    else:
        controller = BlockerController()
        controller.run_menu()

if __name__ == "__main__":
    main()
