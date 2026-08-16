"""Encrypted vault for cover identities.

Legends live on disk during preparation, and plaintext identity files on
a seized laptop are a catastrophe. This module stores identities in a
passphrase-protected, tamper-evident vault file.

Design
------
* Key derivation: PBKDF2-HMAC-SHA256 with a random salt and a
  configurable iteration count (high by default, low in tests).
* Confidentiality: a SHA-256 counter-mode keystream XORs the serialized
  identity JSON.
* Integrity: an HMAC-SHA256 tag over magic + salt + nonce + ciphertext.
  Any tampering fails authentication before decryption is attempted.
* The vault holds many named legends in one file, each entry encrypted
  separately so adding a legend does not re-expose the others.

This is a fiction prop, not audited cryptography -- but it is real,
working code with the usual caveats.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import struct
from typing import Dict, List, Optional

__all__ = [
    "MAGIC",
    "KDF_ITERATIONS",
    "VaultError",
    "Vault",
]

MAGIC = b"COVERID-V1"

#: Default PBKDF2 cost. Tests pass a much smaller value.
KDF_ITERATIONS = 200_000

_SALT_BYTES = 16
_NONCE_BYTES = 8
_TAG_BYTES = 32


class VaultError(ValueError):
    """Raised for vault format, authentication, or usage problems."""


def _derive_keys(passphrase: str, salt: bytes, iterations: int) -> tuple:
    """Derive (encryption_key, mac_key) from the passphrase."""
    material = hashlib.pbkdf2_hmac(
        "sha256", passphrase.encode("utf-8"), salt, iterations, dklen=64)
    return material[:32], material[32:]


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    """Counter-mode SHA-256 keystream of the requested length."""
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hashlib.sha256(
            key + nonce + struct.pack(">Q", counter)).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


class Vault:
    """A passphrase-protected collection of named legends.

    Usage::

        vault = Vault()
        vault.unlock("correct horse", iterations=1000)  # new vault
        vault.put("berlin", identity_dict)
        blob = vault.save()
        ...
        vault2 = Vault.load(blob)
        vault2.unlock("correct horse", iterations=1000)
        ident = vault2.get("berlin")
    """

    def __init__(self) -> None:
        self._entries: Dict[str, bytes] = {}  # name -> ciphertext blob
        self._passphrase: Optional[str] = None
        self._iterations: int = KDF_ITERATIONS

    # -- locking / unlocking ------------------------------------------------

    def unlock(self, passphrase: str,
               iterations: int = KDF_ITERATIONS) -> None:
        """Arm the vault with a passphrase.

        For a loaded vault this also verifies every entry authenticates,
        so a wrong passphrase is caught immediately, not at first read.
        """
        if not passphrase:
            raise VaultError("passphrase must not be empty")
        self._passphrase = passphrase
        self._iterations = iterations
        for name, blob in self._entries.items():
            try:
                self._decrypt(blob)
            except VaultError:
                raise VaultError(
                    f"wrong passphrase (entry {name!r} failed authentication)")

    @property
    def locked(self) -> bool:
        return self._passphrase is None

    def _require_unlocked(self) -> str:
        if self._passphrase is None:
            raise VaultError("vault is locked; call unlock() first")
        return self._passphrase

    # -- entry crypto -------------------------------------------------------

    def _encrypt(self, plaintext: bytes) -> bytes:
        passphrase = self._require_unlocked()
        salt = os.urandom(_SALT_BYTES)
        nonce = os.urandom(_NONCE_BYTES)
        enc_key, mac_key = _derive_keys(passphrase, salt, self._iterations)
        stream = _keystream(enc_key, nonce, len(plaintext))
        ciphertext = bytes(a ^ b for a, b in zip(plaintext, stream))
        mac = hmac.new(mac_key, digestmod="sha256")
        mac.update(MAGIC)
        mac.update(salt)
        mac.update(nonce)
        mac.update(ciphertext)
        return salt + nonce + mac.digest() + ciphertext

    def _decrypt(self, blob: bytes) -> bytes:
        passphrase = self._require_unlocked()
        if len(blob) < _SALT_BYTES + _NONCE_BYTES + _TAG_BYTES:
            raise VaultError("entry too short to be valid")
        salt = blob[:_SALT_BYTES]
        nonce = blob[_SALT_BYTES:_SALT_BYTES + _NONCE_BYTES]
        tag = blob[_SALT_BYTES + _NONCE_BYTES:_SALT_BYTES + _NONCE_BYTES + _TAG_BYTES]
        ciphertext = blob[_SALT_BYTES + _NONCE_BYTES + _TAG_BYTES:]
        enc_key, mac_key = _derive_keys(passphrase, salt, self._iterations)
        mac = hmac.new(mac_key, digestmod="sha256")
        mac.update(MAGIC)
        mac.update(salt)
        mac.update(nonce)
        mac.update(ciphertext)
        if not hmac.compare_digest(mac.digest(), tag):
            raise VaultError("authentication failed")
        stream = _keystream(enc_key, nonce, len(ciphertext))
        return bytes(a ^ b for a, b in zip(ciphertext, stream))

    # -- legend management --------------------------------------------------

    def put(self, name: str, identity: Dict) -> None:
        """Store (or replace) a legend under a name."""
        if not name.strip():
            raise VaultError("legend name must not be empty")
        plaintext = json.dumps(identity, ensure_ascii=False,
                               sort_keys=True).encode("utf-8")
        self._entries[name.strip()] = self._encrypt(plaintext)

    def get(self, name: str) -> Dict:
        """Retrieve and decrypt one legend."""
        blob = self._entries.get(name.strip())
        if blob is None:
            raise VaultError(f"no legend named {name!r}")
        return json.loads(self._decrypt(blob).decode("utf-8"))

    def delete(self, name: str) -> None:
        """Remove a legend. Raises VaultError if absent."""
        if name.strip() not in self._entries:
            raise VaultError(f"no legend named {name!r}")
        del self._entries[name.strip()]

    def names(self) -> List[str]:
        """The stored legend names, sorted. Does not require unlock."""
        return sorted(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    # -- serialization ------------------------------------------------------

    def save(self) -> bytes:
        """Serialize the vault (entries stay encrypted)."""
        payload = {
            name: blob.hex() for name, blob in self._entries.items()
        }
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        return MAGIC + body

    @classmethod
    def load(cls, data: bytes) -> "Vault":
        """Parse save() output. The vault starts locked."""
        if not data.startswith(MAGIC):
            raise VaultError("not a cover-identity vault file")
        try:
            payload = json.loads(data[len(MAGIC):].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise VaultError("corrupt vault body") from exc
        vault = cls()
        for name, hexblob in payload.items():
            try:
                vault._entries[name] = bytes.fromhex(hexblob)
            except ValueError as exc:
                raise VaultError(f"corrupt entry {name!r}") from exc
        return vault
