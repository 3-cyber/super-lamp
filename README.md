# Website Blocker & System Shield

A strict, background website blocking system engineered for Windows with cryptographic access controls, anti-circumvention monitors, and zero-backdoor password enforcement.

---

## ⚡ Quick Download for Communities

Users do not need Python or any development tools installed. 

1. Download the latest **[WebsiteBlocker-Setup.exe](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY/releases/latest)**.
2. Run the installer.
3. Review the mandatory security notice and enter your chosen **Master Password**.
4. The installer automatically starts protection in the background and places shortcuts on your Desktop and Start Menu.

---

## ⚠️ Security Notice (Read Before Installing)

- **Irreversible Password Protection**: You will be prompted to set a Master Password during installation.
- **No Reset / Backdoor**: The console and settings **will never open** unless you supply this password. Protection cannot be stopped or disabled without it.
- **Emergency Recovery Key**: Upon installation, an emergency recovery key is placed in your install directory (`data/RECOVERY_KEY_IMPORTANT.txt`). Save this key in a secure place.

---

## 🛠 Features

- **Automated Tab Closure**: Scans browser titles and URLs in real-time and closes prohibited content instantly (`Ctrl+W` / API).
- **Multi-Browser Support**: Chrome, Edge, Firefox, Brave, Opera, Opera GX, Vivaldi, Tor Browser, and more.
- **Anti-Circumvention Engine**: Automatically detects and terminates unauthorized VPNs, proxies, and bypass tunnels.
- **DNS-over-HTTPS (DoH) Blocking & Hosts Sync**: Prevents DNS bypasses directly through Windows policies and local resolver control.
- **Zero-Setup Installer**: Everything is bundled into a single standalone installer.

---

## 🚀 Building From Source

If you want to compile the installer yourself:

```powershell
# 1. Install requirements
pip install -r requirements.txt

# 2. Compile standalone binary
pyinstaller --noconfirm --onedir --console --name "WebsiteBlocker" --add-data "data;data" main.py

# 3. Compile Inno Setup installer
iscc installer.iss
```

The resulting installer will be located at `../dist-installer/WebsiteBlocker-Setup.exe`.
