# Claims policy

This repository may claim only what a measurer run on a clean checkout has produced.

## Allowed statements

- A named case produced one of: `CHARTER_SPLIT`, `CHARTER_COLLAPSED`, `CHARTER_NARROWED`, `INCOMPLETE`, `UNKNOWN`.
- `independence_claim` is always `not_claimed`.
- Exit codes: `0` = `CHARTER_SPLIT`, `2` = `CHARTER_COLLAPSED` or `CHARTER_NARROWED`, `3` = `INCOMPLETE` or `UNKNOWN`, `1` = usage or I/O error.
- MAC identities are `hmac-sha256:` plus the SHA-256 of a local secret. They are not people.

## Forbidden statements

charterlock never reports INDEPENDENT, TWO_HUMANS, SECURE, or ADMISSIBLE_FOR_PRODUCTION as a verdict or as a derived claim.

Two MAC keys do not prove two people.

SPLIT is a key-and-time verdict, not an organizational verdict.

A green `doctor` or `maturity` run is evidence about this checkout's fixtures. It is not evidence that a stranger's charter is honest, and it is not Unasked `VERIFIED`.

## Residual (M4)

A single operator can mint both MAC keys, supply both `first_exec_at` and `executor_key_ids`, and still obtain `CHARTER_SPLIT`. That result remains `independence_claim: not_claimed`. Organizational independence is an external audit responsibility, not a charterlock output.
