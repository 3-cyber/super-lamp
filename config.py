import os
import sys
from pathlib import Path

# Redirect stdout/stderr if running under pythonw (no GUI console) to prevent print crashes
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")

# Paths
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_FILE = DATA_DIR / "config.json"
PIN_FILE = DATA_DIR / "security.json"
BLOCKLIST_FILE = DATA_DIR / "blocklist.txt"
CUSTOM_BLOCKLIST_FILE = DATA_DIR / "custom_blocklist.txt"
LOG_FILE = LOGS_DIR / "blocker.log"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# External secure storage
APPDATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(BASE_DIR))) / "AdultWebBlocker"
APPDATA_DIR.mkdir(parents=True, exist_ok=True)
EXTERNAL_PIN_FILE = APPDATA_DIR / "security.json"

# Default targeted browser executable names
BROWSER_PROCESSES = {
    "chrome.exe": "Google Chrome",
    "msedge.exe": "Microsoft Edge",
    "msedgewebview2.exe": "Microsoft Edge WebView2",
    "microsoftedge.exe": "Microsoft Edge",
    "microsoftedgecp.exe": "Microsoft Edge CP",
    "edge.exe": "Microsoft Edge",
    "firefox.exe": "Mozilla Firefox / Tor Browser",
    "brave.exe": "Brave Browser",
    "opera.exe": "Opera",
    "opera_gx.exe": "Opera GX",
    "vivaldi.exe": "Vivaldi",
    "waterfox.exe": "Waterfox",
    "librewolf.exe": "LibreWolf",
    "floorp.exe": "Floorp",
    "arc.exe": "Arc Browser",
    "zen.exe": "Zen Browser",
    "thorium.exe": "Thorium Browser",
    "epic.exe": "Epic Privacy Browser",
    "tor.exe": "Tor Core Process",
    "browser.exe": "Tor/Yandex Browser"
}

# Known circumvention / VPN / Tor executables
CIRCUMVENTION_PROCESSES = [
    "tor.exe",
    "openvpn.exe",
    "wireguard.exe",
    "nordvpn.exe",
    "expressvpn.exe",
    "surfshark.exe",
    "protonvpn.exe",
    "mullvad.exe",
    "windscribe.exe",
    "psiphon3.exe",
    "lantern.exe",
    "ultrasurf.exe",
    "hotspotshield.exe"
]

# Inspection loop timing
INSPECTION_INTERVAL = 0.35  # seconds

# Security settings
MAX_PIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes
PBKDF2_ITERATIONS = 200_000

# Default configuration dictionary
DEFAULT_CONFIG = {
    "enabled": True,
    "strict_mode": True,  # Closes Tor browser / VPN circumvention tools if enabled
    "close_tab_method": "ctrl_w",  # 'ctrl_w' or 'kill_process'
    "system_hosts_sync": True,
    "disable_doh": True,
    "adult_keywords_check": True
}
