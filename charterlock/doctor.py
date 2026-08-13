"""Run built-in cases through the measurer. Verdicts must match expected."""

from __future__ import annotations

from typing import Any

from charterlock.cases import all_cases
from charterlock.measure import measure


def run_doctor() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in all_cases():
        result = measure(
            case["charter"],
            executor_key_ids=case["executor_key_ids"],
            first_exec_at=case["first_exec_at"],
            keyring=case["keyring"],
            subject=case.get("subject"),
            subject_kind=case.get("subject_kind"),
        )
        expected = case["expected"]
        ok = result.verdict == expected and result.independence_claim == "not_claimed"
        rows.append(
            {
                "name": case["name"],
                "expected": expected,
                "got": result.verdict,
                "ok": ok,
                "reason": result.reason,
            }
        )
    passed = sum(1 for row in rows if row["ok"])
    return {
        "ok": passed == len(rows) and len(rows) > 0,
        "passed": passed,
        "total": len(rows),
        "rows": rows,
    }
