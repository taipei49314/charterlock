"""M0–M4 maturity evidence for this checkout. Declarations are not evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from charterlock.cases import all_cases
from charterlock.codes import EXIT_BLOCKING, EXIT_SPLIT, EXIT_UNDECIDED, exit_code_for
from charterlock.doctor import run_doctor

REQUIRED_DOC_PHRASES = {
    "CLAIMS_POLICY.md": (
        "Two MAC keys do not prove two people.",
        "never reports INDEPENDENT, TWO_HUMANS, SECURE, or ADMISSIBLE_FOR_PRODUCTION",
        "SPLIT is a key-and-time verdict, not an organizational verdict.",
    ),
    "THREAT_MODEL.md": (
        "caller observations",
        "Host user can mint both keys",
        "does not prove two people",
    ),
    "INVARIANTS.md": (
        "Missing observations never become CHARTER_SPLIT",
        "independence_claim is always not_claimed",
    ),
}


def repo_root() -> Path:
    here = Path(__file__).resolve().parent.parent
    return here


def run_maturity() -> dict[str, Any]:
    doctor = run_doctor()
    cases = {c["name"]: c for c in all_cases()}
    levels: dict[str, dict[str, Any]] = {}

    m0_names = {"naive_self", "missing_charter", "key_split_frozen", "narrowed"}
    m0_ok = doctor["ok"] and m0_names.issubset(cases)
    levels["M0"] = {
        "ok": m0_ok,
        "detail": "measurer + closed vocabulary + four required cases in doctor",
    }

    unbound = next(r for r in doctor["rows"] if r["name"] == "unbound_journey")
    claim = next(r for r in doctor["rows"] if r["name"] == "claim_bound")
    m1_ok = unbound["ok"] and unbound["got"] == "INCOMPLETE" and claim["ok"]
    levels["M1"] = {
        "ok": m1_ok,
        "detail": "unbound journey is INCOMPLETE; claim hash bind can SPLIT",
    }

    narrowed = next(r for r in doctor["rows"] if r["name"] == "narrowed")
    split = next(r for r in doctor["rows"] if r["name"] == "key_split_frozen")
    m2_ok = narrowed["ok"] and narrowed["got"] == "CHARTER_NARROWED" and split["got"] != "CHARTER_NARROWED"
    levels["M2"] = {
        "ok": m2_ok,
        "detail": "proper-subset must is CHARTER_NARROWED, never CHARTER_SPLIT",
    }

    m3_ok = (
        exit_code_for("CHARTER_SPLIT") == EXIT_SPLIT
        and exit_code_for("CHARTER_COLLAPSED") == EXIT_BLOCKING
        and exit_code_for("CHARTER_NARROWED") == EXIT_BLOCKING
        and exit_code_for("INCOMPLETE") == EXIT_UNDECIDED
        and exit_code_for("UNKNOWN") == EXIT_UNDECIDED
    )
    levels["M3"] = {
        "ok": m3_ok,
        "detail": "exit 0=SPLIT, 2=COLLAPSED|NARROWED, 3=INCOMPLETE|UNKNOWN",
    }

    m4_ok, m4_detail = _m4_docs()
    levels["M4"] = {"ok" : m4_ok, "detail": m4_detail}

    passed = sum(1 for row in levels.values() if row["ok"])
    return {
        "ok": passed == len(levels),
        "passed_levels": passed,
        "total_levels": len(levels),
        "levels": levels,
        "doctor": {"passed": doctor["passed"], "total": doctor["total"]},
    }


def _m4_docs() -> tuple[bool, str]:
    root = repo_root()
    missing: list[str] = []
    for filename, phrases in REQUIRED_DOC_PHRASES.items():
        path = root / filename
        if not path.is_file():
            missing.append(f"{filename} missing")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                missing.append(f"{filename} missing phrase: {phrase}")
    if missing:
        return False, "; ".join(missing)
    return True, "claims, threat model, and invariants record the one-human residual"
