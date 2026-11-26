import os
import sys
import time
import re
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple
try:
    import psutil
except ImportError:
    psutil = None

from config import BROWSER_PROCESSES, CIRCUMVENTION_PROCESSES, LOG_FILE
from blocklist import BlocklistManager

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001

# Virtual key codes
VK_CONTROL = 0x11
VK_W = 0x57
KEYEVENTF_KEYUP = 0x0002
WM_CLOSE = 0x0010

ULONG_PTR = ctypes.c_ulonglong

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR)
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
            ("hi", HARDWAREINPUT)
        ]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT)
    ]

INPUT_KEYBOARD = 1

def send_ctrl_w():
    """Sends Ctrl+W to the active foreground window using 64-bit SendInput."""
    inputs = (INPUT * 4)()
    
    # 0: Ctrl DOWN
    inputs[0].type = INPUT_KEYBOARD
    inputs[0].ki.wVk = VK_CONTROL
    inputs[0].ki.wScan = user32.MapVirtualKeyW(VK_CONTROL, 0)
    inputs[0].ki.dwFlags = 0

    # 1: W DOWN
    inputs[1].type = INPUT_KEYBOARD
    inputs[1].ki.wVk = VK_W
    inputs[1].ki.wScan = user32.MapVirtualKeyW(VK_W, 0)
    inputs[1].ki.dwFlags = 0

    # 2: W UP
    inputs[2].type = INPUT_KEYBOARD
    inputs[2].ki.wVk = VK_W
    inputs[2].ki.wScan = user32.MapVirtualKeyW(VK_W, 0)
    inputs[2].ki.dwFlags = KEYEVENTF_KEYUP

    # 3: Ctrl UP
    inputs[3].type = INPUT_KEYBOARD
    inputs[3].ki.wVk = VK_CONTROL
    inputs[3].ki.wScan = user32.MapVirtualKeyW(VK_CONTROL, 0)
    inputs[3].ki.dwFlags = KEYEVENTF_KEYUP

    user32.SendInput(4, ctypes.byref(inputs), ctypes.sizeof(INPUT))

import unicodedata

def clean_window_title(text: str) -> str:
    if not text:
        return ""
    # Remove zero-width spaces and other invisible/formatting characters
    text = re.sub(r"[\u200B-\u200D\uFEFF\u200E\u200F]", "", text)
    # Normalize unicode characters
    text = unicodedata.normalize("NFKC", text)
    return text.strip()

def ensure_default_desktop():
    try:
        h_desk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_desk:
            user32.SetThreadDesktop(h_desk)
            user32.CloseDesktop(h_desk)
    except Exception:
        pass

