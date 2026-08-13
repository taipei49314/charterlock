# Invariants

These are enforced by tests, not by tone.

1. Missing observations never become CHARTER_SPLIT.
2. The same MAC `key_id` on the charter and in `executor_key_ids` never becomes `CHARTER_SPLIT`.
3. A charter with `frozen_at` at or after `first_exec_at` never becomes `CHARTER_SPLIT`.
4. A subject whose `must` set is a proper subset of the charter's `must` never becomes `CHARTER_SPLIT`.
5. The verdict vocabulary is closed: only the five names in `charterlock.codes.VERDICTS`.
6. independence_claim is always not_claimed.
7. `principal_kind` is always `mac_key`. `observation_source` is always `caller`.
8. Exit codes cannot upgrade a blocking or undecided verdict to `0`.
