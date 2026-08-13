# Threat model

## What this tool is for

Refuse to treat a journey or phaseledger-style claim as an exam when the examinee wrote the charter, wrote it after work started, or narrowed the machine-readable `must` set.

## Trust boundary

`first_exec_at` and `executor_key_ids` are caller observations. charterlock does not read clocks, git, or the network. A lying caller can move timestamps or omit their own key.

Host user can mint both keys. Two MAC identities on one disk do not prove two people.

HMAC-SHA256 is a local MAC. It is not Unasked DSSE, not Ed25519, and not a public attestation plane.

## In scope

- Missing or unparseable charter fields → `INCOMPLETE`
- Charter MAC that does not verify against the supplied keyring → `INCOMPLETE`
- `frozen_at >= first_exec_at` → `CHARTER_COLLAPSED`
- `author.key_id` ∈ `executor_key_ids` → `CHARTER_COLLAPSED`
- Subject present but `binds.journey_hash` / `binds.claim_hash` missing or mismatched → `INCOMPLETE`
- Subject `must` a proper subset of charter `intent.must` → `CHARTER_NARROWED`
- Non-MAC actor strings → `UNKNOWN`

## Out of scope

- Proving organizational independence or absence of collusion
- Finding unknown bugs
- Replacing RepoPassport verify, greenwash, phaseledger advance, or Unasked `VERIFIED`
- Parsing RepoPassport YAML (subjects are JSON; the operator projects a journey if needed)
- Semantic equivalence of prose goals (only `{type, id}` sets)
- Protecting secrets on a compromised host
- Multi-user network service

## Residual risk

Time and executor membership can be forged if the caller lies. Binding those observations is the job of an external ledger (phaseledger / Unasked), not this measurer.

Narrowing is set inclusion of `(type, id)`. Renaming an assertion id evades `CHARTER_NARROWED`. That is a schema discipline problem, not a solved semantic one.

does not prove two people — this sentence is load-bearing for maturity M4.
