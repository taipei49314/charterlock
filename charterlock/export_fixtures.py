"""Write cases/ JSON onto disk so the checkout is inspectable without importing."""

from __future__ import annotations

import json
from pathlib import Path

from charterlock.cases import all_cases, keyring


def export_fixtures(root: Path) -> list[Path]:
    fixtures = root / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    index = []
    for case in all_cases():
        folder = fixtures / case["name"]
        folder.mkdir(parents=True, exist_ok=True)
        charter_path = folder / "charter.json"
        obs_path = folder / "observations.json"
        expected_path = folder / "expected.json"
        charter_path.write_text(_dump(case["charter"]), encoding="utf-8")
        observations = {
            "executor_key_ids": case["executor_key_ids"],
            "first_exec_at": case["first_exec_at"],
            "subject_kind": case.get("subject_kind"),
            "subject": case.get("subject"),
        }
        obs_path.write_text(_dump(observations), encoding="utf-8")
        expected_path.write_text(_dump({"verdict": case["expected"]}), encoding="utf-8")
        executor_path = folder / "executor.json"
        executor_path.write_text(
            _dump({"executor_key_ids": case["executor_key_ids"]}),
            encoding="utf-8",
        )
        written.extend([charter_path, obs_path, expected_path, executor_path])
        subject = case.get("subject")
        kind = case.get("subject_kind")
        if isinstance(subject, dict) and kind in {"journey", "claim"}:
            subject_path = folder / f"{kind}.json"
            subject_path.write_text(_dump(subject), encoding="utf-8")
            written.append(subject_path)
        index.append({"name": case["name"], "expected": case["expected"]})
    (fixtures / "keyring.json").write_text(_dump({"keys": keyring()}), encoding="utf-8")
    (fixtures / "INDEX.json").write_text(_dump({"cases": index}), encoding="utf-8")
    written.append(fixtures / "keyring.json")
    written.append(fixtures / "INDEX.json")
    return written


def _dump(obj: object) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
