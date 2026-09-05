"""
guardrails_contest.py — additional checks for the "survive contest" step
(contest-evidence.md), layered on top of the existing guardrails.py rather
than duplicating it.

WHAT'S NEW HERE VS. guardrails.py
guardrails.py already catches outcome prediction, validity judgment, fault/
liability assertions, legal classification, gap-test failures, and generic
advice-giving — all still apply to this step's free-text fields (document,
what_it_shows, notes, inconsistency text, still_cannot_show) and are reused
below via scan_for_leakage(), not reimplemented.

This module adds two things regex can't give you elsewhere:

1. ROW EDITORIALIZING — this step's own specific failure mode. A row is
   supposed to say what a document IS, never what it MEANS for the
   claimant ("this helps you", "this weakens their excuse"). Not covered
   by the base categories because it's specific to table-row commentary.

2. EXACT-MATCH VALIDATION OF STOCK EXCUSES — not a regex at all. The rule
   "copy the fixed excuse list word for word" is a string-equality check,
   not a pattern match, and Python can enforce it with total reliability
   instead of hoping the model complied. This is the same "don't trust an
   LLM to verify an LLM" principle CLAUDE.md already states, applied with
   a stronger tool than regex where one is actually available.

USAGE
    from guardrails import scan_for_leakage
    from guardrails_contest import scan_row_editorializing, validate_excuse_usage

    flags = []
    flags += scan_for_leakage(json.dumps(parsed_response))          # reuse base rules
    flags += scan_row_editorializing(parsed_response)
    flags += validate_excuse_usage(parsed_response, category_key)

Same discipline as guardrails.py: log flags, do not silently rewrite the
model's output, and don't oversell this as exhaustive.
"""

import re
from dataclasses import dataclass

from stock_excuses import excuses_for


@dataclass
class ContestFlag:
    category: str
    detail: str


ROW_EDITORIALIZING_PATTERNS = [
    re.compile(r"\bthis (helps|hurts|weakens|strengthens|supports|undermines)\b", re.I),
    re.compile(r"\b(good|bad|helpful|unhelpful) for (you|your (case|claim))\b", re.I),
    re.compile(r"\bthis (is|looks) (favou?rable|unfavou?rable)\b", re.I),
]

ARGUED_POSITION_PATTERNS = [
    re.compile(r"\byou (should|could|might want to) (say|argue|tell the tribunal)\b", re.I),
    re.compile(r"\bwhen asked,? (say|respond|argue)\b", re.I),
]


def scan_row_editorializing(parsed: dict) -> list[ContestFlag]:
    """Scan the row-level free-text fields for commentary on what a document
    means, rather than what it is. Takes the already-parsed JSON response
    (from output_config.format, so this should already be well-formed)."""
    flags: list[ContestFlag] = []
    text_fields: list[tuple[str, str]] = []

    for row in parsed.get("new_rows", []):
        text_fields.append((f"new_rows[{row.get('row_number')}].what_it_shows", row.get("what_it_shows", "")))
        text_fields.append((f"new_rows[{row.get('row_number')}].document", row.get("document", "")))

    for field_name, text in text_fields:
        for pattern in ROW_EDITORIALIZING_PATTERNS + ARGUED_POSITION_PATTERNS:
            for match in pattern.finditer(text):
                flags.append(ContestFlag(category="row_editorializing", detail=f"{field_name}: {match.group(0)!r}"))

    return flags


def validate_excuse_usage(parsed: dict, category_key: str) -> list[ContestFlag]:
    """For every row claiming to use a stock excuse (source_type ==
    'common_position'), check source_text matches the canonical list for
    this category EXACTLY. A near-miss (paraphrase, added punctuation,
    merged excuses) is flagged, not silently accepted or corrected."""
    flags: list[ContestFlag] = []
    canonical = set(excuses_for(category_key))

    for row in parsed.get("new_rows", []):
        if row.get("source_type") == "common_position":
            text = row.get("source_text", "")
            if text not in canonical:
                flags.append(
                    ContestFlag(
                        category="excuse_tampering",
                        detail=f"row {row.get('row_number')}: {text!r} does not exactly match any excuse for category {category_key!r}",
                    )
                )

    return flags


def renumber_new_rows(parsed: dict, start_at: int) -> dict:
    """Backend-enforced row numbering — do not trust the model's own count.
    Overwrites row_number sequentially starting at start_at, preserving the
    model's own ordering. Mutates and returns the same dict."""
    for i, row in enumerate(parsed.get("new_rows", [])):
        row["row_number"] = start_at + i
    return parsed
