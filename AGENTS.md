# Agent notes

- Do not add runtime dependencies. Stdlib only.
- Do not emit forbidden verdicts. Do not "helpfully" map `CHARTER_SPLIT` to pass/verified/independent.
- Do not weaken fixtures to make `doctor` or `maturity` green.
- Do not parse YAML, call the network, or read the system clock inside `measure()`.
- `first_exec_at` and `executor_key_ids` stay caller observations. Do not silently fetch them from git.
- Two keys are not two people. Do not write that they are.
- Do not commit or push unless a human asked. Tests must be run before any status claim.
