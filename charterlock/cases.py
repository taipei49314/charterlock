"""Built-in admission cases. Fixture JSON on disk is exported from here."""

from __future__ import annotations

from typing import Any

from charterlock.bind import subject_hash
from charterlock.keys import key_id_for_secret, sign_charter

# Fixture-only secrets. Not production keys. Documented in THREAT_MODEL.md.
SECRET_AUTHOR = bytes.fromhex("aa" * 32)
SECRET_EXECUTOR = bytes.fromhex("bb" * 32)
SECRET_THIRD = bytes.fromhex("cc" * 32)

AUTHOR_ID = key_id_for_secret(SECRET_AUTHOR)
EXECUTOR_ID = key_id_for_secret(SECRET_EXECUTOR)
THIRD_ID = key_id_for_secret(SECRET_THIRD)

MUST_A = {"type": "assertion", "id": "invoice-total-exact"}
MUST_B = {"type": "assertion", "id": "invoice-currency-twd"}

FROZEN = "2026-08-14T10:00:00+00:00"
EXEC_AFTER = "2026-08-14T12:00:00+00:00"
EXEC_BEFORE = "2026-08-14T09:00:00+00:00"


def keyring() -> dict[str, str]:
    return {
        AUTHOR_ID: SECRET_AUTHOR.hex(),
        EXECUTOR_ID: SECRET_EXECUTOR.hex(),
        THIRD_ID: SECRET_THIRD.hex(),
    }


def _unsigned(
    *,
    case_id: str,
    author_placeholder: bool = True,
    must: list[dict[str, str]] | None = None,
    journey_hash: str | None = None,
    claim_hash: str | None = None,
    frozen_at: str = FROZEN,
    extra_author: dict[str, str] | None = None,
) -> dict[str, Any]:
    author: dict[str, Any] = extra_author.copy() if extra_author else {}
    if author_placeholder:
        author.setdefault("key_id", "pending")
        author.setdefault("signature", "pending")
    return {
        "charter_version": 1,
        "id": case_id,
        "author": author,
        "frozen_at": frozen_at,
        "intent": {"must": list(must or [MUST_A, MUST_B]), "must_not": [], "non_goals": []},
        "binds": {"journey_hash": journey_hash, "claim_hash": claim_hash},
        "expiry": None,
    }


def journey_full() -> dict[str, Any]:
    return {"must": [MUST_A, MUST_B]}


def journey_narrow() -> dict[str, Any]:
    return {"must": [MUST_A]}


def _signed(case_id: str, secret: bytes, **kwargs: Any) -> dict[str, Any]:
    return sign_charter(_unsigned(case_id=case_id, **kwargs), secret)


def case_naive_self() -> dict[str, Any]:
    journey = journey_full()
    charter = _signed(
        "chr_naive_self",
        SECRET_AUTHOR,
        journey_hash=subject_hash(journey),
    )
    return {
        "name": "naive_self",
        "expected": "CHARTER_COLLAPSED",
        "charter": charter,
        "keyring": keyring(),
        "executor_key_ids": [AUTHOR_ID],
        "first_exec_at": EXEC_AFTER,
        "subject": journey,
        "subject_kind": "journey",
    }


def case_missing_charter() -> dict[str, Any]:
    return {
        "name": "missing_charter",
        "expected": "INCOMPLETE",
        "charter": {"id": "chr_missing"},
        "keyring": keyring(),
        "executor_key_ids": [EXECUTOR_ID],
        "first_exec_at": EXEC_AFTER,
        "subject": journey_full(),
        "subject_kind": "journey",
    }


def case_charter_after_work() -> dict[str, Any]:
    journey = journey_full()
    charter = _signed(
        "chr_after_work",
        SECRET_AUTHOR,
        journey_hash=subject_hash(journey),
        frozen_at=FROZEN,
    )
    return {
        "name": "charter_after_work",
        "expected": "CHARTER_COLLAPSED",
        "charter": charter,
        "keyring": keyring(),
        "executor_key_ids": [EXECUTOR_ID],
        "first_exec_at": EXEC_BEFORE,
        "subject": journey,
        "subject_kind": "journey",
    }


def case_key_split_frozen() -> dict[str, Any]:
    journey = journey_full()
    charter = _signed(
        "chr_split",
        SECRET_AUTHOR,
        journey_hash=subject_hash(journey),
    )
    return {
        "name": "key_split_frozen",
        "expected": "CHARTER_SPLIT",
        "charter": charter,
        "keyring": keyring(),
        "executor_key_ids": [EXECUTOR_ID],
        "first_exec_at": EXEC_AFTER,
        "subject": journey,
        "subject_kind": "journey",
    }


def case_unbound_journey() -> dict[str, Any]:
    journey = journey_full()
    charter = _signed("chr_unbound", SECRET_AUTHOR, journey_hash=None)
    return {
        "name": "unbound_journey",
        "expected": "INCOMPLETE",
        "charter": charter,
        "keyring": keyring(),
        "executor_key_ids": [EXECUTOR_ID],
        "first_exec_at": EXEC_AFTER,
        "subject": journey,
        "subject_kind": "journey",
    }


def case_narrowed() -> dict[str, Any]:
    journey = journey_narrow()
    charter = _signed(
        "chr_narrowed",
        SECRET_AUTHOR,
        journey_hash=subject_hash(journey),
    )
    return {
        "name": "narrowed",
        "expected": "CHARTER_NARROWED",
        "charter": charter,
        "keyring": keyring(),
        "executor_key_ids": [EXECUTOR_ID],
        "first_exec_at": EXEC_AFTER,
        "subject": journey,
        "subject_kind": "journey",
    }


def case_actor_string() -> dict[str, Any]:
    charter = _unsigned(
        case_id="chr_actor",
        author_placeholder=False,
        extra_author={"key_id": "nelson", "signature": "not-a-mac"},
        journey_hash=subject_hash(journey_full()),
    )
    return {
        "name": "actor_string",
        "expected": "UNKNOWN",
        "charter": charter,
        "keyring": keyring(),
        "executor_key_ids": [EXECUTOR_ID],
        "first_exec_at": EXEC_AFTER,
        "subject": journey_full(),
        "subject_kind": "journey",
    }


def case_claim_bound() -> dict[str, Any]:
    claim = journey_full()
    charter = _signed(
        "chr_claim",
        SECRET_AUTHOR,
        claim_hash=subject_hash(claim),
    )
    return {
        "name": "claim_bound",
        "expected": "CHARTER_SPLIT",
        "charter": charter,
        "keyring": keyring(),
        "executor_key_ids": [EXECUTOR_ID],
        "first_exec_at": EXEC_AFTER,
        "subject": claim,
        "subject_kind": "claim",
    }


def all_cases() -> list[dict[str, Any]]:
    return [
        case_naive_self(),
        case_missing_charter(),
        case_charter_after_work(),
        case_key_split_frozen(),
        case_unbound_journey(),
        case_narrowed(),
        case_actor_string(),
        case_claim_bound(),
    ]
