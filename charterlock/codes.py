"""Closed verdict and exit-code vocabulary. Do not extend casually."""

from __future__ import annotations

VERDICTS = (
    "CHARTER_SPLIT",
    "CHARTER_COLLAPSED",
    "CHARTER_NARROWED",
    "INCOMPLETE",
    "UNKNOWN",
)

FORBIDDEN_VERDICTS = (
    "INDEPENDENT",
    "TWO_HUMANS",
    "SECURE",
    "ADMISSIBLE_FOR_PRODUCTION",
    "PASS",
    "VERIFIED",
)

# Hook-friendly process codes (M3).
EXIT_SPLIT = 0
EXIT_USAGE = 1
EXIT_BLOCKING = 2  # COLLAPSED or NARROWED
EXIT_UNDECIDED = 3  # INCOMPLETE or UNKNOWN

BLOCKING_VERDICTS = frozenset({"CHARTER_COLLAPSED", "CHARTER_NARROWED"})
UNDECIDED_VERDICTS = frozenset({"INCOMPLETE", "UNKNOWN"})


def exit_code_for(verdict: str) -> int:
    if verdict == "CHARTER_SPLIT":
        return EXIT_SPLIT
    if verdict in BLOCKING_VERDICTS:
        return EXIT_BLOCKING
    if verdict in UNDECIDED_VERDICTS:
        return EXIT_UNDECIDED
    return EXIT_USAGE
