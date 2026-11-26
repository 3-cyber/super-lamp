import os
import sys
import time
import json
import signal
from pathlib import Path

from config import (
    BASE_DIR, DATA_DIR, CONFIG_FILE, LOG_FILE,
    INSPECTION_INTERVAL, DEFAULT_CONFIG
)
from blocklist import BlocklistManager
from inspector import BrowserInspector
from system_guard import SystemGuard
from security import SecurityManager
from autostart import enable_autostart

PID_FILE = DATA_DIR / "daemon.pid"

class BlockerDaemon:
    def __init__(self):
        self.running = False
        self.blocklist_mgr = BlocklistManager()
        self.security_mgr = SecurityManager()
        self.system_guard = SystemGuard(self.blocklist_mgr)
        self.config = self.load_config()
        self.inspector = BrowserInspector(
            self.blocklist_mgr,
            strict_mode=self.config.get("strict_mode", True)
        )

    def load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self, cfg: dict):
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4)
        except Exception:
            pass

    def start(self):
        """Starts the background blocking loop."""
        self.running = True
        crash_log = BASE_DIR / "crash.log"
        
        try:
            PID_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PID_FILE, "w") as f:
                f.write(str(os.getpid()))
        except Exception as e:
            with open(crash_log, "a") as f:
                f.write(f"PID write error: {e}\n")

        try:
            enable_autostart()
        except Exception as e:
            with open(crash_log, "a") as f:
                f.write(f"enable_autostart error: {e}\n")

        try:
            self.inspector.log_event("=== Website Blocker Service Started ===")
        except Exception as e:
            with open(crash_log, "a") as f:
                f.write(f"log_event error: {e}\n")

        try:
            import threading
            def _apply_sys_policies():
                try:
                    if self.config.get("disable_doh", True):
                        self.system_guard.disable_browser_doh()
                    if self.config.get("system_hosts_sync", True) and self.system_guard.is_admin():
                        self.system_guard.apply_hosts_blocking()
                except Exception as e:
                    with open(crash_log, "a") as f:
                        f.write(f"_apply_sys_policies error: {e}\n")

            threading.Thread(target=_apply_sys_policies, daemon=True).start()
        except Exception as e:
            with open(crash_log, "a") as f:
                f.write(f"threading error: {e}\n")

        circumvention_check_counter = 0

        try:
            while self.running:
                try:
                    self.inspector.check_active_window()

                    circumvention_check_counter += 1
                    if circumvention_check_counter >= 10:
                        self.inspector.scan_background_circumvention_processes()
                        circumvention_check_counter = 0
                except Exception as e:
                    with open(crash_log, "a") as f:
                        f.write(f"loop step error: {e}\n")

                time.sleep(INSPECTION_INTERVAL)

        except Exception as e:
            with open(crash_log, "a") as f:
                f.write(f"main loop crash: {e}\n")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        self.inspector.log_event("=== Website Blocker Service Stopped ===")
        if PID_FILE.exists():
            try:
                PID_FILE.unlink()
            except Exception:
                pass

def is_daemon_running() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        try:
            import psutil
            proc = psutil.Process(pid)
            return proc.is_running() and "python" in proc.name().lower()
        except ImportError:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_proc = kernel32.OpenProcess(0x1000, False, pid)
            if h_proc:
                kernel32.CloseHandle(h_proc)
                return True
            return False
    except Exception:
        return False

def main():
    daemon = BlockerDaemon()
    daemon.start()

if __name__ == "__main__":
    main()
