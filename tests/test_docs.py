"""Documentation contracts. M4 is evidence in files, not a badge."""

from __future__ import annotations

import unittest
from pathlib import Path

from charterlock.codes import FORBIDDEN_VERDICTS, VERDICTS
from charterlock.maturity import REQUIRED_DOC_PHRASES, repo_root

ROOT = repo_root()


class DocContractTests(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        for name in (
            "README.md",
            "LICENSE",
            "SECURITY.md",
            "AGENTS.md",
            "CLAIMS_POLICY.md",
            "THREAT_MODEL.md",
            "INVARIANTS.md",
        ):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_required_phrases(self) -> None:
        for filename, phrases in REQUIRED_DOC_PHRASES.items():
            text = (ROOT / filename).read_text(encoding="utf-8")
            for phrase in phrases:
                with self.subTest(filename=filename, phrase=phrase):
                    self.assertIn(phrase, text)

    def test_readme_lists_closed_vocabulary(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for verdict in VERDICTS:
            self.assertIn(verdict, text)
        for banned in ("INDEPENDENT", "TWO_HUMANS", "SECURE", "ADMISSIBLE_FOR_PRODUCTION"):
            self.assertNotRegex(text, rf"`{banned}`")

    def test_readme_does_not_claim_release(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("pre-alpha", text)
        self.assertIn("no Release", text)


if __name__ == "__main__":
    unittest.main()
