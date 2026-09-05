import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic

app = FastAPI(title="MinLaw SCT Assistant API", version="1.0")

# Enable CORS so your frontend can communicate with the backend seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client (automatically reads ANTHROPIC_API_KEY from environment or Codespaces secrets)
client = anthropic.Anthropic()

class ClaimRequest(BaseModel):
    user_message: str
    conversation_history: list[dict] = []

# System prompt engineered specifically for Singapore Small Claims Tribunals guidelines & AI compliance
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
- In accordance with the Singapore Judiciary's Guide on the Use of Generative AI Tools by Court Users (Registrar’s Circular No. 1 of 2024), remind the user that generative AI is only an organizational tool and they bear ultimate legal responsibility for accuracy.
- Never use inverted commas or decorative quotation marks around arbitrary jargon; state requirements directly and explain them clearly in plain language.
"""

@app.post("/api/analyze-claim")
async def analyze_claim(payload: ClaimRequest):
    try:
        # Construct message payload including history
        messages = payload.conversation_history + [{"role": "user", "content": payload.user_message}]
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=SCT_SYSTEM_PROMPT,
            messages=messages
        )
        
        assistant_reply = response.content[0].text
        
        return {
            "status": "success",
            "reply": assistant_reply,
            "compliance_notice": "Generated output requires independent human verification pursuant to Singapore Court guidelines."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "tribunal": "Small Claims Tribunals Singapore"}