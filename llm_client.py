"""
llm_client.py — single entry point for calling the LLM, so the rest of the
backend (main.py, guardrails.py) doesn't care whether requests go direct to
Anthropic or through OpenRouter.

Swap providers with one env var, no other code changes:
    LLM_PROVIDER=anthropic   (default — calls api.anthropic.com directly)
    LLM_PROVIDER=openrouter  (routes through openrouter.ai, uses OPENROUTER_API_KEY)

CHANGE LOG vs. the version reviewed for Feature 1 (Issue Distillation)
-----------------------------------------------------------------------
Added two things for the "survive contest" feature (evidence-list.md,
infer-category.md, contest-evidence.md), neither changes existing callers:

1. `response_schema` param on call_llm(). When provided, wires to
   `output_config.format` (JSON-schema-constrained output) on the direct
   Anthropic path — verified current and GA against docs.claude.com as of
   this writing, not against a live key. Structured outputs guarantee the
   response is valid JSON matching the schema (constrained decoding, not
   prompting), which removes the "hope the model returns clean JSON" risk
   entirely for anything using it. When response_schema is set, call_llm
   returns the ALREADY-PARSED dict, not a string — check the return type
   at call sites.
   OpenRouter path: does not currently wire this through (OpenRouter's
   OpenAI-compatible layer has its own `response_format` shape, which may
   or may not map cleanly to output_config.format — unverified, flagged
   as a TODO below rather than guessed at). If you're on OpenRouter and
   need structured output today, prompt for JSON explicitly in the system
   prompt and parse defensively (strip ```json fences, try/except) at the
   call site instead of relying on this parameter.

2. `image_or_pdf_block()` helper — builds a Messages API content block
   from raw file bytes, for the file-upload flow (message screenshots,
   receipts, ACRA printouts). Only image/jpeg, image/png, image/gif,
   image/webp, and application/pdf are accepted; anything else raises,
   since the Claude API does not accept .docx/.xlsx directly (convert to
   PDF first if that's ever needed).

Everything else below (provider selection, the effort/no-temperature note)
is unchanged from the version already in the repo.

CORRECTION vs. earlier advice (kept from the original file, still true):
no `temperature` parameter on the current Messages API. Checked directly
against docs.claude.com: models released after Opus 4.6 reject any
temperature value other than 1.0. `output_config.effort` is the current
mechanism for trading off thoroughness against speed/cost, and combines
with `output_config.format` in the same object.

PRIVACY NOTE (see CLAUDE.md "Privacy & data handling")
Routing through OpenRouter adds a second administrative hop: your backend
-> OpenRouter -> Anthropic, instead of your backend -> Anthropic directly.
Confirm prompt logging is OFF in your OpenRouter account settings before
sending real dispute text (or file bytes) through it. This client also
requests per-request Zero Data Retention via `zdr=True` on that path;
verify current support for this parameter/model in OpenRouter's docs at
integration time.

File bytes follow the same "don't log, don't persist" rule as dispute
text — nothing in this module writes uploaded file bytes to disk or to a
log line. Callers in main.py must not do so either.

INSTALL
    pip install anthropic openai python-dotenv --break-system-packages

CONFIG
Create backend/.env (copy backend/.env.example) and fill in real values
yourself, directly in the file — not by typing the key into an AI chat
prompt. backend/.env is already covered by .gitignore — double check that
before ever committing.
"""

import base64
import os
from dotenv import load_dotenv

load_dotenv()  # reads backend/.env if present; real environment variables still win if both are set

PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")

ANTHROPIC_MODEL = "claude-sonnet-5"
OPENROUTER_MODEL = "anthropic/claude-sonnet-5"  # verify slug at https://openrouter.ai/anthropic if you change generations

_ACCEPTED_FILE_MEDIA_TYPES = {
    "image/jpeg": "image",
    "image/png": "image",
    "image/gif": "image",
    "image/webp": "image",
    "application/pdf": "document",
}

