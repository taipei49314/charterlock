"""Bind a journey or phaseledger-style claim to a charter by canonical hash."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from charterlock.canonical import digest_obj

SubjectKind = Literal["journey", "claim"]


def subject_hash(subject: Mapping[str, Any]) -> str:
    """SHA-256 of canonical JSON. This is the only bind algorithm."""
    return digest_obj(dict(subject))


def expected_bind_field(kind: SubjectKind) -> str:
    if kind == "journey":
        return "journey_hash"
    if kind == "claim":
        return "claim_hash"
    raise ValueError(f"unsupported subject kind: {kind!r}")


def bind_matches(
    charter: Mapping[str, Any],
    subject: Mapping[str, Any],
    kind: SubjectKind,
) -> tuple[bool, str | None, str]:
    """Return (ok, bound_value, computed_hash).

    A null or missing bind is not a match. Comparison is exact string equality
    on the hex digest — no prefix stripping, no case folding.
    """
    binds = charter.get("binds")
    computed = subject_hash(subject)
    if not isinstance(binds, Mapping):
        return False, None, computed
    field = expected_bind_field(kind)
    bound = binds.get(field)
    if not isinstance(bound, str) or not bound:
        return False, bound if isinstance(bound, str) else None, computed
    return bound == computed, bound, computed
