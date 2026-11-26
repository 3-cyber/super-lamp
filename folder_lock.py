import os
import sys
import subprocess
import getpass
from pathlib import Path
from config import BASE_DIR
from security import SecurityManager

class FolderLocker:
    def __init__(self, target_dir=BASE_DIR):
        self.target_dir = Path(target_dir)
        self.security_mgr = SecurityManager()
        self.username = getpass.getuser()

    def lock_folder(self) -> tuple[bool, str]:
        """Locks the target directory using Windows NTFS ACLs and hidden attributes."""
        if not self.security_mgr.is_pin_set():
            return False, "Cannot lock folder: A 4-digit PIN must be set first."

        target = str(self.target_dir)
        try:
            # Apply Windows icacls deny rule for the current user
            # (OI)(CI)(F) = Object Inherit, Container Inherit, Full access denied
            cmd = f'icacls "{target}" /deny "{self.username}":(OI)(CI)F'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Hide the folder
            subprocess.run(f'attrib +h +s "{target}"', shell=True, capture_output=True)

            self.security_mgr.set_folder_locked(True)
            return True, f"Folder locked successfully. Access is now denied in Windows Explorer."
        except Exception as e:
            return False, f"Failed to lock folder: {e}"

    def unlock_folder(self, pin: str) -> tuple[bool, str]:
        """Unlocks the target directory after verifying the 4-digit PIN."""
        valid, msg = self.security_mgr.verify_pin(pin)
        if not valid:
            return False, f"Unlock failed: {msg}"

        target = str(self.target_dir)
        try:
            # Remove the deny rule
            cmd = f'icacls "{target}" /remove:d "{self.username}"'
            subprocess.run(cmd, shell=True, capture_output=True, text=True)

            # Unhide folder
            subprocess.run(f'attrib -h -s "{target}"', shell=True, capture_output=True)

            self.security_mgr.set_folder_locked(False)
            return True, "Folder unlocked successfully! Access restored."
        except Exception as e:
            return False, f"Failed to remove permissions: {e}"

    def is_locked(self) -> bool:
        return self.security_mgr.is_folder_locked()

def main():
    locker = FolderLocker()
    if len(sys.argv) > 1 and sys.argv[1].lower() == "lock":
        if not locker.security_mgr.is_pin_set():
            print("No 4-digit PIN configured yet. Run 'python main.py' to setup PIN first.")
            sys.exit(1)
        ok, msg = locker.lock_folder()
        print(msg)
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "unlock":
        pin = input("Enter your 4-digit PIN: ").strip()
        ok, msg = locker.unlock_folder(pin)
        print(msg)
        if ok:
            # Open the folder in File Explorer
            os.startfile(str(locker.target_dir))
    else:
        print(f"Folder status: {'LOCKED' if locker.is_locked() else 'UNLOCKED'}")
        print("Usage: python folder_lock.py [lock|unlock]")

if __name__ == "__main__":
    main()
