# Security

charterlock is a local admission measurer. It has no server, no account, and no network client.

## Report a vulnerability

Open a private GitHub security advisory on `taipei49314/charterlock`. Do not file a public issue for key-handling or signature bugs.

## What this is not

This tool does not sandbox the caller, does not hide MAC secrets, and does not protect a compromised operator account. Fixture keyrings in `fixtures/keyring.json` are published test secrets. Do not reuse them.

## Capability notes

- `keygen` writes hex secrets to a caller-chosen path. That file is the trust root.
- `measure` needs the author secret in the keyring to verify a charter MAC. Without it the verdict is `INCOMPLETE`, not `CHARTER_SPLIT`.
