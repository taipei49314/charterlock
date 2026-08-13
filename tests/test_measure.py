"""Measurer cases. Every README verdict claim is asserted here."""

from __future__ import annotations

import unittest

from charterlock.cases import (
    AUTHOR_ID,
    EXECUTOR_ID,
    all_cases,
    case_actor_string,
    case_charter_after_work,
    case_claim_bound,
    case_key_split_frozen,
    case_missing_charter,
    case_naive_self,
    case_narrowed,
    case_unbound_journey,
    keyring,
)
from charterlock.codes import FORBIDDEN_VERDICTS, VERDICTS
from charterlock.keys import sign_charter
from charterlock.measure import INDEPENDENCE_CLAIM, measure


def _run(case: dict) -> object:
    return measure(
        case["charter"],
        executor_key_ids=case["executor_key_ids"],
        first_exec_at=case["first_exec_at"],
        keyring=case["keyring"],
        subject=case.get("subject"),
        subject_kind=case.get("subject_kind"),
    )


class MeasureCasesTests(unittest.TestCase):
    def test_every_built_in_case(self) -> None:
        for case in all_cases():
            with self.subTest(case["name"]):
                result = _run(case)
                self.assertEqual(result.verdict, case["expected"])
                self.assertEqual(result.independence_claim, INDEPENDENCE_CLAIM)
                self.assertNotIn(result.verdict, FORBIDDEN_VERDICTS)
                self.assertIn(result.verdict, VERDICTS)

    def test_naive_self_is_collapsed(self) -> None:
        result = _run(case_naive_self())
        self.assertEqual(result.verdict, "CHARTER_COLLAPSED")
        self.assertIn("executor_key_ids", result.reason)

    def test_missing_is_incomplete(self) -> None:
        result = _run(case_missing_charter())
        self.assertEqual(result.verdict, "INCOMPLETE")
        self.assertTrue(result.missing_keys)

    def test_time_order_collapse(self) -> None:
        result = _run(case_charter_after_work())
        self.assertEqual(result.verdict, "CHARTER_COLLAPSED")
        self.assertIn("frozen_at", result.reason)

    def test_split_requires_bind_and_two_mac_keys(self) -> None:
        result = _run(case_key_split_frozen())
        self.assertEqual(result.verdict, "CHARTER_SPLIT")
        self.assertEqual(result.author_key_id, AUTHOR_ID)
        self.assertNotEqual(result.author_key_id, EXECUTOR_ID)

    def test_unbound_journey_incomplete(self) -> None:
        self.assertEqual(_run(case_unbound_journey()).verdict, "INCOMPLETE")

    def test_narrowed_is_not_split(self) -> None:
        result = _run(case_narrowed())
        self.assertEqual(result.verdict, "CHARTER_NARROWED")
        self.assertNotEqual(result.verdict, "CHARTER_SPLIT")

    def test_actor_string_is_unknown(self) -> None:
        self.assertEqual(_run(case_actor_string()).verdict, "UNKNOWN")

    def test_claim_bind_can_split(self) -> None:
        self.assertEqual(_run(case_claim_bound()).verdict, "CHARTER_SPLIT")

    def test_bad_signature_incomplete(self) -> None:
        case = case_key_split_frozen()
        charter = dict(case["charter"])
        author = dict(charter["author"])
        author["signature"] = "00" * 32
        charter["author"] = author
        result = measure(
            charter,
            executor_key_ids=case["executor_key_ids"],
            first_exec_at=case["first_exec_at"],
            keyring=case["keyring"],
            subject=case["subject"],
            subject_kind=case["subject_kind"],
        )
        self.assertEqual(result.verdict, "INCOMPLETE")

    def test_empty_must_incomplete(self) -> None:
        case = case_key_split_frozen()
        unsigned = dict(case["charter"])
        intent = dict(unsigned["intent"])
        intent["must"] = []
        unsigned["intent"] = intent
        signed = sign_charter(unsigned, bytes.fromhex(keyring()[AUTHOR_ID]))
        result = measure(
            signed,
            executor_key_ids=case["executor_key_ids"],
            first_exec_at=case["first_exec_at"],
            keyring=case["keyring"],
            subject=case["subject"],
            subject_kind=case["subject_kind"],
        )
        self.assertEqual(result.verdict, "INCOMPLETE")

    def test_split_does_not_claim_two_humans(self) -> None:
        result = _run(case_key_split_frozen())
        self.assertEqual(result.independence_claim, "not_claimed")
        self.assertEqual(result.principal_kind, "mac_key")
        self.assertEqual(result.observation_source, "caller")
        blob = result.format_text()
        for word in FORBIDDEN_VERDICTS:
            self.assertNotIn(f"VERDICT: {word}", blob)


if __name__ == "__main__":
    unittest.main()
