"""CLI: measure, keygen, sign, doctor, maturity. No network."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from charterlock.bind import SubjectKind
from charterlock.codes import EXIT_USAGE, exit_code_for
from charterlock.doctor import run_doctor
from charterlock.keys import generate_secret, key_id_for_secret, sign_charter
from charterlock.maturity import run_maturity
from charterlock.measure import measure


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="charterlock",
        description="Admit a charter as an exam only if the examinee did not write it.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_measure = sub.add_parser("measure", help="run the admission measurer")
    p_measure.add_argument("--charter", required=True, type=Path)
    p_measure.add_argument("--keyring", required=True, type=Path)
    p_measure.add_argument("--executor-keys", required=True, type=Path)
    p_measure.add_argument("--first-exec-at", required=True)
    p_measure.add_argument("--journey", type=Path)
    p_measure.add_argument("--claim", type=Path)
    p_measure.add_argument("--json", action="store_true")

    p_keygen = sub.add_parser("keygen", help="create one local MAC identity")
    p_keygen.add_argument("--out", required=True, type=Path)

    p_sign = sub.add_parser("sign", help="MAC-sign a charter with a keyring identity")
    p_sign.add_argument("--charter", required=True, type=Path)
    p_sign.add_argument("--keyring", required=True, type=Path)
    p_sign.add_argument("--key-id", required=True)
    p_sign.add_argument("--out", type=Path)

    p_doctor = sub.add_parser("doctor", help="run built-in fixture measures")
    p_doctor.add_argument("--json", action="store_true")

    p_mat = sub.add_parser("maturity", help="report M0–M4 evidence on this checkout")
    p_mat.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "measure":
            return _cmd_measure(args)
        if args.cmd == "keygen":
            return _cmd_keygen(args)
        if args.cmd == "sign":
            return _cmd_sign(args)
        if args.cmd == "doctor":
            return _cmd_doctor(args)
        if args.cmd == "maturity":
            return _cmd_maturity(args)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"charterlock: {exc}", file=sys.stderr)
        return EXIT_USAGE
    return EXIT_USAGE


def _cmd_measure(args: argparse.Namespace) -> int:
    if args.journey and args.claim:
        raise ValueError("pass only one of --journey or --claim")
    charter = _load_json(args.charter)
    keyring = _load_keyring(args.keyring)
    executor = _load_json(args.executor_keys)
    executor_ids = executor.get("executor_key_ids")
    if not isinstance(executor_ids, list):
        raise ValueError("executor-keys file must contain executor_key_ids: [str]")
    subject = None
    kind: SubjectKind | None = None
    if args.journey:
        subject = _load_json(args.journey)
        kind = "journey"
    elif args.claim:
        subject = _load_json(args.claim)
        kind = "claim"
    result = measure(
        charter,
        executor_key_ids=executor_ids,
        first_exec_at=args.first_exec_at,
        keyring=keyring,
        subject=subject,
        subject_kind=kind,
    )
    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2, ensure_ascii=False))
    else:
        sys.stdout.write(result.format_text())
    return exit_code_for(result.verdict)


def _cmd_keygen(args: argparse.Namespace) -> int:
    secret = generate_secret()
    kid = key_id_for_secret(secret)
    payload = {"keys": {kid: secret.hex()}}
    existing = {}
    if args.out.exists():
        existing = _load_json(args.out)
        keys = existing.get("keys")
        if not isinstance(keys, dict):
            raise ValueError("existing keyring is not a {keys: {}} object")
        keys = dict(keys)
        keys[kid] = secret.hex()
        payload = {"keys": keys}
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(kid)
    return 0


def _cmd_sign(args: argparse.Namespace) -> int:
    charter = _load_json(args.charter)
    keyring = _load_keyring(args.keyring)
    hex_secret = keyring.get(args.key_id)
    if not isinstance(hex_secret, str):
        raise ValueError(f"key-id not in keyring: {args.key_id}")
    signed = sign_charter(charter, bytes.fromhex(hex_secret))
    text = json.dumps(signed, indent=2, ensure_ascii=False) + "\n"
    target = args.out or args.charter
    target.write_text(text, encoding="utf-8")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    report = run_doctor()
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
    else:
        for row in report["rows"]:
            mark = "ok" if row["ok"] else "FAIL"
            print(f"{mark:4} {row['name']:24} expected={row['expected']} got={row['got']}")
        print(f"doctor: {report['passed']}/{report['total']}")
    return 0 if report["ok"] else 2


def _cmd_maturity(args: argparse.Namespace) -> int:
    report = run_maturity()
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
    else:
        for level, row in report["levels"].items():
            mark = "ok" if row["ok"] else "FAIL"
            print(f"{mark:4} {level}: {row['detail']}")
        print(f"maturity: {report['passed_levels']}/{report['total_levels']}")
    return 0 if report["ok"] else 2


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_keyring(path: Path) -> dict[str, str]:
    data = _load_json(path)
    keys = data.get("keys")
    if not isinstance(keys, Mapping):
        raise ValueError("keyring must contain keys: {key_id: hex_secret}")
    out: dict[str, str] = {}
    for kid, secret in keys.items():
        if not isinstance(kid, str) or not isinstance(secret, str):
            raise ValueError("keyring entries must be string key_id → hex secret")
        out[kid] = secret
    return out


if __name__ == "__main__":
    raise SystemExit(main())
