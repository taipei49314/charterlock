# charterlock

**A journey is not an exam if the examinee wrote it.**

Local admission gate in front of RepoPassport / phaseledger. It does not verify that a journey worked. It answers whether that journey is allowed to count as an exam.

> Status: **pre-alpha**. no Release tag, no PyPI package.  
> Two MAC keys do not prove two people. `independence_claim` is always `not_claimed`.

[![CI](https://github.com/taipei49314/charterlock/actions/workflows/ci.yml/badge.svg)](https://github.com/taipei49314/charterlock/actions/workflows/ci.yml)

## Verdicts (closed)

| Verdict | Meaning |
|---|---|
| `CHARTER_SPLIT` | Charter MAC-verified, frozen before `first_exec_at`, author key ∉ executor set, subject hash bound when a subject is supplied |
| `CHARTER_COLLAPSED` | Same key wrote and sat the exam, or the charter was frozen at/after first execution |
| `CHARTER_NARROWED` | Keys and time are split, but the subject's `must` set is a proper subset of the charter |
| `INCOMPLETE` | Missing fields, bad MAC, or unbound subject (fail-closed) |
| `UNKNOWN` | Observations exist but principals are not MAC identities |

The tool never emits a sixth prettier word. See [CLAIMS_POLICY.md](CLAIMS_POLICY.md).

## Why this is not RepoPassport

RepoPassport asks: did the **declared** journey work?  
charterlock asks: was that journey **allowed to be the exam**?

Greenwash watches tests. Unasked watches who may say a finding is verified. phaseledger watches phase advance. None of them refuse an agent-written `repo-passport.yml`.

## Install / run

Python 3.11+. Zero runtime dependencies.

```bash
git clone https://github.com/taipei49314/charterlock.git
cd charterlock
python -m pip install -e .

python -m charterlock doctor
python -m charterlock maturity
python -m charterlock measure \
  --charter fixtures/key_split_frozen/charter.json \
  --keyring fixtures/keyring.json \
  --executor-keys fixtures/key_split_frozen/executor.json \
  --first-exec-at 2026-08-14T12:00:00+00:00 \
  --journey fixtures/key_split_frozen/journey.json
```

`measure` needs a journey/claim JSON object with a `must` list. The `--executor-keys` file must be `{"executor_key_ids":[...]}`. The fixture `observations.json` files hold both; copy the key list into a dedicated file for real use.

Hook exit codes (M3):

| Code | Meaning |
|---|---|
| 0 | `CHARTER_SPLIT` |
| 2 | `CHARTER_COLLAPSED` or `CHARTER_NARROWED` |
| 3 | `INCOMPLETE` or `UNKNOWN` |
| 1 | usage or I/O error |

## Maturity (this checkout)

Run, do not quote this table from memory:

```bash
python -m charterlock maturity --json
```

| Level | Question |
|---|---|
| M0 | Measurer + closed vocabulary + required cases |
| M1 | Unbound journey is `INCOMPLETE`; claim hash can bind |
| M2 | Proper-subset `must` is `CHARTER_NARROWED` |
| M3 | Exit codes as above |
| M4 | Claims / threat model / invariants record the one-human residual |

## What it will not do

- Replace RepoPassport verify
- Sign an Unasked verified-status
- Prove two humans, two organizations, or no collusion
- Parse YAML, call the network, or trust the system clock

## Docs

- [CLAIMS_POLICY.md](CLAIMS_POLICY.md)
- [THREAT_MODEL.md](THREAT_MODEL.md)
- [INVARIANTS.md](INVARIANTS.md)
- [AGENTS.md](AGENTS.md)
- [SECURITY.md](SECURITY.md)

## License

Apache-2.0
