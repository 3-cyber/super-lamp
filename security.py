import os
import json
import time
import secrets
import hashlib
from typing import Tuple, Optional
from config import PIN_FILE, EXTERNAL_PIN_FILE, MAX_PIN_ATTEMPTS, LOCKOUT_DURATION_SECONDS, PBKDF2_ITERATIONS

class SecurityManager:
    def __init__(self, pin_file=PIN_FILE, external_pin_file=EXTERNAL_PIN_FILE):
        self.pin_file = pin_file
        self.external_pin_file = external_pin_file
        self._ensure_file()

    def _ensure_file(self):
        default_data = {
            "pin_hash": None,
            "salt": None,
            "recovery_key_hash": None,
            "failed_attempts": 0,
            "lockout_until": 0,
            "folder_locked": False
        }
        if not self.pin_file.exists() and not self.external_pin_file.exists():
            self._save_data(default_data)
        elif self.external_pin_file.exists() and not self.pin_file.exists():
            data = self._load_data()
            try:
                with open(self.pin_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception:
                pass

    def _load_data(self) -> dict:
        for p in [self.external_pin_file, self.pin_file]:
            try:
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception:
                continue

        return {
            "pin_hash": None,
            "salt": None,
            "recovery_key_hash": None,
            "failed_attempts": 0,
            "lockout_until": 0,
            "folder_locked": False
        }

    def _save_data(self, data: dict):
        for p in [self.pin_file, self.external_pin_file]:
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception:
                pass

    def is_pin_set(self) -> bool:
        data = self._load_data()
        return bool(data.get("pin_hash") and data.get("salt"))

    def is_folder_locked(self) -> bool:
        data = self._load_data()
        return bool(data.get("folder_locked", False))

    def set_folder_locked(self, locked: bool):
        data = self._load_data()
        data["folder_locked"] = locked
        self._save_data(data)

    def is_locked_out(self) -> Tuple[bool, int]:
        data = self._load_data()
        lockout_until = data.get("lockout_until", 0)
        now = time.time()
        if now < lockout_until:
            remaining = int(lockout_until - now)
            return True, remaining
        return False, 0

    def hash_pin(self, pin: str, salt: bytes) -> str:
        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS
        )
        return hashed.hex()

    def hash_recovery_key(self, recovery_key: str, salt: bytes) -> str:
        cleaned = recovery_key.strip().upper().replace("-", "")
        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            cleaned.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS
        )
        return hashed.hex()

    def set_pin(self, pin: str) -> Tuple[bool, str, str]:
        pin = pin.strip()
        if len(pin) < 4:
            return False, "Password must be at least 4 characters.", ""

        salt = secrets.token_bytes(16)
        pin_hash = self.hash_pin(pin, salt)

        raw_token = secrets.token_hex(12).upper()
        recovery_key = "-".join([raw_token[i:i+4] for i in range(0, len(raw_token), 4)])
        rec_hash = self.hash_recovery_key(recovery_key, salt)

        data = self._load_data()
        data["pin_hash"] = pin_hash
        data["salt"] = salt.hex()
        data["recovery_key_hash"] = rec_hash
        data["failed_attempts"] = 0
        data["lockout_until"] = 0
        self._save_data(data)

        return True, "Master password successfully configured.", recovery_key

    def verify_pin(self, pin: str) -> Tuple[bool, str]:
        is_locked, remaining = self.is_locked_out()
        if is_locked:
            return False, f"Too many failed attempts. Locked out for {remaining} more seconds."

        data = self._load_data()
        stored_hash = data.get("pin_hash")
        salt_hex = data.get("salt")

        if not stored_hash or not salt_hex:
            return False, "No password configured yet."

        salt = bytes.fromhex(salt_hex)
        computed_hash = self.hash_pin(pin.strip(), salt)

        if secrets.compare_digest(stored_hash, computed_hash):
            data["failed_attempts"] = 0
            data["lockout_until"] = 0
            self._save_data(data)
            return True, "Password verified."
        else:
            data["failed_attempts"] = data.get("failed_attempts", 0) + 1
            if data["failed_attempts"] >= MAX_PIN_ATTEMPTS:
                data["lockout_until"] = time.time() + LOCKOUT_DURATION_SECONDS
                self._save_data(data)
                return False, f"Incorrect password. 5 failed attempts reached! Locked out for {LOCKOUT_DURATION_SECONDS // 60} minutes."
            
            remaining_tries = MAX_PIN_ATTEMPTS - data["failed_attempts"]
            self._save_data(data)
            return False, f"Incorrect password. {remaining_tries} attempts remaining before temporary lockout."

    def verify_recovery_key(self, recovery_key: str) -> Tuple[bool, str]:
        data = self._load_data()
        stored_rec_hash = data.get("recovery_key_hash")
        salt_hex = data.get("salt")

        if not stored_rec_hash or not salt_hex:
            return False, "No recovery key available."

        salt = bytes.fromhex(salt_hex)
        computed_rec_hash = self.hash_recovery_key(recovery_key, salt)

        if secrets.compare_digest(stored_rec_hash, computed_rec_hash):
            data["failed_attempts"] = 0
            data["lockout_until"] = 0
            self._save_data(data)
            return True, "Recovery key verified. Lockout reset."
        else:
            return False, "Invalid recovery key."
