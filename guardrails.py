"""
guardrails.py — automated leakage scanner for the Issue Distillation feature.

WHAT THIS IS
Every rule this checks for is already stated in docs/prompts/issue-distillation.md.
This file does not add new rules — it's a cheap, deterministic second check that
the model actually followed them, run AFTER generation and BEFORE the response
reaches the user.

WHY REGEX, NOT A SECOND MODEL CALL
A second Claude call could catch paraphrased violations a regex would miss, but:
  - it adds latency + cost + another network call that can fail live at a demo
  - it's an LLM checking an LLM, which shares failure modes with the thing it's
    checking (CLAUDE.md's own hard rules say "never let one AI answer verify
    another" for user-facing legal claims — the same caution applies here)
  - it can't be read and verified by a human the way a fixed pattern list can
For a 1.5-day build where you explicitly want to be able to validate the
checker yourself, deterministic regex is the right tool.

WHAT THIS WILL NOT CATCH (be honest about this, don't oversell it)
  - Paraphrased violations that don't match any pattern below
    (e.g. "it really seems like he broke his end of the deal" instead of
    "he is in breach")
  - Violations split across a sentence boundary the regex doesn't span
This is a floor, not a guarantee. Treat every flag as "go read this line,"
and periodically read a sample of UNFLAGGED output too.

KNOWN FALSE-POSITIVE RISK
The prompt legitimately quotes the user's own words in the "Inferences
detected" section — if the user said something like "he told me I'm not
entitled to it," that legitimate quote can trip the same patterns as a
model-generated conclusion. For the hackathon: don't auto-block on a flag,
just log it and eyeball it. Building quote-aware scoping is a fast-follow,
not MVP.

USAGE
    from guardrails import scan_for_leakage
    flags = scan_for_leakage(model_output_text)
    if flags:
        print(f"[guardrail] {len(flags)} flag(s): {[f.category for f in flags]}")
        # log flags somewhere you'll actually look during dev/demo rehearsal —
        # do NOT use this to silently rewrite the model's text.

VALIDATE IT YOURSELF
    python guardrails.py
runs the checker against one clean example and one deliberate violation per
category, and prints CAUGHT/MISSED for each so you can see exactly what the
pattern set does and doesn't catch before you trust it.
"""

import re
from dataclasses import dataclass


@dataclass
class LeakageFlag:
    category: str
    pattern: str
    matched_text: str
    start: int
    end: int


# Each category is a distinct way the "reformat only, no conclusions" rule
# can be violated. Add to these lists as you find real misses during testing —
# that's the intended workflow, not a one-time setup.
PATTERNS: dict[str, list[re.Pattern]] = {
    "outcome_prediction": [
        re.compile(r"\byou (will|would|should)( likely| probably)? (win|lose|succeed|fail)\b", re.I),
        re.compile(r"\b(guarantee(d)?|no doubt|certainly) (you|your claim|this)\b", re.I),
    ],
    "validity_judgment": [
        re.compile(r"\byou have a (good|strong|weak|solid|great) (case|claim|argument)\b", re.I),
        re.compile(r"\byour (case|claim|argument) (is|looks|seems) (strong|weak|valid|invalid|solid)\b", re.I),
    ],
    "fault_liability_assertion": [
        re.compile(
            r"\b(he|she|they|the (other party|respondent|landlord|tenant|photographer|company|business|seller|buyer))\s+"
            r"(is|was|are|were)\s+(liable|at fault|in breach|negligent|responsible)\b",
            re.I,
        ),
    ],
    "legal_classification": [
        re.compile(
            r"\bthis (is|looks like|appears to be) a "
            r"(breach of contract|defective goods|unpaid payment|tenancy|contract|negligence) "
            r"(claim|dispute|case|issue)\b",
            re.I,
        ),
    ],
    "gap_test_failure": [
        # This is the prompt's own "gap test" — if a Gap sentence reads this
        # way instead of "you have not shown/mentioned/recorded", it's a
        # legal issue leaking through the reformat-only rule.
        re.compile(r"\bthe (question|issue) is whether\b", re.I),
        re.compile(r"\bwhether (a |the )?(contract|agreement) (was|is) (formed|breached|valid)\b", re.I),
    ],
    "advice_giving": [
        re.compile(r"\bI (recommend|advise|suggest) (that )?you (file|sue|claim|proceed)\b", re.I),
    ],
}


def scan_for_leakage(text: str) -> list[LeakageFlag]:
    """Scan generated output for phrases that likely violate the
    reformat-only / no-conclusions rules. Returns a list of flags —
    empty means clean, or at least, nothing this pattern set catches."""
    flags: list[LeakageFlag] = []
    for category, patterns in PATTERNS.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                flags.append(
                    LeakageFlag(
                        category=category,
                        pattern=pattern.pattern,
                        matched_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                    )
                )
    return flags


if __name__ == "__main__":
    clean_example = """
    You state that the photographer attributed the poor photographs to a
    health condition he did not disclose. You have not mentioned whether
    this was said in writing. Locate any message in which he gave this
    explanation and screenshot it in full, with the date visible.
    """

    violation_examples = {
        "outcome_prediction": "Based on this, you will likely win your claim.",
        "validity_judgment": "You have a strong case here.",
        "fault_liability_assertion": "The landlord is liable for the damage.",
        "legal_classification": "This looks like a breach of contract claim.",
        "gap_test_failure": "The question is whether a contract was formed.",
        "advice_giving": "I recommend you file the claim immediately.",
    }

    print("=== Clean text (expect: no flags) ===")
    result = scan_for_leakage(clean_example)
    if result:
        for f in result:
            print(f"  FALSE POSITIVE [{f.category}]: {f.matched_text!r}")
    else:
        print("  OK — 0 flags")

    print("\n=== One deliberate violation per category (expect: CAUGHT every time) ===")
    for label, text in violation_examples.items():
        result = scan_for_leakage(text)
        status = "CAUGHT" if any(f.category == label for f in result) else "MISSED"
        print(f"  [{status}] {label}: {text!r}")
