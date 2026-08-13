"""On-disk fixtures must match the in-code cases. Doctor is not enough."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from charterlock.maturity import repo_root
from charterlock.measure import measure

ROOT = repo_root()
FIXTURES = ROOT / "fixtures"


class DiskFixtureTests(unittest.TestCase):
    def test_index_and_each_case(self) -> None:
        self.assertTrue((FIXTURES / "INDEX.json").is_file(), "run export before commit")
        index = json.loads((FIXTURES / "INDEX.json").read_text(encoding="utf-8"))
        keyring = json.loads((FIXTURES / "keyring.json").read_text(encoding="utf-8"))["keys"]
        for row in index["cases"]:
            with self.subTest(row["name"]):
                folder = FIXTURES / row["name"]
                charter = json.loads((folder / "charter.json").read_text(encoding="utf-8"))
                obs = json.loads((folder / "observations.json").read_text(encoding="utf-8"))
                expected = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
                result = measure(
                    charter,
                    executor_key_ids=obs["executor_key_ids"],
                    first_exec_at=obs["first_exec_at"],
                    keyring=keyring,
                    subject=obs.get("subject"),
                    subject_kind=obs.get("subject_kind"),
                )
                self.assertEqual(result.verdict, expected["verdict"])
                self.assertEqual(result.independence_claim, "not_claimed")
