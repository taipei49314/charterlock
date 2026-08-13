"""CLI exit codes (M3) and maturity/doctor evidence (M4)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from charterlock.cases import case_key_split_frozen, case_naive_self, case_narrowed, case_unbound_journey
from charterlock.cli import main
from charterlock.codes import EXIT_BLOCKING, EXIT_SPLIT, EXIT_UNDECIDED, EXIT_USAGE
from charterlock.doctor import run_doctor
from charterlock.export_fixtures import export_fixtures
from charterlock.maturity import run_maturity


def _write_measure_inputs(folder: Path, case: dict) -> dict[str, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    charter = folder / "charter.json"
    keyring = folder / "keyring.json"
    executor = folder / "executor.json"
    subject = folder / "subject.json"
    charter.write_text(json.dumps(case["charter"]), encoding="utf-8")
    keyring.write_text(json.dumps({"keys": case["keyring"]}), encoding="utf-8")
    executor.write_text(
        json.dumps({"executor_key_ids": case["executor_key_ids"]}),
        encoding="utf-8",
    )
    subject.write_text(json.dumps(case["subject"]), encoding="utf-8")
    return {"charter": charter, "keyring": keyring, "executor": executor, "subject": subject}


class CliExitTests(unittest.TestCase):
    def test_split_exit_0(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _write_measure_inputs(Path(tmp), case_key_split_frozen())
            code = main(
                [
                    "measure",
                    "--charter",
                    str(paths["charter"]),
                    "--keyring",
                    str(paths["keyring"]),
                    "--executor-keys",
                    str(paths["executor"]),
                    "--first-exec-at",
                    case_key_split_frozen()["first_exec_at"],
                    "--journey",
                    str(paths["subject"]),
                    "--json",
                ]
            )
            self.assertEqual(code, EXIT_SPLIT)

    def test_collapsed_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _write_measure_inputs(Path(tmp), case_naive_self())
            code = main(
                [
                    "measure",
                    "--charter",
                    str(paths["charter"]),
                    "--keyring",
                    str(paths["keyring"]),
                    "--executor-keys",
                    str(paths["executor"]),
                    "--first-exec-at",
                    case_naive_self()["first_exec_at"],
                    "--journey",
                    str(paths["subject"]),
                ]
            )
            self.assertEqual(code, EXIT_BLOCKING)

    def test_narrowed_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _write_measure_inputs(Path(tmp), case_narrowed())
            code = main(
                [
                    "measure",
                    "--charter",
                    str(paths["charter"]),
                    "--keyring",
                    str(paths["keyring"]),
                    "--executor-keys",
                    str(paths["executor"]),
                    "--first-exec-at",
                    case_narrowed()["first_exec_at"],
                    "--journey",
                    str(paths["subject"]),
                ]
            )
            self.assertEqual(code, EXIT_BLOCKING)

    def test_incomplete_exit_3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _write_measure_inputs(Path(tmp), case_unbound_journey())
            code = main(
                [
                    "measure",
                    "--charter",
                    str(paths["charter"]),
                    "--keyring",
                    str(paths["keyring"]),
                    "--executor-keys",
                    str(paths["executor"]),
                    "--first-exec-at",
                    case_unbound_journey()["first_exec_at"],
                    "--journey",
                    str(paths["subject"]),
                ]
            )
            self.assertEqual(code, EXIT_UNDECIDED)

    def test_usage_error_exit_1(self) -> None:
        code = main(["measure", "--charter", "missing.json", "--keyring", "x", "--executor-keys", "y", "--first-exec-at", "z"])
        self.assertEqual(code, EXIT_USAGE)

    def test_both_subject_flags_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _write_measure_inputs(Path(tmp), case_key_split_frozen())
            code = main(
                [
                    "measure",
                    "--charter",
                    str(paths["charter"]),
                    "--keyring",
                    str(paths["keyring"]),
                    "--executor-keys",
                    str(paths["executor"]),
                    "--first-exec-at",
                    case_key_split_frozen()["first_exec_at"],
                    "--journey",
                    str(paths["subject"]),
                    "--claim",
                    str(paths["subject"]),
                ]
            )
            self.assertEqual(code, EXIT_USAGE)


class DoctorMaturityTests(unittest.TestCase):
    def test_doctor_all_green(self) -> None:
        report = run_doctor()
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["passed"], report["total"])
        self.assertGreaterEqual(report["total"], 8)

    def test_maturity_m0_to_m4(self) -> None:
        report = run_maturity()
        self.assertTrue(report["ok"], report)
        for level in ("M0", "M1", "M2", "M3", "M4"):
            self.assertTrue(report["levels"][level]["ok"], (level, report["levels"][level]))

    def test_export_fixtures_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            written = export_fixtures(Path(tmp))
            self.assertTrue(any(p.name == "INDEX.json" for p in written))
            index = json.loads((Path(tmp) / "fixtures" / "INDEX.json").read_text(encoding="utf-8"))
            names = {row["name"] for row in index["cases"]}
            self.assertIn("naive_self", names)
            self.assertIn("narrowed", names)


if __name__ == "__main__":
    unittest.main()
