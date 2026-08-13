"""Deterministic charter admission measurer.

Same inputs → same MeasureResult. Missing observations are INCOMPLETE.
A CHARTER_SPLIT never claims two people.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from charterlock.bind import SubjectKind, bind_matches
from charterlock.canonical import digest_obj
from charterlock.codes import FORBIDDEN_VERDICTS, VERDICTS
from charterlock.keys import is_mac_key_id, secret_from_keyring, verify_charter_signature
from charterlock.schema import CHARTER_VERSION, missing_charter_keys, parse_must_ids, subject_must_list

INDEPENDENCE_CLAIM = "not_claimed"
OBSERVATION_SOURCE = "caller"
PRINCIPAL_KIND = "mac_key"


@dataclass(frozen=True)
class MeasureResult:
    verdict: str
    reason: str
    charter_id: str | None
    author_key_id: str | None
    observation_digest: str
    missing_keys: tuple[str, ...] = ()
    independence_claim: str = INDEPENDENCE_CLAIM
    observation_source: str = OBSERVATION_SOURCE
    principal_kind: str = PRINCIPAL_KIND
    bound_field: str | None = None
    bound_hash: str | None = None
    computed_subject_hash: str | None = None

    def __post_init__(self) -> None:
        if self.verdict not in VERDICTS:
            raise ValueError(f"verdict outside vocabulary: {self.verdict!r}")
        if self.verdict in FORBIDDEN_VERDICTS:
            raise ValueError(f"forbidden verdict: {self.verdict!r}")
        if self.independence_claim != INDEPENDENCE_CLAIM:
            raise ValueError("independence_claim must remain not_claimed")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["missing_keys"] = list(self.missing_keys)
        return d

    def format_text(self) -> str:
        lines = [
            f"VERDICT: {self.verdict}",
            f"reason: {self.reason}",
            f"charter_id: {self.charter_id or ''}",
            f"author_key_id: {self.author_key_id or ''}",
            f"independence_claim: {self.independence_claim}",
            f"observation_source: {self.observation_source}",
            f"principal_kind: {self.principal_kind}",
            f"observation_digest: {self.observation_digest}",
        ]
        if self.missing_keys:
            lines.append(f"missing_keys: {','.join(self.missing_keys)}")
        if self.bound_field:
            lines.append(f"bound_field: {self.bound_field}")
            lines.append(f"bound_hash: {self.bound_hash or ''}")
            lines.append(f"computed_subject_hash: {self.computed_subject_hash or ''}")
        return "\n".join(lines) + "\n"


def measure(
    charter: Mapping[str, Any],
    *,
    executor_key_ids: Sequence[str],
    first_exec_at: str,
    keyring: Mapping[str, str],
    subject: Mapping[str, Any] | None = None,
    subject_kind: SubjectKind | None = None,
) -> MeasureResult:
    """Admit or refuse a charter as an exam for a journey/claim.

    ``executor_key_ids`` and ``first_exec_at`` are caller observations. This
    function does not read clocks, git, or the network.
    """
    if not isinstance(charter, Mapping):
        raise TypeError("charter must be a mapping")

    digest = digest_obj(
        {
            "charter": dict(charter),
            "executor_key_ids": list(executor_key_ids),
            "first_exec_at": first_exec_at,
            "subject": dict(subject) if isinstance(subject, Mapping) else None,
            "subject_kind": subject_kind,
        }
    )

    def result(
        verdict: str,
        reason: str,
        *,
        missing: tuple[str, ...] = (),
        author_key_id: str | None = None,
        bound_field: str | None = None,
        bound_hash: str | None = None,
        computed: str | None = None,
    ) -> MeasureResult:
        cid = charter.get("id")
        return MeasureResult(
            verdict=verdict,
            reason=reason,
            charter_id=cid if isinstance(cid, str) else None,
            author_key_id=author_key_id,
            observation_digest=digest,
            missing_keys=missing,
            bound_field=bound_field,
            bound_hash=bound_hash,
            computed_subject_hash=computed,
        )

    missing = missing_charter_keys(charter)
    if missing:
        return result(
            "INCOMPLETE",
            "missing required charter keys (fail-closed)",
            missing=missing,
        )

    if charter.get("charter_version") != CHARTER_VERSION:
        return result(
            "INCOMPLETE",
            f"unsupported charter_version: {charter.get('charter_version')!r}",
        )

    charter_id = charter.get("id")
    if not isinstance(charter_id, str) or not charter_id.strip():
        return result("INCOMPLETE", "id must be a non-empty string")

    frozen_raw = charter.get("frozen_at")
    frozen_at = _parse_iso8601(frozen_raw)
    exec_at = _parse_iso8601(first_exec_at)
    if frozen_at is None:
        return result("INCOMPLETE", "frozen_at is not a parseable ISO-8601 timestamp")
    if exec_at is None:
        return result("INCOMPLETE", "first_exec_at is not a parseable ISO-8601 timestamp")

    author = charter["author"]
    assert isinstance(author, Mapping)
    author_key_id = author.get("key_id")
    signature = author.get("signature")
    if not isinstance(author_key_id, str) or not author_key_id:
        return result("INCOMPLETE", "author.key_id missing")
    if not isinstance(signature, str) or not signature:
        return result("INCOMPLETE", "author.signature missing", author_key_id=author_key_id)

    if not is_mac_key_id(author_key_id):
        # Actor strings and other schemes cannot be split as MAC principals.
        return result(
            "UNKNOWN",
            "author.key_id is not a hmac-sha256 MAC identity; cannot decide a split",
            author_key_id=author_key_id,
        )

    if not isinstance(keyring, Mapping):
        return result(
            "INCOMPLETE",
            "keyring is required to verify the charter MAC",
            author_key_id=author_key_id,
        )
    secret = secret_from_keyring(keyring, author_key_id)
    if secret is None:
        return result(
            "INCOMPLETE",
            "author.key_id is not present in the keyring or does not match its secret",
            author_key_id=author_key_id,
        )
    if not verify_charter_signature(charter, secret):
        return result(
            "INCOMPLETE",
            "charter MAC signature did not verify",
            author_key_id=author_key_id,
        )

    intent = charter["intent"]
    assert isinstance(intent, Mapping)
    charter_must = parse_must_ids(intent.get("must"))
    if charter_must is None:
        return result(
            "INCOMPLETE",
            "intent.must is not a machine-evaluable list of {type, id}",
            author_key_id=author_key_id,
        )
    if len(charter_must) == 0:
        return result(
            "INCOMPLETE",
            "intent.must is empty; a charter with no machine must is not an exam",
            author_key_id=author_key_id,
        )

    if frozen_at >= exec_at:
        return result(
            "CHARTER_COLLAPSED",
            "charter frozen_at is at or after first_exec_at (exam written after work started)",
            author_key_id=author_key_id,
        )

    exec_ids = _normalize_key_ids(executor_key_ids)
    if exec_ids is None:
        return result(
            "INCOMPLETE",
            "executor_key_ids must be a list of strings",
            author_key_id=author_key_id,
        )
    if not exec_ids:
        return result(
            "UNKNOWN",
            "no executor MAC identities supplied; cannot test author ≠ executor",
            author_key_id=author_key_id,
        )
    if any(not is_mac_key_id(k) for k in exec_ids):
        return result(
            "UNKNOWN",
            "executor_key_ids contains a non-MAC identity; cannot decide a split",
            author_key_id=author_key_id,
        )
    if author_key_id in exec_ids:
        return result(
            "CHARTER_COLLAPSED",
            "author.key_id is in executor_key_ids (examinee wrote the exam)",
            author_key_id=author_key_id,
        )

    bound_field = None
    bound_hash = None
    computed = None
    if subject is not None or subject_kind is not None:
        if subject is None or subject_kind is None:
            return result(
                "INCOMPLETE",
                "subject and subject_kind must be supplied together",
                author_key_id=author_key_id,
            )
        if not isinstance(subject, Mapping):
            return result(
                "INCOMPLETE",
                "subject must be a mapping",
                author_key_id=author_key_id,
            )
        ok, bound_hash, computed = bind_matches(charter, subject, subject_kind)
        bound_field = "journey_hash" if subject_kind == "journey" else "claim_hash"
        if not ok:
            return result(
                "INCOMPLETE",
                f"{bound_field} is missing, null, or does not match the subject hash",
                author_key_id=author_key_id,
                bound_field=bound_field,
                bound_hash=bound_hash,
                computed=computed,
            )

        subject_must = parse_must_ids(subject_must_list(subject))
        if subject_must is None:
            return result(
                "INCOMPLETE",
                "subject.must is not a machine-evaluable list of {type, id}",
                author_key_id=author_key_id,
                bound_field=bound_field,
                bound_hash=bound_hash,
                computed=computed,
            )
        if subject_must < charter_must:
            return result(
                "CHARTER_NARROWED",
                "subject must-set is a proper subset of charter intent.must",
                author_key_id=author_key_id,
                bound_field=bound_field,
                bound_hash=bound_hash,
                computed=computed,
            )

    return result(
        "CHARTER_SPLIT",
        "charter MAC-verified, frozen before first_exec_at, author key not in executor set"
        + ("; subject hash bound" if subject is not None else ""),
        author_key_id=author_key_id,
        bound_field=bound_field,
        bound_hash=bound_hash,
        computed=computed,
    )


def _parse_iso8601(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _normalize_key_ids(value: Sequence[str]) -> list[str] | None:
    if isinstance(value, (str, bytes)):
        return None
    try:
        items = list(value)
    except TypeError:
        return None
    out: list[str] = []
    for item in items:
        if not isinstance(item, str):
            return None
        out.append(item)
    return out
