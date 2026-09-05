"""
llm_client.py — single entry point for calling the LLM, so the rest of the
backend (main.py, guardrails.py) doesn't care whether requests go direct to
Anthropic or through OpenRouter.

Swap providers with one env var, no other code changes:
    LLM_PROVIDER=anthropic   (default — calls api.anthropic.com directly)
    LLM_PROVIDER=openrouter  (routes through openrouter.ai, uses OPENROUTER_API_KEY)

WHY THIS EXISTS
OpenRouter serves Claude Sonnet 5 at anthropic/claude-sonnet-5 through an
OpenAI-compatible chat completions endpoint (https://openrouter.ai/api/v1),
so switching is a different SDK and a different response shape, not a
different product. This wrapper hides that difference from the rest of the
codebase, and means you can flip back to a direct Anthropic key in one env
var change if OpenRouter has a rough moment during the live demo, or the
credit runs out mid-hackathon.

CORRECTION vs. earlier advice: no `temperature` parameter anymore.
An earlier version of this file passed `temperature=0.3` on every call, on
the assumption that lower temperature would make rule-following (the gap
test, no-conclusions) more consistent. Checked against the installed
`anthropic` SDK directly (`pip show anthropic` / inspecting
`messages.create`'s signature) rather than assumed from memory — the
current Messages API has no `temperature`, `top_p`, or `top_k` parameter at
all. In its place is `output_config={"effort": ...}` (low/medium/high/xhigh/
max), which controls how much effort the model puts in rather than
sampling randomness — for a rule-dense task like this, higher effort is the
closer analog to what "low temperature" was trying to achieve, so that's
what's used below. This was caught by actually running the code against
the real SDK rather than trusting the earlier plan — worth doing the same
for anything else in this file before trusting it further.

PRIVACY NOTE (see CLAUDE.md "Privacy & data handling")
Routing through OpenRouter adds a second administrative hop: your backend
-> OpenRouter -> Anthropic, instead of your backend -> Anthropic directly.
OpenRouter does not log prompts by default, but "default" is a dashboard
setting, not a law of physics — confirm prompt logging is OFF in your
OpenRouter account settings before sending real dispute text through it.
This client also requests per-request Zero Data Retention via `zdr=True`
below; verify current support for this parameter/model in OpenRouter's docs
at integration time, since ZDR coverage varies by provider and can change.

INSTALL
    pip install anthropic openai python-dotenv --break-system-packages

CONFIG
Create backend/.env (copy backend/.env.example) and fill in real values
yourself, directly in the file — not by typing the key into an AI chat
prompt (Cline, Claude, or otherwise). Anything you paste into an agent's
chat becomes part of that conversation, which may be logged by whichever
provider powers that agent. backend/.env is already covered by .gitignore
— double check that before ever committing.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads backend/.env if present; real environment variables still win if both are set

PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")

ANTHROPIC_MODEL = "claude-sonnet-5"
OPENROUTER_MODEL = "anthropic/claude-sonnet-5"  # verify slug at https://openrouter.ai/anthropic if you change generations

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


def call_llm(
    system_prompt: str,
    messages: list[dict],
    *,
    effort: str = "high",
    max_tokens: int = 1024,
) -> str:
    """Returns the model's reply as plain text, regardless of provider.

    `messages` is a list of {"role": "user"|"assistant", "content": str}
    dicts — pass a single-item list for a stateless one-shot call (Feature 1),
    or conversation history + the new turn for a stateful call (the original
    analyze-claim endpoint).

    `effort` (Anthropic path only): "low" | "medium" | "high" | "xhigh" | "max".
    Higher effort costs more tokens/latency but should follow a rule-dense
    prompt like this one more reliably — not verified against a live key yet,
    so treat "high" as a starting point to test, not a settled choice.
    """

    if PROVIDER == "openrouter":
        # OpenRouter's OpenAI-compatible layer doesn't expose Anthropic's
        # effort control — sending no extra sampling params and relying on
        # provider defaults until/unless OpenRouter's docs show an
        # equivalent for this model.
        response = _openrouter_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            extra_body={"zdr": True},  # see PRIVACY NOTE above
        )
        return response.choices[0].message.content

    # default: direct Anthropic API
    response = _anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
        output_config={"effort": effort},
    )
    return response.content[0].text


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