class BrowserInspector:
    def __init__(self, blocklist_mgr: BlocklistManager, strict_mode: bool = True):
        self.blocklist_mgr = blocklist_mgr
        self.strict_mode = strict_mode
        self.last_blocked_time = 0
        self.last_blocked_target = ""
        self.consecutive_blocks = {}
        ensure_default_desktop()

    def log_event(self, message: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
                f.write(log_entry)
        except Exception:
            pass

        try:
            if sys.stdout is not None:
                encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
                sys.stdout.write(log_entry.encode(encoding, errors="replace").decode(encoding))
                sys.stdout.flush()
        except Exception:
            pass

    def _get_process_name(self, pid: int) -> str:
        if psutil:
            try:
                name = psutil.Process(pid).name()
                return name.lower() if name else ""
            except Exception:
                pass

        h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if h_proc:
            try:
                buf = ctypes.create_unicode_buffer(512)
                size = wintypes.DWORD(512)
                if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
                    return os.path.basename(buf.value).lower()
            finally:
                kernel32.CloseHandle(h_proc)
        return ""

    def get_foreground_window_info(self) -> Tuple[int, str, str]:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return 0, "", ""

        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        proc_name = self._get_process_name(pid.value)
        return hwnd, title, proc_name

    def close_current_tab(self, hwnd: int):
        """
        Closes the active offending tab or window immediately.
        1. Ensures focus if needed and sends Ctrl+W.
        2. Sends WM_CLOSE and WM_SYSCOMMAND (SC_CLOSE) to hwnd.
        3. If window is still showing adult content after previous attempt,
           immediately escalates to terminating the process.
        """
        count = self.consecutive_blocks.get(hwnd, 0) + 1
        self.consecutive_blocks[hwnd] = count

        # If window has persisted with adult content across checks, forcefully kill process
        if count >= 2:
            self.log_event(f"Escalating: Force terminating browser process for window (HWND: {hwnd}, attempt {count}).")
            self.terminate_process_by_hwnd(hwnd)
            self.consecutive_blocks.pop(hwnd, None)
            return

        # Ensure window is foreground so Ctrl+W closes the offending tab
        try:
            fg_hwnd = user32.GetForegroundWindow()
            if fg_hwnd != hwnd:
                user32.SetForegroundWindow(hwnd)
                time.sleep(0.02)
        except Exception:
            pass

        # Attempt keystrokes
        try:
            send_ctrl_w()
        except Exception:
            pass

        try:
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_W, 0, 0, 0)
            time.sleep(0.01)
            user32.keybd_event(VK_W, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        except Exception:
            pass

        # Direct window close signals
        WM_SYSCOMMAND = 0x0112
        SC_CLOSE = 0xF060
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        user32.PostMessageW(hwnd, WM_SYSCOMMAND, SC_CLOSE, 0)

    def terminate_process_by_hwnd(self, hwnd: int):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value:
            if psutil:
                try:
                    p = psutil.Process(pid.value)
                    for child in p.children(recursive=True):
                        try:
                            child.kill()
                        except Exception:
                            pass
                    p.kill()
                    return
                except Exception:
                    pass

            h_proc = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid.value)
            if h_proc:
                try:
                    kernel32.TerminateProcess(h_proc, 1)
                    return
                finally:
                    kernel32.CloseHandle(h_proc)

            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            user32.PostMessageW(hwnd, 0x0112, 0xF060, 0)

    def extract_domains_from_text(self, text: str) -> list:
        found = re.findall(r"(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}", text)
        return [d.lower() for d in found]

    def _inspect_single_window(self, hwnd: int, title: str, proc_name: str) -> bool:
        if not hwnd or not proc_name or not title:
            return False

        clean_title = clean_window_title(title)
        if not clean_title:
            return False

        # Exact matching for Tor core process / browser
        is_tor_browser = (
            proc_name in ("tor.exe", "tor-browser.exe") 
            or ("tor browser" in clean_title.lower())
        )
        
        if self.strict_mode and is_tor_browser:
            self.log_event(f"BLOCKED: Circumvention tool detected ({proc_name} / '{clean_title}'). Terminating.")
            self.terminate_process_by_hwnd(hwnd)
            return True

        if proc_name not in BROWSER_PROCESSES:
            return False

        extracted_domains = self.extract_domains_from_text(clean_title)
        for dom in extracted_domains:
            if self.blocklist_mgr.is_domain_blocked(dom):
                self.log_event(f"BLOCKED: Adult domain '{dom}' detected in browser window '{clean_title}'. Closing tab/window.")
                self.close_current_tab(hwnd)
                return True

        if self.blocklist_mgr.is_text_suspicious(clean_title):
            self.log_event(f"BLOCKED: Explicit adult content detected in window title '{clean_title}'. Closing tab/window.")
            self.close_current_tab(hwnd)
            return True

        if hwnd in self.consecutive_blocks:
            self.consecutive_blocks.pop(hwnd, None)
        return False

    def check_active_window(self) -> bool:
        ensure_default_desktop()
        # Check foreground window first
        hwnd, title, proc_name = self.get_foreground_window_info()
        if hwnd and proc_name:
            if self._inspect_single_window(hwnd, title, proc_name):
                return True

        # Also scan all top-level browser windows to prevent background tab bypass
        try:
            def enum_cb(h, extra):
                if user32.IsWindowVisible(h):
                    len_ = user32.GetWindowTextLengthW(h)
                    if len_ > 0:
                        buf = ctypes.create_unicode_buffer(len_ + 1)
                        user32.GetWindowTextW(h, buf, len_ + 1)
                        t = buf.value
                        p = wintypes.DWORD()
                        user32.GetWindowThreadProcessId(h, ctypes.byref(p))
                        pname = self._get_process_name(p.value)
                        if pname in BROWSER_PROCESSES:
                            self._inspect_single_window(h, t, pname)
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        except Exception:
            pass

        return False

    def scan_background_circumvention_processes(self):
        if not self.strict_mode or not psutil:
            return

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                raw_name = proc.info.get('name')
                if not raw_name:
                    continue
                name = raw_name.lower()
                if name in CIRCUMVENTION_PROCESSES:
                    self.log_event(f"BLOCKED: Circumvention process detected: {name} (PID: {proc.info['pid']}). Terminating.")
                    proc.kill()
            except Exception:
                continue