_anthropic_client = None
_openrouter_client = None

if PROVIDER == "anthropic":
    import anthropic

    _anthropic_client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

elif PROVIDER == "openrouter":
    from openai import OpenAI

    _openrouter_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
else:
    raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER!r} (expected 'anthropic' or 'openrouter')")


def image_or_pdf_block(file_bytes: bytes, media_type: str) -> dict:
    """Build a Messages API content block (image or document) from raw file
    bytes. Raises ValueError for any media type the Claude API doesn't
    accept directly — the caller (main.py) should turn that into a 400
    with a clear message, e.g. "convert .docx to PDF first."

    Never writes file_bytes to disk or logs them — callers must not either.
    """
    if media_type not in _ACCEPTED_FILE_MEDIA_TYPES:
        raise ValueError(
            f"Unsupported file type {media_type!r}. Claude accepts image/jpeg, "
            f"image/png, image/gif, image/webp, and application/pdf directly. "
            f"Convert other formats (e.g. .docx, .xlsx) to PDF first."
        )
    block_type = _ACCEPTED_FILE_MEDIA_TYPES[media_type]
    b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
    return {
        "type": block_type,
        "source": {"type": "base64", "media_type": media_type, "data": b64},
    }


def call_llm(
    system_prompt: str,
    messages: list[dict],
    *,
    effort: str = "high",
    max_tokens: int = 1024,
    response_schema: dict | None = None,
):
    """Returns the model's reply, regardless of provider.

    Without response_schema: returns plain text (str), same as before.
    With response_schema (direct-Anthropic path only): returns the
    ALREADY-PARSED response (dict), constrained to match the schema via
    output_config.format. Check the return type at call sites that pass
    response_schema.

    `messages` is a list of {"role": "user"|"assistant", "content": ...}
    dicts. `content` can be a plain string (existing behaviour) or a list
    of content blocks — e.g. [{"type": "text", "text": "..."}, image_or_pdf_block(...)]
    — for the file-upload flow. Both forms pass straight through to the
    underlying SDK unchanged.

    `effort` (Anthropic path only): "low" | "medium" | "high" | "xhigh" | "max".
    """

    if PROVIDER == "openrouter":
        if response_schema is not None:
            # See CHANGE LOG above — not wired through for this provider yet.
            raise NotImplementedError(
                "response_schema is not implemented for LLM_PROVIDER=openrouter. "
                "Prompt for JSON explicitly and parse defensively at the call site, "
                "or switch LLM_PROVIDER=anthropic for this endpoint."
            )
        response = _openrouter_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            extra_body={"zdr": True},  # see PRIVACY NOTE above
        )
        return response.choices[0].message.content

    # default: direct Anthropic API
    output_config: dict = {"effort": effort}
    if response_schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": response_schema}

    response = _anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
        output_config=output_config,
    )

    text = response.content[0].text

    if response_schema is not None:
        import json

        return json.loads(text)  # structured outputs guarantee this parses; not wrapped in try/except on purpose —
        # a parse failure here means the schema/response contract itself is broken and should surface loudly, not
        # be swallowed the way a free-text parsing failure would need to be.

    return text


if __name__ == "__main__":
    # Quick manual check — requires a real key for whichever provider is
    # active. Not an automated test; just confirms the wiring works before
    # you plug it into main.py.
    reply = call_llm(
        system_prompt="Reply with exactly one word: OK.",
        messages=[{"role": "user", "content": "Respond now."}],
        max_tokens=10,
    )
    print(f"Provider: {PROVIDER}")
    print(f"Reply: {reply!r}")

    if PROVIDER == "anthropic":
        schema_reply = call_llm(
            system_prompt="Return the word OK as the value field.",
            messages=[{"role": "user", "content": "Go."}],
            max_tokens=50,
            response_schema={
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
                "additionalProperties": False,
            },
        )
        print(f"Structured reply: {schema_reply!r}")
