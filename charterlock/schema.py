"""Charter and subject shape checks. Fail closed on missing machine-readable fields."""

from __future__ import annotations

from typing import Any, Mapping

CHARTER_VERSION = 1
REQUIRED_CHARTER_KEYS = ("charter_version", "id", "author", "frozen_at", "intent", "binds")
REQUIRED_AUTHOR_KEYS = ("key_id", "signature")
REQUIRED_INTENT_KEYS = ("must",)
REQUIRED_BIND_KEYS = ("journey_hash", "claim_hash")


def _missing(required: tuple[str, ...], obj: Mapping[str, Any], prefix: str = "") -> list[str]:
    out: list[str] = []
    for key in required:
        if key not in obj:
            out.append(f"{prefix}{key}")
    return out


def missing_charter_keys(charter: Mapping[str, Any]) -> tuple[str, ...]:
    missing = _missing(REQUIRED_CHARTER_KEYS, charter)
    author = charter.get("author")
    if isinstance(author, Mapping):
        missing.extend(_missing(REQUIRED_AUTHOR_KEYS, author, "author."))
    elif "author" in charter:
        missing.append("author")
    intent = charter.get("intent")
    if isinstance(intent, Mapping):
        missing.extend(_missing(REQUIRED_INTENT_KEYS, intent, "intent."))
    elif "intent" in charter:
        missing.append("intent")
    binds = charter.get("binds")
    if isinstance(binds, Mapping):
        missing.extend(_missing(REQUIRED_BIND_KEYS, binds, "binds."))
    elif "binds" in charter:
        missing.append("binds")
    return tuple(missing)


def parse_must_ids(items: Any) -> frozenset[tuple[str, str]] | None:
    """Return (type, id) pairs, or None if the list is not machine-evaluable."""
    if not isinstance(items, list):
        return None
    ids: list[tuple[str, str]] = []
    for item in items:
        if not isinstance(item, Mapping):
            return None
        kind = item.get("type")
        ident = item.get("id")
        if not isinstance(kind, str) or not kind.strip():
            return None
        if not isinstance(ident, str) or not ident.strip():
            return None
        ids.append((kind.strip(), ident.strip()))
    return frozenset(ids)


def subject_must_list(subject: Mapping[str, Any]) -> Any:
    if "must" in subject:
        return subject.get("must")
    intent = subject.get("intent")
    if isinstance(intent, Mapping) and "must" in intent:
        return intent.get("must")
    return None
