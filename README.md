# Ultimate Porn Blocker

[![Release](https://img.shields.io/github/v/release/YOUR_USERNAME/Ultimate-Porn-Blocker?label=Latest%20Version&logo=windows)](https://github.com/YOUR_USERNAME/Ultimate-Porn-Blocker/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?logo=windows)](https://github.com/YOUR_USERNAME/Ultimate-Porn-Blocker)

A strict, background anti-pornography system engineered for Windows with zero-backdoor password enforcement, anti-circumvention monitors, DoH blocking, and automated tab closure across all major browsers.

---

## ⚡ Quick Download for Communities

Users do not need Python or any development tools installed. 

1. Download the single installer: **[UltimatePornBlocker-Setup.exe](https://github.com/YOUR_USERNAME/Ultimate-Porn-Blocker/releases/latest)**.
2. Run the installer with administrator privileges.
3. Review the mandatory security notice and enter your chosen **Master Password**.
4. The installer automatically starts protection in the background and places shortcuts on your Desktop and Start Menu.

---

## ⚠️ Security Notice (Read Before Installing)

- **Irreversible Password Protection**: You will be prompted to set a Master Password during installation.
- **No Reset / Backdoor**: The console and settings **will never open** unless you supply this password. Protection cannot be stopped or disabled without it.
- **Emergency Recovery Key**: Upon installation, an emergency recovery key is generated and stored in your installation folder (`data/RECOVERY_KEY_IMPORTANT.txt`). Save this key in a secure place.

---

## 🛡️ How It Protects

- **Real-Time Tab & Window Inspection**: Continuously monitors active web tabs across Chrome, Edge, Firefox, Brave, Opera, Opera GX, Vivaldi, and Tor. Any attempt to access adult content instantly closes the tab (`Ctrl+W` / API).
- **Anti-Circumvention Engine**: Automatically detects and terminates unauthorized VPNs, proxies, and bypass tunnels (Tor, Psiphon, Lantern, etc.).
- **DNS-over-HTTPS (DoH) Blocking**: Forces system DNS policies to prevent browsers from resolving around your network filters.
- **Dedicated Adult Blocklist**: Pre-loaded with ~75,000 verified adult domains with regular online updates (general websites like Civitai, YouTube, Google, Reddit, and GitHub are strictly whitelisted and never blocked).
- **Single-Click Setup**: Everything needed to run is bundled into one clean installer with uninstaller support.

---

## 🚀 Building From Source

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Compile standalone binary
pyinstaller --noconfirm --onedir --console --name "UltimatePornBlocker" --add-data "data;data" main.py

# 3. Compile Inno Setup installer
iscc installer.iss
```

The resulting installer will be located at `../dist-installer/UltimatePornBlocker-Setup.exe`.
