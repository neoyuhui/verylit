from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from llm_client import call_llm
from guardrails import scan_for_leakage

app = FastAPI(title="MinLaw SCT Assistant API", version="1.0")

# Enable CORS so the extension can talk to this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NOTE: this repo is currently flat (no backend/ or docs/prompts/ subfolders
# yet — see CLAUDE.md "Repo layout"), so both the test page and the prompt
# file are loaded from right next to this main.py.
BASE_DIR = Path(__file__).resolve().parent


@app.get("/", response_class=HTMLResponse)
async def serve_test_ui():
    """Plain test-chat page for Feature 1 — not the Chrome extension, just a
    same-origin webpage so there's something to actually run and click
    through today. Open the forwarded port 8000 URL in a browser."""
    return (BASE_DIR / "index.html").read_text(encoding="utf-8")


def load_prompt(filename: str) -> str:
    return (BASE_DIR / filename).read_text(encoding="utf-8")


ISSUE_DISTILLATION_PROMPT = load_prompt("issue-distillation.md")

# Kept from the original prototype for the later structured-interview feature.
SCT_SYSTEM_PROMPT = """
You are a neutral structuring assistant for self-represented persons (SRPs) navigating the Small Claims Tribunals (SCT) of Singapore under the State Courts.

Your objective is to help users organize their facts, evidence, and claims while strictly mitigating confirmation bias and hallucinations. You must adhere to the following operational boundaries:

1. JURISDICTION & BOUNDARIES:
- The SCT default claim limit is S$20,000, which can rise to S$30,000 if both parties sign a Memorandum of Consent.
- Eligible disputes include contracts for the sale of goods, provision of services, residential tenancies not exceeding 2 years, and property damage (excluding motor vehicle accidents).
- Employment claims, neighbour disputes, and claims exceeding the financial cap do not belong in the SCT. Explicitly flag if a user's claim falls outside these parameters.

2. BEHAVIOR & TONE:
- Maintain strict neutrality. Never validate a user's assumptions or tell them they will win or lose.
- Ask clarifying questions one at a time to gather timeline details, monetary amounts, and physical evidence (e.g., invoices, text logs, receipts).
- Do not cite fake case laws or external statutes. Stick strictly to the parameters of the Small Claims Tribunals Act 1984.

3. COMPLIANCE & DISCLAIMER MANDATE:
- In accordance with the Singapore Judiciary's Guide on the Use of Generative AI Tools by Court Users (Registrar's Circular No. 1 of 2024), remind the user that generative AI is only an organizational tool and they bear ultimate legal responsibility for accuracy.
- Never use inverted commas or decorative quotation marks around arbitrary jargon; state requirements directly and explain them clearly in plain language.
"""

COMPLIANCE_NOTICE = "Generated output requires independent human verification pursuant to Singapore Court guidelines."


class DistillRequest(BaseModel):
    user_message: str  # the full free-text account; edits/re-runs just resend this, extended


class ClaimRequest(BaseModel):
    user_message: str
    conversation_history: list[dict] = []


@app.post("/api/distill-issue")
async def distill_issue(payload: DistillRequest):
    """Feature 1 — Issue Distillation. Stateless: one free-text message in, one structured problem statement out."""
    try:
        reply = call_llm(
            ISSUE_DISTILLATION_PROMPT,
            [{"role": "user", "content": payload.user_message}],
        )

        flags = scan_for_leakage(reply)
        if flags:
            # Log the categories only — never the user's dispute text. See CLAUDE.md "Privacy & data handling".
            print(f"[guardrail] {len(flags)} flag(s): {[f.category for f in flags]}")

        return {
            "status": "success",
            "reply": reply,
            "guardrail_flags": [f.category for f in flags],  # internal QA field; drop before a public-facing demo if you don't want it visible
            "compliance_notice": COMPLIANCE_NOTICE,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-claim")
async def analyze_claim(payload: ClaimRequest):
    """Original prototype endpoint, kept for the later structured-interview feature. Now routed through llm_client too."""
    try:
        messages = payload.conversation_history + [{"role": "user", "content": payload.user_message}]
        reply = call_llm(SCT_SYSTEM_PROMPT, messages)

        return {
            "status": "success",
            "reply": reply,
            "compliance_notice": COMPLIANCE_NOTICE,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "healthy", "tribunal": "Small Claims Tribunals Singapore"}
