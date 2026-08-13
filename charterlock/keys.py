"""Local HMAC-SHA256 MAC identities. Not people. Not public-key attestation."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from typing import Mapping

from charterlock.canonical import canonical_json

KEY_PREFIX = "hmac-sha256:"
_KEY_ID_RE = re.compile(r"^hmac-sha256:[0-9a-f]{64}$")


def key_id_for_secret(secret: bytes) -> str:
    if not isinstance(secret, (bytes, bytearray)) or len(secret) < 32:
        raise ValueError("secret must be at least 32 bytes")
    return KEY_PREFIX + hashlib.sha256(bytes(secret)).hexdigest()


def generate_secret() -> bytes:
    return os.urandom(32)


def is_mac_key_id(key_id: str) -> bool:
    return isinstance(key_id, str) and bool(_KEY_ID_RE.match(key_id))


def unsigned_charter(charter: Mapping[str, object]) -> dict[str, object]:
    payload = dict(charter)
    author = payload.get("author")
    if isinstance(author, Mapping):
        payload["author"] = {k: v for k, v in author.items() if k != "signature"}
    return payload


def sign_charter(charter: Mapping[str, object], secret: bytes) -> dict[str, object]:
    """Return a copy of charter with author.key_id and author.signature set."""
    kid = key_id_for_secret(secret)
    body = unsigned_charter(charter)
    author = dict(body.get("author") or {})
    author["key_id"] = kid
    body["author"] = author
    signature = hmac.new(
        bytes(secret),
        canonical_json(body).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    author_signed = dict(author)
    author_signed["signature"] = signature
    out = dict(body)
    out["author"] = author_signed
    return out


def verify_charter_signature(charter: Mapping[str, object], secret: bytes) -> bool:
    author = charter.get("author")
    if not isinstance(author, Mapping):
        return False
    claimed_id = author.get("key_id")
    claimed_sig = author.get("signature")
    if claimed_id != key_id_for_secret(secret):
        return False
    if not isinstance(claimed_sig, str) or len(claimed_sig) != 64:
        return False
    body = unsigned_charter(charter)
    expected = hmac.new(
        bytes(secret),
        canonical_json(body).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, claimed_sig)


def secret_from_keyring(keyring: Mapping[str, str], key_id: str) -> bytes | None:
    if not isinstance(keyring, Mapping):
        return None
    hex_secret = keyring.get(key_id)
    if not isinstance(hex_secret, str):
        return None
    try:
        secret = bytes.fromhex(hex_secret)
    except ValueError:
        return None
    if len(secret) < 32:
        return None
    if key_id_for_secret(secret) != key_id:
        return None
    return secret
