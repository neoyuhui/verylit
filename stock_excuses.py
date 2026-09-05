"""
stock_excuses.py — canonical list of common opposing-party positions per SCT
claim category, used by the "survive contest" step (contest-evidence.md).

WHY A SEPARATE MODULE
These strings must be copied into model output EXACTLY, never reworded,
added to, or dropped (see contest-evidence.md "Use the stock excuses exactly
as written"). Keeping them in one Python dict — rather than pasted only into
the prompt text — means:
  1. The category enum used in the JSON schema (infer-category) and the
     excuse list injected into the contest-evidence prompt both derive from
     this one dict, so they can't drift out of sync.
  2. guardrails_contest.py can validate the model's output against this list
     by exact string match, instead of trusting the model to have copied
     correctly.

STATUS (per CLAUDE.md's own honesty convention): these lines were drafted
from the hackathon team's doc, itself noted as "drafted from general
knowledge... should be checked against statute or reviewed by a
practitioner before launch." Treat as demo-ready, not launch-ready.
"""

STOCK_EXCUSES: dict[str, dict[str, object]] = {
    "goods_buyer": {
        "label": "Sale of goods — you are the buyer",
        "excuses": [
            "I delivered what you ordered.",
            "It wasn't defective when you got it.",
            "You inspected it and accepted it.",
            "You damaged it after delivery.",
            "You waited too long to complain.",
            "I offered a repair or replacement and you refused.",
            "You're claiming more than you're owed.",
        ],
    },
    "goods_seller": {
        "label": "Sale of goods — you are the seller",
        "excuses": [
            "You never delivered, or delivered late.",
            "What you delivered wasn't what we agreed.",
            "I already paid.",
            "We never agreed a price.",
            "I cancelled before delivery.",
            "You're claiming more than you're owed.",
        ],
    },
    "services_customer": {
        "label": "Provision of services — you are the customer",
        "excuses": [
            "I did the work we agreed.",
            "I never promised any particular standard or result.",
            "You accepted the work.",
            "You waited too long to complain.",
            "You changed the scope or the instructions.",
            "You caused the problem yourself.",
            "You haven't paid in full.",
            "You're claiming more than you're owed.",
        ],
    },
    "services_provider": {
        "label": "Provision of services — you are the provider",
        "excuses": [
            "You didn't do the work, or didn't do it properly.",
            "We never agreed a price.",
            "I already paid.",
            "I never received an invoice.",
            "I cancelled and you did no work.",
            "You're claiming more than you're owed.",
        ],
    },
    "property_damage": {
        "label": "Damage to property",
        "excuses": [
            "The damage was already there.",
            "Someone else caused it.",
            "I wasn't careless.",
            "You agreed to it, or contributed to it.",
            "The repair cost is excessive.",
            "The property isn't yours.",
            "You're claiming more than you're owed.",
        ],
    },
    "tenancy_tenant": {
        "label": "Residential tenancy (up to 2 years) — you are the tenant",
        "excuses": [
            "I kept the deposit for damage or unpaid rent.",
            "The damage was more than fair wear and tear.",
            "You broke the lease early.",
            "You didn't give proper notice.",
            "You returned the place in poor condition.",
            "You're claiming more than you're owed.",
        ],
    },
    "tenancy_landlord": {
        "label": "Residential tenancy (up to 2 years) — you are the landlord",
        "excuses": [
            "I paid the rent.",
            "That's fair wear and tear.",
            "The damage was already there.",
            "You didn't do the repairs you were supposed to.",
            "I gave proper notice.",
            "You kept the deposit and I owe nothing more.",
            "You're claiming more than you're owed.",
        ],
    },
    "unfair_practice": {
        "label": "Unfair practice (Consumer Protection (Fair Trading) Act)",
        "excuses": [
            "I never said anything false or misleading.",
            "I told you the relevant facts before you signed.",
            "You didn't rely on what I said.",
            "That was my opinion, not a statement of fact.",
            "You didn't suffer any loss.",
            "You're claiming more than you're owed.",
        ],
    },
    "vehicle_deposit": {
        "label": "Refund of motor vehicle deposit",
        "excuses": [
            "I refunded it.",
            "You cancelled for a reason the regulations don't cover.",
            "The deposit went towards the purchase price.",
            "You agreed to bear those costs.",
            "You're claiming more than you're owed.",
        ],
    },
}


def category_enum() -> list[str]:
    """Keys usable directly as a JSON-schema enum for category inference."""
    return list(STOCK_EXCUSES.keys())


def category_choices_text() -> str:
    """Human-readable numbered list of categories, for the inference prompt."""
    lines = []
    for key, entry in STOCK_EXCUSES.items():
        lines.append(f"- {key}: {entry['label']}")
    return "\n".join(lines)


def excuses_for(category_key: str) -> list[str]:
    if category_key not in STOCK_EXCUSES:
        raise KeyError(f"Unknown category key: {category_key!r}")
    return list(STOCK_EXCUSES[category_key]["excuses"])


def excuses_block_for(category_key: str) -> str:
    """Formatted for direct injection into the contest-evidence system prompt."""
    excuses = excuses_for(category_key)
    return "\n".join(f'- "{e}"' for e in excuses)
