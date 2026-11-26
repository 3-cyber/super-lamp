import os
import sys
import io
import json
import zipfile
import secrets
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
VAULT_FILE = BASE_DIR / "vault.enc"
EXTERNAL_VAULT_UNLOCKER = PARENT_DIR / "Unlock_Vault.bat"

# Files excluded from being deleted during encryption
EXCLUDED_NAMES = {
    "vault.enc",
    "vault.py",
    "Unlock_Vault.bat",
    "__pycache__",
    ".git"
}

def derive_aes_key(passphrase: str, salt: bytes) -> bytes:
    """Derives a 256-bit (32-byte) AES key using PBKDF2-HMAC-SHA256 with 600,000 rounds."""
    clean_pass = passphrase.strip().replace("-", "").upper()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    return kdf.derive(clean_pass.encode("utf-8"))

class VaultManager:
    def __init__(self, target_dir=BASE_DIR):
        self.target_dir = Path(target_dir)
        self.vault_file = self.target_dir / "vault.enc"

    def is_vault_locked(self) -> bool:
        return self.vault_file.exists()

    def lock_vault(self, secret_key: str) -> tuple[bool, str]:
        """
        Compresses all files in the project folder, encrypts them with AES-256-GCM,
        writes vault.enc, and securely removes plaintext source files.
        """
        secret_key = secret_key.strip()
        cleaned_key = secret_key.replace("-", "")
        if len(cleaned_key) < 8:
            return False, "Key is too short. Must be at least 8 characters (or your 24-character recovery key)."

        try:
            # 1. Compress directory to memory buffer
            zip_buffer = io.BytesIO()
            files_to_remove = []

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(self.target_dir):
                    dirs[:] = [d for d in dirs if d not in EXCLUDED_NAMES]
                    for file in files:
                        if file in EXCLUDED_NAMES:
                            continue
                        full_path = Path(root) / file
                        rel_path = full_path.relative_to(self.target_dir)
                        zf.write(full_path, arcname=str(rel_path))
                        files_to_remove.append(full_path)

            plaintext_data = zip_buffer.getvalue()
            if not plaintext_data:
                return False, "No files found to encrypt."

            # 2. Derive AES-256 key
            salt = secrets.token_bytes(16)
            aes_key = derive_aes_key(secret_key, salt)

            # 3. Encrypt with AES-256-GCM (Authenticated Encryption)
            aesgcm = AESGCM(aes_key)
            nonce = secrets.token_bytes(12)  # Standard 96-bit nonce for GCM
            ciphertext = aesgcm.encrypt(nonce, plaintext_data, None)

            # Container format: [7 bytes magic] + [16 bytes salt] + [12 bytes nonce] + [ciphertext + tag]
            with open(self.vault_file, "wb") as f:
                f.write(b"VAULTv1")
                f.write(salt)
                f.write(nonce)
                f.write(ciphertext)

            # 4. Remove plaintext files (except vault.py so unlocker script can run)
            for fpath in files_to_remove:
                try:
                    fpath.unlink()
                except Exception:
                    pass

            # Clean empty directories
            for root, dirs, files in os.walk(self.target_dir, topdown=False):
                for d in dirs:
                    dpath = Path(root) / d
                    try:
                        dpath.rmdir()
                    except Exception:
                        pass

            # 5. Create external unlock batch in parent directory
            self._create_external_unlocker()

            return True, "AES-256 Vault locked! Plaintext files securely wiped. Only encrypted vault.enc remains."

        except Exception as e:
            return False, f"Failed to lock vault: {e}"

    def unlock_vault(self, secret_key: str) -> tuple[bool, str]:
        """
        Decrypts vault.enc with AES-256-GCM and unpacks all files back to the project folder.
        """
        if not self.vault_file.exists():
            return False, "No encrypted vault (vault.enc) found."

        try:
            with open(self.vault_file, "rb") as f:
                magic = f.read(7)
                if magic != b"VAULTv1":
                    return False, "Corrupted or unrecognized vault file format."
                salt = f.read(16)
                nonce = f.read(12)
                ciphertext = f.read()

            # Derive AES-256 key
            aes_key = derive_aes_key(secret_key, salt)
            aesgcm = AESGCM(aes_key)

            try:
                # Decrypt and authenticate
                decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            except Exception:
                return False, "AUTHENTICATION FAILED: Incorrect key or corrupted vault. Access denied."

            # Unpack files
            zip_buffer = io.BytesIO(decrypted_bytes)
            with zipfile.ZipFile(zip_buffer, "r") as zf:
                zf.extractall(self.target_dir)

            # Remove vault.enc
            try:
                self.vault_file.unlink()
            except Exception:
                pass

            return True, "AES-256 Vault unlocked and all files restored successfully!"

        except Exception as e:
            return False, f"Error unlocking vault: {e}"

    def _create_external_unlocker(self):
        """Creates Unlock_Vault.bat in the parent directory."""
        bat_content = f"""@echo off
title Unlock AES-256 Vault
cls
echo ========================================================
echo             UNLOCK AES-256 ENCRYPTED VAULT
echo ========================================================
echo.
echo Enter your 24-character secret key or recovery key.
echo Example: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
echo.
set /p KEY="Secret Key: "

python "%~dp0Website blocker\\vault.py" unlock "%KEY%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Decryption failed. Please verify your secret key.
) else (
    echo.
    echo [SUCCESS] Vault unlocked! Opening folder...
    start "" "%~dp0Website blocker"
)

echo.
pause
"""
        try:
            EXTERNAL_VAULT_UNLOCKER.write_text(bat_content, encoding="utf-8")
        except Exception:
            pass

def main():
    vm = VaultManager()
    if len(sys.argv) > 1 and sys.argv[1].lower() == "lock":
        key = ""
        if len(sys.argv) > 2:
            key = sys.argv[2]
        else:
            key = input("Enter your 24-character secret key to encrypt the vault: ").strip()
        ok, msg = vm.lock_vault(key)
        print(msg)
        sys.exit(0 if ok else 1)
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "unlock":
        key = ""
        if len(sys.argv) > 2:
            key = sys.argv[2]
        else:
            key = input("Enter your 24-character secret key to decrypt the vault: ").strip()
        ok, msg = vm.unlock_vault(key)
        print(msg)
        sys.exit(0 if ok else 1)
    else:
        print(f"Vault Status: {'LOCKED (Encrypted with AES-256)' if vm.is_vault_locked() else 'UNLOCKED'}")
        print("Usage: python vault.py [lock|unlock]")

if __name__ == "__main__":
    main()
