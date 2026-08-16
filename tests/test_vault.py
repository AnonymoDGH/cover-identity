"""Tests for cover_identity.vault -- encrypted legend storage."""

from __future__ import annotations

import pytest

from cover_identity import generate
from cover_identity.vault import MAGIC, Vault, VaultError

IT = 1000  # fast KDF for tests


def _vault():
    v = Vault()
    v.unlock("correct horse", iterations=IT)
    return v


def test_put_get_roundtrip():
    v = _vault()
    ident = generate(seed=42)
    v.put("berlin", ident)
    assert v.get("berlin") == ident


def test_multiple_legends():
    v = _vault()
    a = generate(seed=1)
    b = generate(seed=2)
    v.put("alpha", a)
    v.put("beta", b)
    assert v.get("alpha") == a
    assert v.get("beta") == b
    assert len(v) == 2
    assert v.names() == ["alpha", "beta"]


def test_locked_vault_refuses_operations():
    v = Vault()
    with pytest.raises(VaultError):
        v.put("x", {"name": "y"})
    assert v.locked


def test_empty_passphrase_rejected():
    v = Vault()
    with pytest.raises(VaultError):
        v.unlock("", iterations=IT)


def test_empty_name_rejected():
    v = _vault()
    with pytest.raises(VaultError):
        v.put("   ", {"name": "y"})


def test_get_missing_raises():
    v = _vault()
    with pytest.raises(VaultError):
        v.get("ghost")


def test_delete():
    v = _vault()
    v.put("alpha", generate(seed=1))
    v.delete("alpha")
    assert len(v) == 0
    with pytest.raises(VaultError):
        v.delete("alpha")


def test_save_load_roundtrip():
    v = _vault()
    ident = generate(seed=7)
    v.put("oslo", ident)
    blob = v.save()
    assert blob.startswith(MAGIC)

    v2 = Vault.load(blob)
    assert v2.locked
    assert v2.names() == ["oslo"]
    v2.unlock("correct horse", iterations=IT)
    assert v2.get("oslo") == ident


def test_wrong_passphrase_detected_on_unlock():
    v = _vault()
    v.put("oslo", generate(seed=7))
    blob = v.save()
    v2 = Vault.load(blob)
    with pytest.raises(VaultError, match="wrong passphrase"):
        v2.unlock("wrong horse", iterations=IT)


def test_tampered_ciphertext_detected():
    import json
    v = _vault()
    v.put("oslo", generate(seed=7))
    # Tamper with the ciphertext bytes themselves (not the JSON framing):
    # flip one hex digit in the stored entry so the HMAC no longer matches.
    body = json.loads(v.save()[len(MAGIC):].decode("utf-8"))
    name = next(iter(body))
    hexblob = body[name]
    flipped = ("0" if hexblob[-1] != "0" else "1")
    body[name] = hexblob[:-1] + flipped
    tampered = MAGIC + json.dumps(body, sort_keys=True).encode("utf-8")
    v2 = Vault.load(tampered)
    with pytest.raises(VaultError):
        v2.unlock("correct horse", iterations=IT)


def test_bad_magic_rejected():
    with pytest.raises(VaultError):
        Vault.load(b"NOT-A-VAULT")


def test_corrupt_body_rejected():
    with pytest.raises(VaultError):
        Vault.load(MAGIC + b"{not json")


def test_ciphertext_differs_from_plaintext():
    v = _vault()
    ident = generate(seed=3)
    v.put("x", ident)
    blob = v.save()
    # The plaintext name should not appear in the encrypted blob.
    assert ident["name"].encode("utf-8") not in blob


def test_replace_existing():
    v = _vault()
    v.put("x", {"name": "first"})
    v.put("x", {"name": "second"})
    assert v.get("x") == {"name": "second"}
    assert len(v) == 1
